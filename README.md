# Multipoint Environmental Monitoring System

Real-time temperature and humidity monitoring across multiple ESP32 nodes, built for bench testing of humidifier–breathing circuit combinations in a neonatal respiratory device development context.

Developed during R&D internship at **InnAccel Technologies Pvt Ltd, Bengaluru** (Jan 2026 – Present).

---

## Overview

During bench testing of humidifier and breathing circuit combinations for neonatal respiratory devices, it was critical to monitor temperature and humidity simultaneously across multiple junctions in real time. This system deploys multiple ESP32 nodes,each paired with an SHT4x sensor — at key circuit junctions. All nodes transmit data over Wi-Fi to a centralized Flask server, which logs readings to CSV and displays a live status dashboard.

```
Junction → SHT4x Sensor → ESP32 → Wi-Fi (HTTP POST) → Flask Server → CSV Log + Dashboard
```

---

## Sensor Placement

| Node ID | Junction |
|---|---|
| `environment` | ATP conditions |
| `hum_inlet` | Humidifier inlet |
| `hum_outlt` | Humidifier outlet |
| `post_proximal` | Post proximal |
| `y_piece` | Y-piece |

---

## System Architecture

```
┌─────────────┐     I2C      ┌────────┐   HTTP POST   ┌──────────────┐
│  SHT4x (x5) │ ──────────▶ │ ESP32  │ ────────────▶ │ Flask Server │
│  Temp + RH  │             │ (x4)   │   Wi-Fi LAN   │  (Laptop)    │
└─────────────┘             └────────┘               └──────┬───────┘
                                                            │
                                              ┌─────────────┴──────────┐
                                              │                        │
                                       ┌──────▼──────┐       ┌────────▼────────┐
                                       │  CSV Logger │       │  Live Dashboard │
                                       │  (6s snap)  │       │  (2s refresh)   │
                                       └─────────────┘       └─────────────────┘
```

---

## Features

- **Multi-node sensing** — 5 ESP32 nodes operating simultaneously, each reading SHT4x over I2C
- **Real-time dashboard** — live web UI showing temperature, humidity, last update time, and node status (OK / LAGGING) per junction
- **Periodic CSV logging** — synchronized snapshot every 6 seconds across all nodes with timestamps
- **Node health monitoring** — 12-second lag threshold; nodes exceeding this are flagged red on dashboard
- **Transmission interval optimisation** — evaluated at 1s, 3s, 5s, and 6s; 6 seconds identified as optimal for stable multi-node HTTP without request overlap
- **Network resilience** — automatic Wi-Fi reconnection on disconnect; mobile hotspot preferred over corporate LAN to avoid AP isolation issues

---

## Hardware

| Component | Details |
|---|---|
| Microcontroller | ESP32 (built-in Wi-Fi) |
| Sensor | SHT40/SHT41 — I2C, address 0x44, high-precision mode |
| Power | 5V USB per node |
| Server | Laptop running Flask over local Wi-Fi |

---

## Software Stack

**ESP32 Firmware (Arduino)**
- `WiFi.h` — Wi-Fi connectivity
- `HTTPClient.h` — HTTP POST requests
- `Wire.h` — I2C communication
- `SensirionI2cSht4x` — SHT4x sensor library

**Flask Server (Python 3.12)**
- `Flask 3.1.2` — web framework and dashboard
- `csv`, `datetime`, `threading`, `json` — standard library logging and scheduling

---

## Data Format

Each ESP32 node transmits the following JSON payload every 6 seconds:

```json
{
  "esp_id": "y_piece",
  "time": 123456,
  "temperature": 28.94,
  "humidity": 62.93
}
```

CSV log columns:
```
PC_Time | hum_inlet_Temp | hum_inlet_Hum | hum_inlet_Status | hum_outlt_Temp | ...
```
Status values: `1` = healthy, `0` = lagging (no data within 12s threshold)

---

## Setup and Usage

### 1. Flash ESP32 Nodes

Open `esp32_node/sensor_node.ino` in Arduino IDE and configure:

```cpp
const char* ssid     = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverName = "http://YOUR_SERVER_IP:5000/data";
const char* ESP_ID   = "hum_inlet"; // Change per node: hum_inlet, hum_outlt, post_proximal, y_piece
```

Install the required board package and libraries, then flash each ESP32 with its unique `ESP_ID`.

### 2. Run Flask Server

```bash
pip install flask
python flask_server/server.py
```

Server starts at `http://0.0.0.0:5000`. Open in browser for live dashboard.

### 3. Network Setup

- Connect all ESP32 nodes and the laptop to the **same Wi-Fi network**
- Use a **mobile hotspot** rather than a corporate/institutional network — AP isolation on enterprise networks blocks inter-device communication
- Ensure port 5000 is accessible and DHCP is enabled
- Note the laptop's IP address and update `serverName` in ESP32 firmware accordingly

---

## Key Engineering Decisions

**Why 6-second transmission interval?**
Tested at 1s, 3s, and 5s intervals. With 4 nodes transmitting simultaneously, shorter intervals caused overlapping HTTP requests and inconsistent CSV row counts. 6 seconds eliminated request collisions and achieved stable, predictable logging.

**Why mobile hotspot over company Wi-Fi?**
Enterprise networks often enable AP isolation, which prevents devices on the same network from communicating with each other. Mobile hotspots disable AP isolation by default, enabling seamless ESP32-to-server communication.

**Why I2C address 0x44?**
SHT4x supports 0x44 and 0x45. Since each ESP32 hosts a single sensor, 0x44 was used consistently across all nodes.

---

## Results

- Benchmarked **25+ humidifier–breathing circuit configurations** across simulated ambient conditions of 22°C and 30°C
- Sensors validated against F&P MR850 and CH510 humidifier systems
- Derived parameters: Absolute Humidity (mg/L) and Dew Point temperature for moisture content and condensation analysis across the breathing circuit

---

## Repository Structure

```
multipoint-environmental-monitoring-system/
├── esp32_node/
│   └── sensor_node.ino       # ESP32 firmware (configure SSID, IP, ESP_ID before flashing)
├── flask_server/
│   └── server.py             # Flask server with dashboard and CSV logger
├── README.md
└── LICENSE
```

---

## Important Note

This project was developed in an R&D internship context for medical device bench testing. No patient data, clinical records, or proprietary device specifications are included in this repository. Wi-Fi credentials and internal IP addresses have been removed — configure your own network settings before deployment.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
