"""Pytest fixtures for Agent Arsenal tests."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(autouse=True)
def isolate_config(tmp_path, monkeypatch):
    """Isolate config for each test by using a unique temp directory."""
    config_file = tmp_path / ".arsenal" / "settings.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)

    # Import the config module fresh to ensure we patch the right thing
    import agent_arsenal.config as config_module

    # Create a function that returns our config file
    def mock_get_config_path():
        return config_file

    # Replace the function in the module
    monkeypatch.setattr(config_module, "get_config_path", mock_get_config_path)

    # Also need to patch in main module since it imports get_command_directories
    import agent_arsenal.main as main_module

    monkeypatch.setattr(main_module, "get_command_directories", lambda: [])


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config_dir(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a mock .arsenal config directory."""
    config_dir = temp_dir / ".arsenal"
    config_dir.mkdir()
    yield config_dir


@pytest.fixture
def mock_config_file(mock_config_dir: Path) -> Path:
    """Create a mock config file path."""
    return mock_config_dir / "settings.json"


@pytest.fixture
def commands_dir(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary commands directory with some test commands."""
    commands = temp_dir / "commands"
    commands.mkdir()

    # Create a simple test command
    (commands / "test-cmd.md").write_text("""---
name: test-cmd
description: A test command
execution_type: prompt
---

Test command content
""")

    # Create an info.md for the group
    (commands / "info.md").write_text("""---
name: commands
description: Test commands
---
""")

    yield commands


@pytest.fixture
def external_commands_dir(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary external commands directory."""
    external = temp_dir / "external"
    external.mkdir()

    # Create a test command
    (external / "external-cmd.md").write_text("""---
name: external-cmd
description: An external command
execution_type: prompt
---

External command content
""")

    yield external


@pytest.fixture
def sample_config() -> dict:
    """Sample configuration dictionary."""
    return {"command_directories": []}


@pytest.fixture
def populated_config(temp_dir: Path, sample_config: dict) -> dict:
    """Create a config with some directories."""
    sample_config["command_directories"] = [
        str(temp_dir / "dir1"),
        str(temp_dir / "dir2"),
    ]
    return sample_config
