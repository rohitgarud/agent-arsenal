"""Tests for the config module."""

import json
from pathlib import Path

from agent_arsenal.config import (
    DEFAULT_CONFIG,
    add_command_directory,
    get_command_directories,
    get_config_path,
    list_command_directories,
    load_config,
    remove_command_directory,
    save_config,
)


class TestGetConfigPath:
    """Tests for get_config_path function."""

    def test_returns_path_with_settings_json(self):
        """Config path should end with settings.json."""
        path = get_config_path()
        assert path.name == "settings.json"

    def test_returns_path_in_arsenal_dir(self):
        """Config path should be in ~/.arsenal/."""
        path = get_config_path()
        assert ".arsenal" in str(path)


class TestLoadConfig:
    """Tests for load_config function."""

    def test_returns_default_when_file_missing(self):
        """Should return default config when file doesn't exist."""
        config = load_config()
        assert config == DEFAULT_CONFIG

    def test_returns_default_when_file_empty(self, mock_config_file: Path):
        """Should return default config when file is empty."""
        mock_config_file.write_text("")
        config = load_config()
        assert config == DEFAULT_CONFIG

    def test_returns_default_when_json_invalid(self, mock_config_file: Path):
        """Should return default config when JSON is invalid."""
        mock_config_file.write_text("not valid json {")
        config = load_config()
        assert config == DEFAULT_CONFIG

    def test_returns_config_when_valid(
        self, mock_config_file: Path, sample_config: dict
    ):
        """Should return config when file is valid JSON."""
        mock_config_file.write_text(json.dumps(sample_config))
        config = load_config()
        assert config == sample_config

    def test_adds_missing_command_directories_key(
        self, mock_config_file: Path
    ):
        """Should add missing command_directories key."""
        mock_config_file.write_text('{"other": "data"}')
        config = load_config()
        assert "command_directories" in config
        assert config["command_directories"] == []


class TestSaveConfig:
    """Tests for save_config function."""

    def test_creates_config_file(self, sample_config: dict):
        """Should create config file if it doesn't exist."""
        save_config(sample_config)
        config_path = get_config_path()
        assert config_path.exists()

    def test_saves_valid_json(self, sample_config: dict):
        """Should save valid JSON to file."""
        save_config(sample_config)
        config_path = get_config_path()
        content = json.loads(config_path.read_text())
        assert content == sample_config

    def test_overwrites_existing_config(self, sample_config: dict):
        """Should overwrite existing config."""
        # Write initial config
        initial = {"command_directories": ["/initial"]}
        save_config(initial)

        # Overwrite with new config
        save_config(sample_config)

        config_path = get_config_path()
        content = json.loads(config_path.read_text())
        assert content == sample_config


class TestAddCommandDirectory:
    """Tests for add_command_directory function."""

    def test_adds_new_directory(self):
        """Should add a new directory to config."""
        result = add_command_directory("/tmp/new-directory")
        assert result is True

        config = load_config()
        assert "/tmp/new-directory" in config["command_directories"]

    def test_returns_false_for_duplicate(self):
        """Should return False for duplicate directory."""
        add_command_directory("/tmp/test-dup")

        result = add_command_directory("/tmp/test-dup")
        assert result is False

    def test_converts_relative_to_absolute(self):
        """Should convert relative paths to absolute."""
        result = add_command_directory("relative-path")
        assert result is True

        config = load_config()
        assert len(config["command_directories"]) == 1
        # Should be an absolute path now
        assert Path(config["command_directories"][0]).is_absolute()

    def test_accepts_string_path(self):
        """Should accept string paths."""
        result = add_command_directory("/tmp/string-path")
        assert result is True


class TestRemoveCommandDirectory:
    """Tests for remove_command_directory function."""

    def test_removes_existing_directory(self):
        """Should remove an existing directory."""
        add_command_directory("/tmp/to-remove")
        result = remove_command_directory("/tmp/to-remove")
        assert result is True

        config = load_config()
        assert "/tmp/to-remove" not in config["command_directories"]

    def test_returns_false_for_nonexistent(self):
        """Should return False for non-existent directory."""
        result = remove_command_directory("/tmp/does-not-exist")
        assert result is False

    def test_removes_only_specified_directory(self):
        """Should only remove the specified directory."""
        add_command_directory("/tmp/dir1")
        add_command_directory("/tmp/dir2")

        remove_command_directory("/tmp/dir1")

        config = load_config()
        assert "/tmp/dir1" not in config["command_directories"]
        assert "/tmp/dir2" in config["command_directories"]


class TestListCommandDirectories:
    """Tests for list_command_directories function."""

    def test_returns_empty_list_when_none(self):
        """Should return empty list when no directories."""
        dirs = list_command_directories()
        assert dirs == []

    def test_returns_list_of_paths(self):
        """Should return list of Path objects."""
        add_command_directory("/tmp/path1")
        add_command_directory("/tmp/path2")

        dirs = list_command_directories()
        assert len(dirs) == 2
        assert all(isinstance(d, Path) for d in dirs)


class TestGetCommandDirectories:
    """Tests for get_command_directories function."""

    def test_same_as_list_command_directories(self):
        """Should return same as list_command_directories."""
        add_command_directory("/tmp/test")
        assert get_command_directories() == list_command_directories()
