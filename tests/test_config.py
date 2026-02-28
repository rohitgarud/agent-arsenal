"""Tests for the config module."""

import json
from pathlib import Path
from unittest.mock import patch


from agent_arsenal.config import (
    DEFAULT_CONFIG,
    add_command_directory,
    get_command_directories,
    get_config_path,
    get_sandbox_permissions_for_command,
    get_user_commands_dir,
    list_command_directories,
    load_config,
    load_sandbox_config,
    remove_command_directory,
    save_config,
    save_sandbox_config,
)
from agent_arsenal.sandbox import SandboxConfig, SandboxPermissions


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

    def test_adds_missing_command_directories_key(self, mock_config_file: Path):
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


class TestGetUserCommandsDir:
    """Tests for get_user_commands_dir function."""

    def test_returns_path_with_commands_suffix(self):
        """Path should end with .arsenal/commands."""
        path = get_user_commands_dir()
        assert path.name == "commands"
        assert ".arsenal" in str(path)

    def test_returns_absolute_path(self):
        """Should return an absolute path."""
        path = get_user_commands_dir()
        assert path.is_absolute()


class TestUserCommandsAutoDiscovery:
    """Tests for auto-discovery of ~/.arsenal/commands/."""

    def test_includes_user_commands_dir_when_exists(self, monkeypatch, temp_dir: Path):
        """Should include ~/.arsenal/commands/ when it exists."""
        user_commands = temp_dir / ".arsenal" / "commands"
        user_commands.mkdir(parents=True)

        # Mock Path.home() to return our temp_dir
        monkeypatch.setattr("agent_arsenal.config.Path.home", lambda: temp_dir)

        dirs = get_command_directories()
        assert user_commands in dirs

    def test_does_not_include_when_not_exists(self, monkeypatch, temp_dir: Path):
        """Should not include when directory doesn't exist."""
        # Mock Path.home() to return our temp_dir
        monkeypatch.setattr("agent_arsenal.config.Path.home", lambda: temp_dir)

        dirs = get_command_directories()
        user_commands = temp_dir / ".arsenal" / "commands"
        assert user_commands not in dirs

    def test_no_duplicate_when_already_in_config(self, monkeypatch, temp_dir: Path):
        """Should not add duplicate if already in config."""
        user_commands = temp_dir / ".arsenal" / "commands"
        user_commands.mkdir(parents=True)

        # Add to config first
        add_command_directory(str(user_commands))

        # Mock Path.home() to return our temp_dir
        monkeypatch.setattr("agent_arsenal.config.Path.home", lambda: temp_dir)

        dirs = get_command_directories()
        # Should only have one entry
        assert dirs.count(user_commands) == 1

    def test_user_commands_loaded_alongside_config_dirs(
        self, monkeypatch, temp_dir: Path
    ):
        """Should load user commands alongside manually configured dirs."""
        user_commands = temp_dir / ".arsenal" / "commands"
        user_commands.mkdir(parents=True)

        custom_dir = temp_dir / "custom-commands"
        custom_dir.mkdir()
        add_command_directory(str(custom_dir))

        # Mock Path.home() to return our temp_dir
        monkeypatch.setattr("agent_arsenal.config.Path.home", lambda: temp_dir)

        dirs = get_command_directories()
        assert user_commands in dirs
        assert custom_dir in dirs


class TestLoadSandboxConfig:
    """Tests for load_sandbox_config function."""

    def test_returns_default_when_file_missing(self, monkeypatch, mock_config_file: Path):
        """Should return default config when file doesn't exist."""
        # Don't write any file - the isolate_config fixture creates empty dir
        with patch("agent_arsenal.sandbox.DenoSandboxExecutor") as mock_executor:
            mock_instance = mock_executor.return_value
            mock_instance._check_deno_available.return_value = True

            config = load_sandbox_config()
            assert config.enabled is True
            assert config.timeout_seconds == 30
            assert isinstance(config.default_permissions, SandboxPermissions)

    def test_returns_default_when_sandbox_section_missing(
        self, monkeypatch, mock_config_file: Path
    ):
        """Should return defaults when sandbox section not in config."""
        # Write config without sandbox section
        mock_config_file.write_text('{"command_directories": []}')

        with patch("agent_arsenal.sandbox.DenoSandboxExecutor") as mock_executor:
            mock_instance = mock_executor.return_value
            mock_instance._check_deno_available.return_value = True

            config = load_sandbox_config()
            assert config.enabled is True
            assert config.timeout_seconds == 30
            assert isinstance(config.default_permissions, SandboxPermissions)

    def test_parses_valid_sandbox_config(
        self, monkeypatch, tmp_path: Path
    ):
        """Should parse valid sandbox config from file."""
        # Write to the actual config path that get_config_path returns
        config_path = get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            json.dumps({
                "command_directories": [],
                "sandbox": {
                    "enabled": False,
                    "timeout_seconds": 60,
                    "default_permissions": {
                        "allow_read": ["/tmp"],
                        "allow_write": ["/tmp"],
                        "allow_net": True,
                        "allow_env": ["HOME"],
                        "allow_run": ["bash"],
                    },
                },
            })
        )

        with patch("agent_arsenal.sandbox.DenoSandboxExecutor") as mock_executor:
            mock_instance = mock_executor.return_value
            mock_instance._check_deno_available.return_value = True

            config = load_sandbox_config()
            assert config.enabled is False
            assert config.timeout_seconds == 60
            assert config.default_permissions.allow_read == ["/tmp"]
            assert config.default_permissions.allow_write == ["/tmp"]
            assert config.default_permissions.allow_net is True
            assert config.default_permissions.allow_env == ["HOME"]
            assert config.default_permissions.allow_run == ["bash"]

    def test_disables_sandbox_when_deno_not_available(
        self, monkeypatch, tmp_path: Path
    ):
        """Should disable sandbox when Deno is not installed."""
        # Write to the actual config path that get_config_path returns
        config_path = get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            json.dumps({
                "sandbox": {
                    "enabled": True,
                    "timeout_seconds": 30,
                },
            })
        )

        with patch("agent_arsenal.sandbox.DenoSandboxExecutor") as mock_executor:
            mock_instance = mock_executor.return_value
            mock_instance._check_deno_available.return_value = False

            config = load_sandbox_config()
            assert config.enabled is False


class TestSaveSandboxConfig:
    """Tests for save_sandbox_config function."""

    def test_creates_config_file(self, monkeypatch, mock_config_file: Path):
        """Should create config file if it doesn't exist."""
        config = SandboxConfig(enabled=True, timeout_seconds=30)
        save_sandbox_config(config)

        config_path = get_config_path()
        assert config_path.exists()

    def test_saves_valid_json(self, monkeypatch, mock_config_file: Path):
        """Should save valid JSON to file."""
        perms = SandboxPermissions(
            allow_read=["/tmp"],
            allow_write=["/tmp"],
            allow_net=False,
            allow_env=["HOME"],
            allow_run=False,
        )
        config = SandboxConfig(enabled=True, timeout_seconds=60, default_permissions=perms)
        save_sandbox_config(config)

        config_path = get_config_path()
        content = json.loads(config_path.read_text())
        assert "sandbox" in content
        assert content["sandbox"]["enabled"] is True
        assert content["sandbox"]["timeout_seconds"] == 60

    def test_handles_allow_run_as_bool(self, monkeypatch, mock_config_file: Path):
        """Should save allow_run when it's a boolean."""
        perms = SandboxPermissions(allow_run=True)
        config = SandboxConfig(enabled=True, default_permissions=perms)
        save_sandbox_config(config)

        content = json.loads(get_config_path().read_text())
        assert content["sandbox"]["default_permissions"]["allow_run"] is True

    def test_handles_allow_run_as_list(self, monkeypatch, mock_config_file: Path):
        """Should save allow_run when it's a list."""
        perms = SandboxPermissions(allow_run=["bash", "python"])
        config = SandboxConfig(enabled=True, default_permissions=perms)
        save_sandbox_config(config)

        content = json.loads(get_config_path().read_text())
        assert content["sandbox"]["default_permissions"]["allow_run"] == ["bash", "python"]


class TestGetSandboxPermissionsForCommand:
    """Tests for get_sandbox_permissions_for_command function."""

    def test_returns_global_defaults_when_no_override(self):
        """Should return global defaults when no command-specific overrides."""
        global_config = SandboxConfig(
            default_permissions=SandboxPermissions(
                allow_read=["/home"],
                allow_net=True,
            )
        )
        frontmatter = {}

        perms = get_sandbox_permissions_for_command(frontmatter, global_config)

        assert perms.allow_read == ["/home"]
        assert perms.allow_net is True

    def test_merges_command_specific_permissions(self):
        """Should merge command-specific permissions with global defaults."""
        global_config = SandboxConfig(
            default_permissions=SandboxPermissions(
                allow_read=["/home"],
                allow_write=[],
                allow_net=False,
                allow_env=[],
                allow_run=False,
            )
        )
        frontmatter = {
            "sandbox_permissions": {
                "allow_read": ["/tmp"],
                "allow_net": True,
            }
        }

        perms = get_sandbox_permissions_for_command(frontmatter, global_config)

        # Command-specific should override
        assert perms.allow_read == ["/tmp"]
        assert perms.allow_net is True
        # Global should remain when not overridden
        assert perms.allow_write == []
        assert perms.allow_env == []
        assert perms.allow_run is False

    def test_returns_defaults_when_frontmatter_not_dict(self):
        """Should return global defaults when sandbox_permissions is not a dict."""
        global_config = SandboxConfig(
            default_permissions=SandboxPermissions(
                allow_read=["/home"],
            )
        )
        frontmatter = {"sandbox_permissions": "not a dict"}

        perms = get_sandbox_permissions_for_command(frontmatter, global_config)

        assert perms.allow_read == ["/home"]

    def test_partial_override(self):
        """Should only override specified permissions."""
        global_config = SandboxConfig(
            default_permissions=SandboxPermissions(
                allow_read=["/home", "/data"],
                allow_write=["/tmp"],
                allow_net=False,
                allow_env=["HOME", "PATH"],
                allow_run=["bash"],
            )
        )
        frontmatter = {
            "sandbox_permissions": {
                "allow_net": True,
            }
        }

        perms = get_sandbox_permissions_for_command(frontmatter, global_config)

        assert perms.allow_read == ["/home", "/data"]
        assert perms.allow_write == ["/tmp"]
        assert perms.allow_net is True
        assert perms.allow_env == ["HOME", "PATH"]
        assert perms.allow_run == ["bash"]
