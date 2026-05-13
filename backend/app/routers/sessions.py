from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import models, schemas

router = APIRouter()

@router.post('/sessions/', response_model=schemas.SessionOut)
async def create_session(name: str, db: AsyncSession = Depends(get_db)):
    session = models.Session(name=name)
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return session

@router.get('/sessions/', response_model=list[schemas.SessionOut])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(models.Session.__table__.select())
    return result.all()