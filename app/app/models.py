from datetime import date
from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
  title: str = Field(..., min_length=1, max_length=100)
  category: str = Field(..., min_length=1, max_length=50)
  amount: float = Field(..., gt=0)
  spent_on: date = Field(default_factory=date.today)
  notes: str = Field(default="", max_length=250)


class ExpenseOut(ExpenseCreate):
  id: int
