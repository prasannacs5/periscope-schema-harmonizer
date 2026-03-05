"""Unity Catalog SQL execution via Databricks statement execution API."""
import time
from databricks.sdk.service.sql import StatementState
from server.config import get_workspace_client, WAREHOUSE_ID


def run_sql(sql: str, wait: bool = True):
    w = get_workspace_client()
    resp = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=sql.strip(),
        wait_timeout="50s",
    )
    if not wait:
        return resp
    while resp.status.state in (StatementState.PENDING, StatementState.RUNNING):
        time.sleep(2)
        resp = w.statement_execution.get_statement(resp.statement_id)
    if resp.status.state != StatementState.SUCCEEDED:
        raise RuntimeError(f"SQL failed [{resp.status.state}]: {resp.status.error}")
    return resp


def fetch_rows(sql: str) -> list[dict]:
    resp = run_sql(sql)
    if not resp.result or not resp.result.data_array:
        return []
    cols = [c.name for c in resp.manifest.schema.columns]
    return [dict(zip(cols, row)) for row in resp.result.data_array]
