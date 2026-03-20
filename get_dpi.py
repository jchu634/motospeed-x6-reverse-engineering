from logging import DEBUG

import usb.core
import usb.util

from loghandlers import setup_logging

# HID control transfer parameters
SET_REPORT_REQUEST_TYPE = 0x21  # host→device, class, interface
SET_REPORT_REQUEST = 0x09
REPORT_TYPE_OUTPUT = 0x02
REPORT_ID = 0xB3
INTERFACE_NUMBER = 4

READ_TIMEOUT_MS = 3000
REPORT_SIZE = 64

VID = 0x0BDA
PID = 0xFFE0
ALT_PID = 0xFFF1


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
    wValue = (REPORT_TYPE_OUTPUT << 8) | REPORT_ID  # 0x02B3

    log.debug(
        f"Sending SET_REPORT: "
        f"bmRequestType={SET_REPORT_REQUEST_TYPE:#04x} "
        f"bRequest={SET_REPORT_REQUEST:#04x} "
        f"wValue={wValue:#06x} "
        f"wIndex={INTERFACE_NUMBER} "
        f"len={len(report_data)} "
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


def read_interrupt_response(dev: usb.core.Device, log) -> None:
    cfg = dev.get_active_configuration()
    intf = cfg[(INTERFACE_NUMBER, 0)]

    ep_in = usb.util.find_descriptor(
        intf,
        custom_match=lambda e: (
            usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
        ),
    )

    if ep_in is None:
        log.error(f"No IN endpoint found on interface {INTERFACE_NUMBER}")
        return

    log.info(
        f"Reading response from EP {ep_in.bEndpointAddress:#04x} "
        f"(max packet {ep_in.wMaxPacketSize})"
    )

    try:
        data = dev.read(
            ep_in.bEndpointAddress, ep_in.wMaxPacketSize, timeout=READ_TIMEOUT_MS
        )
        print(f"Response ({len(data)} bytes): {bytes(data).hex()}")
        log.info(f"Response ({len(data)} bytes): {bytes(data).hex()}")
    except usb.core.USBError as e:
        log.error(f"Read failed: {e}")


def main():
    log = setup_logging(
        "logs/get_dpi.log", console_level=DEBUG, file_level=DEBUG, level=DEBUG
    )

    # Build report: 0xB3 0x06 + zero padding to 64 bytes total
    report_data = bytes([0xB3, 0x06] + [0x00] * (REPORT_SIZE - 2))
    print(f"Report data ({len(report_data)} bytes): {report_data.hex()}")

    dev = find_device(VID, PID, log)
    if dev is None:
        dev = find_device(VID, ALT_PID, log)
        if dev is None:
            return

    # Not-needed on windows
    # if dev.is_kernel_driver_active(INTERFACE_NUMBER):
    #     dev.detach_kernel_driver(INTERFACE_NUMBER)

    try:
        dev.set_configuration()
        usb.util.claim_interface(dev, INTERFACE_NUMBER)
        log.info(f"Claimed interface {INTERFACE_NUMBER}")

        if not send_set_report(dev, report_data, log):
            return

        read_interrupt_response(dev, log)

    except usb.core.USBError as e:
        log.error(f"USB error: {e}")
    finally:
        usb.util.release_interface(dev, INTERFACE_NUMBER)
        log.info("Interface released")


if __name__ == "__main__":
    main()
