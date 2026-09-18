from pathlib import Path

import pytest
import sqlglot
from vault.warehouse import Connection
from vault.warehouse_vault import compile_project

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("engine", ["databricks", "snowflake", "clickhouse"])
def test_warehouse_hub_link_satellite_compile(engine, tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("compile must not connect")

    monkeypatch.setattr(Connection, "connect", forbidden)
    plan = compile_project(
        ROOT / "examples/replacement/project.json",
        ROOT / "examples/warehouses" / f"{engine}-vault.json",
        tmp_path / "plan",
    )
    assert len(plan["models"]) == 5
    for spec in plan["models"].values():
        for sql in [
            spec["ddl"],
            spec["insert"],
            spec["query"],
            *[c["sql"] for c in spec["checks"]],
        ]:
            sqlglot.parse_one(sql, read=engine)
        assert "read_csv" not in spec["insert"].lower()
    if engine == "clickhouse":
        assert "MergeTree" in plan["models"]["hub_customer"]["ddl"]
