from contextlib import contextmanager
import os
import sqlite3
from app.logger import get_logger
from app.models import ExpenseCreate

logger = get_logger(__name__)
DB_PATH = os.getenv("DB_PATH", "expenses.db")


@contextmanager
def get_connection():
  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row
  try:
    yield conn
    conn.commit()
  except sqlite3.Error as exc:
    conn.rollback()
    logger.exception("Database transaction failed: %s", exc)
    raise
  finally:
    conn.close()


def init_db() -> None:
  with get_connection() as conn:
    conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                spent_on TEXT NOT NULL,
                notes TEXT DEFAULT ''
            )
            """)
  logger.info("Database initialized at %s", DB_PATH)


def add_expense(item: ExpenseCreate) -> dict:
  with get_connection() as conn:
    cur = conn.execute(
        """
            INSERT INTO expenses (title, category, amount, spent_on, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
        (
            item.title.strip(),
            item.category.strip(),
            round(item.amount, 2),
            item.spent_on.isoformat(),
            item.notes.strip(),
        ),
    )
    row = conn.execute(
        "SELECT * FROM expenses WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    logger.info(
        "Added expense id=%s amount=%.2f", row["id"], row["amount"]
    )
    return dict(row)


def list_expenses(category: str | None = None) -> list[dict]:
  with get_connection() as conn:
    if category:
      rows = conn.execute(
          "SELECT * FROM expenses WHERE LOWER(category) = LOWER(?) ORDER BY"
          " spent_on DESC, id DESC",
          (category.strip(),),
      ).fetchall()
    else:
      rows = conn.execute(
          "SELECT * FROM expenses ORDER BY spent_on DESC, id DESC"
      ).fetchall()
    return [dict(r) for r in rows]


def delete_expense(expense_id: int) -> bool:
  with get_connection() as conn:
    cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    deleted = cur.rowcount > 0
    if deleted:
      logger.info("Deleted expense id=%s", expense_id)
    return deleted


def get_summary() -> dict:
  with get_connection() as conn:
    total_row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count FROM"
        " expenses"
    ).fetchone()
    cat_rows = conn.execute("""
            SELECT category, ROUND(SUM(amount), 2) AS total
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
            """).fetchall()
    return {
        "total_spent": round(float(total_row["total"]), 2),
        "transaction_count": int(total_row["count"]),
        "by_category": [dict(r) for r in cat_rows],
    }
