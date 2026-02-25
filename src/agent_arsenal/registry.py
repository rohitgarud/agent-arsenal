"""Command registry for discovering and loading commands from filesystem."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Command:
    """Represents a single command loaded from a .md file."""

    name: str
    path: Path
    parent: Optional[str] = None
    is_group: bool = False


@dataclass
class CommandGroup:
    """Represents a command group (folder)."""

    name: str
    path: Path
    description: str = ""
    commands: List[Command] = field(default_factory=list)
    subgroups: List["CommandGroup"] = field(default_factory=list)

    def __post_init__(self):
        if self.commands is None:
            self.commands = []
        if self.subgroups is None:
            self.subgroups = []


class CommandRegistry:
    """Registry for discovering and managing commands from the commands/ folder."""

    def __init__(
        self, commands_dir: Path, external_dirs: Optional[List[Path]] = None
    ):
        """Initialize the registry with a commands directory.

        Args:
            commands_dir: Path to the commands/ directory
            external_dirs: Optional list of external directories to scan for commands
        """
        self.commands_dir = commands_dir
        self.external_dirs = external_dirs or []
        self.command_tree: Dict[str, CommandGroup] = {}
        self._commands_cache: Dict[str, Command] = {}

    def scan_directory(
        self, current_dir: Optional[Path] = None, external_only: bool = False
    ) -> CommandGroup:
        """Recursively scan commands directory and build command tree.

        Args:
            current_dir: Directory to scan (defaults to commands_dir)
            external_only: If True, skip built-in commands_dir check

        Returns:
            The root CommandGroup
        """
        if current_dir is None:
            current_dir = self.commands_dir

        group_name = (
            current_dir.name
            if current_dir != self.commands_dir or external_only
            else "root"
        )
        info_file = current_dir / "info.md"
        description = ""

        if info_file.exists():
            from agent_arsenal.parser import parse_markdown_command

            fm, _ = parse_markdown_command(info_file)
            description = fm.get("description", "")

        group = CommandGroup(
            name=group_name, path=current_dir, description=description
        )

        if not current_dir.exists():
            return group

        for item in current_dir.iterdir():
            if item.is_dir():
                if not item.name.startswith(("_", ".")):
                    sub_group = self.scan_directory(
                        item, external_only=external_only
                    )
                    group.subgroups.append(sub_group)
            elif item.suffix == ".md" and item.name != "info.md":
                if not item.name.startswith(("_", ".")):
                    cmd_name = item.stem
                    # First-match-wins: skip if command already exists
                    cache_key = f"{group_name}.{cmd_name}"
                    if cache_key not in self._commands_cache:
                        group.commands.append(
                            Command(
                                name=cmd_name, path=item, parent=group_name
                            )
                        )
                        self._commands_cache[cache_key] = group.commands[-1]

        return group

    def scan_all(self) -> CommandGroup:
        """Scan built-in commands directory and all external directories.

        Built-in commands take precedence over external commands with the same name.

        Returns:
            The root CommandGroup with all commands
        """
        # Scan built-in commands directory first (takes precedence)
        root_group = self.scan_directory()

        # Scan external directories in order (lower priority)
        for ext_dir in self.external_dirs:
            if ext_dir.exists() and ext_dir.is_dir():
                self._scan_external_directory(ext_dir, root_group)

        return root_group

    def _scan_external_directory(
        self, ext_dir: Path, root_group: CommandGroup
    ) -> None:
        """Scan an external directory for commands and add them to the root group.

        External directories are flattened - all commands are added to the root group
        with 'external' as the parent prefix.

        Args:
            ext_dir: External directory to scan
            root_group: Root group to add commands to
        """
        if not ext_dir.exists() or not ext_dir.is_dir():
            return

        # Get all existing command names (for first-match-wins)
        existing_names = {cmd.name for cmd in root_group.commands}

        for item in ext_dir.iterdir():
            if item.is_dir():
                # Recursively scan subdirectories
                if not item.name.startswith(("_", ".")):
                    self._scan_external_directory(item, root_group)
            elif item.suffix == ".md" and item.name != "info.md":
                if not item.name.startswith(("_", ".")):
                    cmd_name = item.stem
                    # First-match-wins: skip if command with same name already exists
                    if cmd_name not in existing_names:
                        root_group.commands.append(
                            Command(
                                name=cmd_name, path=item, parent="external"
                            )
                        )
                        existing_names.add(cmd_name)
                        # Add to cache for lookup
                        self._commands_cache[f"external.{cmd_name}"] = (
                            root_group.commands[-1]
                        )

    def get_command(self, name: str) -> Optional[Command]:
        """Lookup command by dotted path (e.g., 'database.connect')."""
        return self._commands_cache.get(name)

    def list_commands(self, group: Optional[str] = None) -> List[Command]:
        """List all commands, optionally filtered by group.

        Args:
            group: Optional group name to filter by

        Returns:
            List of Command objects
        """
        # TODO: Implement command listing
        return []
