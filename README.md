# Python SDK for Passmark BurnInTest Plugin

A Python SDK for creating custom plugins for Passmark BurnInTest software. This library provides a high-level interface for developing burn-in test plugins that can communicate with BurnInTest through shared memory.

The SDK is created to simplify the development of BurnInTest plugins by providing an abstract base class, type-safe interface, error handling, and metrics tracking. The library refers to the official [Passmark BurninTest Sample Application](https://www.passmark.com/downloads/BurnInTest_sample_plugin.zip).

This is an independent, third‑party extension and is not affiliated with, endorsed by, or sponsored by the official Burnin Test or its publisher Passmark; use is at your own risk, and no warranties are provided.


## Features

- **Abstract Base Plugin Class**: Provides a complete plugin lifecycle framework
- **Shared Memory Communication**: Handles connection to BurnInTest via shared memory
- **Test Phase Management**: Support for write, read, and verify test phases
- **Metrics Tracking**: Automatic tracking of operation counts and error metrics

## Compatibility

- **Python**: 3.12+
- **BurnInTest**: Compatible with BurnInTest v9 and later
- **Operating Systems**: Windows

## Quick Start

### Basic Plugin Example

```python
import logging
import time
from py_burnin_plugin import BurnInPlugin, StatusCode

class MyTestPlugin(BurnInPlugin):
    def __init__(self):
        super().__init__("My Test Plugin")
    
    def execute_write_phase(self) -> bool:
        """Execute the write phase of the test."""
        self.get_interface().status_code = StatusCode.PLUGIN_WRITING
        self.get_interface().status = "Writing test data..."
        
        # Perform write operations
        for i in range(100):
            time.sleep(0.01)
            self.get_interface().increment_metrics(write_ops=1)
        
        return True
    
    def execute_read_phase(self) -> bool:
        """Execute the read phase of the test."""
        self.get_interface().status_code = StatusCode.PLUGIN_READING
        self.get_interface().status = "Reading test data..."
        
        # Perform read operations
        for i in range(100):
            time.sleep(0.01)
            self.get_interface().increment_metrics(read_ops=1)
        
        return True
    
    def execute_verify_phase(self) -> bool:
        """Execute the verify phase of the test."""
        self.get_interface().status_code = StatusCode.PLUGIN_VERIFYING
        self.get_interface().status = "Verifying test data..."
        
        # Perform verification
        self.get_interface().increment_metrics(verify_ops=100)
        
        return True

# Run the plugin
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    plugin = MyTestPlugin()
    
    # Pass the shared memory name from BurnInTest
    plugin.run("SharedMemoryName")
```

## Core Components

### BurnInPlugin Class

The abstract base class that all plugins must inherit from. Provides:

- Plugin lifecycle management (start, stop, cleanup)
- Test phase execution (write, read, verify)
- Error handling and reporting
- Metrics tracking
- Duty cycle management

#### Required Methods

```python
@abstractmethod
def execute_write_phase(self) -> bool:
    """Execute the write phase. Must return True on success."""
    pass

@abstractmethod
def execute_read_phase(self) -> bool:
    """Execute the read phase. Must return True on success."""
    pass

@abstractmethod
def execute_verify_phase(self) -> bool:
    """Execute the verify phase. Must return True on success."""
    pass
```

#### Optional Hook Methods

```python
def on_start(self) -> None:
    """Called when plugin starts execution."""

def on_stop(self) -> None:
    """Called when plugin stops execution."""

def on_cycle_start(self, cycle: int) -> None:
    """Called at the start of each test cycle."""

def on_cycle_end(self, cycle: int) -> None:
    """Called at the end of each test cycle."""

def on_error(self, error: PluginError) -> None:
    """Called when an error occurs."""
```

### PluginInterface Class

Provides type-safe access to BurnInTest shared memory interface:

```python
interface = plugin.get_interface()

# Status and progress
interface.status = "Running test..."
interface.status_code = StatusCode.PLUGIN_WRITING
interface.cycle = 5

# Metrics
interface.update_metrics(write_ops=1000, read_ops=1000, verify_ops=1000)
interface.increment_metrics(write_ops=10, read_ops=10)

# Error reporting
interface.set_error("Test failed", ErrorSeverity.CRITICAL, "Detailed error message")

# User-defined fields
interface.set_user_field(1, "Temperature", "45°C", enabled=True)
field_data = interface.get_user_field(1)

# Window and display
interface.window_title = "My Custom Test"
interface.write_label = "Writes"
interface.read_label = "Reads"
interface.verify_label = "Verifies"
```

## Error Handling

The SDK provides comprehensive error handling with different severity levels:

```python
from py_burnin_plugin import ErrorSeverity, PluginError

try:
    # Your plugin code here
    pass
except PluginError as e:
    # Handle plugin-specific errors
    print(f"Plugin error: {e}")
except Exception as e:
    # Handle other exceptions
    plugin.on_error(PluginError(f"Unexpected error: {e}", ErrorSeverity.CRITICAL))
```

### Error Severity Levels

- `NONE`: No error
- `INFORMATION`: Informational message
- `WARNING`: Warning condition
- `SERIOUS`: Serious error
- `CRITICAL`: Critical error
- `TERMINAL`: Terminal error

## Status Codes

Track plugin execution state with status codes:

```python
from py_burnin_plugin import StatusCode

interface.status_code = StatusCode.PLUGIN_WRITING
interface.status_code = StatusCode.PLUGIN_READING
interface.status_code = StatusCode.PLUGIN_VERIFYING
interface.status_code = StatusCode.PLUGIN_WAITING
interface.status_code = StatusCode.PLUGIN_CLEANUP
interface.status_code = StatusCode.PLUGIN_ERROR
```

## Examples

See the `examples/` directory for complete plugin examples:

- `plugin.py`: Basic plugin implementation with all phases
- Additional examples demonstrating advanced features

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

- Create an issue on the GitHub repository
- Check the examples directory for usage patterns
- Review the API documentation


