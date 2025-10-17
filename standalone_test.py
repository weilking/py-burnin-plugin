import mmap
import os
import subprocess
import sys
import time
from ctypes import sizeof

from plugin_interface import PLUGININTERFACE


def simulate_burnin_test():
    """Simulate the BurnInTest application by creating shared memory and starting the plugin"""
    # Create a unique shared memory name
    shared_mem_name = f"BITest_{os.getpid()}"

    try:
        # Create shared memory
        h_mapped = mmap.mmap(-1, sizeof(PLUGININTERFACE), shared_mem_name)

        # Get interface object
        interface = PLUGININTERFACE.from_buffer(h_mapped)

        # Set initial values that BurnInTest would set
        interface.IN_TestRunning = 1
        interface.IN_DutyCycle = 75  # 75% duty cycle

        # Start the plugin in a separate process
        plugin_process = subprocess.Popen([sys.executable, "main.py", shared_mem_name])

        print("Started plugin process with shared memory:", shared_mem_name)
        print("Plugin process ID:", plugin_process.pid)

        # Monitor and display plugin status
        try:
            cycle_count = -1
            while True:
                # Update the display if the cycle count has changed
                if interface.OUT_iCycle != cycle_count:
                    cycle_count = interface.OUT_iCycle

                    print("\n--- Plugin Status ---")
                    print(f"Window Title: {interface.OUT_szWindowTitle.decode('ascii', 'ignore').strip('\0')}")
                    print(f"Cycle: {interface.OUT_iCycle}")
                    print(f"Status: {interface.OUT_szStatus.decode('ascii', 'ignore').strip('\0')}")
                    print(f"Write Ops: {interface.OUT_i64WriteOps}")
                    print(f"Read Ops: {interface.OUT_i64ReadOps}")
                    print(f"Verify Ops: {interface.OUT_i64VerifyOps}")

                    # Check for errors
                    if interface.OUT_bNewError:
                        print(f"Error ({interface.OUT_iErrorCount}): {interface.OUT_szError.decode('ascii', 'ignore').strip('\0')}")
                        interface.OUT_bNewError = False

                # Check if user wants to stop
                if msvcrt_available:
                    if msvcrt.kbhit():
                        key = msvcrt.getch()
                        if key == b'q':
                            print("Stopping test...")
                            break

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("Test interrupted by user")

        # Signal plugin to stop
        interface.IN_TestRunning = 0

        # Wait for plugin to exit
        plugin_process.wait(timeout=5)
        print("Plugin process exited with code:", plugin_process.returncode)

        # Clean up
        h_mapped.close()

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

# Try to import msvcrt for keyboard handling (Windows only)
msvcrt_available = False
try:
    import msvcrt
    msvcrt_available = True
except ImportError:
    print("msvcrt not available, press Ctrl+C to stop the test")

if __name__ == "__main__":
    sys.exit(simulate_burnin_test())
