def rgba32_to_rgba64(bytelist: bytes):
    rgba64_bytes = bytearray()
    for byte in bytearray(bytelist):
        rgba64_bytes.append(byte)
        rgba64_bytes.append(byte)
    return bytes(rgba64_bytes)