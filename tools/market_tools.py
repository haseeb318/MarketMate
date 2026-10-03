import sqlite3
from pathlib import Path
from typing import Any
from crewai.tools import tool
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "marketmate.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_sales_trends(days: int = 30) -> list[dict[str, Any]]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT
            p.name AS product,
            p.category,
            SUM(o.quantity) AS units_sold,
            SUM(o.revenue) AS revenue
        FROM orders o
        JOIN products p ON p.id = o.product_id
        WHERE o.order_date >= date('now', ?)
        GROUP BY p.id
        ORDER BY units_sold DESC
        """,
        (f"-{days} days",),
    ).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def get_inventory() -> list[dict[str, Any]]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT
            id,
            name,
            category,
            price,
            cost,
            stock
        FROM products
        ORDER BY stock ASC
        """
    ).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def get_product_margins() -> list[dict[str, Any]]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT
            id,
            name,
            price,
            cost,
            ROUND(price - cost, 2) AS profit_per_unit,
            ROUND((price - cost) * 100.0 / price, 2) AS margin_percent
        FROM products
        ORDER BY margin_percent DESC
        """
    ).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def get_upcoming_events(days: int = 30) -> list[dict[str, Any]]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT
            name,
            event_date,
            description
        FROM events
        WHERE event_date BETWEEN date('now')
        AND date('now', ?)
        ORDER BY event_date ASC
        """,
        (f"+{days} days",),
    ).fetchall()

    conn.close()
    return [dict(row) for row in rows]
def ensure_post_queue_table() -> None:
    conn = get_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS post_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT NOT NULL,
            platform TEXT NOT NULL,
            scheduled_date TEXT NOT NULL,
            scheduled_time TEXT NOT NULL,
            content_type TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()

@tool("save_post_to_queue")
def save_post_to_queue(
    product: str,
    platform: str,
    scheduled_date: str,
    scheduled_time: str,
    content_type: str,
    content: str,
) -> int:
    """Save a marketing post to the MarketMate approval queue."""
    ensure_post_queue_table()

    conn = get_connection()

    cursor = conn.execute(
        """
        INSERT INTO post_queue
        (
            product,
            platform,
            scheduled_date,
            scheduled_time,
            content_type,
            content,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, 'Pending')
        """,
        (
            product,
            platform,
            scheduled_date,
            scheduled_time,
            content_type,
            content,
        ),
    )

    conn.commit()
    post_id = cursor.lastrowid
    conn.close()

    return post_id


def get_post_queue(status: str | None = None) -> list[dict[str, Any]]:
    ensure_post_queue_table()

    conn = get_connection()
    conn.row_factory = sqlite3.Row

    if status:
        rows = conn.execute(
            """
            SELECT *
            FROM post_queue
            WHERE status = ?
            ORDER BY scheduled_date, scheduled_time
            """,
            (status,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT *
            FROM post_queue
            ORDER BY scheduled_date, scheduled_time
            """
        ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def update_post_status(post_id: int, status: str) -> None:
    ensure_post_queue_table()

    conn = get_connection()

    conn.execute(
        """
        UPDATE post_queue
        SET status = ?
        WHERE id = ?
        """,
        (status, post_id),
    )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("MarketMate tools test")
    print("=" * 40)

    print("\nSales trends:")
    print(get_sales_trends())

    print("\nInventory:")
    print(get_inventory())

    print("\nProduct margins:")
    print(get_product_margins())

    print("\nUpcoming events:")
    print(get_upcoming_events())