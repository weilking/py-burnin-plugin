"""BurnInTest SDK - Base Plugin Class.

Abstract base class for all BurnInTest plugins. Provides the plugin
lifecycle framework and common functionality.
"""

import importlib.metadata
import json
import logging
import os
import time
from abc import ABC, abstractmethod

from ..core.common import ConnectionError, ErrorSeverity, PluginError, StatusCode
from ..core.connection import PluginConnection


class BurnInPlugin(ABC):
    """Abstract base class for BurnInTest plugins.

    Provides the plugin lifecycle framework and common functionality.
    Subclasses must implement the abstract methods to define their
    specific test behavior.
    """

    def __init__(self,
                 plugin_name: str,
                 logger: logging.Logger | None = None,
                 delay: float = 0.02) -> None:
        """Initialize the plugin.

        Args:
            plugin_name (str): Name of the plugin.
            logger (logging.Logger | None): Optional logger instance.
            delay (float): Delay between operations in seconds.
        """
        self.plugin_name = plugin_name
        self._logger = logger or logging.getLogger(f"{__name__}.{plugin_name}")

        # Connection and interface
        self._connection: PluginConnection | None = None
        self._interface = None

        # Plugin state
        self._is_running = False
        self._current_cycle = 0
        self._start_time: float | None = None

        self._delay = delay

        # Configuration storage
        self._config = {}

        self._logger.info(f"Plugin '{plugin_name}' initialized")

    @property
    def is_running(self) -> bool:
        """Check if plugin is currently running."""
        return self._is_running

    @property
    def current_cycle(self) -> int:
        """Get current test cycle number."""
        return self._current_cycle

    @property
    def version(self) -> str:
        return importlib.metadata.version("py-burnin-plugin")

    def run(self, shared_memory_name: str) -> None:
        """Run the plugin with the specified shared memory.

        Args:
            shared_memory_name (str): Name of shared memory object.

        Raises:
            ConnectionError: If connection fails.
            PluginError: If plugin execution fails.
        """
        if self._is_running:
            raise PluginError("Plugin is already running")

        self._logger.info(f"Starting plugin '{self.plugin_name}'")

        try:
            # Establish connection
            self._connection = PluginConnection(self._logger)

            if not self._connection.connect(shared_memory_name):
                raise ConnectionError("Failed to connect to shared memory")

            self._interface = self._connection.get_interface()

            # Set plugin metadata
            self._interface.window_title = self.plugin_name
            self._interface.interface_version = 4

            # Start plugin lifecycle
            self._start_time = time.time()
            self._is_running = True

            # Call startup hook
            self.on_start()

            # Main plugin loop
            self._run_plugin_loop()

        except Exception as e:
            self._logger.exception(f"Plugin execution failed: {e}")
            self.on_error(PluginError(f"Plugin execution failed: {e}"))
            raise
        finally:
            self._cleanup()

    def stop(self) -> None:
        """Stop the plugin gracefully."""
        if not self._is_running:
            return

        self._logger.info("Stopping plugin")
        self._is_running = False

        # Call stop hook
        self.on_stop()

    def _run_plugin_loop(self) -> None:
        """Main plugin execution loop."""
        self._logger.info("Starting plugin execution loop")

        try:
            while self._is_running and self._interface.test_running:
                # Update cycle counter
                self._current_cycle = self._interface.cycle

                # Execute cycle start hook
                self.on_cycle_start(self._current_cycle)

                # Execute test phases
                if not self._execute_test_phases():
                    break

                # Execute cycle end hook
                self.on_cycle_end(self._current_cycle)

                # Handle duty cycle delay
                self._handle_duty_cycle()

            # Handle when test is finished.
            self.on_test_end()

        except Exception as e:
            self._logger.exception(f"Error in plugin loop: {e}")
            self.on_error(PluginError(f"Error in plugin loop: {e}"))
            raise

    def _execute_test_phases(self) -> bool:
        """Execute all test phases for current cycle.

        Returns:
            bool: True if all phases executed successfully, False otherwise.
        """
        phases = [
            ("Write", self.execute_write_phase),
            ("Read", self.execute_read_phase),
            ("Verify", self.execute_verify_phase),
        ]

        for phase, phase_method in phases:
            if not self._is_running or not self._interface.test_running:
                return False

            self._current_phase = phase

            try:
                # Execute phase
                result = phase_method()

                if not result:
                    self._logger.error(f"Phase {phase} failed.")
                    self._interface.set_error(
                        f"{phase} phase failed.",
                        ErrorSeverity.CRITICAL
                    )
                    self.on_error(PluginError(f"Phase {phase} failed."))
                    return False

                self._logger.debug(f"Phase {phase} completed.")

            except Exception as e:
                self._logger.exception(f"Exception in {phase} phase: {e}")
                self._interface.set_error(
                    f"Exception in {phase} phase: {e}",
                    ErrorSeverity.CRITICAL
                )
                self.on_error(PluginError(f"Exception in {phase} phase: {e}"))
                return False
        return True

    def _handle_duty_cycle(self) -> None:
        """Handle duty cycle timing."""
        if not self._interface:
            return

        duty_cycle = self._interface.duty_cycle
        if duty_cycle < 100:
            # Calculate sleep time based on duty cycle
            sleep_time = (100 - duty_cycle) * self._delay  # base for 0% duty cycle
            if sleep_time > 0:
                self._logger.debug(f"Duty cycle delay: {sleep_time:.3f}s")
                time.sleep(sleep_time)

    def _get_error_severity(self, error: str | None) -> ErrorSeverity:
        """Determine error severity based on error message.

        Args:
            error (str | None): Error message to analyze.

        Returns:
            ErrorSeverity: Determined severity level.
        """
        if not error:
            return ErrorSeverity.WARNING

        error_lower = error.lower()
        if any(keyword in error_lower for keyword in ["critical", "fatal", "failed"]):
            return ErrorSeverity.CRITICAL
        elif any(keyword in error_lower for keyword in ["error", "exception"]):
            return ErrorSeverity.SERIOUS
        elif any(keyword in error_lower for keyword in ["warning", "warn"]):
            return ErrorSeverity.WARNING
        else:
            return ErrorSeverity.INFORMATION

    def _cleanup(self) -> None:
        """Cleanup plugin resources."""
        self._logger.info("Cleaning up plugin resources")

        try:
            # Set cleanup status
            if self._interface:
                self._interface.status_code = StatusCode.PLUGIN_CLEANUP
                self._interface.test_stopped = True

            # Stop plugin
            self.stop()

            # Disconnect
            if self._connection:
                self._connection.disconnect()
                self._connection = None

            self._interface = None

        except Exception as e:
            self._logger.exception(f"Error during cleanup: {e}")

        # Log final statistics
        if self._start_time:
            runtime = time.time() - self._start_time
            self._logger.info(
                f"Plugin finished. Runtime: {runtime:.2f}s, "
                f"Cycles: {self._current_cycle}"
            )

    # Abstract methods that must be implemented by subclasses

    @abstractmethod
    def execute_write_phase(self) -> bool:
        """Execute the write phase of the test.

        Returns:
            bool: True if write phase executed successfully, False otherwise.
        """
        pass

    @abstractmethod
    def execute_read_phase(self) -> bool:
        """Execute the read phase of the test.

        Returns:
            bool: True if read phase executed successfully, False otherwise.
        """
        pass

    @abstractmethod
    def execute_verify_phase(self) -> bool:
        """Execute the verify phase of the test.

        Returns:
            bool: True if verify phase executed successfully, False otherwise.
        """
        pass

    def on_start(self) -> None:
        """Called when plugin starts execution."""
        self._logger.info("Plugin started")

    def on_stop(self) -> None:
        """Called when plugin stops execution."""
        self._logger.info("Plugin stopped")

    def on_cycle_start(self, cycle: int) -> None:
        """Called at the start of each test cycle.

        Args:
            cycle (int): Current cycle number.
        """
        self._logger.debug(f"Cycle {cycle} started")

    def on_cycle_end(self, cycle: int) -> None:
        """Called at the end of each test cycle.

        Args:
            cycle (int): Current cycle number.
        """
        self._logger.debug(f"Cycle {cycle} ended")

    def on_error(self, error: PluginError) -> None:
        """Called when an error occurs.

        Args:
            error (PluginError): The error that occurred.
        """
        self._logger.error(f"Plugin error: {error}")

    # Utility methods for subclasses

    def get_interface(self):
        """Get the plugin interface for direct access.

        Returns:
            PluginInterface: Interface instance (available during execution).
        """
        return self._interface

    def log_info(self, message: str) -> None:
        """Log info message.

        Args:
            message (str): Message to log.
        """
        self._logger.info(message)

    def log_warning(self, message: str) -> None:
        """Log warning message.

        Args:
            message (str): Message to log.
        """
        self._logger.warning(message)

    def log_error(self, message: str) -> None:
        """Log error message.

        Args:
            message (str): Message to log.
        """
        self._logger.error(message)

    def log_debug(self, message: str) -> None:
        """Log debug message.

        Args:
            message (str): Message to log.
        """
        self._logger.debug(message)

    def load_from_config(self, config_filename: str = "") -> None:
        """Load configuration fields from a JSON file and store in self._config.

        Args:
            config_filename (str): Name of the JSON config file. If empty, automatically
                loads from the same directory as the plugin code.

        Raises:
            FileNotFoundError: If the config file is not found.
            json.JSONDecodeError: If the config file is not valid JSON.
            PluginError: If there's an error loading the configuration.
        """
        try:
            # Determine config file path
            if not config_filename:
                # Use the same directory as the plugin code
                plugin_dir = os.path.dirname(__file__)
                config_filename = os.path.join(plugin_dir, "config.json")
                self._logger.info(f"No config filename provided, using default: {config_filename}")
            else:
                # If relative path, make it relative to the plugin directory
                if not os.path.isabs(config_filename):
                    plugin_dir = os.path.dirname(__file__)
                    config_filename = os.path.join(plugin_dir, config_filename)

            # Check if file exists
            if not os.path.exists(config_filename):
                raise FileNotFoundError(f"Configuration file not found: {config_filename}")

            # Load and parse JSON
            with open(config_filename, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Store configuration
            self._config = config_data
            self._logger.info(f"Configuration loaded successfully from: {config_filename}")

        except FileNotFoundError as e:
            self._logger.exception(f"Configuration file not found: {e}")
            raise
        except json.JSONDecodeError as e:
            self._logger.exception(f"Invalid JSON in configuration file: {e}")
            raise
        except Exception as e:
            self._logger.exception(f"Error loading configuration: {e}")
            raise PluginError(f"Failed to load configuration: {e}")

    def get_config_value(self, field_name: str, default_value=None):
        """Get a value from the configuration by field name.

        Args:
            field_name (str): Name of the field to retrieve. Supports dot notation for nested fields
                (e.g., "database.host" for config["database"]["host"]).
            default_value: Value to return if field is not found.

        Returns:
            The field value if found, otherwise the default_value.
        """
        try:
            # Handle nested field access with dot notation
            keys = field_name.split('.')
            value = self._config

            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default_value

            return value

        except Exception as e:
            self._logger.warning(f"Error accessing config field '{field_name}': {e}")
            return default_value

    def __str__(self) -> str:
        """String representation of plugin state."""
        return (
            f"BurnInPlugin(name='{self.plugin_name}', "
            f"running={self._is_running}, "
            f"cycle={self._current_cycle}, "
        )

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"BurnInPlugin(plugin_name={self.plugin_name!r}, "
            f"is_running={self._is_running}, "
            f"current_cycle={self._current_cycle}, "
        )
