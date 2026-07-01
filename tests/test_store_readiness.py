import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from scripts import check_store_readiness as readiness


def test_default_base_dir_prefers_localappdata(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))

    import mail_imap_cleaner_v1 as app

    expected = tmp_path / "LocalAppData" / "UniversalMailCleaner"
    assert app._default_base_dir() == expected


def test_config_read_file_prefers_store_path(monkeypatch, tmp_path):
    import mail_imap_cleaner_v1 as app

    store_config = tmp_path / "LocalAppData" / "UniversalMailCleaner" / "config.json"
    legacy_config = tmp_path / "home" / ".mail_cleaner" / "config.json"
    monkeypatch.setattr(app, "CONFIG_FILE", store_config)
    monkeypatch.setattr(app, "LEGACY_CONFIG_FILE", legacy_config)

    legacy_config.parent.mkdir(parents=True)
    legacy_config.write_text("{}", encoding="utf-8")
    assert app._config_read_file() == legacy_config

    store_config.parent.mkdir(parents=True)
    store_config.write_text("{}", encoding="utf-8")
    assert app._config_read_file() == store_config


def test_store_readiness_collects_expected_gate_keys():
    results = readiness.collect_results(ROOT)
    by_key = {result.key: result for result in results}

    assert by_key["desktop_config_path"].status == "ok"
    assert by_key["gmail_token_path"].status == "ok"
    assert by_key["secret_ignores"].status == "ok"
    assert "public_store_values" in by_key
    assert "wack_report" in by_key


def test_store_readiness_json_output_is_valid(capsys):
    exit_code = readiness.main(["--json", "--allow-blockers"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, list)
    assert any(item["key"] == "desktop_config_path" for item in payload)


def test_no_store_secrets_in_tracked_guardrails():
    results = readiness.collect_results(ROOT)
    blockers = {result.key for result in results if result.status == "blocker"}

    assert "tracked_secret_artifacts" not in blockers
    assert "secret_ignores" not in blockers
