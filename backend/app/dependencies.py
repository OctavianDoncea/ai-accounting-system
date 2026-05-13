from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import session
from app.database import get_db
from app import models
from sqlalchemy import select

async def get_current_session(x_session_id: int = Header(..., alias='X-Session-ID'), db: AsyncSession = Depends(get_db)) -> models.Session:
    result = await db.execute(select(models.Session).where(models.Session.id == x_session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail='Session not found')

    return session