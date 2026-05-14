import csv
import io
import json
import logging
import os
import ollama
from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_session
from app.database import get_db
from app.models import Session, Transaction, ChartOfAccount

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/bank-statements', tags=['bank-statements'])

OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')


def _parse_confidence(val: Any) -> float:
    if val is None:
        return 0.0
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return max(0.0, min(1.0, float(val)))
    if isinstance(val, str):
        return max(0.0, min(1.0, float(val.strip())))
    raise ValueError('confidence must be a number')


def _normalize_llm_classification(raw: dict) -> dict:
    """Accept common LLM JSON variants (numeric codes, string confidence, camelCase)."""
    if not isinstance(raw, dict):
        raise ValueError('Response is not a JSON object')

    code = raw.get('account_code')
    if code is None:
        code = raw.get('accountCode') or raw.get('code')

    if code is None or code == '':
        return {'account_code': None, 'confidence': _parse_confidence(raw.get('confidence', raw.get('score')))}

    if isinstance(code, bool):
        raise ValueError('Invalid account_code')
    if isinstance(code, (int, float)):
        f = float(code)
        acct = str(int(f)) if f == int(f) else str(code).strip()
    elif isinstance(code, str):
        acct = code.strip()
    else:
        raise ValueError('account_code has invalid type')

    conf = _parse_confidence(raw.get('confidence', raw.get('score')))
    return {'account_code': acct, 'confidence': conf}


async def classify_transaction(description: str, amount: float, accounts: List[dict]) -> dict:
    accounts_text = '\n'.join([f"- {a['code']} {a['name']} ({a['type']})" for a in accounts])
    system_prompt = (
        'You are a precise accounting AI. Given a bank transaction and a chart of accounts, '
        'pick the single best account code from the chart.\n\n'
        'Reply with one JSON object only, with exactly these keys:\n'
        '- "account_code": a string, the chart code only (e.g. "6100"), or null if none fits.\n'
        '- "confidence": a number from 0 to 1.\n\n'
        f'Chart of Accounts:\n{accounts_text}'
    )
    user_prompt = f'Transaction: {description}\nAmount: {amount:.2f}'

    try:
        client = ollama.AsyncClient()
        response = await client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            format='json',
            options={'temperature': 0.0}
        )
        raw = json.loads(response['message']['content'])
        return _normalize_llm_classification(raw)
    except Exception as e:
        logger.warning('Classification failed: %s', e)
        return {'account_code': None, 'confidence': 0.0, 'error': str(e)}

@router.post('/classify')
async def classify_bank_statement(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), session: Session = Depends(get_current_session)):
    # Validate type file
    if not file.filename.lower().endswith('csv'):
        raise HTTPException(400, 'Only CSV files are supported')

    # Load session's chart of accounts
    result = await db.execute(ChartOfAccount.__table__.select().where(ChartOfAccount.session_id == session.id))
    accounts = [{'code': r.code, 'name': r.name, 'type': r.type} for r in result]
    if not accounts:
        raise HTTPException(400, 'No chart of accounts — seed data first')

    # Parse CSV
    contents = await file.read()
    try:
        text = contents.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(400, 'File must be UTF-8 encoded')

    csv_reader = csv.reader(io.StringIO(text))
    rows = list(csv_reader)
    if not rows:
        raise HTTPException(400, 'CSV file is empty')

    # Detect header row (must contain 'date' and 'amount') 
    header_idx = None
    for i, row in enumerate(rows):
        row_lower = [c.lower().strip() for c in row]
        if 'date' in row_lower and ('amount' in row_lower or 'sum' in row_lower):
            header_idx = i
            break

    if header_idx is None:
        raise HTTPException(400, "CSV must have a header row with 'Date' and 'Amount' columns")

    headers = [h.lower().strip() for h in rows[header_idx]]
    date_col = headers.index('date')
    desc_col = next((headers.index(c) for c in ['description', 'memo', 'narrative', 'payee', 'text'] if c in headers), 1)
    amount_col = headers.index('amount') if 'amount' in headers else 2
    data_rows = rows[header_idx + 1:]

    # SSE streaming + classification + DB insert
    async def event_generator():
        transactions_to_create = []
        total = len(data_rows)

        for idx, row in enumerate(data_rows):
            try:
                date_str = row[date_col].strip()
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                description = row[desc_col].strip() if len(row) > desc_col else ''
                amount_str = (row[amount_col].strip().replace(',', '').replace('€', '').replace('$', ''))
                amount = float(amount_str)
            except (ValueError, IndexError) as e:
                yield f'data: {json.dumps({'event': 'error', 'row': idx+1, 'error': f'Bad data: {e}'})}\n\n'
                continue

            classification = await classify_transaction(description, amount, accounts)
            acct_code = classification.get('account_code')
            confidence = classification.get('confidence', 0.0)

            event = {
                'event': 'progress',
                'row': idx+1,
                'total': total,
                'description': description,
                'amount': amount,
                'account_code': acct_code,
                'confidence': confidence,
            }
            yield f'data: {json.dumps(event)}\n\n'

            if acct_code:
                account = next((a for a in accounts if a['code'] == acct_code), None)
                if account:
                    transactions_to_create.append(
                        {
                            'session_id': session.id,
                            'date': parsed_date,
                            'description': description,
                            'amount': amount,
                            'currency': 'USD',
                            'source': 'BANK_STATEMENT',
                            'status': 'unposted',
                        }
                    )
                else:
                    yield f'data: {json.dumps({'event': 'error', 'row': idx+1, 'error': f'Unknown account code: {acct_code}'})}\n\n'

        if transactions_to_create:
            await db.execute(insert(Transaction), transactions_to_create)
            await db.commit()
            yield f'data: {json.dumps({'event': 'complete', 'created': len(transactions_to_create)})}\n\n'
        else:
            yield f'data: {json.dumps({'event': 'complete', 'created': 0})}\n\n'

    return StreamingResponse(event_generator(), media_type='text/event-stream')