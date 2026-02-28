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
REPORT_DATA = bytes([REPORT_ID, 0x06] + [0x00] * 19)  # 21 bytes total

# Interrupt IN endpoint for the battery response (EP5 IN)
BATTERY_ENDPOINT = 0x85
# Report ID in byte 0 of the battery HID payload
BATTERY_REPORT_ID = 0xB4
# Battery value offset within the raw HID payload (0x2F - 0x1B = 20)
BATTERY_OFFSET = 20

READ_LENGTH = 64
READ_TIMEOUT_MS = 3000
MAX_READ_ATTEMPTS = 20


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


def send_set_report(dev: usb.core.Device, log) -> bool:
    """Send the SET_REPORT control transfer to EP0 to trigger battery data."""

    wValue = (REPORT_TYPE_OUTPUT << 8) | REPORT_ID  # 0x02B5

    log.debug(
        f"Sending SET_REPORT: "
        f"bmRequestType={SET_REPORT_REQUEST_TYPE:#04x} "
        f"bRequest={SET_REPORT_REQUEST:#04x} "
        f"wValue={wValue:#06x} "
        f"wIndex={INTERFACE_NUMBER} "
        f"data={REPORT_DATA.hex()}"
    )

    try:
        bytes_sent = dev.ctrl_transfer(
            bmRequestType=SET_REPORT_REQUEST_TYPE,
            bRequest=SET_REPORT_REQUEST,
            wValue=wValue,
            wIndex=INTERFACE_NUMBER,
            data_or_wLength=REPORT_DATA,
            timeout=READ_TIMEOUT_MS,
        )
        log.info(f"SET_REPORT sent successfully ({bytes_sent} bytes)")
        return True
    except usb.core.USBError as e:
        log.error(f"SET_REPORT failed: {e}")
        return False


def read_battery_level(dev: usb.core.Device, log) -> int | None:
    """Read from EP 0x85 until a battery report is received."""
    log.info(
        f"Listening on endpoint {BATTERY_ENDPOINT:#04x} "
        f"for report ID {BATTERY_REPORT_ID:#04x}..."
    )

    for attempt in range(1, MAX_READ_ATTEMPTS + 1):
        try:
            data = dev.read(BATTERY_ENDPOINT, READ_LENGTH, timeout=READ_TIMEOUT_MS)
        except usb.core.USBTimeoutError:
            log.warning(f"Attempt {attempt}/{MAX_READ_ATTEMPTS}: read timed out")
            continue
        except usb.core.USBError as e:
            log.error(f"Attempt {attempt}/{MAX_READ_ATTEMPTS}: read error: {e}")
            return None

        log.debug(
            f"Attempt {attempt}/{MAX_READ_ATTEMPTS}: "
            f"[{len(data)} bytes] {bytes(data).hex()}"
        )

        if data[0] == BATTERY_REPORT_ID:
            if len(data) > BATTERY_OFFSET:
                battery = data[BATTERY_OFFSET]
                log.info(
                    f"Battery report matched: raw={battery:#04x} ({battery} decimal)"
                )
                return battery
            else:
                log.warning(
                    f"Battery report too short: "
                    f"{len(data)} bytes, need >{BATTERY_OFFSET}"
                )
        else:
            log.debug(f"Skipping report ID={data[0]:#04x}")

    log.error(f"No battery report received after {MAX_READ_ATTEMPTS} attempts.")
    return None


def main():
    log = setup_logging(
        "logs/battery.log", console_level=DEBUG, file_level=DEBUG, level=DEBUG
    )
    log.info("Starting mouse battery level reader")

    # Fill in your VID/PID here
    VID = 0x0BDA
    PID = 0xFFE0

    dev = find_device(VID, PID, log)
    if dev is None:
        return

    try:
        usb.util.claim_interface(dev, INTERFACE_NUMBER)
        log.info(f"Claimed interface {INTERFACE_NUMBER}")

        if not send_set_report(dev, log):
            return

        battery = read_battery_level(dev, log)

        if battery is not None:
            print(f"Battery level: {battery}% (raw: {battery:#04x})")
        else:
            log.error("Failed to retrieve battery level.")

    except usb.core.USBError as e:
        log.error(f"USB error: {e}")
    finally:
        usb.util.release_interface(dev, INTERFACE_NUMBER)
        log.info("Interface released")


if __name__ == "__main__":
    main()
