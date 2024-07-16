# Govee BLE to MQTT Bridge

This Python script listens for BLE advertisements from Govee devices, processes the data, and publishes it to an MQTT broker. It supports optional username and password authentication for the MQTT broker, as well as optional Home Assistant autodiscovery messages.

## Features

- Listens for BLE advertisements from Govee devices.
- Processes temperature, humidity, battery level, and RSSI data.
- Publishes processed data to an MQTT broker.
- Supports optional MQTT authentication.
- Provides options for verbose output and raw data printing.
- Optionally sends Home Assistant autodiscovery messages.

## Requirements

- Python 3
- [Bleson](https://pypi.org/project/bleson/)
- [Paho MQTT](https://pypi.org/project/paho-mqtt/)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/nullsumme/govee-ble-to-mqtt.git
    cd govee-ble-to-mqtt
    ```

2. Create and activate a virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3. Install the required Python packages:
    ```bash
    pip install bleson paho-mqtt
    ```

## Usage

```bash
usage: goveelog.py [-h] [-r] [--mqtt_host MQTT_HOST] [--mqtt_port MQTT_PORT]
                   [--mqtt_topic MQTT_TOPIC] [--mqtt_username MQTT_USERNAME]
                   [--mqtt_password MQTT_PASSWORD] [--ha_discovery] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -r, --raw             print raw data to stdout
  --mqtt_host MQTT_HOST
                        hostname or IP of the MQTT broker (default: localhost)
  --mqtt_port MQTT_PORT
                        port of the MQTT broker (default: 1883)
  --mqtt_topic MQTT_TOPIC
                        MQTT topic to publish to (default: govee/sensor_data)
  --mqtt_username MQTT_USERNAME
                        MQTT username
  --mqtt_password MQTT_PASSWORD
                        MQTT password
  --ha_discovery        enable Home Assistant autodiscovery messages
  -v, --verbose         verbose output to watch the threads
```

## Examples

### Basic Usage

Listen for BLE advertisements and publish data to the default MQTT broker (`localhost:1883`) without authentication.

```bash
python3 goveelog.py
```

### Using a Custom MQTT Broker

Specify a custom MQTT broker host and port.

```bash
python3 goveelog.py --mqtt_host example.com --mqtt_port 1884
```

### Using MQTT Authentication

Provide MQTT username and password for authentication.

```bash
python3 goveelog.py --mqtt_host example.com --mqtt_port 1884 --mqtt_username yourusername --mqtt_password yourpassword
```

### Enable Home Assistant Autodiscovery

Enable Home Assistant autodiscovery messages.

```bash
python3 goveelog.py --ha_discovery
```

### Verbose Mode

Enable verbose output to see more detailed information.

```bash
python3 goveelog.py -v
```

### Print Raw Data

Print the raw JSON data to stdout.

```bash
python3 goveelog.py -r
```

## Running as a Systemd Service

To run the script as a service on a Linux system, you can create a systemd service entry.

1. Create a systemd service file:
    ```bash
    sudo nano /etc/systemd/system/govee-mqtt.service
    ```

2. Add the following content to the file:
    ```ini
    [Unit]
    Description=Govee BLE to MQTT Bridge
    After=network.target

    [Service]
    User=yourusername
    WorkingDirectory=/path/to/govee-ble-to-mqtt
    ExecStart=/path/to/govee-ble-to-mqtt/.venv/bin/python /path/to/govee-ble-to-mqtt/goveelog.py --mqtt_host your_mqtt_host --mqtt_port your_mqtt_port --mqtt_topic your_mqtt_topic --mqtt_username your_mqtt_username --mqtt_password your_mqtt_password --ha_discovery
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```

    Replace `/path/to/govee-ble-to-mqtt` with the actual path to the directory where you cloned the repository, and replace the placeholders (`yourusername`, `your_mqtt_host`, `your_mqtt_port`, `your_mqtt_topic`, `your_mqtt_username`, `your_mqtt_password`) with your actual configuration.

3. Reload the systemd manager configuration:
    ```bash
    sudo systemctl daemon-reload
    ```

4. Enable the service to start on boot:
    ```bash
    sudo systemctl enable govee-mqtt.service
    ```

5. Start the service:
    ```bash
    sudo systemctl start govee-mqtt.service
    ```

6. Check the status of the service:
    ```bash
    sudo systemctl status govee-mqtt.service
    ```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## Acknowledgements

- Govee BLE parsing is based on: [sensor.goveetemp_bt_hci](https://github.com/Home-Is-Where-You-Hang-Your-Hack/sensor.goveetemp_bt_hci)
- Bleson: A Python Bluetooth Low Energy (BLE) library.
- Paho MQTT: A Python MQTT client library.