import ctypes
from ctypes import (Structure, c_int, c_uint, c_bool, c_char, c_int64, 
                   LittleEndianStructure)

# Constants from PluginTestInterface.h
PLUGIN_INTERFACE_VERSION = 4
PLUGIN_MAXDISPLAYTEXT = 20
PLUGIN_MAXERRORTEXT = 100
PLUGIN_MAXERRORTEXTLONG = 201

# Status constants
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

# Error severity
ERRORNONE = 0
ERRORINFORMATION = 1
ERRORWARNING = 2
ERRORSERIOUS = 3
ERRORCRITICAL = 4
ERRORTERM = 5

class PLUGININTERFACE(LittleEndianStructure):
    _pack_ = 1  # Ensure no padding between fields
    
    _fields_ = [
        # Input fields
        ("IN_TestRunning", c_int),
        ("IN_DutyCycle", c_int),
        
        # Output fields
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
        
        # User defined fields 1-2
        ("OUT_bUserDef1", c_bool),
        ("OUT_szUserDef1", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_szUserDefVal1", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_bUserDef2", c_bool),
        ("OUT_szUserDef2", c_char * PLUGIN_MAXDISPLAYTEXT),
        ("OUT_szUserDefVal2", c_char * PLUGIN_MAXDISPLAYTEXT),
        
        # Event flags
        ("OUT_bDisplayTextSet", c_bool),
        ("OUT_bNewError", c_bool),
        ("OUT_bNewStatus", c_bool),
        ("OUT_bNewUserDefVal1", c_bool),
        ("OUT_bNewUserDefVal2", c_bool),
        ("OUT_bTestStopped", c_bool),
        
        # User defined fields 3-6
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
        
        # V4 interface additions
        ("OUT_szErrorLong", c_char * PLUGIN_MAXERRORTEXTLONG),
    ]

def strn_clean_cpy(text_out, text_in, max_len):
    """Replicate the C++ strn_clean_cpy function"""
    # Convert input to bytes if it's a string
    if isinstance(text_in, str):
        text_in = text_in.encode('ascii', 'ignore')
    
    # Ensure we don't exceed max length
    text_in = text_in[:max_len-1]
    
    # Clean the string (remove funny characters, '%' and '\')
    cleaned = bytearray()
    for b in text_in:
        if b < 0x20 or b == ord('%') or b == ord('\\'):
            cleaned.append(ord(' '))
        else:
            cleaned.append(b)
    
    # Ensure null termination
    cleaned = cleaned.ljust(max_len, b'\0')
    
    # Copy to output
    ctypes.memmove(text_out, cleaned, max_len) 