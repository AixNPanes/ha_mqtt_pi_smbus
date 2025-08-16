# ha_mqtt_pi_smbus

[![CI](https://github.com/AixNPanes/ha_mqtt_pi_smbus/actions/workflows/ci.yml/badge.svg)](https://github.com/AixNPanes/ha_mqtt_pi_smbus/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/AixNPanes/ha_mqtt_pi_smbus/branch/main/graph/badge.svg)](https://codecov.io/gh/AixNPanes/ha_mqtt_pi_smbus)

> 🏠 **Home Assistant MQTT Pi SMBus** — A simple web server + frontend to toggle MQTT and discovery states on a Raspberry Pi using Flask, MQTT, and SMBus sensors.

---

## 🚀 Features

- 🔌 MQTT connect/disconnect toggle
- 🔎 Home Assistant discovery support
- 🌐 Flask backend with status UI
- 📊 Device diagnostics (via MQTT sensors)
- 🧪 Unit tested (Python + JavaScript) with coverage reports
- ⚙️ Systemd service helpers for easy installation on Raspberry Pi

---

## 📦 Installation

Clone the repo:

```
bash
git clone https://github.com/AixNPanes/ha_mqtt_pi_smbus.git
cd ha_mqtt_pi_smbus
```

Create your Python virtual environment:

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Install Node.js dependencies:

```
npm install
```

## ⚡️ Running the app

Run the Flask server:

```
source venv/bin/activate
flask run
```

Visit http://localhost:5000 (or your configured host).

🛠 Systemd Service Helpers
This project includes Makefile targets for running the example app as a user-mode systemd service (no root required):

Command	Description
make service-install	Install systemd service
make service-uninstall	Remove systemd service
make service-start	Start the service
make service-stop	Stop the service
make service-status	Show current status
make service-logs	Dump logs from journal + /var/log
make service-logs-follow	Stream logs live

## 🧪 Running tests

Python tests

```
make test-python
```

JavaScript tests

```
make test-javascript
```

All tests

```
make test
```

🛠 Debugging with device/config/state
When testing MQTT discovery, Home Assistant provides a helpful debug topic:

device/config/state
If you subscribe to this topic (for example, with mosquitto_sub):

mosquitto_sub -v -t 'homeassistant/#' | grep config/state

You may also subscribe to the device/config/state topic in the "Configure" for the MQTT integration in Home Assistant. If you then publish a message on the topic device/config/get (the message content is ignored), Home Assistant will publish the parsed device configuration it currently holds for your entity.  Note: for security reasons, the MQTT broker, port, username and password will be returned as generic values if they exist in the configuration.

This is useful for:

✅ Verifying that discovery messages are being received

✅ Checking that fields like name, unique_id, device_class, and state_topic were parsed correctly

✅ Debugging mismatches between your published config and what HA actually registered

⚠️ These messages are for debugging only — they aren’t intended for automations.



## ✅ Continuous Integration

GitHub Actions: Runs tests & uploads coverage

Codecov: Publishes coverage reports for insights

## 🤝 Contributing

PRs are welcome!
If you’d like to add features or fix bugs:

1. Fork this repo
1.  Create a feature branch: git checkout -b feature/my-feature
1.  Commit changes and push
1.  Open a pull request

## 📄 License
This project is licensed under the Zero-Clause BSD License (0BSD).
See LICENSE for the full text.



