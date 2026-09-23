from app.analytics.sql_generator import generate_sql
from app.analytics.sql_validator import validate_sql
from app.analytics.duckdb_service import execute_read_only_query
from app.utils.json_utils import clean_json_data


def ask_data(question: str) -> dict:
    try:
        # 1. Generate SQL from the user's question
        generated = generate_sql(question)

        sql = generated.get("sql", "")
        explanation = generated.get("explanation", "")

        if not sql:
            return {
                "status": "error",
                "stage": "sql_generation",
                "message": "No SQL was generated.",
                "results": [],
            }

        # 2. Validate the SQL before execution
        is_safe, validation_message = validate_sql(sql)

        if not is_safe:
            return {
                "status": "blocked",
                "stage": "sql_validation",
                "reason": validation_message,
                "sql": sql,
                "results": [],
            }

        # 3. Execute the safe SQL in DuckDB
        dataframe = execute_read_only_query(sql)

        # Convert dataframe into JSON-friendly records
        records = clean_json_data(
    dataframe.to_dict(
        orient="records"
    )
)

        return {
            "status": "success",
            "sql": sql,
            "explanation": explanation,
            "row_count": len(records),
            "results": records,
        }

    except Exception as error:
        return {
            "status": "error",
            "stage": "data_query",
            "error_type": type(error).__name__,
            "message": str(error),
            "results": [],
        }