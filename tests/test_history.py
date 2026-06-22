"""Tests for history.py — SQLite prompt history."""

from history import (
    clear_history,
    delete_prompt,
    export_history,
    get_history,
    get_prompt,
    save_prompt,
)


class TestSavePrompt:
    """Tests for save_prompt()."""

    def test_save_returns_id(self):
        pid = save_prompt("prebuilt", "sword_maiden", "劍姬", "女",
                          "sd", "zh", "3:4", "three_view", "test prompt")
        assert isinstance(pid, int)
        assert pid > 0
        delete_prompt(pid)  # cleanup

    def test_save_and_retrieve(self):
        pid = save_prompt("custom", "custom", "忍者", "男",
                          "mj", "en", "16:9", "expressions", "ninja prompt")
        record = get_prompt(pid)
        assert record is not None
        assert record["mode"] == "custom"
        assert record["char_label"] == "忍者"
        assert record["model"] == "mj"
        assert record["output_type"] == "expressions"
        assert record["prompt"] == "ninja prompt"
        delete_prompt(pid)

    def test_save_special_chars(self):
        pid = save_prompt("prebuilt", "test", "測試", "",
                          "sd", "zh", "", "three_view",
                          "lineart, kimono, 漢服, «test»")
        record = get_prompt(pid)
        assert record is not None
        assert "漢服" in record["prompt"]
        delete_prompt(pid)


class TestGetHistory:
    """Tests for get_history()."""

    def test_empty_history(self):
        data = get_history(page=1)
        # May not be empty due to other tests, just check structure
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data

    def test_pagination(self):
        ids = []
        for i in range(5):
            pid = save_prompt("test", f"char{i}", "", "",
                              "sd", "zh", "", "three_view", f"prompt{i}")
            ids.append(pid)
        data = get_history(page=1, per_page=3)
        assert len(data["items"]) <= 3
        data = get_history(page=2, per_page=3)
        assert len(data["items"]) > 0 or data["pages"] >= 2
        for pid in ids:
            delete_prompt(pid)

    def test_filter_by_model(self):
        pid1 = save_prompt("test", "a", "", "", "sd", "zh", "", "three_view", "p1")
        pid2 = save_prompt("test", "b", "", "", "mj", "zh", "", "three_view", "p2")
        data = get_history(page=1, model="sd")
        assert all(r["model"] == "sd" for r in data["items"])
        delete_prompt(pid1)
        delete_prompt(pid2)


class TestDeletePrompt:
    """Tests for delete_prompt()."""

    def test_delete_exists(self):
        pid = save_prompt("test", "x", "", "", "sd", "zh", "", "t", "p")
        assert delete_prompt(pid) is True
        assert get_prompt(pid) is None

    def test_delete_nonexistent(self):
        assert delete_prompt(999999) is False


class TestClearHistory:
    """Tests for clear_history()."""

    def test_clear(self):
        save_prompt("test", "a", "", "", "sd", "zh", "", "t", "p")
        save_prompt("test", "b", "", "", "mj", "zh", "", "t", "p")
        count = clear_history()
        assert count >= 2
        data = get_history(page=1)
        assert data["total"] == 0


class TestExport:
    """Tests for export_history()."""

    def test_export_json(self):
        pid = save_prompt("test", "char", "角色", "女",
                          "nai", "en", "1:1", "chibi_version", "chibi prompt")
        content = export_history(format="json")
        assert '"output_type": "chibi_version"' in content
        assert '"prompt": "chibi prompt"' in content
        delete_prompt(pid)

    def test_export_csv(self):
        pid = save_prompt("test", "char", "角色", "女",
                          "sd", "zh", "", "three_view", "csv test")
        content = export_history(format="csv")
        assert "output_type" in content.split("\n")[0]
        assert "csv test" in content
        delete_prompt(pid)
