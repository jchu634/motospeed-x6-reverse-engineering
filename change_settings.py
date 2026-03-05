import argparse
import os
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


def clear_console():
    """Clears the console screen based on the operating system."""
    # Windows
    if os.name == "nt":
        os.system("cls")
    # macOS, Linux
    else:
        os.system("clear")


def show_commands():
    clear_console()
    print("Commands:")
    print("l : toggle lift up distance (low, high)")
    print("r : toggle ripple")
    print("a : toggle angle snap")
    print("m : toggle motion sync")
    print("e : toggle esports mode")
    print("d : change debounce time")
    print("s : change sleep time")
    print("c : show current states")
    print("h : show commands again")
    print("q : quit")


def create_general_report_data(rawCommands) -> bytes:
    return bytes(
        [
            REPORT_ID,
            0x42,
            rawCommands[0],
            rawCommands[1],
            rawCommands[2],
            rawCommands[3],
            0x00,
            0x01,
            rawCommands[4],
        ]
        + [0x00] * 12
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


def apply_settings(dev: usb.core.Device, rawCommands, log) -> bool:
    """Helper function to claim interface, send report, and release interface."""
    try:
        usb.util.claim_interface(dev, INTERFACE_NUMBER)
        log.info(f"Claimed interface {INTERFACE_NUMBER}")
        report_data = create_general_report_data(rawCommands)

        if not send_set_report(dev, report_data, log):
            return False
    except usb.core.USBError as e:
        log.error(f"USB error: {e}")
        return False
    finally:
        usb.util.release_interface(dev, INTERFACE_NUMBER)
        log.info("Interface released")

    return True


def flip(inp):
    if inp == 0x01:
        return 0x02
    return 0x01


def main():

    log = setup_logging(
        "logs/settings.log", console_level=DEBUG, file_level=DEBUG, level=DEBUG
    )

    VID = 0x0BDA
    PID = 0xFFE0
    alt_PID = 0xFFF1

    dev = find_device(VID, PID, log)
    if dev is None:
        dev = find_device(VID, alt_PID, log)
        if dev is None:
            return

    rawCommands = [0x01, 0x01, 0x02, 0x01, 0x01]

    show_commands()
    while True:
        command = input()[0]
        match command:
            case "l":
                rawCommands[0] = flip(rawCommands[0])
                apply_settings(dev, rawCommands, log)
            case "r":
                rawCommands[1] = flip(rawCommands[1])
                apply_settings(dev, rawCommands, log)
            case "a":
                rawCommands[2] = flip(rawCommands[2])
                apply_settings(dev, rawCommands, log)
            case "m":
                rawCommands[3] = flip(rawCommands[3])
                apply_settings(dev, rawCommands, log)
            case "e":
                rawCommands[4] = flip(rawCommands[4])
                apply_settings(dev, rawCommands, log)
            case "d":
                n = int(input("Enter Debounce (ms)(0-20): "))
                print("0x" + f"{n:02X}" if 0 <= n <= 20 else "out of range")
                report = bytes([REPORT_ID, 0x43, n] + [0x00] * 18)
                send_set_report(dev, report, log)
            case "s":
                n = int(input("Enter Sleep Time (minutes)(0-255): "))
                print("0x" + f"{n:02X}" if 0 <= n <= 255 else "out of range")
                report = bytes([REPORT_ID, 0x0A, 0x01, n] + [0x00] * 17)
                send_set_report(dev, report, log)
            case "c":
                print("Not done yet")
            case "h":
                show_commands()
            case "q":
                break
            case _:
                pass


if __name__ == "__main__":
    main()
