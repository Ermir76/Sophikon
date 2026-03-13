"""
Helpers for local media storage paths/URLs.
"""

from pathlib import Path

from app.core.config import settings


def get_backend_root() -> Path:
    """Return backend project root (parent of app/)."""
    return Path(__file__).resolve().parents[2]


def get_media_root() -> Path:
    """Resolve configured media root to an absolute path."""
    root = Path(settings.MEDIA_ROOT)
    if root.is_absolute():
        return root
    return get_backend_root() / root


def get_avatar_directory() -> Path:
    """Absolute local directory for avatar files."""
    return get_media_root() / settings.AVATAR_UPLOAD_SUBDIR


def ensure_media_directories() -> None:
    """Create media directories if they do not already exist."""
    get_avatar_directory().mkdir(parents=True, exist_ok=True)


def build_media_url(relative_path: Path) -> str:
    """Build a public media URL from a media-root relative path."""
    prefix = settings.MEDIA_URL_PREFIX.rstrip("/")
    relative = relative_path.as_posix().lstrip("/")
    return f"{prefix}/{relative}"


def get_media_relative_path_from_url(url: str | None) -> Path | None:
    """
    Parse a local media URL back into a media-root relative path.

    Returns None when URL is external or does not use MEDIA_URL_PREFIX.
    """
    if not url:
        return None
    prefix = settings.MEDIA_URL_PREFIX.rstrip("/")
    if not url.startswith(f"{prefix}/"):
        return None
    remainder = url.removeprefix(f"{prefix}/").strip()
    if not remainder:
        return None
    return Path(remainder)
