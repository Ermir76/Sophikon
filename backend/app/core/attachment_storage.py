"""
Helpers for private local attachment storage.

Attachment files are stored outside publicly mounted media directories and are
served only through authenticated API download endpoints.
"""

from pathlib import Path

from app.core.config import settings
from app.core.storage import get_backend_root


def get_attachment_root() -> Path:
    """Resolve configured private attachment root to an absolute path."""
    root = Path(settings.ATTACHMENT_STORAGE_ROOT)
    if not root.is_absolute():
        root = get_backend_root() / root
    return root / settings.ATTACHMENT_UPLOAD_SUBDIR


def ensure_attachment_root() -> Path:
    """Create the private attachment root directory when missing."""
    root = get_attachment_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_attachment_path(storage_path: str) -> Path | None:
    """
    Resolve a storage path within attachment root safely.

    Returns None if the path attempts traversal outside attachment root.
    """
    root = get_attachment_root().resolve()
    candidate = (root / storage_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate
