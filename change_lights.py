import argparse
from logging import DEBUG

import usb.core
import usb.util

from loghandlers import setup_logging

# Control transfer parameters parsed from Wireshark
SET_REPORT_REQUEST_TYPE = 0x21  # host→device, class, interface
SET_REPORT_REQUEST = 0x09
REPORT_TYPE_OUTPUT = 0x02
REPORT_ID = 0xB5
INTERFACE_NUMBER = 4

READ_TIMEOUT_MS = 3000


def parse_hex_color(hex_color: str) -> tuple[int, int, int]:
    """Parse a hex color string (e.g., 'FF0000' or '#FF0000' or '0xFF0000') to RGB tuple."""

    hex_color = hex_color.lower().replace("#", "").replace("0x", "")

    # Validate length
    if len(hex_color) != 6:
        raise ValueError(
            f"Hex color must be 6 characters, got {len(hex_color)}: {hex_color}"
        )

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return r, g, b


def create_static_report_data(r: int, g: int, b: int, brightness: int) -> bytes:
    """Create REPORT_DATA with RGB values inserted."""
    return bytes(
        [REPORT_ID, 0x24, 0x01, brightness, 0x80, r, g, b] + [0x00] * 14
    )  # 21 bytes total


def find_device(vid: int, pid: int, log) -> usb.core.Device | None:
    dev = usb.core.find(idVendor=vid, idProduct=pid)
    if dev is None:
        log.error(f"Device {vid:#06x}:{pid:#06x} not found.")
    else:
        log.info(
            f"Found device: {vid:#06x}:{pid:#06x} "
            f"'{usb.util.get_string(dev, dev.iManufacturer)}' - "
            f"'{usb.util.get_string(dev, dev.iProduct)}'"
        )
    return dev


def send_set_report(dev: usb.core.Device, report_data: bytes, log) -> bool:
    """Send the SET_REPORT control transfer to EP0 to trigger battery data."""

    wValue = (REPORT_TYPE_OUTPUT << 8) | REPORT_ID  # 0x02B5

    log.debug(
        f"Sending SET_REPORT: "
        f"bmRequestType={SET_REPORT_REQUEST_TYPE:#04x} "
        f"bRequest={SET_REPORT_REQUEST:#04x} "
        f"wValue={wValue:#06x} "
        f"wIndex={INTERFACE_NUMBER} "
        f"data={report_data.hex()}"
    )

    try:
        bytes_sent = dev.ctrl_transfer(
            bmRequestType=SET_REPORT_REQUEST_TYPE,
            bRequest=SET_REPORT_REQUEST,
            wValue=wValue,
            wIndex=INTERFACE_NUMBER,
            data_or_wLength=report_data,
            timeout=READ_TIMEOUT_MS,
        )
        log.info(f"SET_REPORT sent successfully ({bytes_sent} bytes)")
        return True
    except usb.core.USBError as e:
        log.error(f"SET_REPORT failed: {e}")
        return False


def main():

    parser = argparse.ArgumentParser(description="Change mouse LED color")
    parser.add_argument(
        "-b", "--brightness", type=int, default=255, help="Light Brightness (0-255)"
    )
    parser.add_argument("-c", "--clear", help="Disables lights", action="store_true")
    parser.add_argument(
        "-s", "--static_hex_color", type=str, help="Hex color (e.g., FF0000 for red)"
    )

    args = parser.parse_args()

    if args.brightness > 255 or args.brightness < 0:
        print("Invalid Brightness Value")
        return
    elif args.clear:
        report_data = bytes([REPORT_ID, 0x24] + [0x00] * 19)

    elif args.static_hex_color:
        try:
            r, g, b = parse_hex_color(args.static_hex_color)
            print(f"Parsed color: R={r} G={g} B={b}")
            print(f"Parsed color Hex: R={r:#04x} G={g:#04x} B={b:#04x}")
        except ValueError as e:
            print(f"Error parsing hex color: {e}")
            return

        report_data = create_static_report_data(r, g, b, args.brightness)

    print(f"Report data: {report_data.hex()}")

    log = setup_logging(
        "logs/lights.log", console_level=DEBUG, file_level=DEBUG, level=DEBUG
    )

    VID = 0x0BDA
    PID = 0xFFE0
    alt_PID = 0xFFF1

    dev = find_device(VID, PID, log)
    if dev is None:
        dev = find_device(VID, alt_PID, log)
        if dev is None:
            return

    try:
        usb.util.claim_interface(dev, INTERFACE_NUMBER)
        log.info(f"Claimed interface {INTERFACE_NUMBER}")

        if not send_set_report(dev, report_data, log):
            return

    except usb.core.USBError as e:
        log.error(f"USB error: {e}")
    finally:
        usb.util.release_interface(dev, INTERFACE_NUMBER)
        log.info("Interface released")


if __name__ == "__main__":
    main()
