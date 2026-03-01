import usb.core
import usb.util


def describe_device(dev):
    """Generate a text description of a USB device and its interfaces."""
    info = []
    info.append(f"Device: VID=0x{dev.idVendor:04X}, PID=0x{dev.idProduct:04X}")

    try:
        manufacturer = usb.util.get_string(dev, dev.iManufacturer)
        product = usb.util.get_string(dev, dev.iProduct)
        serial = usb.util.get_string(dev, dev.iSerialNumber)
    except (usb.core.USBError, NotImplementedError, ValueError):
        manufacturer, product, serial = None, None, None

    if manufacturer:
        info.append(f"  Manufacturer: {manufacturer}")
    if product:
        info.append(f"  Product: {product}")
    if serial:
        info.append(f"  Serial Number: {serial}")

    # Each configuration may represent different modes
    for cfg in dev:
        info.append(f"  Configuration {cfg.bConfigurationValue}:")
        for intf in cfg:
            info.append(
                f"    Interface {intf.bInterfaceNumber}: "
                f"Class=0x{intf.bInterfaceClass:02X}, "
                f"Subclass=0x{intf.bInterfaceSubClass:02X}, "
                f"Protocol=0x{intf.bInterfaceProtocol:02X}"
            )
    return "\n".join(info)


def main():
    """Enumerate and describe all connected USB devices."""
    devices = usb.core.find(find_all=True)
    devices = list(devices)

    if not devices:
        print("No USB devices found.")
        return

    for idx, dev in enumerate(devices, start=1):
        print(f"\n=== Device {idx} ===")
        print(describe_device(dev))


if __name__ == "__main__":
    main()
