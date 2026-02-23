"""Command registry for discovering and loading commands from filesystem."""

from dataclasses import dataclass
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
    commands: List[Command] = None
    subgroups: List["CommandGroup"] = None

    def __post_init__(self):
        if self.commands is None:
            self.commands = []
        if self.subgroups is None:
            self.subgroups = []


class CommandRegistry:
    """Registry for discovering and managing commands from the commands/ folder."""

    def __init__(self, commands_dir: Path):
        """Initialize the registry with a commands directory.

        Args:
            commands_dir: Path to the commands/ directory
        """
        self.commands_dir = commands_dir
        self.command_tree: Dict[str, CommandGroup] = {}
        self._commands_cache: Dict[str, Command] = {}

    def scan_directory(self, current_dir: Optional[Path] = None) -> CommandGroup:
        """Recursively scan commands directory and build command tree.

        Returns:
            The root CommandGroup
        """
        if current_dir is None:
            current_dir = self.commands_dir

        group_name = current_dir.name if current_dir != self.commands_dir else "root"
        info_file = current_dir / "info.md"
        description = ""

        if info_file.exists():
            from agent_arsenal.parser import parse_markdown_command

            fm, _ = parse_markdown_command(info_file)
            description = fm.get("description", "")

        group = CommandGroup(name=group_name, path=current_dir, description=description)

        for item in current_dir.iterdir():
            if item.is_dir():
                if not item.name.startswith(("_", ".")):
                    group.subgroups.append(self.scan_directory(item))
            elif item.suffix == ".md" and item.name != "info.md":
                if not item.name.startswith(("_", ".")):
                    cmd_name = item.stem
                    group.commands.append(
                        Command(name=cmd_name, path=item, parent=group_name)
                    )
                    self._commands_cache[f"{group_name}.{cmd_name}"] = group.commands[
                        -1
                    ]

        return group

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
        pass
