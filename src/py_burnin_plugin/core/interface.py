from ctypes import Structure, c_bool, c_char, c_int, c_int64, c_uint
from datetime import datetime

from .common import (
    PLUGIN_MAXDISPLAYTEXT,
    PLUGIN_MAXERRORTEXT,
    PLUGIN_MAXERRORTEXTLONG,
    ErrorSeverity,
    StatusCode,
    ValidationError,
)


class PluginInterfaceStructure(Structure):
#    _pack_ = 1  # Prevent padding between fields
    _fields_ = [
        ("IN_TestRunning", c_int),
        ("IN_DutyCycle", c_int),
        ("OUT_Plugin_interface_version", c_int),
        ("OUT_szWindowTitle", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_iCycle", c_uint),
        ("OUT_iStatus", c_int),
        ("OUT_szStatus", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_iErrorCount", c_int),
        ("OUT_szError", c_char * PLUGIN_MAXERRORTEXT),
        ("OUT_iErrorSeverity", c_int),
        ("OUT_szWriteOps", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_i64WriteOps", c_int64),
        ("OUT_szReadOps", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_i64ReadOps", c_int64),
        ("OUT_szVerifyOps", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_i64VerifyOps", c_int64),
        ("OUT_bUserDef1", c_bool),
        ("OUT_szUserDef1", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_szUserDefVal1", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_bUserDef2", c_bool),
        ("OUT_szUserDef2", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_szUserDefVal2", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_bDisplayTextSet", c_bool),
        ("OUT_bNewError", c_bool),
        ("OUT_bNewStatus", c_bool),
        ("OUT_bNewUserDefVal1", c_bool),
        ("OUT_bNewUserDefVal2", c_bool),
        ("OUT_bTestStopped", c_bool),
        # V3+ fields
        ("OUT_bUserDef3", c_bool),
        ("OUT_szUserDef3", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_szUserDefVal3", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_bUserDef4", c_bool),
        ("OUT_szUserDef4", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_szUserDefVal4", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_bUserDef5", c_bool),
        ("OUT_szUserDef5", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_szUserDefVal5", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_bUserDef6", c_bool),
        ("OUT_szUserDef6", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_szUserDefVal6", c_char * PLUGIN_MAXDISPLAYTEXT),
        # V4 field
        ("OUT_szErrorLong", c_char * PLUGIN_MAXERRORTEXTLONG),
    ]


class PluginInterface:
    """High-level interface for BurnInTest PLUGININTERFACE structure.

    Provides type-safe methods for accessing and manipulating shared memory
    fields with proper validation and error handling.
    """

    def __init__(self, structure: PluginInterfaceStructure) -> None:
        """Initialize interface with PLUGININTERFACE structure.

        Args:
            structure (PluginInterfaceStructure): The shared memory structure instance.

        Raises:
            ValidationError: If structure is invalid.
        """
        if not isinstance(structure, PluginInterfaceStructure):
            msg = "Invalid PLUGININTERFACE structure provided"
            raise ValidationError(msg)

        self._struct = structure
        self._last_status_update = datetime.now()
        self._last_error_update = datetime.now()

    # Input properties (read-only)
    @property
    def test_running(self) -> bool:
        """Check if BurnInTest is currently running tests."""
        return bool(self._struct.IN_TestRunning)

    @property
    def duty_cycle(self) -> int:
        """Get current duty cycle percentage (0-100)."""
        return self._struct.IN_DutyCycle

    # Output properties (read/write)
    @property
    def interface_version(self) -> int:
        """Get plugin interface version."""
        return self._struct.OUT_Plugin_interface_version

    @interface_version.setter
    def interface_version(self, version: int) -> None:
        """Set plugin interface version."""
        if not isinstance(version, int) or version < 0:
            msg = "Interface version must be a non-negative integer"
            raise ValidationError(msg)
        self._struct.OUT_Plugin_interface_version = version

    @property
    def cycle(self) -> int:
        """Get current test cycle number."""
        return self._struct.OUT_iCycle

    @cycle.setter
    def cycle(self, cycle: int) -> None:
        """Set current test cycle number."""
        if not isinstance(cycle, int) or cycle < 0:
            msg = "Cycle must be a non-negative integer"
            raise ValidationError(msg)
        self._struct.OUT_iCycle = cycle

    def increment_cycle(self) -> None:
        """Increment current test cycle number."""
        self._struct.OUT_iCycle += 1


    @property
    def status(self) -> str:
        """Get current status text."""
        return self._struct.OUT_szStatus.decode('utf-8', errors='ignore').rstrip('\x00')

    @status.setter
    def status(self, status: str) -> None:
        """Set current status text.

        Args:
            status (str): Status text.

        Raises:
            ValidationError: If status is too long.
        """
        if not isinstance(status, str):
            msg = "Status must be a string"
            raise ValidationError(msg)

        if len(status) >= PLUGIN_MAXDISPLAYTEXT:
            msg = f"Status must be less than {PLUGIN_MAXDISPLAYTEXT} characters"
            raise ValidationError(msg)

        self._struct.OUT_szStatus = status.encode()
        self._struct.OUT_bNewStatus = True
        self._last_status_update = datetime.now()

    @property
    def status_code(self) -> StatusCode:
        """Get current status code."""
        return StatusCode(self._struct.OUT_iStatus)

    @status_code.setter
    def status_code(self, code: StatusCode) -> None:
        """Set current status code."""
        if not isinstance(code, StatusCode):
            msg = "Status code must be a StatusCode enum value"
            raise ValidationError(msg)
        self._struct.OUT_iStatus = code.value

    @property
    def error_count(self) -> int:
        """Get total error count."""
        return self._struct.OUT_iErrorCount

    @error_count.setter
    def error_count(self, count: int) -> None:
        """Set total error count."""
        if not isinstance(count, int) or count < 0:
            msg = "Error count must be a non-negative integer"
            raise ValidationError(msg)
        self._struct.OUT_iErrorCount = count

    @property
    def error_message(self) -> str:
        """Get current error message."""
        return self._struct.OUT_szError.decode('utf-8', errors='ignore').rstrip('\x00')

    @error_message.setter
    def error_message(self, message: str) -> None:
        """Set current error message.

        Args:
            message (str): Error message (max 99 characters).

        Raises:
            ValidationError: If message is too long.
        """
        if not isinstance(message, str):
            msg = "Error message must be a string"
            raise ValidationError(msg)

        if len(message) >= PLUGIN_MAXERRORTEXT:
            msg = f"Error message must be less than {PLUGIN_MAXERRORTEXT} characters"
            raise ValidationError(msg)

        self._struct.OUT_szError = message.encode()
        self._struct.OUT_bNewError = True
        self._last_error_update = datetime.now()

    @property
    def error_severity(self) -> ErrorSeverity:
        """Get current error severity."""
        return ErrorSeverity(self._struct.OUT_iErrorSeverity)

    @error_severity.setter
    def error_severity(self, severity: ErrorSeverity) -> None:
        """Set current error severity."""
        if not isinstance(severity, ErrorSeverity):
            msg = "Error severity must be an ErrorSeverity enum value"
            raise ValidationError(msg)
        self._struct.OUT_iErrorSeverity = severity.value

    @property
    def error_long(self) -> str:
        """Get long error message."""
        return self._struct.OUT_szErrorLong.decode('utf-8', errors='ignore').rstrip('\x00')

    @error_long.setter
    def error_long(self, message: str) -> None:
        """Set long error message.

        Args:
            message (str): Long error message (max 200 characters).

        Raises:
            ValidationError: If message is too long.
        """
        if not isinstance(message, str):
            msg = "Error message must be a string"
            raise ValidationError(msg)

        if len(message) >= PLUGIN_MAXERRORTEXTLONG:
            msg = f"Error message must be less than {PLUGIN_MAXERRORTEXTLONG} characters"
            raise ValidationError(msg)

        self._struct.OUT_szErrorLong = message.encode()

    # Operation metrics
    @property
    def write_operations(self) -> int:
        """Get write operation count."""
        return self._struct.OUT_i64WriteOps

    @write_operations.setter
    def write_operations(self, count: int) -> None:
        """Set write operation count."""
        if not isinstance(count, int) or count < 0:
            msg = "Write operations must be a non-negative integer"
            raise ValidationError(msg)
        self._struct.OUT_i64WriteOps = count

    @property
    def read_operations(self) -> int:
        """Get read operation count."""
        return self._struct.OUT_i64ReadOps

    @read_operations.setter
    def read_operations(self, count: int) -> None:
        """Set read operation count."""
        if not isinstance(count, int) or count < 0:
            msg = "Read operations must be a non-negative integer"
            raise ValidationError(msg)
        self._struct.OUT_i64ReadOps = count

    @property
    def verify_operations(self) -> int:
        """Get verify operation count."""
        return self._struct.OUT_i64VerifyOps

    @verify_operations.setter
    def verify_operations(self, count: int) -> None:
        """Set verify operation count."""
        if not isinstance(count, int) or count < 0:
            msg = "Verify operations must be a non-negative integer"
            raise ValidationError(msg)
        self._struct.OUT_i64VerifyOps = count

    # Operation labels
    @property
    def write_label(self) -> str:
        """Get write operation label."""
        return self._struct.OUT_szWriteOps.decode('utf-8', errors='ignore').rstrip('\x00')

    @write_label.setter
    def write_label(self, label: str) -> None:
        """Set write operation label."""
        self._validate_label(label)
        self._struct.OUT_szWriteOps = label.encode()

    @property
    def read_label(self) -> str:
        """Get read operation label."""
        return self._struct.OUT_szReadOps.decode('utf-8', errors='ignore').rstrip('\x00')

    @read_label.setter
    def read_label(self, label: str) -> None:
        """Set read operation label."""
        self._validate_label(label)
        self._struct.OUT_szReadOps = label.encode()


    @property
    def verify_label(self) -> str:
        """Get verify operation label."""
        return self._struct.OUT_szVerifyOps.decode('utf-8', errors='ignore').rstrip('\x00')

    @verify_label.setter
    def verify_label(self, label: str) -> None:
        """Set verify operation label."""
        self._validate_label(label)
        self._struct.OUT_szVerifyOps = label.encode()


    # User-defined fields
    def get_user_field(self, field_id: int) -> dict[str, str]:
        """Get user-defined field configuration and value.

        Args:
            field_id (int): Field ID (1-6).

        Returns:
            dict[str, str]: Dictionary with 'label', 'value', and 'enabled' keys.

        Raises:
            ValidationError: If field_id is invalid.
        """
        if not 1 <= field_id <= 6:
            msg = "Field ID must be between 1 and 6"
            raise ValidationError(msg)

        field_map = {
            1: ("OUT_szUserDef1", "OUT_szUserDefVal1", "OUT_bUserDef1"),
            2: ("OUT_szUserDef2", "OUT_szUserDefVal2", "OUT_bUserDef2"),
            3: ("OUT_szUserDef3", "OUT_szUserDefVal3", "OUT_bUserDef3"),
            4: ("OUT_szUserDef4", "OUT_szUserDefVal4", "OUT_bUserDef4"),
            5: ("OUT_szUserDef5", "OUT_szUserDefVal5", "OUT_bUserDef5"),
            6: ("OUT_szUserDef6", "OUT_szUserDefVal6", "OUT_bUserDef6"),
        }

        label_attr, value_attr, enabled_attr = field_map[field_id]

        return {
            "label": getattr(self._struct, label_attr).decode('utf-8', errors='ignore').rstrip('\x00'),
            "value": getattr(self._struct, value_attr).decode('utf-8', errors='ignore').rstrip('\x00'),
            "enabled": bool(getattr(self._struct, enabled_attr)),
        }

    def set_user_field(self, field_id: int, label: str, value: str, enabled: bool = True) -> None:
        """Set user-defined field configuration and value.

        Args:
            field_id (int): Field ID (1-6).
            label (str): Field label (max 19 characters).
            value (str): Field value (max 19 characters).
            enabled (bool): Whether field is enabled.

        Raises:
            ValidationError: If parameters are invalid.
        """
        if not 1 <= field_id <= 6:
            msg = "Field ID must be between 1 and 6"
            raise ValidationError(msg)


        field_map = {
            1: ("OUT_szUserDef1", "OUT_szUserDefVal1", "OUT_bUserDef1", "OUT_bNewUserDefVal1"),
            2: ("OUT_szUserDef2", "OUT_szUserDefVal2", "OUT_bUserDef2", "OUT_bNewUserDefVal2"),
            3: ("OUT_szUserDef3", "OUT_szUserDefVal3", "OUT_bUserDef3", None),
            4: ("OUT_szUserDef4", "OUT_szUserDefVal4", "OUT_bUserDef4", None),
            5: ("OUT_szUserDef5", "OUT_szUserDefVal5", "OUT_bUserDef5", None),
            6: ("OUT_szUserDef6", "OUT_szUserDefVal6", "OUT_bUserDef6", None),
        }

        label_attr, value_attr, enabled_attr, new_value_attr = field_map[field_id]

        setattr(self._struct, label_attr, label.encode())
        setattr(self._struct, value_attr, value.encode())

        setattr(self._struct, enabled_attr, enabled)

        # Set new value flag for fields 1 and 2
        if new_value_attr is not None:
            setattr(self._struct, new_value_attr, True)

    # Display and window management
    @property
    def window_title(self) -> str:
        """Get window title."""
        return self._struct.OUT_szWindowTitle.decode('utf-8', errors='ignore').rstrip('\x00')

    @window_title.setter
    def window_title(self, title: str) -> None:
        """Set window title."""
        self._validate_label(title)
        self._struct.OUT_szWindowTitle = title.encode()

    @property
    def display_text_set(self) -> bool:
        """Check if display text has been set."""
        return bool(self._struct.OUT_bDisplayTextSet)

    @display_text_set.setter
    def display_text_set(self, set_flag: bool) -> None:
        """Set display text flag."""
        self._struct.OUT_bDisplayTextSet = set_flag

    @property
    def test_stopped(self) -> bool:
        """Check if test has been stopped."""
        return bool(self._struct.OUT_bTestStopped)

    @test_stopped.setter
    def test_stopped(self, stopped: bool) -> None:
        """Set test stopped flag."""
        self._struct.OUT_bTestStopped = stopped

    def set_error(self, message: str, severity: ErrorSeverity, long_message: str | None = None) -> None:
        """Set error information.

        Args:
            message (str): Error message.
            severity (ErrorSeverity): Error severity.
            long_message (str | None): Optional long error message.
        """
        self.error_message = message
        self.error_severity = severity
        self.error_count += 1

        if long_message:
            self.error_long = long_message

    def update_metrics(self, write_ops: int | None = None,
                      read_ops: int | None = None,
                      verify_ops: int | None = None) -> None:
        """Update operation metrics.

        Args:
            write_ops (int | None): Write operation count.
            read_ops (int | None): Read operation count.
            verify_ops (int | None): Verify operation count.
        """
        if write_ops is not None:
            self.write_operations = write_ops
        if read_ops is not None:
            self.read_operations = read_ops
        if verify_ops is not None:
            self.verify_operations = verify_ops

    def increment_metrics(self, write_ops: int = 0,
                         read_ops: int = 0,
                         verify_ops: int = 0,
                         error_count: int = 0) -> None:
        """Increment operation metrics.

        Args:
            write_ops (int): Write operations to add.
            read_ops (int): Read operations to add.
            verify_ops (int): Verify operations to add.
            error_count (int): Error count to add.
        """
        if write_ops > 0:
            self.write_operations += write_ops
        if read_ops > 0:
            self.read_operations += read_ops
        if verify_ops > 0:
            self.verify_operations += verify_ops
        if error_count > 0:
            self.error_count += error_count


    def reset_flags(self) -> None:
        """Reset all notification flags."""
        self._struct.OUT_bNewError = False
        self._struct.OUT_bNewStatus = False
        self._struct.OUT_bNewUserDefVal1 = False
        self._struct.OUT_bNewUserDefVal2 = False

    # Private helper methods
    def _validate_label(self, label: str) -> None:
        """Validate label string.

        Args:
            label (str): Label to validate.

        Raises:
            ValidationError: If label is invalid.
        """
        if not isinstance(label, str):
            msg = "Label must be a string"
            raise ValidationError(msg)

        if len(label) >= PLUGIN_MAXDISPLAYTEXT:
            msg = f"Label must be less than {PLUGIN_MAXDISPLAYTEXT} characters"
            raise ValidationError(msg)

    def get_structure(self) -> PluginInterfaceStructure:
        """Get the underlying PLUGININTERFACE structure.

        Returns:
            PluginInterfaceStructure: The underlying structure.
        """
        return self._struct

    def __str__(self) -> str:
        """String representation of interface state."""
        return (
            f"PluginInterface(cycle={self.cycle}, status='{self.status}', "
            f"test_running={self.test_running}, errors={self.error_count})"
        )
