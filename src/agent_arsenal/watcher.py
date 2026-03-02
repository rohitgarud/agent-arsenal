"""Hot reload functionality for command files (Phase 2)."""

import logging
import threading
import time
from collections.abc import Callable, Generator
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent_arsenal.registry import CommandRegistry


logger = logging.getLogger(__name__)


def _md_filter(change: Any, path: str) -> bool:
    """Filter to only watch .md files.

    Args:
        change: The type of change (added, modified, deleted)
        path: The file path

    Returns:
        True if the file is a .md file
    """
    return path.endswith(".md")


class CommandWatcher:
    """Watch commands directory for changes and trigger reload.

    Uses watchfiles library for efficient filesystem monitoring.
    """

    def __init__(
        self,
        commands_dir: Path,
        reload_callback: Callable,
        debounce_ms: int = 500,
    ):
        """Initialize watcher.

        Args:
            commands_dir: Directory to watch
            reload_callback: Function to call on changes
            debounce_ms: Debounce time in milliseconds (default 500ms)
        """
        self.commands_dir = commands_dir
        self.reload_callback = reload_callback
        self.debounce_ms = debounce_ms
        self._watching = False
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._generator: Generator | None = None

    def start(self):
        """Start watching for file changes in background thread."""
        import watchfiles  # type: ignore[import-not-found]

        if self._watching:
            return

        self._stop_event.clear()
        self._watching = True

        # Create generator for watching
        self._generator = watchfiles.watch(
            self.commands_dir,
            watch_filter=_md_filter,
            debounce=self.debounce_ms,
            stop_event=self._stop_event,
            raise_interrupt=False,
        )

        # Start in background thread
        def watch_loop():
            last_reload = 0.0
            debounce_seconds = self.debounce_ms / 1000

            try:
                for changes in self._generator:  # type: ignore
                    if not changes:
                        continue

                    # Debounce
                    current_time = time.time()
                    if current_time - last_reload < debounce_seconds:
                        continue

                    last_reload = current_time

                    # Call reload callback
                    try:
                        self.reload_callback()
                    except Exception as e:
                        logger.warning("Watcher callback error (non-fatal): %s", e)

                    # Check if we should stop
                    if self._stop_event.is_set():
                        break

            except Exception as e:
                logger.warning("Watcher error (non-fatal): %s", e)
            finally:
                self._watching = False

        self._thread = threading.Thread(target=watch_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop watching."""
        self._stop_event.set()
        self._watching = False

        if self._generator:
            try:
                self._generator.close()
            except Exception as e:
                logger.debug("Error closing watcher generator: %s", e)
            self._generator = None

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def watch(self):
        """Blocking watch loop - waits for changes and reloads."""
        import watchfiles  # type: ignore[import-not-found]

        self._stop_event.clear()
        self._watching = True

        # Create generator for watching
        generator = watchfiles.watch(
            self.commands_dir,
            watch_filter=_md_filter,
            debounce=self.debounce_ms,
            stop_event=self._stop_event,
            raise_interrupt=False,
        )

        last_reload = 0.0
        debounce_seconds = self.debounce_ms / 1000

        try:
            for changes in generator:
                # Filter for .md files only (already done by filter, but double check)
                if not changes:
                    continue

                # Debounce
                current_time = time.time()
                if current_time - last_reload < debounce_seconds:
                    continue

                last_reload = current_time

                # Call reload callback
                print(f"Detected changes in {len(changes)} file(s), reloading...")
                try:
                    self.reload_callback()
                    print("Reloaded successfully!")
                except Exception as e:
                    print(f"Error reloading: {e}")

                # Check if we should stop
                if self._stop_event.is_set():
                    break

        except KeyboardInterrupt:
            print("\nStopping watcher...")
        finally:
            self._watching = False
            try:
                generator.close()
            except Exception:
                pass

    @property
    def is_watching(self) -> bool:
        """Check if watcher is active."""
        return self._watching


def enable_hot_reload(
    commands_dir: Path,
    registry: "CommandRegistry",
    debounce_ms: int = 500,
) -> Callable[[], None]:
    """Enable hot reload for command registry.

    Args:
        commands_dir: Commands directory to watch
        registry: Registry to reload on changes
        debounce_ms: Debounce time in milliseconds

    Returns:
        Cleanup function to stop the watcher
    """
    watcher = CommandWatcher(
        commands_dir=commands_dir,
        reload_callback=registry.scan_all,
        debounce_ms=debounce_ms,
    )
    watcher.start()

    def cleanup():
        watcher.stop()

    return cleanup
