"""Metadata, Manifest, and Discoverability Parity Tests for UniversalMailCleaner."""

from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parent.parent

INVARIANTS = [
    "INV-LOCAL-01",
    "INV-CRED-02",
    "INV-SAFE-03",
    "INV-UNDO-04",
    "INV-CONFIRM-05",
    "INV-TLS-06",
    "INV-LEASTPRIV-07",
    "INV-LAZYLOAD-08",
    "INV-PORTABLE-09",
    "INV-SLA-10",
]

EXPECTED_EN_ANCHORS = [
    "#architecture",
    "#workflow-lifecycle",
    "#core-capabilities--security-invariants",
    "#target-personas--use-cases",
    "#comparative-matrix--alternatives",
    "#feature-highlights",
    "#visual-interface--screenshot",
    "#supported-providers",
    "#quick-start--setup",
    "#configuration--credential-safety",
    "#scheduler--automated-maintenance",
    "#ecosystem--sibling-tools",
    "#third-party-licenses--compliance",
    "#security-policy--slas",
    "#license--faq",
]

EXPECTED_DE_ANCHORS = [
    "#architektur",
    "#workflow-lebenszyklus",
    "#kernfähigkeiten--sicherheitsinvarianten",
    "#zielgruppen--anwendungsfälle",
    "#vergleichsmatrix--alternativen",
    "#funktions-highlights",
    "#visuelle-oberfläche--screenshot",
    "#unterstützte-anbieter",
    "#schnellstart--installation",
    "#konfiguration--zugangsdaten-sicherheit",
    "#zeitplaner--automatisierte-wartung",
    "#ökosystem--geschwister-werkzeuge",
    "#drittanbieter-lizenzen--compliance",
    "#sicherheitsrichtlinie--slas",
    "#lizenz--faq",
]


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
        "THIRD_PARTY_LICENSES.md",
        "MARKETING-LOG.txt",
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
    assert "Last-checked: 2026-09-14" in content
    assert "THIRD_PARTY_LICENSES.md" in content
    assert "MARKETING-LOG.txt" in content
    for inv in INVARIANTS:
        assert inv in content, f"Invariant {inv} missing in llms.txt"


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


def test_german_readme_parity():
    """Verify that README_de.md and README-DE.md are identical."""
    de_path1 = ROOT / "README_de.md"
    de_path2 = ROOT / "README-DE.md"
    assert de_path1.exists(), "README_de.md missing"
    assert de_path2.exists(), "README-DE.md missing"
    assert de_path1.read_bytes() == de_path2.read_bytes(), "README_de.md and README-DE.md must be byte-identical"


def test_navigation_anchors_bilingual_parity():
    """Verify 15-point quick navigation anchor parity in README.md and README_de.md."""
    en_content = (ROOT / "README.md").read_text(encoding="utf-8")
    de_content = (ROOT / "README_de.md").read_text(encoding="utf-8")

    assert len(EXPECTED_EN_ANCHORS) == 15, "Expected 15 EN navigation anchors"
    assert len(EXPECTED_DE_ANCHORS) == 15, "Expected 15 DE navigation anchors"

    for anchor in EXPECTED_EN_ANCHORS:
        assert f"({anchor})" in en_content, f"Anchor {anchor} missing from README.md navigation"

    for anchor in EXPECTED_DE_ANCHORS:
        assert f"({anchor})" in de_content, f"Anchor {anchor} missing from README_de.md navigation"


def test_ten_governance_invariants():
    """Verify all 10 governance and runtime invariants are documented across files."""
    en_content = (ROOT / "README.md").read_text(encoding="utf-8")
    de_content = (ROOT / "README_de.md").read_text(encoding="utf-8")
    tpl_content = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
    mkt_content = (ROOT / "MARKETING-LOG.txt").read_text(encoding="utf-8")

    for inv in INVARIANTS:
        assert inv in en_content, f"Invariant {inv} missing in README.md"
        assert inv in de_content, f"Invariant {inv} missing in README_de.md"
        assert inv in tpl_content, f"Invariant {inv} missing in THIRD_PARTY_LICENSES.md"
        assert inv in mkt_content, f"Invariant {inv} missing in MARKETING-LOG.txt"


def test_target_personas_present():
    """Verify all 4 target personas are present in README and marketing files."""
    en_content = (ROOT / "README.md").read_text(encoding="utf-8")
    de_content = (ROOT / "README_de.md").read_text(encoding="utf-8")
    mkt_content = (ROOT / "MARKETING-LOG.txt").read_text(encoding="utf-8")

    assert "Privacy-Conscious Professionals" in en_content
    assert "Storage-Constrained" in en_content
    assert "Power Users" in en_content
    assert "Solo Developers" in en_content

    assert "Datenschutzbewusste Fachanwender" in de_content
    assert "Speicherplatz-limitierte" in de_content
    assert "Power-User" in de_content
    assert "Solo-Entwickler" in de_content

    assert "Persona 1:" in mkt_content
    assert "Persona 2:" in mkt_content
    assert "Persona 3:" in mkt_content
    assert "Persona 4:" in mkt_content


def test_comparative_matrix_present():
    """Verify comparative matrix dimensions and alternatives."""
    en_content = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Cleanfox" in en_content
    assert "Mailstrom" in en_content
    assert "Comparative Matrix" in en_content
    assert "Zero-Egress" in en_content


def test_third_party_licenses_audit():
    """Verify THIRD_PARTY_LICENSES.md structure and content."""
    tpl_path = ROOT / "THIRD_PARTY_LICENSES.md"
    assert tpl_path.exists(), "THIRD_PARTY_LICENSES.md missing"
    content = tpl_path.read_text(encoding="utf-8")

    assert "PySide6" in content
    assert "keyring" in content
    assert "google-auth-oauthlib" in content
    assert "google-api-python-client" in content
    assert "MIT" in content
    assert "LGPL-3.0" in content
    assert "Apache-2.0" in content


def test_pep621_project_urls():
    """Verify PEP 621 extended project URLs in pyproject.toml."""
    pyproject_path = ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    urls = data["project"]["urls"]
    assert "Third-Party Licenses" in urls
    assert "Marketing Log" in urls
    assert "LLM Ready" in urls
    assert "Security Policy" in urls
    assert "Issues" in urls
    assert "Changelog" in urls
    assert "blob/master/CHANGELOG.md" in urls["Changelog"]


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
                raise AssertionError(f"Invalid UTF-8 encoding in {path}: {exc}") from exc


def test_ci_workflows_timeout_and_concurrency():
    """Verify all GitHub Actions workflows define timeout-minutes and concurrency guards."""
    workflows_dir = ROOT / ".github" / "workflows"
    assert workflows_dir.exists() and workflows_dir.is_dir(), ".github/workflows directory missing"

    workflow_files = list(workflows_dir.glob("*.yml"))
    assert len(workflow_files) >= 3, f"Expected at least 3 workflow files, found {len(workflow_files)}"

    for wf_path in workflow_files:
        content = wf_path.read_text(encoding="utf-8")
        assert "timeout-minutes:" in content, f"Workflow {wf_path.name} is missing timeout-minutes runaway guard"
        if wf_path.name in ["ci.yml", "source-platform-smoke.yml"]:
            assert "concurrency:" in content, f"Workflow {wf_path.name} is missing concurrency configuration"
            assert "cancel-in-progress: true" in content, f"Workflow {wf_path.name} is missing cancel-in-progress"


def test_stale_workflow_present_and_valid():
    """Verify stale.yml workflow presence, action version, and configuration."""
    stale_path = ROOT / ".github" / "workflows" / "stale.yml"
    assert stale_path.exists(), "stale.yml workflow missing"
    content = stale_path.read_text(encoding="utf-8")
    assert "actions/stale@v9" in content
    assert "cron: '30 1 * * *'" in content
    assert "timeout-minutes: 10" in content
    assert "issues: write" in content
    assert "pull-requests: write" in content


def test_gitignore_multihost_and_canonical_lock_defense():
    """Verify .gitignore blocks multi-host sync conflicts, locks, and temporary artifacts."""
    gitignore_path = ROOT / ".gitignore"
    assert gitignore_path.exists(), ".gitignore missing"
    content = gitignore_path.read_text(encoding="utf-8")

    expected_patterns = [
        "* (kopie)*",
        "* (copy)*",
        "*conflicted copy*",
        "*-ASUS*",
        "*-WORKSTATION*",
        "*-LAPTOP*",
        "*.sync-conflict-*",
        "LOCK",
        "LOCK.*",
        "LOCK.permissions.json",
        "uv.lock",
        ".coverage",
        ".ruff_cache/",
        ".pytest_cache/",
    ]
    for pat in expected_patterns:
        assert pat in content, f"Pattern {pat} missing from .gitignore"


def test_pytest_configuration_and_pep621_urls():
    """Verify pytest addopts, ruff rules, and extended PEP 621 URLs in pyproject.toml."""
    pyproject_path = ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    # Pytest configuration
    pytest_opts = data.get("tool", {}).get("pytest", {}).get("ini_options", {})
    assert "addopts" in pytest_opts, "addopts missing from [tool.pytest.ini_options]"
    assert "-ra -v" in pytest_opts["addopts"], "Expected '-ra -v' in pytest addopts"

    # Ruff configuration
    ruff_select = data.get("tool", {}).get("ruff", {}).get("lint", {}).get("select", [])
    assert "C4" in ruff_select, "C4 rule missing from [tool.ruff.lint] select"

    # Extended URLs
    urls = data["project"]["urls"]
    assert "Bug Tracker" in urls
    assert "Parent Organization" in urls
    assert "Umbrella Ecosystem" in urls


def test_security_policy_bilingual_and_sla():
    """Verify SECURITY.md contains bilingual policy, supported versions, contacts, and 48h SLA."""
    sec_path = ROOT / "SECURITY.md"
    assert sec_path.exists(), "SECURITY.md missing"
    content = sec_path.read_text(encoding="utf-8")

    assert "## Deutsch" in content
    assert "## English" in content
    assert "48 Stunden" in content or "48 hours" in content
    assert "INV-SLA-10" in content
    assert "INV-LOCAL-01" in content
    assert "INV-CRED-02" in content
    assert "INV-SAFE-03" in content
    assert "security@doc-bricks.org" in content
    assert "support@lukasgeiger.com" in content
    assert "1.2.x" in content


def test_changelog_and_marketing_pfad_a_records():
    """Verify CHANGELOG.md and MARKETING-LOG.txt document Pfad A technical hygiene."""
    changelog_content = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    marketing_content = (ROOT / "MARKETING-LOG.txt").read_text(encoding="utf-8")

    assert "Pfad A Technical Hygiene" in changelog_content
    assert "2026-09-14" in changelog_content

    assert "PFAD_A_TECHNICAL_HYGIENE_AND_CI_HARDENING" in marketing_content
    assert "2026-09-14" in marketing_content
