from contextlib import asynccontextmanager
from pathlib import Path
from app.database import add_expense, delete_expense, get_summary, init_db, list_expenses
from app.logger import get_logger
from app.models import ExpenseCreate, ExpenseOut
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

logger = get_logger(__name__)
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
  init_db()
  yield


app = FastAPI(
    title="Expense Tracker Capstone",
    version="1.0.0",
    lifespan=lifespan,
)

if STATIC_DIR.exists():
  app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def serve_frontend():
  return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/expenses", response_model=list[ExpenseOut])
def api_list_expenses(category: str | None = None):
  return list_expenses(category)


@app.post(
    "/api/expenses",
    response_model=ExpenseOut,
    status_code=status.HTTP_201_CREATED,
)
def api_create_expense(payload: ExpenseCreate):
  try:
    return add_expense(payload)
  except Exception as exc:
    logger.error("Failed to create expense: %s", exc)
    raise HTTPException(
        status_code=500, detail="Could not save expense."
    ) from exc


@app.delete("/api/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_expense(expense_id: int):
  if not delete_expense(expense_id):
    raise HTTPException(status_code=404, detail="Expense not found.")


@app.get("/api/summary")
def api_summary():
  return get_summary()
