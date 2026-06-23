"""Helpers for secrets-free UniversalMailCleaner profile exchange."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Iterable

from models import CleanRule, MailAccount

PROFILE_SCHEMA = "universalmailcleaner-profile-v1"
PROFILE_APP = "UniversalMailCleaner"

_DEFAULT_SETTINGS = {
    "safe_mode": True,
    "selected_rule_folders": ["INBOX"],
    "large_item_threshold_mb": 10,
    "scan_mail": True,
    "scan_drive": False,
    "scheduler": {
        "enabled": False,
        "interval_hours": 24,
        "run_on_startup": False,
        "last_run": "",
        "next_run": "",
    },
}


def default_profile_settings() -> dict:
    """Return a deep copy of the canonical profile settings defaults."""

    return deepcopy(_DEFAULT_SETTINGS)


def _normalize_folder_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    folders = [str(folder).strip() for folder in value if str(folder).strip()]
    return folders or ["INBOX"]


def merge_profile_settings(raw_settings: dict | None) -> dict:
    """Merge partial settings into the canonical export/import defaults."""

    settings = default_profile_settings()
    if not isinstance(raw_settings, dict):
        return settings

    for key in ("safe_mode", "large_item_threshold_mb", "scan_mail", "scan_drive"):
        if key in raw_settings:
            settings[key] = raw_settings[key]

    if "selected_rule_folders" in raw_settings:
        settings["selected_rule_folders"] = _normalize_folder_list(
            raw_settings.get("selected_rule_folders")
        )

    scheduler = raw_settings.get("scheduler")
    if isinstance(scheduler, dict):
        for key in ("enabled", "interval_hours", "run_on_startup", "last_run", "next_run"):
            if key in scheduler:
                settings["scheduler"][key] = scheduler[key]

    return settings


def _serialize_accounts(accounts: Iterable[MailAccount]) -> list[dict]:
    return [
        {
            "name": account.name,
            "protocol": account.protocol,
            "host": account.host,
            "port": account.port,
            "user": account.user,
            "trash_folder": account.trash_folder,
        }
        for account in accounts
    ]


def _serialize_rules(rules: Iterable[CleanRule]) -> list[dict]:
    return [
        {
            "name": rule.name,
            "target_account": rule.target_account,
            "filter_type": rule.filter_type,
            "value": rule.value,
            "active": rule.active,
        }
        for rule in rules
    ]


def _serialize_settings(settings: dict | None) -> dict:
    merged = merge_profile_settings(settings)
    return {
        "safe_mode": bool(merged["safe_mode"]),
        "selected_rule_folders": _normalize_folder_list(
            merged.get("selected_rule_folders")
        ),
        "large_item_threshold_mb": int(merged["large_item_threshold_mb"]),
        "scan_mail": bool(merged["scan_mail"]),
        "scan_drive": bool(merged["scan_drive"]),
        "scheduler": {
            "enabled": bool(merged["scheduler"]["enabled"]),
            "interval_hours": int(merged["scheduler"]["interval_hours"]),
            "run_on_startup": bool(merged["scheduler"]["run_on_startup"]),
        },
    }


def build_profile_payload(
    accounts: Iterable[MailAccount],
    rules: Iterable[CleanRule],
    settings: dict | None,
    exported_at: str | None = None,
) -> dict:
    """Build the portable profile payload from the current app state."""

    timestamp = exported_at or datetime.now().astimezone().isoformat(timespec="seconds")
    return {
        "schema": PROFILE_SCHEMA,
        "app": PROFILE_APP,
        "exported_at": timestamp,
        "accounts": _serialize_accounts(accounts),
        "rules": _serialize_rules(rules),
        "settings": _serialize_settings(settings),
    }


def write_profile(
    path: str | Path,
    accounts: Iterable[MailAccount],
    rules: Iterable[CleanRule],
    settings: dict | None,
    exported_at: str | None = None,
) -> dict:
    """Write a profile payload as UTF-8 JSON and return the payload."""

    payload = build_profile_payload(accounts, rules, settings, exported_at=exported_at)
    # FIX: atomar schreiben (tmp + replace), sonst zerstoert ein Crash/Lock waehrend
    # write_text eine bestehende Profil-JSON (abgeschnitten/leer).
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)
    return payload


def _load_rule(rule_data: dict) -> CleanRule:
    if not isinstance(rule_data, dict):
        raise ValueError("Regel-Eintrag ist kein Objekt.")

    if "filter_type" in rule_data and "target_account" in rule_data:
        return CleanRule.from_dict(rule_data)

    name = str(rule_data.get("name", "")).strip()
    target_account = str(
        rule_data.get("target_account", rule_data.get("account", "Alle"))
    ).strip() or "Alle"
    filter_type = str(
        rule_data.get("filter_type", rule_data.get("type", ""))
    ).strip()
    value = rule_data.get("value", "")

    if value == "" and filter_type == "older_than_days":
        value = rule_data.get("older_than_days", "")
    if value == "" and filter_type == "size_mb":
        value = rule_data.get("size_mb", "")

    if not name or not filter_type or value == "":
        raise ValueError("Regel-Eintrag ist unvollständig.")

    return CleanRule(name, target_account, filter_type, str(value), bool(rule_data.get("active", True)))


def load_profile_payload(payload: dict) -> tuple[list[MailAccount], list[CleanRule], dict]:
    """Validate and convert a profile payload into app state."""

    if not isinstance(payload, dict):
        raise ValueError("Profil ist kein JSON-Objekt.")
    if payload.get("schema") != PROFILE_SCHEMA:
        raise ValueError(
            f"Unbekanntes Profil-Schema: {payload.get('schema')!r}"
        )

    raw_accounts = payload.get("accounts", [])
    raw_rules = payload.get("rules", [])
    if not isinstance(raw_accounts, list) or not isinstance(raw_rules, list):
        raise ValueError("Konten und Regeln müssen Listen sein.")

    # FIX: isinstance-Guard (analog _load_rule fuer rules) -> ein Nicht-dict-Konten-
    # Eintrag (z.B. "accounts": ["foo"]) wirft sonst AttributeError in from_dict und
    # bricht den GANZEN Profil-Import ab (asymmetrisch zu rules, die geschuetzt waren).
    for _acc in raw_accounts:
        if not isinstance(_acc, dict):
            raise ValueError("Konten-Eintrag ist kein Objekt.")
    accounts = [MailAccount.from_dict(item) for item in raw_accounts]
    rules = [_load_rule(item) for item in raw_rules]
    settings = merge_profile_settings(payload.get("settings"))

    if "selected_rule_folders" not in (payload.get("settings") or {}):
        folder_sets = []
        for item in raw_rules:
            if isinstance(item, dict) and isinstance(item.get("folders"), list):
                folder_sets.append(_normalize_folder_list(item.get("folders")))
        if folder_sets and all(folder_set == folder_sets[0] for folder_set in folder_sets):
            settings["selected_rule_folders"] = folder_sets[0]

    return accounts, rules, settings


def read_profile(path: str | Path) -> tuple[list[MailAccount], list[CleanRule], dict]:
    """Read and parse a profile JSON file."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return load_profile_payload(payload)
