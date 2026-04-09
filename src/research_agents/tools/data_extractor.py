"""Tool handlers for the Data Extractor agent."""

from __future__ import annotations

import json

from research_agents.services.container import ServiceContainer
from research_agents.services.database import TableNotFoundError


def handle_query_database(input_dict: dict, services: ServiceContainer) -> str:
    table = input_dict.get("table", "")
    filters = input_dict.get("filters")
    if not table:
        return json.dumps({
            "status": "error",
            "error_type": "invalid_input",
            "source": "query_database",
            "message": "table parameter is required",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })
    try:
        rows = services.database.query(table, filters=filters)
        return json.dumps({"status": "success", "data": {"table": table, "rows": rows}})
    except TableNotFoundError:
        return json.dumps({
            "status": "error",
            "error_type": "not_found",
            "source": f"database:{table}",
            "message": f"Table not found: {table}",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })


def handle_transform_data(input_dict: dict, services: ServiceContainer) -> str:
    table = input_dict.get("table", "")
    columns = input_dict.get("columns")
    aggregate = input_dict.get("aggregate")
    aggregate_column = input_dict.get("aggregate_column")
    if not table:
        return json.dumps({
            "status": "error",
            "error_type": "invalid_input",
            "source": "transform_data",
            "message": "table parameter is required",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })
    try:
        rows = services.database.query(table)
        # Apply column selection
        if columns:
            rows = [{k: r[k] for k in columns if k in r} for r in rows]
        # Apply aggregation
        result: dict = {"table": table, "row_count": len(rows)}
        if aggregate and aggregate_column:
            values = [r.get(aggregate_column) for r in rows if r.get(aggregate_column) is not None]
            numeric = [v for v in values if isinstance(v, int | float)]
            agg = {"function": aggregate, "column": aggregate_column}
            if aggregate == "sum":
                agg["value"] = sum(numeric)
            elif aggregate == "average":
                agg["value"] = sum(numeric) / len(numeric) if numeric else 0
            elif aggregate == "count":
                agg["value"] = len(numeric)
            elif aggregate == "max":
                agg["value"] = max(numeric) if numeric else None
            elif aggregate == "min":
                agg["value"] = min(numeric) if numeric else None
            result["aggregate"] = agg
        else:
            result["rows"] = rows
        return json.dumps({"status": "success", "data": result})
    except TableNotFoundError:
        return json.dumps({
            "status": "error",
            "error_type": "not_found",
            "source": f"database:{table}",
            "message": f"Table not found: {table}",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })


def handle_validate_schema(input_dict: dict, services: ServiceContainer) -> str:
    table = input_dict.get("table", "")
    if not table:
        return json.dumps({
            "status": "error",
            "error_type": "invalid_input",
            "source": "validate_schema",
            "message": "table parameter is required",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })
    try:
        schema = services.database.get_schema(table)
        return json.dumps({"status": "success", "data": schema})
    except TableNotFoundError:
        return json.dumps({
            "status": "error",
            "error_type": "not_found",
            "source": f"database:{table}",
            "message": f"Table not found: {table}",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })


def handle_format_output(input_dict: dict, services: ServiceContainer) -> str:
    table = input_dict.get("table", "")
    filters = input_dict.get("filters")
    if not table:
        return json.dumps({
            "status": "error",
            "error_type": "invalid_input",
            "source": "format_output",
            "message": "table parameter is required",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })
    try:
        rows = services.database.query(table, filters=filters)
        schema = services.database.get_schema(table)
        col_names = [c["name"] for c in schema["columns"]]
        summary_lines = [f"Table: {table} ({len(rows)} rows)"]
        summary_lines.append(f"Columns: {', '.join(col_names)}")
        if rows:
            summary_lines.append(f"Sample row: {rows[0]}")
        return json.dumps({
            "status": "success",
            "data": {"summary": "\n".join(summary_lines), "row_count": len(rows)},
        })
    except TableNotFoundError:
        return json.dumps({
            "status": "error",
            "error_type": "not_found",
            "source": f"database:{table}",
            "message": f"Table not found: {table}",
            "retry_eligible": False,
            "fallback_available": False,
            "partial_data": None,
        })
