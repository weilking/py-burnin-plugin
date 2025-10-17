import sys
import time
import ctypes
from ctypes import wintypes
import logging

# Constants from PluginTestInterface.h
PLUGIN_INTERFACE_VERSION = 4
PLUGIN_MAXDISPLAYTEXT = 20
PLUGIN_MAXERRORTEXT = 100
PLUGIN_MAXERRORTEXTLONG = 201

# Error severity enum
ERRORNONE = 0
ERRORINFORMATION = 1
ERRORWARNING = 2
ERRORSERIOUS = 3
ERRORCRITICAL = 4
ERRORTERM = 5

# Status codes
PLUGIN_WRITING = 3
PLUGIN_READING = 4
PLUGIN_VERIFYING = 5
PLUGIN_WAITING = 6

# Define PLUGININTERFACE structure with exact memory layout
class PLUGININTERFACE(ctypes.Structure):
#    _pack_ = 1  # Prevent padding between fields
    _fields_ = [
        ("IN_TestRunning", ctypes.c_int),
        ("IN_DutyCycle", ctypes.c_int),
        ("OUT_Plugin_interface_version", ctypes.c_int),
        ("OUT_szWindowTitle", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_iCycle", ctypes.c_uint),
        ("OUT_iStatus", ctypes.c_int),
        ("OUT_szStatus", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_iErrorCount", ctypes.c_int),
        ("OUT_szError", ctypes.c_char * PLUGIN_MAXERRORTEXT),
        ("OUT_iErrorSeverity", ctypes.c_int),
        ("OUT_szWriteOps", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_i64WriteOps", ctypes.c_int64),
        ("OUT_szReadOps", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_i64ReadOps", ctypes.c_int64),
        ("OUT_szVerifyOps", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_i64VerifyOps", ctypes.c_int64),
        ("OUT_bUserDef1", ctypes.c_bool),
        ("OUT_szUserDef1", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_szUserDefVal1", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_bUserDef2", ctypes.c_bool),
        ("OUT_szUserDef2", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_szUserDefVal2", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_bDisplayTextSet", ctypes.c_bool),
        ("OUT_bNewError", ctypes.c_bool),
        ("OUT_bNewStatus", ctypes.c_bool),
        ("OUT_bNewUserDefVal1", ctypes.c_bool),
        ("OUT_bNewUserDefVal2", ctypes.c_bool),
        ("OUT_bTestStopped", ctypes.c_bool),
        # V3+ fields
        ("OUT_bUserDef3", ctypes.c_bool),
        ("OUT_szUserDef3", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_szUserDefVal3", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_bUserDef4", ctypes.c_bool),
        ("OUT_szUserDef4", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_szUserDefVal4", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_bUserDef5", ctypes.c_bool),
        ("OUT_szUserDef5", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_szUserDefVal5", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_bUserDef6", ctypes.c_bool),
        ("OUT_szUserDef6", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_szUserDefVal6", ctypes.c_char * PLUGIN_MAXDISPLAYTEXT),
        # V4 field
        ("OUT_szErrorLong", ctypes.c_char * PLUGIN_MAXERRORTEXTLONG),
    ]

# Windows API functions
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

OpenFileMapping = kernel32.OpenFileMappingW
OpenFileMapping.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
OpenFileMapping.restype = wintypes.HANDLE

MapViewOfFile = kernel32.MapViewOfFile
MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
                          wintypes.DWORD, ctypes.c_size_t]
MapViewOfFile.restype = ctypes.c_void_p

UnmapViewOfFile = kernel32.UnmapViewOfFile
UnmapViewOfFile.argtypes = [ctypes.c_void_p]
UnmapViewOfFile.restype = wintypes.BOOL

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('plugin.log'),
        logging.StreamHandler()
    ]
)

# Helper function to sanitize strings
def strn_clean_cpy(dest, src, max_len):
    cleaned = bytearray()
    for i in range(max_len):
        if i >= len(src):
            break
        c = src[i]
        if c == 0 or c == b'\0':
            break
        if c < 0x20 or c in (b'%', b'\\'):
            cleaned.append(ord(' '))
        else:
            cleaned.append(c)
    # Ensure null-termination
    if len(cleaned) < max_len:
        cleaned += b'\0' * (max_len - len(cleaned))
    ctypes.memmove(dest, bytes(cleaned), max_len)

def get_last_error():
    """Get formatted Windows error message"""
    error_code = ctypes.GetLastError()
    msg = ctypes.FormatError(error_code)
    return f"Error {error_code}: {msg}"

def main():
    logging.info("==== Plugin starting ====")
    
    if len(sys.argv) != 1:
        print("Incorrect command line arguments")
        logging.error(f"Incorrect command line arguments, {len(sys.argv)}, {sys.argv}")
        sys.exit(1)

    shm_name = sys.argv[0]
    if not shm_name.startswith("BI"):
        logging.error("Shared memory name must start with 'BI'")
        sys.exit(1)

    # Open shared memory
    logging.info(f"Attempting to open file mapping at {shm_name}...")
    h_map = OpenFileMapping(0xF001F, False, shm_name)
    if not h_map:
        print("Failed to open file mapping")
        logging.error(f"OpenFileMapping failed - {get_last_error()}")
        sys.exit(1)
    logging.info(f"File mapping opened successfully. Handle: {h_map}")

    # Map view of file
    logging.info("Attempting to map view...")
    address = MapViewOfFile(h_map, 0xF001F, 0, 0, 0)
    if not address:
        logging.error(f"MapViewOfFile failed - {get_last_error()}")
        CloseHandle(h_map)
        print("Failed to map view")

        sys.exit(1)

    logging.info(f"View mapped at address: {address}")
    bit_interface = PLUGININTERFACE.from_address(address)
    logging.debug("Shared memory structure initialized")

    # Initialize values
    bit_interface.OUT_Plugin_interface_version = 4
    bit_interface.OUT_iCycle = 0
    bit_interface.OUT_iErrorCount = 0
    bit_interface.OUT_i64WriteOps = 0
    bit_interface.OUT_i64ReadOps = 0
    bit_interface.OUT_i64VerifyOps = 0

    # Set initial strings
    strn_clean_cpy(bit_interface.OUT_szWindowTitle, b"Test plugin", PLUGIN_MAXDISPLAYTEXT)
    strn_clean_cpy(bit_interface.OUT_szStatus, b"Starting", PLUGIN_MAXDISPLAYTEXT)
    strn_clean_cpy(bit_interface.OUT_szWriteOps, b"Write (MBytes):", PLUGIN_MAXDISPLAYTEXT)
    strn_clean_cpy(bit_interface.OUT_szReadOps, b"Read (MBytes):", PLUGIN_MAXDISPLAYTEXT)
    strn_clean_cpy(bit_interface.OUT_szVerifyOps, b"Verify (MBytes):", PLUGIN_MAXDISPLAYTEXT)
    
    bit_interface.OUT_bDisplayTextSet = True
    bit_interface.OUT_bUserDef1 = True
    bit_interface.OUT_bUserDef2 = True

    i_test_phase = 1
    i_num_writes = 100  # Demo value

    try:
        while bit_interface.IN_TestRunning:
            logging.debug("Running")
            logging.info(f"Duty cycle: {bit_interface.IN_DutyCycle}")
            # Write phase
            bit_interface.OUT_iStatus = PLUGIN_WRITING
            strn_clean_cpy(bit_interface.OUT_szStatus, b"Plug-in write", PLUGIN_MAXDISPLAYTEXT)
            bit_interface.OUT_bNewStatus = True

            for i in range(i_num_writes):
                time.sleep(0.01)
                bit_interface.OUT_i64WriteOps += 1
                # Update user-defined values
                if i_test_phase == 1:
                    val = f"{bit_interface.OUT_i64WriteOps} writes step 1".encode()
                    strn_clean_cpy(bit_interface.OUT_szUserDefVal1, val, PLUGIN_MAXDISPLAYTEXT)
                    bit_interface.OUT_bNewUserDefVal1 = True

            # Read phase
            bit_interface.OUT_iStatus = PLUGIN_READING
            strn_clean_cpy(bit_interface.OUT_szStatus, b"Plug-in read", PLUGIN_MAXDISPLAYTEXT)
            bit_interface.OUT_bNewStatus = True

            for i in range(i_num_writes):
                time.sleep(0.01)
                bit_interface.OUT_i64ReadOps += 1
                if i_test_phase == 1:
                    val = f"{bit_interface.OUT_i64ReadOps} reads step 1".encode()
                    strn_clean_cpy(bit_interface.OUT_szUserDefVal2, val, PLUGIN_MAXDISPLAYTEXT)
                    bit_interface.OUT_bNewUserDefVal2 = True

            # Verify phase
            bit_interface.OUT_iStatus = PLUGIN_VERIFYING
            bit_interface.OUT_i64VerifyOps += 1
            # Simulate error for demo
            bit_interface.OUT_iErrorCount += 1
            strn_clean_cpy(bit_interface.OUT_szError,
                           b"Plugin error: ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                           PLUGIN_MAXERRORTEXT)
            bit_interface.OUT_iErrorSeverity = ERRORINFORMATION
            bit_interface.OUT_bNewError = True

            # Update cycle counter
            bit_interface.OUT_iCycle += 1

            # Duty cycle delay
            sleep_time = (100 - bit_interface.IN_DutyCycle) * 0.02
            if sleep_time > 0:
                time.sleep(sleep_time)

            # Phase change after 10 cycles
            if bit_interface.OUT_iCycle >= 10 and i_test_phase == 1:
                while bit_interface.OUT_bDisplayTextSet:
                    time.sleep(0.1)
                # Update labels for phase 2
                strn_clean_cpy(bit_interface.OUT_szWindowTitle, b"Test plugin2", PLUGIN_MAXDISPLAYTEXT)
                strn_clean_cpy(bit_interface.OUT_szStatus, b"Testing XYZ", PLUGIN_MAXDISPLAYTEXT)
                # ... update other labels
                bit_interface.OUT_bDisplayTextSet = True
                i_test_phase = 2

        logging.debug("Stopped")
    finally:
        # Cleanup
        bit_interface.OUT_iStatus = 7  # PLUGIN_CLEANUP
        UnmapViewOfFile(address)
        CloseHandle(h_map)

if __name__ == "__main__":
    main()