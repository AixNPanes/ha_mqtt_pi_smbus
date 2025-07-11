# ha_mqtt_pi_smbus

[![CI](https://github.com/AixNPanes/ha_mqtt_pi_smbus/actions/workflows/ci.yml/badge.svg)](https://github.com/AixNPanes/ha_mqtt_pi_smbus/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/AixNPanes/ha_mqtt_pi_smbus/branch/main/graph/badge.svg)](https://codecov.io/gh/AixNPanes/ha_mqtt_pi_smbus)

> 🏠 **Home Assistant MQTT Pi SMBus** — A simple web server + frontend to toggle MQTT and discovery states on a Raspberry Pi using Flask, MQTT, and SMBus sensors.

---

## 🚀 Features

- MQTT connect/disconnect toggle
- Discovery toggle for device scanning
- Flask backend with async MQTT updates
- Simple JavaScript UI with status badges
- Unit tested (Python + JavaScript) with coverage reports

---

## 📦 Installation

Clone the repo:

```bash
git clone https://github.com/AixNPanes/ha_mqtt_pi_smbus.git
cd ha_mqtt_pi_smbus
```

Create your Python virtual environment:

```python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Install Node.js dependencies:

```npm install
```

## ⚡️ Running the app

Run the Flask server:

```source venv/bin/activate
flask run
```

Visit http://localhost:5000 (or your configured host).

## 🧪 Running tests

Python tests

```make test-python
```

JavaScript tests

```make test-javascript
```

All tests

```make test
```

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



