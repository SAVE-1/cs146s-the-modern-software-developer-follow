from agent import check_path

def test_path_is_in_current_dir(tmp_path):
    (tmp_path / "data.txt").write_text("hello")
    assert check_path("data.txt", tmp_path)

def test_missing_file(tmp_path):
    assert not check_path("nope.txt", tmp_path)
