from functools import wraps
from pathlib import Path

class OutsideRootError(ValueError):
    """Raised when a path escapes the allowed root directory."""

def resolve_within(root: Path, path: str | Path) -> Path:
    """Return the resolved path, or raise OutsideRootError if it escapes root."""
    root = root.resolve()
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise OutsideRootError(f"{path!r} is outside {root}")
    return resolved

def sandboxed(root: Path | None = None):
    """
    Sandboxes agent operations to cwd
    """
    root = (root or Path.cwd()).resolve()

    def decorator(func):
        @wraps(func)
        def wrapper(path, *args, **kwargs):
            try:
                resolved = resolve_within(root, path)
            except OutsideRootError as e:
                return f"Error: {e}"  # the model sees this
            return func(resolved, *args, **kwargs)
        return wrapper
    return decorator
