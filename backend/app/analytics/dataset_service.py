import json
import re
from pathlib import Path
from datetime import datetime
from app.utils.json_utils import clean_json_data

import pandas as pd

from app.analytics.duckdb_service import get_connection


# ==================================================
# Helper: safe SQL identifier
# ==================================================

def safe_identifier(value: str) -> str:
    """
    Convert filenames and sheet names into safe DuckDB table names.

    Example:
    "Purchase Orders" -> "purchase_orders"
    """

    value = value.lower().strip()

    value = re.sub(
        r"[^a-z0-9_]+",
        "_",
        value,
    )

    value = re.sub(
        r"_+",
        "_",
        value,
    )

    value = value.strip("_")

    if not value:
        value = "dataset"

    # SQL table names should not start with a number
    if value[0].isdigit():
        value = f"data_{value}"

    return value


# ==================================================
# Helper: normalize dataframe data types
# ==================================================

def normalize_dataframe_types(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Detect common date columns and convert them
    from strings into real datetime values.

    Example:
    planned_date -> datetime64
    actual_date  -> datetime64
    order_date   -> datetime64
    """

    dataframe = dataframe.copy()

    for column in dataframe.columns:
        column_name = str(column).lower()

        # Detect likely date/time columns
        is_date_column = (
            "date" in column_name
            or column_name.endswith("_at")
            or "timestamp" in column_name
        )

        if not is_date_column:
            continue

        try:
            converted = pd.to_datetime(
                dataframe[column],
                errors="coerce",
            )

            # Only replace the original column if
            # at least one valid date was detected.
            if converted.notna().any():
                dataframe[column] = converted

        except Exception:
            # Keep original values if conversion fails
            pass

    return dataframe


# ==================================================
# Dataset registry
# ==================================================

def ensure_registry():
    """
    Create a small DuckDB metadata table that tracks
    every uploaded CSV/XLSX dataset.
    """

    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS dataset_registry (
            table_name VARCHAR PRIMARY KEY,
            source_file VARCHAR,
            source_type VARCHAR,
            sheet_name VARCHAR,
            row_count BIGINT,
            columns_json VARCHAR,
            uploaded_at TIMESTAMP
        )
        """
    )

    connection.close()


# ==================================================
# Store dataframe in DuckDB
# ==================================================

def store_dataframe(
    dataframe: pd.DataFrame,
    table_name: str,
    source_file: str,
    source_type: str,
    sheet_name: str | None = None,
):
    """
    Store a pandas DataFrame as a DuckDB table
    and register its metadata.
    """

    # Convert obvious date columns first
    dataframe = normalize_dataframe_types(
        dataframe
    )

    connection = get_connection()

    # Register dataframe temporarily inside DuckDB
    connection.register(
        "incoming_dataframe",
        dataframe,
    )

    # table_name has already been sanitized
    connection.execute(
        f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT *
        FROM incoming_dataframe
        """
    )

    connection.unregister(
        "incoming_dataframe"
    )

    # Build column metadata
    columns = []

    for column in dataframe.columns:
        columns.append(
            {
                "name": str(column),
                "dtype": str(
                    dataframe[column].dtype
                ),
            }
        )

    # Remove old registry entry if the same table
    # is uploaded again.
    connection.execute(
        """
        DELETE FROM dataset_registry
        WHERE table_name = ?
        """,
        [table_name],
    )

    # Insert fresh metadata
    connection.execute(
        """
        INSERT INTO dataset_registry (
            table_name,
            source_file,
            source_type,
            sheet_name,
            row_count,
            columns_json,
            uploaded_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            table_name,
            source_file,
            source_type,
            sheet_name,
            len(dataframe),
            json.dumps(columns),
            datetime.now(),
        ],
    )

    connection.close()

    return {
        "table_name": table_name,
        "sheet_name": sheet_name,
        "rows": len(dataframe),
        "columns": columns,
    }


# ==================================================
# Load CSV
# ==================================================

def load_csv(
    file_path: Path,
) -> dict:
    """
    Load one CSV file into DuckDB.
    """

    dataframe = pd.read_csv(
        file_path
    )

    table_name = safe_identifier(
        file_path.stem
    )

    result = store_dataframe(
        dataframe=dataframe,
        table_name=table_name,
        source_file=file_path.name,
        source_type="csv",
    )

    return {
        "filename": file_path.name,
        "type": "csv",
        "tables": [
            result
        ],
    }


# ==================================================
# Load Excel
# ==================================================

def load_excel(
    file_path: Path,
) -> dict:
    """
    Load every worksheet from an XLSX workbook.

    One sheet:
        inventory.xlsx
        -> inventory

    Multiple sheets:
        operations.xlsx
        Inventory
        Shipments

        -> operations_inventory
        -> operations_shipments
    """

    excel_file = pd.ExcelFile(
        file_path,
        engine="openpyxl",
    )

    sheet_names = (
        excel_file.sheet_names
    )

    tables = []

    for sheet_name in sheet_names:

        dataframe = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            engine="openpyxl",
        )

        # Skip completely empty sheets
        if dataframe.empty:
            continue

        # One-sheet workbook
        if len(sheet_names) == 1:

            table_name = safe_identifier(
                file_path.stem
            )

        # Multi-sheet workbook
        else:

            table_name = safe_identifier(
                f"{file_path.stem}_{sheet_name}"
            )

        result = store_dataframe(
            dataframe=dataframe,
            table_name=table_name,
            source_file=file_path.name,
            source_type="xlsx",
            sheet_name=sheet_name,
        )

        tables.append(
            result
        )

    return {
        "filename": file_path.name,
        "type": "xlsx",
        "tables": tables,
    }


# ==================================================
# Main ingestion function
# ==================================================

def ingest_structured_file(
    file_path: Path,
) -> dict:
    """
    Detect file type and import it into DuckDB.
    """

    ensure_registry()

    extension = (
        file_path.suffix.lower()
    )

    if extension == ".csv":
        return load_csv(
            file_path
        )

    if extension == ".xlsx":
        return load_excel(
            file_path
        )

    raise ValueError(
        "Only CSV and XLSX files are supported."
    )


# ==================================================
# List datasets
# ==================================================

def list_datasets() -> list[dict]:
    """
    Return metadata for every imported dataset.
    """

    ensure_registry()

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            table_name,
            source_file,
            source_type,
            sheet_name,
            row_count,
            columns_json,
            uploaded_at
        FROM dataset_registry
        ORDER BY uploaded_at DESC
        """
    ).fetchall()

    connection.close()

    datasets = []

    for row in rows:

        datasets.append(
            {
                "table_name": row[0],
                "source_file": row[1],
                "source_type": row[2],
                "sheet_name": row[3],
                "row_count": row[4],
                "columns": json.loads(
                    row[5]
                ),
                "uploaded_at": str(
                    row[6]
                ),
            }
        )

    return datasets


# ==================================================
# Get one dataset preview
# ==================================================

def get_dataset_preview(
    table_name: str,
    limit: int = 10,
) -> dict | None:
    """
    Return dataset metadata and the first N rows.
    """

    ensure_registry()

    safe_name = safe_identifier(
        table_name
    )

    connection = get_connection()

    metadata = connection.execute(
        """
        SELECT
            table_name,
            source_file,
            source_type,
            sheet_name,
            row_count,
            columns_json
        FROM dataset_registry
        WHERE table_name = ?
        """,
        [safe_name],
    ).fetchone()

    if not metadata:
        connection.close()
        return None

    # Prevent huge previews
    limit = max(
        1,
        min(
            limit,
            100,
        ),
    )

    dataframe = connection.execute(
        f"""
        SELECT *
        FROM {safe_name}
        LIMIT {limit}
        """
    ).fetchdf()

    connection.close()

    return {
        "table_name": metadata[0],
        "source_file": metadata[1],
        "source_type": metadata[2],
        "sheet_name": metadata[3],
        "row_count": metadata[4],
        "columns": json.loads(
            metadata[5]
        ),
        "preview": clean_json_data(
    dataframe.to_dict(
        orient="records"
    )
),
    }


# ==================================================
# Dynamic database schema
# ==================================================

def get_database_schema() -> list[dict]:
    """
    Return all registered DuckDB tables and their columns.

    This is used by Qwen so SQL generation is based on
    the actual uploaded datasets rather than a hardcoded schema.
    """

    ensure_registry()

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            table_name,
            source_file,
            sheet_name,
            columns_json
        FROM dataset_registry
        ORDER BY table_name
        """
    ).fetchall()

    connection.close()

    schema = []

    for row in rows:

        schema.append(
            {
                "table_name": row[0],
                "source_file": row[1],
                "sheet_name": row[2],
                "columns": json.loads(
                    row[3]
                ),
            }
        )

    return schema