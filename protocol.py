"""Divoom Timebox Evo protocol encoding.

Based on: https://github.com/RomRider/node-divoom-timebox-evo/blob/master/PROTOCOL.md

The Timebox Evo has a 16x16 pixel LED matrix.
Communication happens over Bluetooth RFCOMM.
Messages are framed: 01 LLLL PAYLOAD CRCR 02
"""

import math


def int2hexlittle(value: int) -> str:
    """Convert integer to 2-byte LSB-first hex string."""
    byte1 = value & 0xFF
    byte2 = (value >> 8) & 0xFF
    return f"{byte1:02x}{byte2:02x}"


def _get_color_string(colors: list[tuple[int, int, int]]) -> str:
    """Build color palette hex string from list of (R, G, B) tuples."""
    return "".join(f"{r:02x}{g:02x}{b:02x}" for r, g, b in colors)


def _get_pixel_string(pixels: list[int], nb_colors: int) -> str:
    """Encode pixel color indices into protocol pixel string.

    Each pixel references a color index from the palette.
    The encoding packs indices using the minimum number of bits.
    """
    if nb_colors <= 1:
        nb_bits = 1
    else:
        nb_bits_f = math.log2(nb_colors)
        nb_bits = int(nb_bits_f) if nb_bits_f == int(nb_bits_f) else int(nb_bits_f) + 1

    # Build bit string: for each pixel, convert index to 8-bit binary,
    # reverse it, take first nb_bits
    bit_string = ""
    for pixel in pixels:
        binary = format(pixel, "08b")[::-1][:nb_bits]
        bit_string += binary

    # Pad to multiple of 8
    while len(bit_string) % 8 != 0:
        bit_string += "0"

    # Process 8 bits at a time: reverse each group, convert to hex byte
    result = ""
    for i in range(0, len(bit_string), 8):
        byte = bit_string[i : i + 8][::-1]
        result += f"{int(byte, 2):02x}"

    return result


def build_image_message(
    pixels: list[int], colors: list[tuple[int, int, int]]
) -> bytes:
    """Build a complete image message for the Timebox Evo.

    Args:
        pixels: List of 256 ints — color indices for each pixel
                (16x16, left-to-right, top-to-bottom).
        colors: List of (R, G, B) tuples — the color palette.

    Returns:
        Raw bytes ready to send over Bluetooth RFCOMM.
    """
    nb_colors = len(colors)
    nn = f"{nb_colors:02x}" if nb_colors < 256 else "00"

    color_data = _get_color_string(colors)
    pixel_data = _get_pixel_string(pixels, nb_colors)

    # IMAGE_DATA = AA + LLLL + 000000 + NN + COLOR_DATA + PIXEL_DATA
    # Calculate total byte count of IMAGE_DATA (including LLLL itself)
    image_data_bytes = (
        1  # AA
        + 2  # LLLL
        + 3  # 000000
        + 1  # NN
        + len(color_data) // 2
        + len(pixel_data) // 2
    )
    llll = int2hexlittle(image_data_bytes)
    image_data = "aa" + llll + "000000" + nn + color_data + pixel_data

    # Full payload with fixed image header
    payload = "44000a0a04" + image_data

    return _wrap_message(payload)


def build_brightness_message(brightness: int) -> bytes:
    """Build a brightness command (0-100)."""
    brightness = max(0, min(100, brightness))
    payload = f"74{brightness:02x}"
    return _wrap_message(payload)


def build_countdown_message(minutes: int, seconds: int, start: bool = True) -> bytes:
    """Activate the device's built-in countdown timer.
    
    Args:
        minutes: Minutes (0-99).
        seconds: Seconds (0-59).
        start: True to start, False to stop.
    """
    minutes = max(0, min(99, minutes))
    seconds = max(0, min(59, seconds))
    action = "01" if start else "00"
    payload = f"7203{action}{minutes:02x}{seconds:02x}"
    return _wrap_message(payload)


def build_volume_message(volume: int) -> bytes:
    """Set device volume (0-100)."""
    volume = max(0, min(100, volume))
    vol_encoded = int(volume * 15 / 100)
    payload = f"08{vol_encoded:02x}"
    return _wrap_message(payload)


def _wrap_message(payload: str) -> bytes:
    """Wrap a hex payload in the Timebox Evo message frame.

    Format: 01 LLLL PAYLOAD CRCR 02
    """
    # LLLL = (payload length + CRC length) in bytes, LSB first
    # CRC is 4 hex chars = 2 bytes
    length = (len(payload) + 4) // 2
    llll = int2hexlittle(length)

    # CRC = sum of all bytes in (LLLL + PAYLOAD), LSB first
    crc_input = llll + payload
    crc_sum = sum(int(crc_input[i : i + 2], 16) for i in range(0, len(crc_input), 2))
    crcr = int2hexlittle(crc_sum)

    message_hex = "01" + llll + payload + crcr + "02"
    return bytes.fromhex(message_hex)
