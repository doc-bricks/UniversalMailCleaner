"""Metadata, Manifest, and Discoverability Parity Tests for UniversalMailCleaner."""

from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parent.parent


def test_version_parity():
    """Verify version consistency across pyproject.toml, main module, and documentation."""
    # 1. pyproject.toml
    pyproject_path = ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml missing"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    version = pyproject_data["project"]["version"]
    assert version == "1.2.0", f"Unexpected version in pyproject.toml: {version}"

    # 2. mail_imap_cleaner_v1.py
    main_py = ROOT / "mail_imap_cleaner_v1.py"
    assert main_py.exists(), "mail_imap_cleaner_v1.py missing"
    main_content = main_py.read_text(encoding="utf-8")
    assert f'__version__ = "{version}"' in main_content
    assert 'APP_VERSION = __version__' in main_content

    # 3. CHANGELOG.md
    changelog_path = ROOT / "CHANGELOG.md"
    assert changelog_path.exists(), "CHANGELOG.md missing"
    changelog_content = changelog_path.read_text(encoding="utf-8")
    assert f"[{version}]" in changelog_content, f"Version {version} not found in CHANGELOG.md"

    # 4. README.md & README-DE.md / README_de.md badges
    for readme_name in ["README.md", "README-DE.md", "README_de.md"]:
        readme_path = ROOT / readme_name
        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8")
            assert f"Version-v{version}-blue" in content or f"v{version}" in content


def test_manifest_files_exist():
    """Verify all critical repo files exist and are non-empty."""
    required_files = [
        "pyproject.toml",
        "requirements.txt",
        "README.md",
        "README-DE.md",
        "README_de.md",
        "llms.txt",
        "CHANGELOG.md",
        "LICENSE",
        "SECURITY.md",
        "mail_imap_cleaner_v1.py",
        "imap_client.py",
        "gmail_service.py",
        "workers.py",
        "models.py",
        "profile_exchange.py",
        "scheduler_widget.py",
    ]
    for filename in required_files:
        p = ROOT / filename
        assert p.exists(), f"Required manifest file missing: {filename}"
        assert p.stat().st_size > 0, f"Manifest file is empty: {filename}"


def test_llms_txt_structure():
    """Verify llms.txt structure and metadata."""
    llms_path = ROOT / "llms.txt"
    assert llms_path.exists(), "llms.txt missing"
    content = llms_path.read_text(encoding="utf-8")

    assert "doc-bricks/UniversalMailCleaner" in content
    assert "https://github.com/doc-bricks/UniversalMailCleaner" in content
    assert "doc-bricks" in content
    assert "open-bricks" in content
    assert "MIT" in content
    assert "Search Phrases" in content
    assert "Disambiguation" in content
    assert "Safety Model" in content
    assert "Last-checked: 2026-08-16" in content


def test_ecosystem_and_badges_parity():
    """Verify ecosystem badges and links in README files."""
    for readme_name in ["README.md", "README-DE.md", "README_de.md"]:
        readme_path = ROOT / readme_name
        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8")
            assert "doc-bricks" in content
            assert "open-bricks" in content
            assert "llms.txt" in content
            assert "LICENSE" in content or "MIT" in content


def test_utf8_hygiene():
    """Verify all text files have valid UTF-8 encoding without corruption."""
    text_extensions = {".py", ".md", ".toml", ".txt", ".json", ".bat"}
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in text_extensions:
            if ".git" in path.parts or ".pytest_cache" in path.parts or ".ruff_cache" in path.parts:
                continue
            try:
                content = path.read_text(encoding="utf-8")
                assert "\ufffd" not in content, f"Replacement character found in {path}"
            except UnicodeDecodeError as exc:
                raise AssertionError(f"Invalid UTF-8 encoding in {path}: {exc}")
