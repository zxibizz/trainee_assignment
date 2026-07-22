"""Data-access layer for products (SQLite)."""

import sqlite3

from app.db import get_connection
from app.schemas import Product, ProductCreate, ProductUpdate


def _row_to_product(row: sqlite3.Row) -> Product:
    return Product(**dict(row))


class ProductRepository:
    """All SQL for the ``products`` table lives here."""

    def _build_filter(
        self,
        *,
        section: str | None,
        name: str | None,
        min_price: float | None,
        max_price: float | None,
        has_discount: bool | None,
    ) -> tuple[str, list]:
        clauses: list[str] = []
        params: list = []
        if section is not None:
            clauses.append("section = ?")
            params.append(section)
        if name is not None:
            # Escape LIKE wildcards so the filter is a literal substring match.
            escaped = (
                name.lower()
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            clauses.append("LOWER(name) LIKE ? ESCAPE '\\'")
            params.append(f"%{escaped}%")
        if min_price is not None:
            clauses.append("price >= ?")
            params.append(min_price)
        if max_price is not None:
            clauses.append("price <= ?")
            params.append(max_price)
        if has_discount is not None:
            clauses.append("discount > 0" if has_discount else "discount = 0")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return where, params

    def list(
        self,
        *,
        section: str | None = None,
        name: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        has_discount: bool | None = None,
        limit: int,
        offset: int,
    ) -> tuple[list[Product], int]:
        """Return a page of products plus the total matching the filter."""
        where, params = self._build_filter(
            section=section,
            name=name,
            min_price=min_price,
            max_price=max_price,
            has_discount=has_discount,
        )
        with get_connection() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM products {where}", params
            ).fetchone()[0]
            rows = conn.execute(
                f"SELECT * FROM products {where} ORDER BY id LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()
        return [_row_to_product(r) for r in rows], total

    def get(self, product_id: int) -> Product | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM products WHERE id = ?", (product_id,)
            ).fetchone()
        return _row_to_product(row) if row is not None else None

    def create(self, body: ProductCreate) -> Product:
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO products (name, section, description, discount, price) "
                "VALUES (?, ?, ?, ?, ?)",
                (body.name, body.section, body.description, body.discount, body.price),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM products WHERE id = ?", (cur.lastrowid,)
            ).fetchone()
        return _row_to_product(row)

    def update(self, product_id: int, body: ProductUpdate) -> Product | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM products WHERE id = ?", (product_id,)
            ).fetchone()
            if row is None:
                return None

            fields = body.model_dump(exclude_unset=True)
            if fields:
                assignments = ", ".join(f"{k} = ?" for k in fields)
                params = list(fields.values()) + [product_id]
                conn.execute(f"UPDATE products SET {assignments} WHERE id = ?", params)
                conn.commit()

            row = conn.execute(
                "SELECT * FROM products WHERE id = ?", (product_id,)
            ).fetchone()
        return _row_to_product(row)

    def delete(self, product_id: int) -> bool:
        with get_connection() as conn:
            cur = conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
        return cur.rowcount > 0
