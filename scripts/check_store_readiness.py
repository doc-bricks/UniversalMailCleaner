"""Windows Store readiness preflight for UniversalMailCleaner.

The check is intentionally conservative: it separates implementation readiness
from external Partner Center and WACK gates that cannot be completed on every
developer workstation.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"ok", "warn", "blocker"}


@dataclass(frozen=True)
class CheckResult:
    key: str
    status: str
    summary: str

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"invalid status: {self.status}")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_store_package(root: Path) -> tuple[dict, list[CheckResult]]:
    path = root / "store_package.json"
    if not path.exists():
        return {}, [CheckResult("store_package", "blocker", "store_package.json fehlt")]
    try:
        payload = json.loads(_read_text(path))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [CheckResult("store_package", "blocker", f"store_package.json unlesbar: {exc}")]

    missing = [
        key
        for key in (
            "app_id",
            "display_name",
            "version",
            "publisher",
            "privacy_url",
            "support_url",
        )
        if not payload.get(key)
    ]
    if missing:
        return payload, [
            CheckResult("store_package", "blocker", f"Pflichtfelder fehlen: {', '.join(missing)}")
        ]
    return payload, [CheckResult("store_package", "ok", "Store-Metadaten-Datei vorhanden")]


def _is_placeholder(value: object) -> bool:
    text = str(value or "").strip().lower()
    return not text or "todo" in text or "example." in text or "placeholder" in text


def _tracked_files(root: Path) -> list[str]:
    git_dir = root / ".git"
    if not git_dir.exists():
        return []
    try:
        proc = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            text=True,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]


def _check_public_store_values(payload: dict) -> list[CheckResult]:
    blockers = []
    for key in ("publisher", "privacy_url", "support_url"):
        if _is_placeholder(payload.get(key)):
            blockers.append(key)
    if blockers:
        return [
            CheckResult(
                "public_store_values",
                "blocker",
                "Partner-Center-Werte noch Platzhalter: " + ", ".join(blockers),
            )
        ]
    return [
        CheckResult(
            "public_store_values",
            "ok",
            "Publisher-, Privacy- und Support-Werte gesetzt",
        )
    ]


def _check_local_data_paths(root: Path) -> list[CheckResult]:
    main_source = _read_text(root / "mail_imap_cleaner_v1.py")
    gmail_source = _read_text(root / "gmail_service.py")
    checks: list[CheckResult] = []

    if "LOCALAPPDATA" in main_source and "LEGACY_CONFIG_FILE" in main_source:
        checks.append(
            CheckResult(
                "desktop_config_path",
                "ok",
                "Desktop-Konfiguration schreibt nach LOCALAPPDATA und liest Legacy-Konfigurationen",
            )
        )
    else:
        checks.append(
            CheckResult(
                "desktop_config_path",
                "blocker",
                "Desktop-Konfiguration ist nicht Store-tauglich auf LOCALAPPDATA migriert",
            )
        )

    if "LOCALAPPDATA" in gmail_source and "gmail_token.json" in gmail_source:
        checks.append(
            CheckResult("gmail_token_path", "ok", "Gmail-OAuth-Token liegt unter LOCALAPPDATA")
        )
    else:
        checks.append(CheckResult(
            "gmail_token_path",
            "blocker",
            "Gmail-OAuth-Tokenpfad ist nicht lokal isoliert",
        ))
    return checks


def _check_secret_guardrails(root: Path) -> list[CheckResult]:
    gitignore = _read_text(root / ".gitignore")
    required_patterns = [
        "credentials.json",
        "client_secret*.json",
        "token.json",
        "*.pem",
        "*.key",
        "*.db",
        "*.sqlite",
    ]
    missing = [pattern for pattern in required_patterns if pattern not in gitignore]
    if missing:
        return [
            CheckResult(
                "secret_ignores",
                "blocker",
                "Sensible Muster fehlen in .gitignore: " + ", ".join(missing),
            )
        ]

    tracked = _tracked_files(root)
    forbidden_names = {"credentials.json", "token.json", "gmail_token.json"}
    forbidden_suffixes = (".pem", ".key", ".sqlite", ".db")
    tracked_forbidden = [
        name
        for name in tracked
        if Path(name).name in forbidden_names
        or name.endswith(forbidden_suffixes)
        or Path(name).name.startswith("client_secret")
    ]
    if tracked_forbidden:
        return [
            CheckResult(
                "tracked_secret_artifacts",
                "blocker",
                "Getrackte sensible Dateien gefunden: " + ", ".join(tracked_forbidden),
            )
        ]
    return [
        CheckResult(
            "secret_ignores",
            "ok",
            "Secret-/Token-/Datenbankartefakte sind ausgeschlossen",
        )
    ]


def _check_runtime_materials(root: Path) -> list[CheckResult]:
    required = [
        "README.md",
        "README-DE.md",
        "SECURITY.md",
        "THIRD_PARTY_LICENSES.txt",
        "UniversalMailCleaner.spec",
        "UniversalMailCleaner_icon.ico",
        "build_exe.bat",
        "START.bat",
        "docs/WINDOWS_STORE_READINESS.md",
    ]
    missing = [path for path in required if not (root / path).exists()]
    if missing:
        return [CheckResult(
            "runtime_materials",
            "blocker",
            "Release-Material fehlt: " + ", ".join(missing),
        )]
    return [
        CheckResult(
            "runtime_materials",
            "ok",
            "Runtime-, Lizenz- und Store-Dokumente vorhanden",
        )
    ]


def _check_wack_and_msix(root: Path) -> list[CheckResult]:
    msix_candidates = list((root / "releases").glob("**/*.msix"))
    wack_reports = list((root / "releases").glob("**/wack_*.xml"))
    results: list[CheckResult] = []
    if msix_candidates:
        results.append(
            CheckResult(
                "msix_artifact",
                "ok",
                "MSIX-Artefakt im lokalen Release-Workspace gefunden",
            )
        )
    else:
        results.append(CheckResult(
            "msix_artifact",
            "blocker",
            "Kein lokales MSIX-Artefakt für WACK gefunden",
        ))
    if wack_reports:
        results.append(CheckResult("wack_report", "ok", "WACK-XML-Report gefunden"))
    else:
        results.append(CheckResult("wack_report", "blocker", "WACK-XML-Report fehlt noch"))
    return results


def collect_results(root: Path = PROJECT_ROOT) -> list[CheckResult]:
    payload, package_results = _load_store_package(root)
    results = list(package_results)
    results.extend(_check_public_store_values(payload) if payload else [])
    results.extend(_check_local_data_paths(root))
    results.extend(_check_secret_guardrails(root))
    results.extend(_check_runtime_materials(root))
    results.extend(_check_wack_and_msix(root))
    return results


def summarize(results: list[CheckResult]) -> str:
    counts = {
        status: sum(1 for result in results if result.status == status)
        for status in STATUSES
    }
    status = "BLOCKED" if counts["blocker"] else "WARN" if counts["warn"] else "OK"
    lines = [f"UniversalMailCleaner Store readiness: {status}"]
    lines.append(f"OK={counts['ok']} WARN={counts['warn']} BLOCKER={counts['blocker']}")
    for result in results:
        lines.append(f"[{result.status.upper()}] {result.key}: {result.summary}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable results")
    parser.add_argument(
        "--allow-blockers",
        action="store_true",
        help="Return 0 even when external Store/WACK blockers remain",
    )
    args = parser.parse_args(argv)

    results = collect_results()
    has_blocker = any(result.status == "blocker" for result in results)

    if args.json:
        print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))
    else:
        print(summarize(results))

    if has_blocker and not args.allow_blockers:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
