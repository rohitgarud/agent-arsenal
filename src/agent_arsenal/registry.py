"""Command registry for discovering and loading commands from filesystem."""

import fnmatch
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
        self,
        group: str | None = None,
        max_depth: int | None = None,
        apply_filter: bool = True,
    ) -> CommandGroup:
        """List all commands as a hierarchical tree.

        Args:
            group: Optional group name to filter by (becomes new root)
            max_depth: Maximum depth to traverse (None = unlimited, 0 = show all)
            apply_filter: Whether to apply include/exclude filtering (default: True)

        Returns:
            CommandGroup root with nested commands and subgroups
        """
        # Scan all commands to get the full tree
        root_group = self.scan_all()

        # Apply include/exclude filtering
        if apply_filter:
            from agent_arsenal.config import load_command_filter

            filter_config = load_command_filter()
            if filter_config.get("include") or filter_config.get("exclude"):
                root_group = self.filter_commands(
                    root_group,
                    filter_config.get("include", []),
                    filter_config.get("exclude", []),
                )

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

    # =============================================================================
    # Command Filter Methods
    # =============================================================================

    def _get_all_command_paths(
        self,
        group: CommandGroup | None = None,
        prefix: str = "",
    ) -> set[str]:
        """Get all command paths in the tree as strings.

        Args:
            group: Root group to scan (defaults to full scan)
            prefix: Prefix for building path strings

        Returns:
            Set of paths like {"database/seed", "api/users/list", ...}
        """
        if group is None:
            group = self.scan_all()

        paths: set[str] = set()

        # Add commands in this group
        for cmd in group.commands:
            if prefix:
                cmd_path = f"{prefix}/{cmd.name}"
            else:
                cmd_path = cmd.name
            paths.add(cmd_path)

        # Recurse into subgroups
        for subgroup in group.subgroups:
            if prefix:
                subgroup_path = f"{prefix}/{subgroup.name}"
            else:
                subgroup_path = subgroup.name
            paths.update(self._get_all_command_paths(subgroup, subgroup_path))

        return paths

    def _matches_pattern(self, command_path: str, pattern: str) -> bool:
        """Check if command path matches a single pattern.

        Args:
            command_path: Full path like "database/seed" or group path like "database"
            pattern: Pattern to match against

        Returns:
            True if matches
        """
        # Exact match
        if command_path == pattern:
            return True

        # Group match - pattern is a group name that is a prefix of command_path
        # e.g., "database" matches "database/seed" but not "database2/seed"
        if command_path.startswith(pattern + "/"):
            return True

        # Glob patterns (fnmatch)
        # Simple glob: "api/*" matches "api/users" but not "api/users/list"
        if "*" in pattern:
            # Check if it's a recursive glob (/**)
            if pattern.endswith("/**"):
                base_pattern = pattern[:-3]  # Remove /**
                # Match base and anything after
                if command_path == base_pattern:
                    return True
                if command_path.startswith(base_pattern + "/"):
                    return True
            else:
                # For glob patterns like "api/*", also check if the group itself matches
                # "api/*" should match group "api" (meaning all commands in api)
                # First check if fnmatch matches the full path
                if fnmatch.fnmatch(command_path, pattern):
                    return True
                # Then check if the pattern without the glob suffix matches as a group
                # e.g., "api/*" -> "api" should match group "api"
                prefix = pattern.rstrip("*").rstrip("/")
                if prefix and (command_path == prefix or command_path.startswith(prefix + "/")):
                    return True

        return False

    def _matches_any_pattern(self, command_path: str, patterns: list[str]) -> bool:
        """Check if command matches any pattern in the list.

        Args:
            command_path: Full command path
            patterns: List of patterns

        Returns:
            True if matches any pattern
        """
        for pattern in patterns:
            if self._matches_pattern(command_path, pattern):
                return True
        return False

    def _get_all_subgroup_names(
        self,
        group: CommandGroup,
        prefix: str = "",
    ) -> set[str]:
        """Get all subgroup names including nested ones.

        Args:
            group: Root group to scan
            prefix: Prefix for building path strings

        Returns:
            Set of subgroup paths like {"database", "database/migrate", ...}
        """
        names: set[str] = set()

        for subgroup in group.subgroups:
            if prefix:
                subgroup_path = f"{prefix}/{subgroup.name}"
            else:
                subgroup_path = subgroup.name
            names.add(subgroup_path)
            # Recurse into subgroups
            names.update(self._get_all_subgroup_names(subgroup, subgroup_path))

        return names

    def filter_commands(
        self,
        group: CommandGroup,
        include: list[str],
        exclude: list[str],
    ) -> CommandGroup:
        """Filter command tree based on include/exclude patterns.

        Args:
            group: Root CommandGroup to filter
            include: List of patterns to include (empty = all)
            exclude: List of patterns to exclude

        Returns:
            New CommandGroup with filtering applied
        """
        # If both are empty, return original
        if not include and not exclude:
            return group

        # Get all command paths for reference
        all_paths = self._get_all_command_paths(group)
        all_groups = self._get_all_subgroup_names(group)

        # Determine which commands should be included
        included_paths: set[str] = set()

        if include:
            # Start with empty and add matches
            for pattern in include:
                # Check if pattern matches a group
                for group_name in all_groups:
                    if self._matches_pattern(group_name, pattern):
                        # Add all commands in this group
                        for path in all_paths:
                            if path.startswith(group_name + "/") or path == group_name:
                                included_paths.add(path)

                # Check if pattern matches a command
                for path in all_paths:
                    if self._matches_pattern(path, pattern):
                        included_paths.add(path)
        else:
            # No include list - include all
            included_paths = all_paths.copy()

        # Apply exclude - remove matching paths
        if exclude:
            for pattern in exclude:
                # Find all paths matching the exclude pattern
                paths_to_remove = set()
                for path in included_paths:
                    if self._matches_pattern(path, pattern):
                        paths_to_remove.add(path)
                included_paths -= paths_to_remove

        # Build filtered tree
        return self._build_filtered_tree(group, included_paths)

    def _build_filtered_tree(
        self,
        group: CommandGroup,
        included_paths: set[str],
        prefix: str = "",
    ) -> CommandGroup:
        """Build a filtered command tree.

        Args:
            group: Original CommandGroup
            included_paths: Set of paths to include
            prefix: Current path prefix

        Returns:
            New filtered CommandGroup
        """
        # Filter commands in this group
        filtered_commands: list[Command] = []
        for cmd in group.commands:
            if prefix:
                cmd_path = f"{prefix}/{cmd.name}"
            else:
                cmd_path = cmd.name

            if cmd_path in included_paths:
                filtered_commands.append(cmd)

        # Filter subgroups
        filtered_subgroups: list[CommandGroup] = []
        for subgroup in group.subgroups:
            if prefix:
                subgroup_path = f"{prefix}/{subgroup.name}"
            else:
                subgroup_path = subgroup.name

            # Check if this subgroup has any included commands
            subgroup_included = self._build_filtered_tree(
                subgroup, included_paths, subgroup_path
            )
            # Only include subgroup if it has commands or subgroups
            if subgroup_included.commands or subgroup_included.subgroups:
                filtered_subgroups.append(subgroup_included)

        return CommandGroup(
            name=group.name,
            path=group.path,
            description=group.description,
            commands=filtered_commands,
            subgroups=filtered_subgroups,
        )
