import logging
import sys
import time

from py_burnin_plugin import BurnInPlugin, ErrorSeverity, StatusCode


class TestPlugin(BurnInPlugin):
    def __init__(self, shm_name, logger):
        super().__init__(shm_name, logger)
        self.test_phase = 1
        self.num_writes = 100


    def on_start(self):
        self._interface.window_title = "Test Plugin"
        self._interface.write_label = "Write"
        self._interface.read_label = "Read"
        self._interface.verify_label = "Verify"

        self._interface.set_user_field(1, "Message 1", "0 writes")
        self._interface.set_user_field(2, "Message 2", "0 reads")

        return super().on_start()

    def execute_write_phase(self):
        # Write phase
        self._interface.status_code = StatusCode.PLUGIN_WRITING
        self._interface.status = "Plug-in write"

        for i in range(self.num_writes):
            time.sleep(0.01)
            self._interface.increment_metrics(write_ops=1)
            # Update user-defined values
            if self.test_phase == 1:
                val = f"{self._interface.write_operations} writes step 1"
                self._interface.set_user_field(1, "Message 1", val)
        return True

    def execute_read_phase(self):
        self._interface.status_code = StatusCode.PLUGIN_READING
        self._interface.status = "Plug-in read"

        for i in range(self.num_writes):
            time.sleep(0.01)
            self._interface.increment_metrics(read_ops=1)
            if self.test_phase == 1:
                val = f"{self._interface.read_operations} reads step 1"
                self._interface.set_user_field(2, "Message 2", val)
        return True

    def execute_verify_phase(self):
        self._interface.status_code = StatusCode.PLUGIN_VERIFYING
        self._interface.status = "Plug-in verify"

        self._interface.increment_metrics(verify_ops=1)
        # Simulate error for demo
        self._interface.increment_metrics(error_count=1)
        self._interface.error_message = "Plugin error: ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self._interface.error_severity = ErrorSeverity.INFORMATION
        return True

    def on_cycle_start(self, cycle):
        logging.debug("Running")
        logging.info(f"Duty cycle: {self._interface.duty_cycle}")
        return super().on_cycle_start(cycle)

    def on_cycle_end(self, cycle):
        self._interface.increment_cycle()

        # Phase change after 10 cycles
        if self._interface.cycle >= 10 and self.test_phase == 1:
            while self._interface.display_text_set:
                time.sleep(0.1)
            # Update labels for phase 2
            self._interface.window_title = "Test plugin2"
            self._interface.status = "Testing XYZ"
            self._interface.display_text_set = True
            self.test_phase = 2


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

    plugin = TestPlugin("Test Plugin 101", logger)
    plugin.run(shm_name)


if __name__ == "__main__":
    main()
