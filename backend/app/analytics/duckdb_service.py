from pathlib import Path
import duckdb


DB_PATH = Path("data/supplychain.duckdb")


def get_connection():
    return duckdb.connect(str(DB_PATH))


def load_inventory_csv(csv_path: str):
    connection = get_connection()

    connection.execute(
        """
        CREATE OR REPLACE TABLE inventory AS
        SELECT *
        FROM read_csv_auto(?)
        """,
        [csv_path],
    )

    connection.close()


def get_inventory_preview():
    connection = get_connection()

    result = connection.execute(
        """
        SELECT *
        FROM inventory
        LIMIT 10
        """
    ).fetchdf()

    connection.close()

    return result
def get_items_below_reorder():
    connection = get_connection()

    result = connection.execute(
        """
        SELECT
            sku,
            product,
            quantity,
            reorder_level,
            reorder_level - quantity AS shortage
        FROM inventory
        WHERE quantity < reorder_level
        ORDER BY shortage DESC
        """
    ).fetchdf()

    connection.close()

    return result
def execute_read_only_query(sql: str):
    connection = get_connection()

    try:
        result = connection.execute(sql).fetchdf()

        return result

    finally:
        connection.close()