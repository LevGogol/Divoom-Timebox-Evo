"""Listen for button presses on the Divoom Timebox Evo.

Connects via RFCOMM and prints raw messages received from the device.
Press any button on the speaker to see the data.
Ctrl+C to stop.
"""

import socket
import time

from draw_pixel import MAC_ADDRESS, RFCOMM_CHANNEL


def main():
    print(f"Connecting to {MAC_ADDRESS}...")
    sock = socket.socket(
        socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
    )
    sock.settimeout(10)
    try:
        sock.connect((MAC_ADDRESS, RFCOMM_CHANNEL))
    except OSError as e:
        print(f"Connection failed: {e}")
        return
    print("Connected! Waiting for button presses... (Ctrl+C to stop)\n")

    sock.settimeout(0.5)
    try:
        while True:
            try:
                data = sock.recv(1024)
                if data:
                    hex_str = data.hex(" ")
                    print(f"[{len(data):3d} bytes] {hex_str}")
            except socket.timeout:
                continue
            except OSError:
                print("Connection lost.")
                break
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
