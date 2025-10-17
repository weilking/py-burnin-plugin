from ctypes import memmove


def strn_clean_cpy(text_out, text_in, max_len):
    """Replicate the C++ strn_clean_cpy function"""
    # Convert input to bytes if it's a string
    if isinstance(text_in, str):
        text_in = text_in.encode('ascii', 'ignore')

    # Ensure we don't exceed max length
    text_in = text_in[:max_len-1]

    cleaned = bytearray()
    for i in range(max_len):
        if i >= len(text_in):
            break
        c = text_in[i]
        if c == 0 or c == b'\0':
            break
        if c < 0x20 or c in (b'%', b'\\'):
            cleaned.append(ord(' '))
        else:
            cleaned.append(c)
    # Ensure null-termination
    if len(cleaned) < max_len:
        cleaned += b'\0' * (max_len - len(cleaned))
    memmove(text_out, bytes(cleaned), max_len)
