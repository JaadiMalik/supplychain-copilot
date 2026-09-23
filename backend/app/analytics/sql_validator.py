import sqlglot
from sqlglot import exp

from app.analytics.dataset_service import get_database_schema


BLOCKED_WORDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "COPY",
    "ATTACH",
    "DETACH",
    "INSTALL",
    "LOAD",
    "EXPORT",
    "IMPORT",
    "PRAGMA",
]


def validate_sql(
    sql: str,
) -> tuple[bool, str]:

    cleaned_sql = sql.strip()

    if not cleaned_sql:
        return False, "SQL is empty."

    upper_sql = cleaned_sql.upper()

    # -----------------------------
    # Block dangerous operations
    # -----------------------------

    for word in BLOCKED_WORDS:

        if word in upper_sql:
            return (
                False,
                f"Blocked SQL operation: {word}",
            )

    # -----------------------------
    # Parse SQL
    # -----------------------------

    try:
        parsed = sqlglot.parse(
            cleaned_sql,
            read="duckdb",
        )

    except Exception as error:
        return (
            False,
            f"Invalid SQL: {error}",
        )

    if len(parsed) != 1:
        return (
            False,
            "Only one SQL statement is allowed.",
        )

    statement = parsed[0]

    if not isinstance(
        statement,
        exp.Select,
    ):
        return (
            False,
            "Only SELECT queries are allowed.",
        )

    # -----------------------------
    # Get allowed DuckDB tables
    # -----------------------------

    schema = get_database_schema()

    allowed_tables = {
        item["table_name"]
        for item in schema
    }

    # -----------------------------
    # Check every table referenced
    # -----------------------------

    referenced_tables = {
        table.name
        for table in statement.find_all(
            exp.Table
        )
    }

    unknown_tables = (
        referenced_tables
        - allowed_tables
    )

    if unknown_tables:
        return (
            False,
            "Unknown table(s): "
            + ", ".join(
                sorted(unknown_tables)
            ),
        )

    return True, "SQL is safe."