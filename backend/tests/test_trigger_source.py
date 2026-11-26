"""Pruebas del origen (manual o programada) de cada ejecución del ETL."""
import importlib.util
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync_etl.py"


@pytest.mark.parametrize("event, expected", [
    ("schedule", "scheduled"),
    ("workflow_dispatch", "manual"),
    (None, "manual"),
])
def test_origen_segun_el_evento(event, expected, monkeypatch):
    monkeypatch.chdir(Path.cwd())  # el script cambia de carpeta al importarse
    spec = importlib.util.spec_from_file_location("sync_etl_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.trigger_source(event) == expected


@pytest.mark.parametrize("source", ["scheduled", "manual", None])
def test_historial_devuelve_el_origen(test_client, mock_db, valid_token, source):
    audit = SimpleNamespace(
        audit_id=1, started_at=datetime(2026, 11, 26, 14, 42), finished_at=None, duration_ms=7000,
        status="success", is_full_run=False, error_message=None, artists_new=0, tracks_new=0,
        history_new=6, history_skipped=0, trigger_source=source,
    )
    query = mock_db.query.return_value.filter_by.return_value
    query.count.return_value = 1
    query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [audit]

    res = test_client.get("/v1/etl/history", headers={"Authorization": f"Bearer {valid_token}"})

    assert res.status_code == 200
    assert res.json()["runs"][0]["trigger_source"] == source
