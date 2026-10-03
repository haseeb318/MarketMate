"""
MarketMate – market_tools.py
Database helpers and CrewAI tools for the MarketMate marketing agent.

Phase 8 additions
─────────────────
- StockGuardError / PostingCapError / FakeClaimsError custom exceptions
- STOCK_THRESHOLD=20, MAX_POSTS_PER_DAY=5 safety constants
- Regex-based fake-claims detection (discount %, 'only X left', wrong price)
- _check_stock_guard / _check_fake_claims / _check_posting_cap helpers
- count_posts_for_date / find_next_available_date public helpers
- save_post_to_queue runs all checks before any INSERT
- All DB connections wrapped in try/finally (connection-leak fix)
- save_post_to_queue returns a str confirmation message (not a bare int)
"""
from __future__ import annotations

import re
import sqlite3
from datetime import date as _date, timedelta
from pathlib import Path
from typing import Any

from crewai.tools import tool

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "marketmate.db"

# ─── Safety constants ─────────────────────────────────────────────────────────
STOCK_THRESHOLD: int = 20   # posts blocked when product stock is below this
MAX_POSTS_PER_DAY: int = 5  # max non-rejected posts per scheduled calendar day


# ─── Custom exceptions ────────────────────────────────────────────────────────
class StockGuardError(ValueError):
    """Raised when a post targets a product whose stock is below STOCK_THRESHOLD."""


class PostingCapError(ValueError):
    """Raised when adding a post would exceed MAX_POSTS_PER_DAY for that date."""


class FakeClaimsError(ValueError):
    """Raised when generated content contains claims not supported by database facts."""


# ─── Fake-claims regex patterns ───────────────────────────────────────────────
# Explicit percentage discounts: '20% off', '30% discount', '15% sale', …
_DISCOUNT_PCT_RE = re.compile(
    r"\b\d{1,3}\s*%\s*(?:off|discount|reduction|sale|rebate|chhoot)\b",
    re.IGNORECASE,
)
# Stock-scarcity phrases: 'only 3 left', 'only 5 remaining', 'only 2 bacha', …
_ONLY_LEFT_RE = re.compile(
    r"\bonly\s+(\d+)\s*(?:units?\s+)?(?:left|remaining|available|bacha?|baqi)\b",
    re.IGNORECASE,
)
# Inline price mentions: 'Rs. 2,999', 'PKR1299', '₨ 500', 'rupees 1800', …
_PRICE_RE = re.compile(
    r"(?:rs\.?|pkr\.?|\u20a8|rupees?)\s*([\d,]+)",
    re.IGNORECASE,
)


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def get_sales_trends(days: int = 30) -> list[dict[str, Any]]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
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
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_inventory() -> list[dict[str, Any]]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT id, name, category, price, cost, stock
            FROM products
            ORDER BY stock ASC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_product_margins() -> list[dict[str, Any]]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                id,
                name,
                price,
                cost,
                ROUND(price - cost, 2)                    AS profit_per_unit,
                ROUND((price - cost) * 100.0 / price, 2) AS margin_percent
            FROM products
            ORDER BY margin_percent DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_upcoming_events(days: int = 30) -> list[dict[str, Any]]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT name, event_date, description
            FROM events
            WHERE event_date BETWEEN date('now') AND date('now', ?)
            ORDER BY event_date ASC
            """,
            (f"+{days} days",),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def ensure_post_queue_table() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS post_queue (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                product        TEXT NOT NULL,
                platform       TEXT NOT NULL,
                scheduled_date TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                content_type   TEXT NOT NULL,
                content        TEXT NOT NULL,
                status         TEXT NOT NULL DEFAULT 'Pending',
                created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


# ─── Posting-cap helpers ──────────────────────────────────────────────────────

def count_posts_for_date(target_date: str) -> int:
    """Return the number of non-rejected posts scheduled for *target_date* (YYYY-MM-DD)."""
    ensure_post_queue_table()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) FROM post_queue
            WHERE scheduled_date = ? AND status != 'Rejected'
            """,
            (target_date,),
        ).fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()


def find_next_available_date(
    start_date: str,
    cap: int = MAX_POSTS_PER_DAY,
) -> str:
    """Return the earliest date on or after *start_date* that still has room under *cap*."""
    current = _date.fromisoformat(start_date)
    for _ in range(14):           # search up to two weeks ahead
        if count_posts_for_date(current.isoformat()) < cap:
            return current.isoformat()
        current += timedelta(days=1)
    return current.isoformat()    # fallback: two-plus weeks out


# ─── Private safety helpers ───────────────────────────────────────────────────

def _get_product_price(product_name: str) -> float | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT price FROM products WHERE LOWER(name) = LOWER(?)",
            (product_name,),
        ).fetchone()
        return float(row[0]) if row else None
    finally:
        conn.close()


def _get_product_stock(product_name: str) -> int | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT stock FROM products WHERE LOWER(name) = LOWER(?)",
            (product_name,),
        ).fetchone()
        return int(row[0]) if row else None
    finally:
        conn.close()


def _check_stock_guard(product_name: str) -> None:
    """Raise StockGuardError when the product's stock is below STOCK_THRESHOLD."""
    stock = _get_product_stock(product_name)
    if stock is not None and stock < STOCK_THRESHOLD:
        raise StockGuardError(
            f"Stock guard blocked post for '{product_name}': "
            f"only {stock} units in stock (threshold: {STOCK_THRESHOLD}). "
            "Remove this product from the campaign or replenish stock first."
        )


def _check_fake_claims(product_name: str, content: str) -> None:
    """Raise FakeClaimsError if content contains claims not backed by database facts."""
    violations: list[str] = []

    # 1. Percentage discounts — no discount data exists in DB
    if _DISCOUNT_PCT_RE.search(content):
        violations.append(
            "percentage discount claim (e.g. '20% off') — "
            "no discount data exists in the database"
        )

    # 2. 'Only X left' stock-scarcity claims
    m = _ONLY_LEFT_RE.search(content)
    if m:
        claimed = int(m.group(1))
        real_stock = _get_product_stock(product_name)
        tolerance = max(5, int((real_stock or 0) * 0.10))
        if real_stock is None or abs(claimed - real_stock) > tolerance:
            violations.append(
                f"stock-scarcity claim 'only {claimed} left' — "
                f"database stock for '{product_name}' is {real_stock}"
            )

    # 3. Explicit price claims that don't match the database price
    real_price = _get_product_price(product_name)
    if real_price is not None:
        for price_m in _PRICE_RE.finditer(content):
            raw = price_m.group(1).replace(",", "")
            if raw.isdigit():
                claimed_price = int(raw)
                if abs(claimed_price - real_price) > 50:   # ±50 PKR rounding tolerance
                    violations.append(
                        f"price claim '{price_m.group()}' — "
                        f"database price for '{product_name}' is Rs. {real_price:.0f}"
                    )
                    break

    if violations:
        raise FakeClaimsError(
            f"Post for '{product_name}' contains unsupported claims: "
            + "; ".join(violations)
            + ". Use only facts provided by the data tools."
        )


def _check_posting_cap(scheduled_date: str) -> None:
    """Raise PostingCapError when the daily cap would be exceeded."""
    current_count = count_posts_for_date(scheduled_date)
    if current_count >= MAX_POSTS_PER_DAY:
        next_date = find_next_available_date(scheduled_date)
        raise PostingCapError(
            f"Daily cap of {MAX_POSTS_PER_DAY} posts reached for {scheduled_date}. "
            f"Next available date: {next_date}. "
            "Please reschedule this post to that date."
        )

# ─── CrewAI tool ─────────────────────────────────────────────────────────────

@tool("save_post_to_queue")
def save_post_to_queue(
    product: str,
    platform: str,
    scheduled_date: str,
    scheduled_time: str,
    content_type: str,
    content: str,
) -> str:
    """
    Save a marketing post to the MarketMate approval queue.

    Safety checks applied before saving (all raise informative errors on failure):
      - Stock guard    : blocks posts for products below STOCK_THRESHOLD units
      - Fake claims    : blocks invented discounts, prices, or scarcity claims
      - Posting cap    : blocks posts that would exceed MAX_POSTS_PER_DAY for that date

    Returns a confirmation string with the new post ID on success.
    """
    ensure_post_queue_table()

    # ── Phase 8 safety gates ──────────────────────────────────────────────────
    _check_stock_guard(product)
    _check_fake_claims(product, content)
    _check_posting_cap(scheduled_date)
    # ─────────────────────────────────────────────────────────────────────────

    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO post_queue
                (product, platform, scheduled_date, scheduled_time,
                 content_type, content, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending')
            """,
            (product, platform, scheduled_date, scheduled_time, content_type, content),
        )
        conn.commit()
        post_id = cursor.lastrowid
    finally:
        conn.close()

    return (
        f"Post saved successfully (ID: {post_id}). "
        f"Product: {product} | Platform: {platform} | "
        f"Scheduled: {scheduled_date} at {scheduled_time}."
    )


# ─── Queue management ─────────────────────────────────────────────────────────

def get_post_queue(status: str | None = None) -> list[dict[str, Any]]:
    ensure_post_queue_table()
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        if status:
            rows = conn.execute(
                """
                SELECT * FROM post_queue
                WHERE status = ?
                ORDER BY scheduled_date, scheduled_time
                """,
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM post_queue
                ORDER BY scheduled_date, scheduled_time
                """
            ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_post_status(post_id: int, status: str) -> None:
    ensure_post_queue_table()
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE post_queue SET status = ? WHERE id = ?",
            (status, post_id),
        )
        conn.commit()
    finally:
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