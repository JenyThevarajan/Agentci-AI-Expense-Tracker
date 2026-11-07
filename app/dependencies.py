"""Wire HTTP dependencies to the expense service."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.repository import SqlAlchemyExpenseRepository
from app.service import ExpenseService


def get_service(session: Session = Depends(get_session)) -> ExpenseService:
    return ExpenseService(SqlAlchemyExpenseRepository(session))
