"""Data models for Universal Mail Cleaner.

Contains dataclasses for IMAP account configuration and cleanup rules.
"""
from dataclasses import dataclass, asdict


@dataclass
class MailAccount:
    """Represents an IMAP or Gmail API account configuration."""

    name: str           # display name (e.g. "My GMX")
    host: str           # e.g. imap.gmx.net (unused for Gmail API accounts)
    user: str           # e.g. user@gmx.de
    port: int = 993
    trash_folder: str = ""   # manual override, otherwise auto-detect
    protocol: str = "IMAP"   # "IMAP" or "Gmail API"

    def to_dict(self): return asdict(self)

    @classmethod
    def from_dict(cls, d):
        # Accept old config entries that lack the 'protocol' key
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass
class CleanRule:
    """Defines a cleanup rule for automatic email deletion."""

    name: str
    target_account: str  # account name or "All"
    filter_type: str     # older_than_days, subject, sender, size_mb
    value: str
    active: bool = True

    def to_dict(self): return asdict(self)

    @classmethod
    def from_dict(cls, d): return cls(**d)
