import logging
import time
from ctypes import GetLastError, WinDLL, c_size_t, c_void_p, create_unicode_buffer
from ctypes.wintypes import BOOL, DWORD, HANDLE, LPCWSTR

from .common import (
    ConnectionError,
    InterfaceError,
    StatusCode,
)
from .interface import PluginInterface, PluginInterfaceStructure

# Shared memory constants
SHARED_MEMORY_PREFIX = "BI"
DEFAULT_BUFFER_SIZE = 4096
CONNECTION_TIMEOUT = 5000  # milliseconds
FILE_MAP_ALL_ACCESS = 0xF001F

class WindowsAPI:
    """Windows API wrapper for shared memory operations."""

    def __init__(self) -> None:
        """Initialize Windows API handles."""
        self.kernel32 = WinDLL('kernel32', use_last_error=True)

        # Setup function signatures
        self.OpenFileMapping = self.kernel32.OpenFileMappingW
        self.OpenFileMapping.argtypes = [
            DWORD,
            BOOL,
            LPCWSTR
        ]
        self.OpenFileMapping.restype = HANDLE

        self.MapViewOfFile = self.kernel32.MapViewOfFile
        self.MapViewOfFile.argtypes = [
            HANDLE,
            DWORD,
            DWORD,
            DWORD,
            c_size_t
        ]
        self.MapViewOfFile.restype = c_void_p

        self.UnmapViewOfFile = self.kernel32.UnmapViewOfFile
        self.UnmapViewOfFile.argtypes = [c_void_p]
        self.UnmapViewOfFile.restype = BOOL

        self.CloseHandle = self.kernel32.CloseHandle
        self.CloseHandle.argtypes = [HANDLE]
        self.CloseHandle.restype = BOOL

        self.GetLastError = GetLastError
        self.FormatMessage = self.kernel32.FormatMessageW

    def get_last_error(self) -> str:
        """Get formatted Windows error message."""
        error_code = self.GetLastError()
        if error_code == 0:
            return "No error"

        # Format the error message
        buffer = create_unicode_buffer(256)
        self.FormatMessage(
            0x00001000,  # FORMAT_MESSAGE_FROM_SYSTEM
            None,
            error_code,
            0,
            buffer,
            len(buffer),
            None
        )

        return f"Error {error_code}: {buffer.value.strip()}"

class PluginConnection:
    """
    Manages shared memory connection to BurnInTest.

    Handles connection lifecycle, error recovery, and provides
    access to the PluginInterface for communication.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """
        Initialize connection manager.

        Args:
            logger: Optional logger instance
        """
        self._api = WindowsAPI()
        self._logger = logger or logging.getLogger(__name__)

        # Connection state
        self._shared_memory_name: str | None = None
        self._file_mapping_handle: int | None = None
        self._mapped_address: int | None = None
        self._interface: PluginInterface | None = None
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Check if currently connected to shared memory."""
        return self._is_connected and self._interface is not None

    @property
    def shared_memory_name(self) -> str | None:
        """Get shared memory name."""
        return self._shared_memory_name

    def connect(self, shared_memory_name: str, timeout_ms: int = CONNECTION_TIMEOUT) -> bool:
        """
        Connect to BurnInTest shared memory.
        
        Args:
            shared_memory_name: Name of shared memory object (must start with 'BI')
            timeout_ms: Connection timeout in milliseconds
            
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            ConnectionError: If connection fails
            ValidationError: If shared_memory_name is invalid
        """
        if self._is_connected:
            self._logger.warning("Already connected to shared memory")
            return True

        # Validate shared memory name
        if not isinstance(shared_memory_name, str):
            msg = "Shared memory name must be a string"
            raise ConnectionError(msg)

        if not shared_memory_name.startswith(SHARED_MEMORY_PREFIX):
            msg = f"Shared memory name must start with '{SHARED_MEMORY_PREFIX}'"
            raise ConnectionError(msg)

        self._shared_memory_name = shared_memory_name
        self._logger.info(f"Attempting to connect to shared memory: {shared_memory_name}")

        try:
            # Open file mapping
            self._file_mapping_handle = self._api.OpenFileMapping(
                FILE_MAP_ALL_ACCESS, False, shared_memory_name
            )

            if not self._file_mapping_handle:
                error_msg = self._api.get_last_error()
                msg = f"Failed to open file mapping: {error_msg}"
                raise ConnectionError(msg)

            self._logger.debug(f"File mapping opened successfully. Handle: {self._file_mapping_handle}")

            # Map view of file
            self._mapped_address = self._api.MapViewOfFile(
                self._file_mapping_handle, FILE_MAP_ALL_ACCESS, 0, 0, 0
            )

            if not self._mapped_address:
                error_msg = self._api.get_last_error()
                self._cleanup_handles()
                msg = f"Failed to map view of file: {error_msg}"
                raise ConnectionError(msg)

            self._logger.debug(f"View mapped at address: {self._mapped_address}")

            # Create interface structure
            try:
                structure = PluginInterfaceStructure.from_address(self._mapped_address)
                self._interface = PluginInterface(structure)
            except Exception as e:
                self._cleanup_handles()
                msg = f"Failed to create interface structure: {e}"
                raise ConnectionError(msg) from e

            # Initialize interface
            self._initialize_interface()

            # Update connection state
            self._is_connected = True

            self._logger.info(f"Successfully connected to shared memory: {shared_memory_name}")
            return True

        except ConnectionError:
            raise
        except Exception as e:
            self._cleanup_handles()
            msg = f"Unexpected error during connection: {e}"
            raise ConnectionError(msg) from e

    def disconnect(self) -> None:
        """Disconnect from shared memory and cleanup resources."""
        if not self._is_connected:
            self._logger.debug("Not connected, nothing to disconnect")
            return

        self._logger.info("Disconnecting from shared memory")

        try:
            # Set test stopped flag if interface is available
            if self._interface:
                self._interface.test_stopped = True
                self._interface.status_code = StatusCode.PLUGIN_CLEANUP
                self._logger.debug("Set test stopped flag")
        except Exception as e:
            self._logger.warning(f"Failed to set test stopped flag: {e}")

        # Cleanup resources
        self._cleanup_handles()

        # Reset state
        self._interface = None
        self._is_connected = False
        self._shared_memory_name = None

        self._logger.info("Disconnected from shared memory")

    def get_interface(self) -> PluginInterface:
        """
        Get the plugin interface.
        
        Returns:
            PluginInterface instance
            
        Raises:
            ConnectionError: If not connected
        """
        if not self._is_connected or not self._interface:
            msg = "Not connected to shared memory"
            raise ConnectionError(msg)

        return self._interface

    def _initialize_interface(self) -> None:
        """Initialize interface with default values."""
        if not self._interface:
            return

        try:
            # Set interface version
            self._interface.interface_version = 4

            # Set initial labels
            self._interface.write_label = "Write (MBytes):"
            self._interface.read_label = "Read (MBytes):"
            self._interface.verify_label = "Verify (MBytes):"

            # Set initial status
            self._interface.status = "Initializing"
            self._interface.status_code = StatusCode.PLUGIN_STARTUP

            # Enable user-defined fields
            self._interface.set_user_field(1, "Custom Field 1", "Ready", True)
            self._interface.set_user_field(2, "Custom Field 2", "Ready", True)

            # Set display text flag
            self._interface.display_text_set = True

            self._logger.debug("Interface initialized with default values")

        except Exception as e:
            msg = f"Failed to initialize interface: {e}"
            raise InterfaceError(msg) from e

    def _cleanup_handles(self) -> None:
        """Clean up Windows API handles."""
        if self._mapped_address:
            try:
                if not self._api.UnmapViewOfFile(self._mapped_address):
                    error_msg = self._api.get_last_error()
                    self._logger.warning(f"Failed to unmap view of file: {error_msg}")
                else:
                    self._logger.debug("Successfully unmapped view of file")
            except Exception as e:
                self._logger.warning(f"Error unmapping view of file: {e}")
            finally:
                self._mapped_address = None

        if self._file_mapping_handle:
            try:
                if not self._api.CloseHandle(self._file_mapping_handle):
                    error_msg = self._api.get_last_error()
                    self._logger.warning(f"Failed to close file mapping handle: {error_msg}")
                else:
                    self._logger.debug("Successfully closed file mapping handle")
            except Exception as e:
                self._logger.warning(f"Error closing file mapping handle: {e}")
            finally:
                self._file_mapping_handle = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.disconnect()

        # Don't suppress exceptions
        if exc_type is not None:
            self._logger.error(f"Exception in context: {exc_type.__name__}: {exc_val}")

        return False

    def __str__(self) -> str:
        """String representation of connection state."""
        if self._is_connected:
            return (
                f"PluginConnection(connected=True, name='{self._shared_memory_name}', "
                f"connected_time={time.time() - self._connection_time:.1f}s)"
            )
        else:
            return "PluginConnection(connected=False)"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"PluginConnection(shared_memory_name={self._shared_memory_name!r}, "
            f"is_connected={self._is_connected}, "
            f"file_mapping_handle={self._file_mapping_handle}, "
            f"mapped_address={self._mapped_address})"
        )
