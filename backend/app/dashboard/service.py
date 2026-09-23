from pathlib import Path

from app.analytics.duckdb_service import get_connection
from app.analytics.dataset_service import list_datasets
from app.analytics.supplier_service import list_supplier_aliases
from app.config import DATA_DIR
from app.rag.vector_store import get_document_records


DOCUMENT_DIR = DATA_DIR / "documents"


def find_dataset(
    datasets: list[dict],
    required_columns: set[str],
) -> dict | None:
    """
    Find the newest dataset containing all required columns.

    This keeps the dashboard independent of specific filenames.
    """

    for dataset in datasets:
        columns = {
            column["name"]
            for column in dataset.get(
                "columns",
                [],
            )
        }

        if required_columns.issubset(
            columns
        ):
            return dataset

    return None


def get_document_stats() -> dict:
    """
    Count PDFs, pages and vector chunks.
    """

    DOCUMENT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pdf_files = list(
        DOCUMENT_DIR.glob("*.pdf")
    )

    total_chunks = 0
    total_pages = set()

    for pdf_file in pdf_files:
        try:
            records = get_document_records(
                pdf_file.name
            )

            ids = records.get(
                "ids",
                [],
            )

            metadatas = records.get(
                "metadatas",
                [],
            )

            total_chunks += len(ids)

            for metadata in metadatas:
                if metadata:
                    page = metadata.get(
                        "page"
                    )

                    if page is not None:
                        total_pages.add(
                            (
                                pdf_file.name,
                                page,
                            )
                        )

        except Exception:
            # Dashboard should still load even if one
            # document has a metadata problem.
            continue

    return {
        "documents": len(pdf_files),
        "pages": len(total_pages),
        "chunks": total_chunks,
    }


def get_dashboard_summary() -> dict:
    """
    Build deterministic operational dashboard KPIs.
    """

    datasets = list_datasets()

    aliases = list_supplier_aliases()

    document_stats = (
        get_document_stats()
    )

    connection = get_connection()

    # ==============================================
    # Find useful operational tables dynamically
    # ==============================================

    shipment_dataset = find_dataset(
        datasets,
        {
            "shipment_id",
            "status",
            "planned_date",
        },
    )

    purchase_order_dataset = find_dataset(
        datasets,
        {
            "po_number",
            "status",
            "ordered_qty",
            "received_qty",
            "unit_cost",
        },
    )

    inventory_dataset = find_dataset(
        datasets,
        {
            "sku",
            "quantity",
            "reorder_level",
        },
    )

    # ==============================================
    # Defaults
    # ==============================================

    delayed_shipments = 0
    open_purchase_orders = 0
    low_stock_items = 0
    open_po_outstanding_value = 0

    # ==============================================
    # Delayed shipments
    # ==============================================

    if shipment_dataset:
        table_name = (
            shipment_dataset[
                "table_name"
            ]
        )

        delayed_shipments = (
            connection.execute(
                f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE LOWER(status)
                IN (
                    'delayed',
                    'delivered late'
                )
                """
            ).fetchone()[0]
        )

    # ==============================================
    # Open purchase orders
    # ==============================================

    if purchase_order_dataset:
        table_name = (
            purchase_order_dataset[
                "table_name"
            ]
        )

        open_purchase_orders = (
            connection.execute(
                f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE LOWER(status) = 'open'
                """
            ).fetchone()[0]
        )

        result = connection.execute(
            f"""
            SELECT
                COALESCE(
                    SUM(
                        GREATEST(
                            ordered_qty
                            - COALESCE(
                                received_qty,
                                0
                            ),
                            0
                        )
                        * unit_cost
                    ),
                    0
                )
            FROM {table_name}
            WHERE LOWER(status) = 'open'
            """
        ).fetchone()

        open_po_outstanding_value = (
            result[0] or 0
        )

    # ==============================================
    # Low-stock items
    # ==============================================

    if inventory_dataset:
        table_name = (
            inventory_dataset[
                "table_name"
            ]
        )

        low_stock_items = (
            connection.execute(
                f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE quantity < reorder_level
                """
            ).fetchone()[0]
        )

    connection.close()

    # ==============================================
    # Dataset statistics
    # ==============================================

    total_rows = sum(
        dataset.get(
            "row_count",
            0,
        )
        for dataset in datasets
    )

    recent_datasets = []

    for dataset in datasets[:5]:
        recent_datasets.append(
            {
                "table_name":
                    dataset[
                        "table_name"
                    ],

                "source_file":
                    dataset[
                        "source_file"
                    ],

                "sheet_name":
                    dataset.get(
                        "sheet_name"
                    ),

                "row_count":
                    dataset.get(
                        "row_count",
                        0,
                    ),

                "columns":
                    len(
                        dataset.get(
                            "columns",
                            [],
                        )
                    ),
            }
        )

    return {
        "status": "success",

        "metrics": {
            "documents":
                document_stats[
                    "documents"
                ],

            "document_pages":
                document_stats[
                    "pages"
                ],

            "document_chunks":
                document_stats[
                    "chunks"
                ],

            "datasets":
                len(datasets),

            "dataset_rows":
                total_rows,

            "supplier_aliases":
                len(aliases),

            "delayed_shipments":
                delayed_shipments,

            "open_purchase_orders":
                open_purchase_orders,

            "low_stock_items":
                low_stock_items,

            "open_po_outstanding_value":
                float(
                    open_po_outstanding_value
                ),
        },

        "recent_datasets":
            recent_datasets,

        "detected_tables": {
            "shipments":
                shipment_dataset[
                    "table_name"
                ]
                if shipment_dataset
                else None,

            "purchase_orders":
                purchase_order_dataset[
                    "table_name"
                ]
                if purchase_order_dataset
                else None,

            "inventory":
                inventory_dataset[
                    "table_name"
                ]
                if inventory_dataset
                else None,
        },
    }