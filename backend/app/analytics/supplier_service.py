import re
from datetime import datetime

from app.analytics.duckdb_service import get_connection


def normalize_supplier_name(name: str) -> str:
    """
    Normalize supplier names for registry lookup only.

    This function does NOT decide whether two companies
    are the same legal entity.
    """

    value = name.lower().strip()

    value = re.sub(
        r"[^\w\s]",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def ensure_supplier_registry():
    """
    Create the supplier alias registry if required.
    """

    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS supplier_alias_registry (
            alias_key VARCHAR PRIMARY KEY,
            alias_name VARCHAR,
            canonical_name VARCHAR,
            created_at TIMESTAMP
        )
        """
    )

    connection.close()


def add_supplier_alias(
    alias_name: str,
    canonical_name: str,
) -> dict:
    """
    Add or update an explicit supplier alias.
    """

    ensure_supplier_registry()

    alias_name = alias_name.strip()
    canonical_name = canonical_name.strip()

    if not alias_name:
        raise ValueError(
            "Alias name is required."
        )

    if not canonical_name:
        raise ValueError(
            "Canonical supplier name is required."
        )

    alias_key = normalize_supplier_name(
        alias_name
    )

    connection = get_connection()

    connection.execute(
        """
        DELETE FROM supplier_alias_registry
        WHERE alias_key = ?
        """,
        [alias_key],
    )

    connection.execute(
        """
        INSERT INTO supplier_alias_registry (
            alias_key,
            alias_name,
            canonical_name,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        [
            alias_key,
            alias_name,
            canonical_name,
            datetime.now(),
        ],
    )

    connection.close()

    return {
        "alias_name": alias_name,
        "canonical_name": canonical_name,
        "resolved": True,
    }


def resolve_supplier(
    supplier_name: str,
) -> dict:
    """
    Resolve an operational supplier name to its
    canonical/legal supplier name.
    """

    ensure_supplier_registry()

    alias_key = normalize_supplier_name(
        supplier_name
    )

    connection = get_connection()

    row = connection.execute(
        """
        SELECT
            alias_name,
            canonical_name
        FROM supplier_alias_registry
        WHERE alias_key = ?
        """,
        [alias_key],
    ).fetchone()

    connection.close()

    if row:
        return {
            "original_name": supplier_name,
            "canonical_name": row[1],
            "alias_resolved": True,
        }

    return {
        "original_name": supplier_name,
        "canonical_name": supplier_name,
        "alias_resolved": False,
    }


def list_supplier_aliases() -> list[dict]:
    """
    Return all supplier aliases.
    """

    ensure_supplier_registry()

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            alias_name,
            canonical_name,
            created_at
        FROM supplier_alias_registry
        ORDER BY alias_name
        """
    ).fetchall()

    connection.close()

    return [
        {
            "alias_name": row[0],
            "canonical_name": row[1],
            "created_at": str(row[2]),
        }
        for row in rows
    ]


def delete_supplier_alias(
    alias_name: str,
) -> dict:
    """
    Delete one supplier alias.
    """

    ensure_supplier_registry()

    alias_key = normalize_supplier_name(
        alias_name
    )

    connection = get_connection()

    existing = connection.execute(
        """
        SELECT alias_name, canonical_name
        FROM supplier_alias_registry
        WHERE alias_key = ?
        """,
        [alias_key],
    ).fetchone()

    if not existing:
        connection.close()

        return {
            "deleted": False,
            "alias_name": alias_name,
        }

    connection.execute(
        """
        DELETE FROM supplier_alias_registry
        WHERE alias_key = ?
        """,
        [alias_key],
    )

    connection.close()

    return {
        "deleted": True,
        "alias_name": existing[0],
        "canonical_name": existing[1],
    }