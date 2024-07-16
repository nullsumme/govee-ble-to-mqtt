import argparse
import time
import json
from bleson import get_provider, Observer
from bleson.logger import log, set_level, ERROR, DEBUG
from pprint import pprint
from struct import unpack_from
import paho.mqtt.client as mqtt

set_level(ERROR)

govee_devices = {}
log_interval = 59

def mqtt_publish(event, data):
    """
    Publish sensor data to an MQTT broker and optionally send Home Assistant autodiscovery messages.

    Parameters:
    - event: Name of the event (e.g., sensor name).
    - data: Dictionary containing sensor data.
    """
    if not data:
        print("Not publishing empty data for: ", event)
        return

    try:
        client = mqtt.Client()
        if args.mqtt_username and args.mqtt_password:
            client.username_pw_set(args.mqtt_username, args.mqtt_password)
        client.connect(args.mqtt_host, args.mqtt_port, 60)
        client.loop_start()

        # Prepare payload for publishing
        payload = {
            'temperature': data['temperature'],
            'humidity': data['humidity'],
            'battery': data['battery'],
            'rssi': data['rssi'],
            'timestamp': data['timestamp']
        }

        if args.verbose:
            print(f"Publishing {event} to MQTT [{args.mqtt_host}:{args.mqtt_port}] on topic {args.mqtt_topic}: {payload}")

        # Publish sensor data
        client.publish(args.mqtt_topic, json.dumps(payload))

        # Send Home Assistant autodiscovery messages if enabled
        if args.ha_discovery:
            send_ha_discovery_messages(client, data)

        client.loop_stop()

    except mqtt.MQTTException as e:
        print(f"Failed to connect to MQTT broker: {e}")
        print(f"  Payload was: {payload}")

def send_ha_discovery_messages(client, data):
    """
    Send Home Assistant autodiscovery messages.

    Parameters:
    - client: MQTT client instance.
    - data: Dictionary containing sensor data.
    """
    device_id = data['address'].replace(":", "").lower()
    device_name = data['name']

    discovery_payloads = [
        {
            "device_class": "temperature",
            "name": "Temperature",
            "unit_of_measurement": "°C",
            "value_template": "{{ value_json.temperature }}",
            "unique_id": f"{device_id}_temperature"
        },
        {
            "device_class": "humidity",
            "name": "Humidity",
            "unit_of_measurement": "%",
            "value_template": "{{ value_json.humidity }}",
            "unique_id": f"{device_id}_humidity"
        },
        {
            "device_class": "battery",
            "name": "Battery",
            "unit_of_measurement": "%",
            "value_template": "{{ value_json.battery }}",
            "unique_id": f"{device_id}_battery"
        },
        {
            "device_class": "signal_strength",
            "name": "RSSI",
            "unit_of_measurement": "dBm",
            "value_template": "{{ value_json.rssi }}",
            "unique_id": f"{device_id}_rssi"
        }
    ]

    for payload in discovery_payloads:
        payload["state_topic"] = args.mqtt_topic
        payload["device"] = {
            "identifiers": [device_id],
            "name": device_name,
            "model": "Govee Sensor",
            "manufacturer": "Govee"
        }
        client.publish(f"homeassistant/sensor/{device_id}/{payload['device_class']}/config", json.dumps(payload), retain=True)

def twos_complement(n: int, w: int = 16) -> int:
    """
    Convert an integer to its two's complement representation.

    Parameters:
    - n: Integer to convert.
    - w: Width (number of bits) of the integer.

    Returns:
    - Two's complement representation of the integer.
    """
    if n & (1 << (w - 1)):
        n = n - (1 << w)
    return n

def process(mac):
    """
    Process the data from a Govee device and publish it via MQTT.

    Parameters:
    - mac: MAC address of the Govee device.
    """
    govee_device = govee_devices[mac]
    if args.raw or args.verbose:
        pprint(govee_device)
    mqtt_publish(govee_device['name'], govee_device)

def on_advertisement(advertisement):
    """
    Callback function for BLE advertisement data.

    Parameters:
    - advertisement: BLE advertisement data.
    """
    log.debug(advertisement)

    mac = advertisement.address.address
    if mac in govee_devices and advertisement.mfg_data is not None:
        time_now = time.time()
        if time_now - govee_devices[mac]["last_log"] > log_interval:
            prefix = int(advertisement.mfg_data.hex()[0:4], 16)

            # H5074 devices
            if prefix == 0x88EC and len(advertisement.mfg_data) == 9:
                raw_temp, hum, batt = unpack_from("<HHB", advertisement.mfg_data, 3)
                govee_devices[mac]["temperature"] = float(twos_complement(raw_temp) / 100.0)
                govee_devices[mac]["humidity"] = float(hum / 100.0)
                govee_devices[mac]["battery"] = int(batt)
                govee_devices[mac]["timestamp"] = time_now
                govee_devices[mac]["address"] = mac

                if advertisement.rssi is not None and advertisement.rssi != 0:
                    govee_devices[mac]["rssi"] = advertisement.rssi
                process(mac)
                govee_devices[mac]["last_log"] = time_now

            # H5179 devices
            if prefix == 0x0188 and len(advertisement.mfg_data) == 11:
                raw_temp, hum, batt = unpack_from("<HHB", advertisement.mfg_data, 6)
                govee_devices[mac]["temperature"] = float(twos_complement(raw_temp) / 100.0)
                govee_devices[mac]["humidity"] = float(hum / 100.0)
                govee_devices[mac]["battery"] = int(batt)
                govee_devices[mac]["timestamp"] = time_now
                govee_devices[mac]["address"] = mac

                if advertisement.rssi is not None and advertisement.rssi != 0:
                    govee_devices[mac]["rssi"] = advertisement.rssi
                process(mac)
                govee_devices[mac]["last_log"] = time_now

    # Add new Govee device if detected
    if advertisement.name is not None and advertisement.name.startswith("Govee"):
        if mac not in govee_devices:
            govee_devices[mac] = {
                "address": mac,
                "name": advertisement.name.split("'")[0],
                "last_log": 0,
                "timestamp": 0
            }
            if args.verbose:
                print("Found " + govee_devices[mac]["name"])

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="BLE to MQTT bridge for Govee devices with optional Home Assistant autodiscovery"
    )

    parser.add_argument("-r", "--raw", dest="raw", action="store_true", help="Print JSON data to stdout")
    parser.add_argument("--mqtt_host", dest="mqtt_host", default="localhost", help="Hostname of MQTT broker (default: localhost)")
    parser.add_argument("--mqtt_port", dest="mqtt_port", type=int, default=1883, help="Port of MQTT broker (default: 1883)")
    parser.add_argument("--mqtt_topic", dest="mqtt_topic", default="govee/sensor_data", help="MQTT topic to publish to (default: govee/sensor_data)")
    parser.add_argument("--mqtt_username", dest="mqtt_username", help="MQTT username")
    parser.add_argument("--mqtt_password", dest="mqtt_password", help="MQTT password")
    parser.add_argument("--ha_discovery", dest="ha_discovery", action="store_true", help="Enable Home Assistant autodiscovery messages")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode")

    args = parser.parse_args()

    # Set up BLE observer
    adapter = get_provider().get_adapter()
    observer = Observer(adapter)
    observer.on_advertising_data = on_advertisement

    try:
        # Start observing BLE advertisements
        while True:
            observer.start()
            time.sleep(0.5)
            observer.stop()
    except KeyboardInterrupt:
        observer.stop()
