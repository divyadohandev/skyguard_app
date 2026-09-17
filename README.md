# 🌦️ SkyGuard AI — Intelligent Anomaly Detection for Automatic Weather Stations

> **SIH 2026 | Problem Statement 26073 | Disaster Management | Software**
>
> An AI/ML-assisted quality-control and anomaly-detection system for Automatic Weather Station (AWS) telemetry.

## 📌 Project Overview

**SkyGuard AI** is a prototype system designed to detect suspicious or anomalous observations coming from Automatic Weather Stations.

It combines **machine learning with multiple quality-control checks** instead of relying on a single anomaly detector.

### Core idea

> **An extreme reading should not automatically be treated as a sensor fault.**

For example, if one station reports **58°C** while nearby stations are around 28°C, it may indicate a sensor problem. If several nearby stations report similarly high temperatures, it may represent a genuine regional extreme.

SkyGuard AI therefore considers **ML, physical limits, temporal behavior, and spatial/buddy evidence**.

---

## 🎯 Problem Statement

### AI/ML-Based Intelligent Anomaly Detection for Automatic Weather Stations (AWS)

The system aims to identify:

1. Normal observations
2. Possible sensor faults
3. Sudden/unrealistic changes
4. Spatially inconsistent observations
5. Potential regional weather extremes

It also provides an explanation and recommended operational action.

---

## 💡 Solution Architecture

```text
AWS / ESP32 Sensor Data
          ↓
     Data Ingestion
          ↓
   Basic Validation
          ↓
 ┌────────┴───────────┐
 ↓        ↓           ↓
Physics  Temporal     Spatial
Checks   Checks       / Buddy Check
 └────────┬───────────┘
          ↓
    Isolation Forest
          ↓
    Evidence Fusion
          ↓
 Anomaly Classification
          ↓
 Explanation + Confidence
          ↓
 Self-Healing / Quarantine
          ↓
    Streamlit Dashboard
```

---

## ⭐ Key Features

### 1. Real-Time Telemetry Processing

The backend receives:

- Temperature
- Humidity
- Pressure
- Station ID
- Timestamp
- Sequence ID

### 2. Machine Learning Anomaly Detection

Uses **Isolation Forest** from Scikit-learn.

It is an unsupervised model that identifies observations that are unusual compared with learned normal data.

The ML model indicates that a sample is unusual; it does **not by itself prove that a sensor is broken**.

### 3. Physics-Based QC

Current prototype ranges:

| Parameter | Prototype Range |
|---|---:|
| Temperature | -20°C to 50°C |
| Humidity | 10% to 95% |
| Pressure | 995 to 1025 hPa |

These are prototype configuration values, not official IMD operational thresholds.

### 4. Temporal Consistency

Compares the current reading with the previous reading from the same station.

Prototype warning thresholds include:

- Temperature change > 10°C
- Humidity change > 30%
- Pressure change > 10 hPa

### 5. Spatial / Buddy Check

Compares a station with configured peer-station baselines.

This helps distinguish:

```text
One station → extreme value
Nearby stations → normal
        ↓
Possible sensor fault
```

from:

```text
Several stations → similar extreme values
        ↓
Possible regional weather event
```

The current peer data is prototype/hardcoded.

### 6. Evidence Fusion

The decision combines:

```text
ML anomaly
+ Physics failure
+ Temporal discontinuity
+ Spatial disagreement
        ↓
Anomaly decision
```

The current confidence score is a **prototype evidence score, not a calibrated probability**.

### 7. Explainable Feature Contribution

The dashboard shows which signals contributed to the decision.

Example:

```text
ML Anomaly Signal       → Active
Temporal Discontinuity  → Active
Spatial Disagreement   → Active
Temperature Violation  → Inactive
```

The current prototype uses feature-contribution indicators. It should **not be described as SHAP** unless SHAP is actually implemented.

### 8. Fault Classification

Prototype categories include:

- Thermal Spike / ADC Surge Fault
- Humidity Sensor Fault
- Pressure Sensor Drift
- General Sensor Anomaly

### 9. Self-Healing / Data Recovery

For anomalous data, the prototype can recommend:

```text
Quarantine original reading
        ↓
Estimate replacement value
        ↓
Use estimate downstream
        ↓
Inspect / calibrate sensor
```

This is **data-level recovery**, not physical sensor repair.

---

## 🖥️ Dashboard

The frontend uses **Streamlit**.

It provides:

- Active station information
- Temperature, humidity and pressure
- Anomaly status
- Sensor health indicator
- Historical telemetry
- QC pipeline
- Feature explanations
- Recommended actions
- Station/fleet visualization

---

## 🔄 End-to-End Data Flow

```text
Sensor / ESP32
     ↓
Telemetry Packet
     ↓
FastAPI Backend
     ↓
Input Validation
     ↓
Physics QC
     ↓
Temporal QC
     ↓
Spatial QC
     ↓
Isolation Forest
     ↓
Evidence Fusion
     ↓
Classification
     ↓
Explanation / Action
     ↓
Streamlit Dashboard
```

---

## 🏗️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Streamlit | Monitoring dashboard |
| Backend | FastAPI | REST API |
| API Server | Uvicorn | Runs FastAPI |
| ML | Scikit-learn | Isolation Forest |
| Data Processing | Pandas | Data handling |
| Numerical Computing | NumPy | Numerical operations |
| Visualization | Plotly | Charts |
| Map/UI | PyDeck / Streamlit | Station visualization |
| Telemetry Client | Requests | Simulator → API |
| Edge Prototype | ESP32 | Future sensor source |
| Deployment | Streamlit Cloud + Render | Hosting |
| Language | Python | Main language |

---

## 📁 Project Structure

```text
skyguard_app/
│
├── app.py
│   └── Streamlit dashboard
│
├── backend.py
│   └── FastAPI backend
│
├── sensor_stream.py
│   └── Telemetry simulator
│
├── ml_engine/
│   ├── anomaly_model.py
│   │   └── Isolation Forest model
│   │
│   └── weather_normal_data.csv
│       └── Prototype normal training data
│
├── requirements.txt
│   └── Python dependencies
│
├── render.yaml
│   └── Render configuration
│
└── .gitignore
    └── Local/secrets exclusions
```

---

## 🧠 ML Model

The Isolation Forest model uses:

```text
temperature
humidity
pressure
```

Current configuration:

```python
IsolationForest(
    n_estimators=100,
    contamination=0.05,
    random_state=42
)
```

The current training dataset contains **5,000 synthetic normal observations**.

### ⚠️ Important

The training data is synthetic and is **not official IMD historical AWS data**.

Production deployment should use real AWS observations and labelled/validated fault cases.

---

## 🔌 API

### Deployed Backend

```text
https://skyguard-app-xeak.onrender.com
```

### Swagger Documentation

```text
https://skyguard-app-xeak.onrender.com/docs
```

### OpenAPI

```text
https://skyguard-app-xeak.onrender.com/openapi.json
```

### POST `/api/v1/detect`

Sends telemetry for analysis.

Example:

```json
{
  "station_id": "AWS-IND-001",
  "temperature": 28.4,
  "humidity": 68.2,
  "pressure": 1012.7
}
```

### GET `/api/v1/latest`

Returns the latest processed reading.

### GET `/health`

Checks backend health and model status.

---

## 🧪 Telemetry Simulator

`sensor_stream.py` simulates an AWS station.

It can inject a temperature fault such as:

```text
Normal temperature → 24–32°C
Injected fault      → 58.4°C
```

This allows the complete pipeline to be demonstrated without physical hardware.

---

## 🌐 Current Deployment

### Streamlit Dashboard

```text
https://skyguardapp-ykibmzfrwzv4h5ntoufrgx.streamlit.app/
```

### Render Backend

```text
https://skyguard-app-xeak.onrender.com
```

### Swagger

```text
https://skyguard-app-xeak.onrender.com/docs
```

---

## 💻 Local Setup

### 1. Clone

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd skyguard_app
```

### 2. Create virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Start backend

```powershell
python -m uvicorn backend:app --reload --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

### 5. Start dashboard

Open a second PowerShell:

```powershell
python -m streamlit run app.py
```

Dashboard:

```text
http://localhost:8501
```

### 6. Run simulator

For local testing, use:

```text
http://127.0.0.1:8000/api/v1/detect
```

Then:

```powershell
python sensor_stream.py
```

---

## 🧪 Demo Scenarios

### Normal Weather

```text
Temperature → Normal
Humidity    → Normal
Pressure    → Normal
        ↓
ACCEPTED
```

### Isolated Temperature Spike

```text
Station A → 58°C
Nearby stations → ~28°C
        ↓
ANOMALOUS
Possible sensor fault
```

### Sudden Change

```text
Previous → 28°C
Current  → 45°C
        ↓
Temporal warning
```

### Regional Extreme

```text
Station A → 45°C
Station B → 44.5°C
Station C → 45.2°C
```

If multiple stations agree, spatial evidence can support a regional-event interpretation. Production decisions require real observations and validated meteorological rules.

---

## 🩺 Sensor Health

The prototype can derive a transparent health indicator from anomaly evidence.

Concept:

```text
Normal + Consistent
        ↓
High health

Repeated anomalies
        ↓
Health degradation

Severe / persistent faults
        ↓
Critical status
```

This is a prototype composite indicator, not a certified sensor-health measurement.

---

## 🔐 Transparency

The project distinguishes between:

### Live/runtime data

Data received by the deployed API or simulator.

### Prototype data

Includes:

- Synthetic historical series
- Synthetic training data
- Prototype peer baselines
- Demonstration fault scenarios

These should not be presented as official real-world observations.

---

## ⚠️ Current Limitations

1. Training data is synthetic.
2. Real IMD AWS historical data is not yet integrated.
3. Peer-station information is prototype/hardcoded.
4. Spatial checking currently focuses on temperature for the configured prototype station.
5. Temporal state is stored in memory.
6. Restarting the backend resets previous-station state.
7. There is no production database.
8. Confidence is not calibrated probability.
9. Sensor health is a prototype composite indicator.
10. Self-healing is data estimation, not physical repair.
11. Fault classification is currently rule-based.
12. `sequence_id` is accepted but not yet used as a decision feature.
13. Production requires authentication, persistence, monitoring, logging, rate limiting and secure secret management.

---

## 🚀 Future Scope

### Real AWS Data

Integrate:

- Real AWS telemetry
- Historical observations
- Station metadata
- Coordinates
- Sensor metadata

### Advanced ML

Evaluate:

```text
Isolation Forest
+
Autoencoders
+
Time-series models
+
Statistical methods
```

### Advanced Spatial Intelligence

Add:

- Real nearby stations
- Spatial interpolation
- Regional residuals
- Weather-field consistency
- Geographic clustering

### Sensor Degradation

Detect:

```text
Slow drift
Frozen values
Repeated spikes
Increasing noise
Bias
Intermittent failure
```

### Edge AI

Deploy lightweight QC/anomaly checks on ESP32 or another edge device.

### Production Architecture

```text
AWS Sensors
     ↓
Edge Gateway
     ↓
Message Broker
     ↓
Streaming Pipeline
     ↓
QC + ML Engine
     ↓
Time-Series Database
     ↓
Alerting
     ↓
Monitoring Dashboard
```

---

## 🏆 Design Principle

The key idea is **not simply detecting extreme values**.

The system asks:

```text
Is it physically plausible?
        +
Did it change unexpectedly?
        +
Does it agree with nearby stations?
        +
Is it unusual according to ML?
        ↓
Combined evidence
        ↓
Explanation + recommended action
```

This helps reduce the risk of incorrectly rejecting genuine extreme weather observations.

---

## 🎤 SIH Jury — 30 Second Explanation

> **SkyGuard AI is an intelligent quality-control layer for Automatic Weather Stations. Instead of relying on one ML model or simply rejecting extreme values, we combine physical range checks, temporal consistency, spatial buddy checks and Isolation Forest anomaly detection. The evidence is fused to identify suspicious observations, explain why they were flagged, and recommend actions such as quarantining the reading or using an estimated replacement. The key idea is to distinguish an isolated sensor fault from a genuine regional weather extreme. Our current prototype uses synthetic training and peer data, with the architecture designed for integration with real AWS and IMD data.**

---

## 📚 Important Terminology

| Term | Meaning |
|---|---|
| AWS | Automatic Weather Station |
| QC | Quality Control |
| ML | Machine Learning |
| API | Application Programming Interface |
| FastAPI | Python framework for APIs |
| Streamlit | Python dashboard framework |
| Isolation Forest | Unsupervised anomaly detector |
| Temporal Check | Previous-vs-current reading check |
| Spatial/Buddy Check | Peer-station comparison |
| Telemetry | Data transmitted by a device |
| Anomaly | Unusual observation |
| Quarantine | Prevent suspicious data from normal use |
| Imputation | Estimating a replacement value |
| XAI | Explainable AI |

---

## 🤝 Contribution

Possible contribution areas:

- Real AWS datasets
- Fault-labelled datasets
- ML models
- Time-series analysis
- Spatial algorithms
- Edge AI
- Database integration
- MLOps
- Dashboard
- Testing and evaluation

Workflow:

```text
Clone
 ↓
Create branch
 ↓
Make changes
 ↓
Test
 ↓
Commit
 ↓
Push
 ↓
Pull Request
```

---

## 📦 Project Status

**SIH 2026 Prototype / Demonstration System**

The architecture is intended to evolve from synthetic-data and simulator-based testing toward real AWS telemetry, validated models, persistent storage and production-grade monitoring.

---

## 👩‍💻 Project Information

**Project:** SkyGuard AI  
**SIH Problem Statement:** PS 26073  
**Domain:** Disaster Management  
**Category:** Software  
**Core Technologies:** Python, FastAPI, Streamlit, Scikit-learn, Pandas, NumPy

---

> ### 🌦️ SkyGuard AI
> **Detect the anomaly. Understand the cause. Protect the data.**
