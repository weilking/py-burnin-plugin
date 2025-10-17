import sys
import time
import ctypes
from ctypes import wintypes
import logging

from py_burnin_plugin import (
    ConnectionError,
    ErrorSeverity,
    InterfaceError,
    PluginError,
    StatusCode,
    ValidationError,
    PluginConnection,
    PluginInterface,
    PluginInterfaceStructure,
)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('basic_plugin.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    logging.info("==== Plugin starting ====")
    if len(sys.argv) != 1:
        print("Incorrect command line arguments")
        logging.error(f"Incorrect command line arguments, {len(sys.argv)}, {sys.argv}")
        sys.exit(1)
        
    shm_name = sys.argv[0]

    connection = PluginConnection(logger)
    connection.connect(shm_name)

    interface = connection.get_interface()

    i_test_phase = 1
    i_num_writes = 100  # Demo value    

    try:
        while interface.test_running:
            logging.debug("Running")
            logging.info(f"Duty cycle: {interface.duty_cycle}")
            # Write phase
            interface.status_code = StatusCode.PLUGIN_WRITING
            interface.status = "Plug-in write"

            for i in range(i_num_writes):
                time.sleep(0.01)
                interface.increment_metrics(write_ops=1)
                # Update user-defined values
                if i_test_phase == 1:
                    val = f"{interface.write_operations} writes step 1".encode()
                    interface.set_user_field(1, "OUT_szUserDefVal1", val)

            # Read phase
            interface.status_code = StatusCode.PLUGIN_READING
            interface.status = "Plug-in read"

            for i in range(i_num_writes):
                time.sleep(0.01)
                interface.increment_metrics(read_ops=1)
                if i_test_phase == 1:
                    val = f"{interface.read_operations} reads step 1".encode()
                    interface.set_user_field(1, "OUT_szUserDefVal2", val)

            # Verify phase
            interface.status_code = StatusCode.PLUGIN_VERIFYING
            interface.status = "Plug-in verify"

            interface.increment_metrics(verify_ops=1)
            # Simulate error for demo
            interface.increment_metrics(error_count=1)
            interface.error_message = "Plugin error: ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            interface.error_severity = ErrorSeverity.INFORMATION

            # Update cycle counter
            interface.increment_cycle()

            # Duty cycle delay
            sleep_time = (100 - interface.duty_cycle) * 0.02
            if sleep_time > 0:
                time.sleep(sleep_time)

            # Phase change after 10 cycles
            if interface.cycle >= 10 and i_test_phase == 1:
                while interface.display_text_set:
                    time.sleep(0.1)
                # Update labels for phase 2
                interface.window_title = "Test plugin2"
                interface.status = "Testing XYZ"
                # ... update other labels
                interface.display_text_set = True
                i_test_phase = 2

        logging.debug("Stopped")
    finally:
        # Cleanup
        interface.status_code = StatusCode.PLUGIN_CLEANUP

        connection.disconnect()


if __name__ == "__main__":
    main()