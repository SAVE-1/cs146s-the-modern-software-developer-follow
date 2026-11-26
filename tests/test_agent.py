# test_sandbox.py
import pytest
from sandbox import OutsideRootError, resolve_within, sandboxed


def test_file_inside_root(tmp_path):
    result = resolve_within(tmp_path, "a.txt")
    assert result == tmp_path.resolve() / "a.txt"


def test_dotdot_escape(tmp_path):
    with pytest.raises(OutsideRootError):
        resolve_within(tmp_path, "../outside.txt")


def test_absolute_path_escape(tmp_path):
    with pytest.raises(OutsideRootError):
        resolve_within(tmp_path, "/etc/passwd")


def test_sibling_with_same_prefix(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    (tmp_path / "proj-evil").mkdir()
    with pytest.raises(OutsideRootError):
        resolve_within(root, "../proj-evil/x.txt")


def test_symlink_escape(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("secret")
    (root / "link").symlink_to(secret)
    with pytest.raises(OutsideRootError):
        resolve_within(root, "link")


def test_decorator_blocks_and_returns_error(tmp_path):
    @sandboxed(tmp_path)
    def read_file(path):
        return path.read_text()

    assert read_file("../x.txt").startswith("Error")


def test_decorator_passes_resolved_path(tmp_path):
    (tmp_path / "a.txt").write_text("hello")

    @sandboxed(tmp_path)
    def read_file(path):
        return path.read_text()

    assert read_file("a.txt") == "hello"
