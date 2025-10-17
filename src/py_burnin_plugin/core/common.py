from datetime import datetime
from enum import Enum

# Plugin Interface Constants
PLUGIN_INTERFACE_VERSION = 4
PLUGIN_MAXDISPLAYTEXT = 20
PLUGIN_MAXERRORTEXT = 100
PLUGIN_MAXERRORTEXTLONG = 201

class ErrorSeverity(Enum):
    """Error severity levels for BurnInTest error reporting."""
    NONE = 0
    INFORMATION = 1
    WARNING = 2
    SERIOUS = 3
    CRITICAL = 4
    TERMINAL = 5

class StatusCode(Enum):
    """Status codes for BurnInTest plugin states."""
    PLUGIN_NOSTATUS = 0
    PLUGIN_STARTUP = 1
    PLUGIN_ALLOCATE = 2
    PLUGIN_WRITING = 3
    PLUGIN_READING = 4
    PLUGIN_VERIFYING = 5
    PLUGIN_WAITING = 6
    PLUGIN_CLEANUP = 7
    PLUGIN_ERROR = 8
    PRE_TEST_PLUGIN_COMPLETED = 9
    PLUGIN_MAXVAL = 10

class PluginError(Exception):
    """Base exception for BurnInTest plugin errors."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.WARNING,
        original_error: Exception | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.original_error = original_error
        self.timestamp = datetime.now()

    def __str__(self) -> str:
        return f"[{self.severity.name}] {self.message}"

class ConnectionError(PluginError):
    """Exception raised when plugin connection fails."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message, ErrorSeverity.CRITICAL, original_error)


class InterfaceError(PluginError):
    """Exception raised when interface operations fail."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message, ErrorSeverity.SERIOUS, original_error)


class ValidationError(PluginError):
    """Exception raised when data validation fails."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message, ErrorSeverity.WARNING)
        self.field = field
