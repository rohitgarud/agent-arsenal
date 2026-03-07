"""Command registry for discovering and loading commands from filesystem."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Command:
    """Represents a single command loaded from a .md file."""

    name: str
    path: Path
    parent: str | None = None
    is_group: bool = False


@dataclass
class CommandGroup:
    """Represents a command group (folder)."""

    name: str
    path: Path
    description: str = ""
    commands: list[Command] = field(default_factory=list)
    subgroups: list["CommandGroup"] = field(default_factory=list)


class CommandRegistry:
    """Registry for discovering and managing commands from the commands/ folder."""

    def __init__(self, commands_dir: Path, external_dirs: list[Path] | None = None):
        """Initialize the registry with a commands directory.

        Args:
            commands_dir: Path to the commands/ directory
            external_dirs: Optional list of external directories to scan for commands
        """
        self.commands_dir = commands_dir
        self.external_dirs = external_dirs or []
        self.command_tree: dict[str, CommandGroup] = {}
        self._commands_cache: dict[str, Command] = {}

    def scan_directory(
        self, current_dir: Path | None = None, external_only: bool = False
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

        group = CommandGroup(name=group_name, path=current_dir, description=description)

        if not current_dir.exists():
            return group

        for item in current_dir.iterdir():
            if item.is_dir():
                if not item.name.startswith(("_", ".")):
                    sub_group = self.scan_directory(item, external_only=external_only)
                    group.subgroups.append(sub_group)
            elif item.suffix == ".md" and item.name != "info.md":
                if not item.name.startswith(("_", ".")):
                    cmd_name = item.stem
                    # First-match-wins: skip if command already exists
                    cache_key = f"{group_name}.{cmd_name}"
                    if cache_key not in self._commands_cache:
                        group.commands.append(
                            Command(name=cmd_name, path=item, parent=group_name)
                        )
                        self._commands_cache[cache_key] = group.commands[-1]

        return group

    def scan_all(self) -> CommandGroup:
        """Scan built-in commands directory and all external directories.

        Built-in commands take precedence over external commands with the same name.

        Returns:
            The root CommandGroup with all commands
        """
        # Clear cache to ensure fresh scan (needed when scan_all is called multiple times)
        self._commands_cache.clear()

        # Scan built-in commands directory first (takes precedence)
        root_group = self.scan_directory()

        # Scan external directories in order (lower priority)
        for ext_dir in self.external_dirs:
            if ext_dir.exists() and ext_dir.is_dir():
                self._scan_external_directory(ext_dir, root_group)

        return root_group

    def _scan_external_directory(self, ext_dir: Path, root_group: CommandGroup) -> None:
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
                            Command(name=cmd_name, path=item, parent="external")
                        )
                        existing_names.add(cmd_name)
                        # Add to cache for lookup
                        self._commands_cache[f"external.{cmd_name}"] = (
                            root_group.commands[-1]
                        )

    def get_command(self, name: str) -> Command | None:
        """Lookup command by dotted path (e.g., 'database.connect')."""
        return self._commands_cache.get(name)

    def refresh(self) -> None:
        """Refresh the command cache by re-scanning directories.

        This clears the internal cache and re-discovers all commands,
        useful for when commands have been added or removed while
        the application is running.
        """
        self._commands_cache.clear()
        self.command_tree.clear()
        # Re-scan to populate the cache
        self.scan_all()

    def list_commands(
        self, group: str | None = None, max_depth: int | None = None
    ) -> CommandGroup:
        """List all commands as a hierarchical tree.

        Args:
            group: Optional group name to filter by (becomes new root)
            max_depth: Maximum depth to traverse (None = unlimited, 0 = show all)

        Returns:
            CommandGroup root with nested commands and subgroups
        """
        # Scan all commands to get the full tree
        root_group = self.scan_all()

        # Filter by group if specified
        if group:
            # Find the requested group in the tree
            found_group = self._find_group(root_group, group)
            if found_group is None:
                # Group not found - return empty group with the requested name
                return CommandGroup(
                    name=group,
                    path=root_group.path,
                    description=f"Group '{group}' not found",
                )
            # Apply depth limiting to the found group
            if max_depth is not None and max_depth > 0:
                return self._filter_by_depth(found_group, max_depth)
            return found_group

        # Apply depth limiting to root if specified
        if max_depth is not None and max_depth > 0:
            return self._filter_by_depth(root_group, max_depth)

        return root_group

    def _find_group(self, root: CommandGroup, group_name: str) -> CommandGroup | None:
        """Find a group by name in the command tree.

        Args:
            root: Root group to search in
            group_name: Name of the group to find

        Returns:
            CommandGroup if found, None otherwise
        """
        # Check this group
        if root.name == group_name:
            return root

        # Check subgroups recursively
        for subgroup in root.subgroups:
            found = self._find_group(subgroup, group_name)
            if found:
                return found

        # Also check root's direct commands for 'external' group
        if group_name == "external":
            return CommandGroup(
                name="external",
                path=root.path,
                description="External commands",
                commands=[cmd for cmd in root.commands if cmd.parent == "external"],
            )

        return None

    def _filter_by_depth(self, group: CommandGroup, max_depth: int) -> CommandGroup:
        """Recursively limit the depth of a command group tree.

        Args:
            group: CommandGroup to filter
            max_depth: Maximum depth (1 = root only, 2 = root + direct children, etc.)

        Returns:
            New CommandGroup with depth limiting applied
        """
        if max_depth <= 1:
            # Return shallow copy with empty subgroups/commands
            return CommandGroup(
                name=group.name,
                path=group.path,
                description=group.description,
                commands=group.commands,
                subgroups=[],  # No subgroups at depth 1
            )

        # Recursively filter subgroups
        filtered_subgroups = [
            self._filter_by_depth(subgroup, max_depth - 1)
            for subgroup in group.subgroups
        ]

        return CommandGroup(
            name=group.name,
            path=group.path,
            description=group.description,
            commands=group.commands,
            subgroups=filtered_subgroups,
        )
