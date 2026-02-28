"""Common exceptions for agent-arsenal."""


class ArsenalError(Exception):
    """Base exception for all agent-arsenal errors."""

    pass


class CommandNotFoundError(ArsenalError):
    """Raised when a requested command cannot be found."""

    pass


class CommandExecutionError(ArsenalError):
    """Raised when command execution fails."""

    pass


class ValidationError(ArsenalError):
    """Raised when command validation fails."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")


class ConfigurationError(ArsenalError):
    """Raised when configuration is invalid or missing."""

    pass


class StateError(ArsenalError):
    """Raised when state operations fail."""

    pass


class ExecutorError(ArsenalError):
    """Raised when executor encounters an error."""

    pass
