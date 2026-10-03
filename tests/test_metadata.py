"""Metadata, Manifest, and Discoverability Parity Tests for UniversalMailCleaner."""

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

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

EXPECTED_SECTION_ANCHORS = [f"#sec-{i:02d}" for i in range(1, 19)]

LEGACY_EN_ANCHORS = [
    "architecture",
    "workflow-lifecycle",
    "visual-interface--screenshot",
    "core-capabilities--security-invariants",
    "feature-highlights",
    "target-personas--use-cases",
    "comparative-matrix--alternatives",
    "supported-providers",
    "quick-start--setup",
    "configuration--credential-safety",
    "scheduler--automated-maintenance",
    "ecosystem--sibling-tools",
    "third-party-licenses--compliance",
    "security-policy--slas",
    "license--faq",
]

LEGACY_DE_ANCHORS = [
    "architektur",
    "workflow-lebenszyklus",
    "visuelle-oberflaeche--screenshot",
    "kernfaehigkeiten--sicherheitsinvarianten",
    "funktions-highlights",
    "zielgruppen--anwendungsfaelle",
    "vergleichsmatrix--alternativen",
    "unterstuetzte-anbieter",
    "schnellstart--installation",
    "konfiguration--zugangsdaten-sicherheit",
    "zeitplaner--automatisierte-wartung",
    "oekosystem--geschwister-werkzeuge",
    "drittanbieter-lizenzen--compliance",
    "sicherheitsrichtlinie--slas",
    "lizenz--urheberrecht",
]

EXPECTED_TOPICS = [
    "desktop-app",
    "email",
    "email-management",
    "imap",
    "pyside6",
    "mail-cleaner",
    "email-cleanup",
    "gmail-api",
    "gmail-cleaner",
    "local-first",
    "oauth2",
    "privacy-first",
    "scheduler",
    "imap-cleaner",
    "large-email-finder",
    "mailbox-cleaner",
    "mailbox-cleanup",
    "safe-delete",
    "gmail-cleanup",
    "inbox-cleanup",
]


def test_version_parity():
    """Verify version consistency across pyproject.toml, main module, and documentation."""
    # 1. pyproject.toml
    pyproject_path = ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml missing"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    version = pyproject_data["project"]["version"]
    assert version == "1.2.1", f"Unexpected version in pyproject.toml: {version}"

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

    # 5. Machine-readable and third-party license version surfaces
    version_markers = {
        "llms.txt": f"- Version: {version}",
        "THIRD_PARTY_LICENSES.md": f"**Version:** `{version}`<br>",
        "THIRD_PARTY_LICENSES.txt": f"Version: {version}",
    }
    for filename, marker in version_markers.items():
        content = (ROOT / filename).read_text(encoding="utf-8")
        assert marker in content, f"Current version missing from {filename}"


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
        "NOTICE",
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


def test_root_notice_attribution():
    """Verify root NOTICE file structure, copyright, and third-party references."""
    notice_path = ROOT / "NOTICE"
    assert notice_path.exists(), "NOTICE file missing"
    content = notice_path.read_text(encoding="utf-8")
    assert "UniversalMailCleaner" in content
    assert "Lukas Geiger" in content
    assert "doc-bricks" in content
    assert "open-bricks" in content
    assert "THIRD_PARTY_LICENSES.md" in content


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
    assert "NOTICE" in content
    assert "Last-checked: 2026-10-03" in content or "Last-checked: 2026-10-01" in content or "Last-checked: 2026-09-26" in content
    assert "Architectural Topology: Section 1 ASCII Four-View Topology" in content
    assert "THIRD_PARTY_LICENSES.md" in content
    assert "THIRD_PARTY_LICENSES.txt" in content
    assert "CONTRIBUTING.md" in content
    assert "MARKETING-LOG.txt" in content
    assert "§ 521 BGB" in content
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
            assert "NOTICE" in content


def test_german_readme_parity():
    """Verify that README_de.md and README-DE.md are identical."""
    de_path1 = ROOT / "README_de.md"
    de_path2 = ROOT / "README-DE.md"
    assert de_path1.exists(), "README_de.md missing"
    assert de_path2.exists(), "README-DE.md missing"
    assert de_path1.read_bytes() == de_path2.read_bytes(), "README_de.md and README-DE.md must be byte-identical"


def test_18_point_navigation_and_reciprocal_anchors():
    """Verify 18-point quick navigation and reciprocal anchor parity across README.md and README_de.md."""
    en_content = (ROOT / "README.md").read_text(encoding="utf-8")
    de_content = (ROOT / "README_de.md").read_text(encoding="utf-8")

    assert len(EXPECTED_SECTION_ANCHORS) == 18, "Expected 18 section anchors"

    for anchor in EXPECTED_SECTION_ANCHORS:
        assert f"({anchor})" in en_content, f"Section link {anchor} missing in README.md"
        assert f'id="{anchor[1:]}"' in en_content, f"Anchor id {anchor[1:]} missing in README.md"
        assert f"({anchor})" in de_content, f"Section link {anchor} missing in README_de.md"
        assert f'id="{anchor[1:]}"' in de_content, f"Anchor id {anchor[1:]} missing in README_de.md"

    for legacy in LEGACY_EN_ANCHORS:
        assert f'id="{legacy}"' in en_content, f"Legacy EN anchor {legacy} missing in README.md"

    for legacy in LEGACY_DE_ANCHORS:
        assert f'id="{legacy}"' in de_content, f"Legacy DE anchor {legacy} missing in README_de.md"


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

    assert "PERSONA-01" in en_content
    assert "PERSONA-02" in en_content
    assert "PERSONA-03" in en_content
    assert "PERSONA-04" in en_content

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


def test_third_party_licenses_audit_and_sbom():
    """Verify THIRD_PARTY_LICENSES.md structure, Level 1 SBOM, and NOTICE cross-reference."""
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
    assert "NOTICE" in content
    assert "2026-09-26" in content
    assert "RunAsInvoker" in content
    assert "INV-USER-02" in content
    assert "Level 1 SBOM Invariant Cross-Reference Matrix" in content
    for inv in INVARIANTS:
        assert inv in content, f"Invariant {inv} missing from SBOM table in THIRD_PARTY_LICENSES.md"


def test_pep621_metadata_and_topics():
    """Verify PEP 621 extended project URLs, license-files, and 20 topics in pyproject.toml."""
    pyproject_path = ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    # license-files
    project = data["project"]
    assert "license-files" in project
    assert "NOTICE" in project["license-files"]
    assert "LICENSE" in project["license-files"]
    assert "THIRD_PARTY_LICENSES.md" in project["license-files"]
    assert "THIRD_PARTY_LICENSES.txt" in project["license-files"]

    # 20 topics / keywords
    keywords = project.get("keywords", [])
    assert len(keywords) == 20, f"Expected 20 keywords in pyproject.toml, found {len(keywords)}"
    for topic in EXPECTED_TOPICS:
        assert topic in keywords, f"Topic {topic} missing from pyproject.toml keywords"

    # URLs
    urls = project["urls"]
    assert "Third-Party Licenses" in urls
    assert "Marketing Log" in urls
    assert "LLM Ready" in urls
    assert "Security Policy" in urls
    assert "Issues" in urls
    assert "Changelog" in urls
    assert "Notice" in urls
    assert "blob/master/NOTICE" in urls["Notice"]
    assert "Bug Tracker" in urls
    assert "Parent Organization" in urls
    assert "Umbrella Ecosystem" in urls


def test_statutory_notice_and_version_freeze():
    """Verify Section 18 statutory notice (§ 521 BGB) and strict version freeze (T-20260920-167562623)."""
    en_content = (ROOT / "README.md").read_text(encoding="utf-8")
    de_content = (ROOT / "README_de.md").read_text(encoding="utf-8")

    assert "§ 521 BGB" in en_content
    assert "Gefälligkeitsrecht" in en_content
    assert "§ 521 BGB" in de_content
    assert "Gefälligkeitsrecht" in de_content

    # Strict version freeze after authorized versioned source release: 1.2.1
    pyproject_path = ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    assert data["project"]["version"] == "1.2.1"


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
    assert len(workflow_files) >= 4, f"Expected at least 4 workflow files, found {len(workflow_files)}"

    for wf_path in workflow_files:
        content = wf_path.read_text(encoding="utf-8")
        assert "timeout-minutes:" in content, f"Workflow {wf_path.name} is missing timeout-minutes runaway guard"
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
    assert "cancel-in-progress: true" in content
    assert "issues: write" in content
    assert "pull-requests: write" in content


def test_welcome_workflow_present_and_valid():
    """Verify welcome.yml workflow presence, action version, permissions, and timeouts."""
    welcome_path = ROOT / ".github" / "workflows" / "welcome.yml"
    assert welcome_path.exists(), "welcome.yml workflow missing"
    content = welcome_path.read_text(encoding="utf-8")
    assert "actions/first-interaction@v3" in content
    assert "timeout-minutes: 5" in content
    assert "cancel-in-progress: true" in content
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
        "*-ASUS-GEI*",
        "*-WORKSTATION*",
        "*-WORKSTATION-LG*",
        "*_WORKSTATION*",
        "*_WORKSTATION-LG*",
        "*-WORKSTATION.*",
        "*-WORKSTATION-LG.*",
        "*-LAPTOP*",
        "*-Mac Studio*",
        "*-MacBook*",
        "*-IDEAPAD*",
        "*.sync-conflict-*",
        "LOCK",
        "LOCK.*",
        "LOCK.user.*",
        "LOCK.until.*",
        "LOCK.condition.*",
        "LOCK.permissions.json",
        ".automation-lock",
        "uv.lock",
        ".coverage",
        ".ruff_cache/",
        ".pytest_temp/",
        ".pytest_tmp*/",
        ".nyc_output/",
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
    assert pytest_opts.get("minversion") == "7.0"
    assert "addopts" in pytest_opts, "addopts missing from [tool.pytest.ini_options]"
    assert "-ra -v --basetemp=.pytest_temp" in pytest_opts["addopts"]
    norecursedirs = pytest_opts.get("norecursedirs", [])
    assert ".pytest_temp" in norecursedirs
    assert ".hypothesis" in norecursedirs

    # Ruff configuration
    ruff_select = data.get("tool", {}).get("ruff", {}).get("lint", {}).get("select", [])
    assert "C4" in ruff_select, "C4 rule missing from [tool.ruff.lint] select"


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


def test_changelog_and_marketing_records():
    """Verify CHANGELOG.md and MARKETING-LOG.txt document Pfad A and Pfad B records."""
    changelog_content = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    marketing_content = (ROOT / "MARKETING-LOG.txt").read_text(encoding="utf-8")

    assert "Pfad A Technical Hygiene" in changelog_content
    assert "2026-10-01" in changelog_content
    assert "2026-09-26" in changelog_content
    assert "2026-09-14" in changelog_content
    assert "welcome.yml" in changelog_content
    assert "auto-assign.yml" in changelog_content
    assert "label-sync.yml" in changelog_content
    assert "PFAD_A_TECHNICAL_HYGIENE_AND_CI_HARDENING" in marketing_content
    assert "2026-10-01" in marketing_content
    assert "2026-09-26" in marketing_content

    assert "PFAD_B_DISCOVERABILITY_AND_DESIGN" in marketing_content
    assert "2026-10-03" in changelog_content
    assert "2026-10-03 01:50 CEST" in marketing_content
    assert "2026-09-22" in marketing_content
    assert "18-POINT BILINGUAL NAVIGATION" in marketing_content


def test_auto_assign_workflow_present_and_valid():
    """Verify auto-assign.yml presence, action version, permissions, and timeout."""
    auto_assign_path = ROOT / ".github" / "workflows" / "auto-assign.yml"
    assert auto_assign_path.exists(), "auto-assign.yml workflow missing"
    content = auto_assign_path.read_text(encoding="utf-8")
    assert "actions/github-script@v7" in content
    assert "timeout-minutes: 5" in content
    assert "cancel-in-progress: true" in content
    assert "pull-requests: write" in content
    assert "issues: write" in content


def test_label_sync_workflow_and_labels_present():
    """Verify label-sync.yml and labels.yml presence, action version, and labels."""
    label_sync_path = ROOT / ".github" / "workflows" / "label-sync.yml"
    assert label_sync_path.exists(), "label-sync.yml workflow missing"
    ls_content = label_sync_path.read_text(encoding="utf-8")
    assert "EndBug/label-sync@v2" in ls_content
    assert "timeout-minutes: 5" in ls_content
    assert "cancel-in-progress: true" in ls_content
    assert "issues: write" in ls_content

    labels_path = ROOT / ".github" / "labels.yml"
    assert labels_path.exists(), ".github/labels.yml missing"
    labels_content = labels_path.read_text(encoding="utf-8")
    assert "name: bug" in labels_content
    assert "name: enhancement" in labels_content
    assert "name: documentation" in labels_content
    assert "name: wontfix" in labels_content


def test_contributing_guide_present_and_invariants():
    """Verify CONTRIBUTING.md presence, bilingual text, 10 invariants, and Plan D."""
    contrib_path = ROOT / "CONTRIBUTING.md"
    assert contrib_path.exists(), "CONTRIBUTING.md missing"
    content = contrib_path.read_text(encoding="utf-8")
    assert "## English" in content
    assert "## Deutsch" in content
    assert "RunAsInvoker" in content
    assert "INV-USER-02" in content
    assert "T-20260920-167562623" in content
    assert "T-20261003-933110552" in content
    assert "1.2.1" in content
    assert "Plan D" in content
    for inv in INVARIANTS:
        assert inv in content, f"Invariant {inv} missing in CONTRIBUTING.md"


def test_third_party_licenses_plain_text_companion_invariants():
    """Verify THIRD_PARTY_LICENSES.txt Level 1 SBOM text companion structure and invariants."""
    txt_path = ROOT / "THIRD_PARTY_LICENSES.txt"
    assert txt_path.exists(), "THIRD_PARTY_LICENSES.txt missing"
    content = txt_path.read_text(encoding="utf-8")
    assert "doc-bricks/UniversalMailCleaner" in content
    assert "2026-10-03" in content or "2026-10-01" in content
    assert "RunAsInvoker" in content
    assert "§ 521 BGB" in content
    assert "NOTICE" in content
    for inv in INVARIANTS:
        assert inv in content, f"Invariant {inv} missing in THIRD_PARTY_LICENSES.txt"


def test_pep621_extended_urls_and_license_files():
    """Verify Contributing, Plain-Text License, Third-Party Licenses Text, and Level 1 SBOM URLs."""
    pyproject_path = ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    urls = data["project"]["urls"]
    assert "Contributing" in urls
    assert "Plain-Text License" in urls
    assert "Third-Party Licenses (Text)" in urls
    assert "Level 1 SBOM" in urls
    license_files = data["project"]["license-files"]
    assert "THIRD_PARTY_LICENSES.txt" in license_files
    assert "NOTICE" in license_files


def test_extended_gitignore_multihost_and_lock_defense():
    """Verify .gitignore includes Desktop.ini, IDEAPAD-GEI, and canonical lock patterns."""
    gi_path = ROOT / ".gitignore"
    assert gi_path.exists(), ".gitignore missing"
    content = gi_path.read_text(encoding="utf-8")
    for pattern in ["Desktop.ini", "*-IDEAPAD-GEI*", "LOCK.dev.*", "LOCK.antigravity.*", "LOCK.bugsearch.*", "TASKPLAN_*.md"]:
        assert pattern in content, f"Pattern {pattern} missing in .gitignore"


def test_ascii_four_view_architectural_topology_parity():
    """Verify ASCII Four-View Architectural Topology in README.md and README_de.md."""
    en_content = (ROOT / "README.md").read_text(encoding="utf-8")
    de_content = (ROOT / "README_de.md").read_text(encoding="utf-8")

    en_views = [
        "[VIEW 1: CALLER RUNTIMES, DESKTOP USER INTERACTION & UI CONTROLS]",
        "[VIEW 2: UNIVERSALMAILCLEANER CORE FILTER & ASYNCHRONOUS WORKER ENGINE]",
        "[VIEW 3: SECURE OS KEYRING & PROTOCOL STORAGE TIERS / IMAP & GMAIL APIS]",
        "[VIEW 4: AIR-GAP DEFENSE PERIMETER, ZERO-EGRESS & DATA SAFETY BOUNDARIES]",
    ]
    for view in en_views:
        assert view in en_content, f"English topology view missing in README.md: {view}"

    de_views = [
        "[SICHT 1: DESKTOP-BENUTZEROBERFLÄCHE & INTERAKTIONS-SCHICHT]",
        "[SICHT 2: UNIVERSALMAILCLEANER KERN-ENGINE & ASYNCHRONE WORKER]",
        "[SICHT 3: ZUGANGSDATEN-SCHUTZ & PROTOKOLL-ENDPUNKTE (IMAP & GMAIL)]",
        "[SICHT 4: LOKALER SCHUTZPERIMETER, ZERO-EGRESS & WIDERRUFS-SICHERHEIT]",
    ]
    for view in de_views:
        assert view in de_content, f"German topology view missing in README_de.md: {view}"

    for inv in INVARIANTS:
        assert inv in en_content
        assert inv in de_content


def test_recency_and_badge_currency():
    """Verify 2026-10-03 currency across badges, llms.txt, SBOM, and CHANGELOG."""
    en_content = (ROOT / "README.md").read_text(encoding="utf-8")
    de_content = (ROOT / "README_de.md").read_text(encoding="utf-8")
    llms_content = (ROOT / "llms.txt").read_text(encoding="utf-8")
    tpl_content = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
    txt_content = (ROOT / "THIRD_PARTY_LICENSES.txt").read_text(encoding="utf-8")
    changelog_content = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    mkt_content = (ROOT / "MARKETING-LOG.txt").read_text(encoding="utf-8")

    assert "Last--Checked-2026--10--03-blue" in en_content
    assert "Zuletzt--Gepr%C3%BCft-2026--10--03-blue" in de_content
    assert "Last-checked: 2026-10-03" in llms_content
    assert "Audit Date:** 2026-10-03" in tpl_content
    assert "Audit Date: 2026-10-03" in txt_content
    assert "2026-10-03" in changelog_content
    assert "2026-10-03 01:50 CEST" in mkt_content


def test_third_party_licenses_plain_text_companion_recency():
    """Verify THIRD_PARTY_LICENSES.txt Level 1 SBOM text companion recency and invariants."""
    txt_path = ROOT / "THIRD_PARTY_LICENSES.txt"
    assert txt_path.exists()
    content = txt_path.read_text(encoding="utf-8")
    assert "2026-10-03" in content
    assert "doc-bricks/UniversalMailCleaner" in content
    assert "RunAsInvoker" in content
    assert "§ 521 BGB" in content
    assert "NOTICE" in content
    for inv in INVARIANTS:
        assert inv in content
