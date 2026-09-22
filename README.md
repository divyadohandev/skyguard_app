# SkyGuard AI

> **SIH 2026 | Problem Statement 26073 | Disaster Management | Software**

SkyGuard AI is a prototype quality-control and anomaly-detection system for Automatic Weather Station (AWS) telemetry. It combines an unsupervised machine-learning model with deterministic meteorological checks and a monitoring dashboard so that an unusual observation can be flagged, explained, and replaced with an estimated value for downstream use.

The central design principle is simple:

> An extreme reading is not automatically a faulty reading.

A single station reporting 58 °C while nearby stations remain near 28 °C may have a sensor problem. Several nearby stations reporting the same extreme may instead indicate a genuine regional event. SkyGuard AI is designed to provide evidence for that distinction. The current repository is a demonstration prototype using synthetic training data and configured demo stations; it is not an operational IMD system.

## Contents

- [What the prototype does](#what-the-prototype-does)
- [Architecture](#architecture)
- [Repository structure](#repository-structure)
- [Technology stack](#technology-stack)
- [ML and quality-control logic](#ml-and-quality-control-logic)
- [API reference](#api-reference)
- [Streamlit dashboard](#streamlit-dashboard)
- [Telemetry simulator](#telemetry-simulator)
- [Landing page](#landing-page)
- [Local setup](#local-setup)
- [Demo scenarios](#demo-scenarios)
- [Tests](#tests)
- [Transparency and limitations](#transparency-and-limitations)
- [Future scope](#future-scope)
- [Project information](#project-information)

## What the prototype does

SkyGuard AI processes three atmospheric measurements:

| Field | Unit | Meaning |
|---|---:|---|
| `station_id` | identifier | Source AWS node |
| `temperature` | °C | Ambient temperature |
| `humidity` | % | Relative humidity |
| `pressure` | hPa | Atmospheric pressure |

For each submitted reading, the backend:

1. Calculates dew point from temperature and relative humidity.
2. Scores the three-value observation with an Isolation Forest trained on the bundled normal-weather dataset.
3. Checks whether dew point is greater than ambient temperature.
4. Checks whether temperature is outside the backend bounds of -10 °C to 50 °C.
5. Combines the ML result and these rule checks into `is_anomaly`.
6. Assigns a rule-based classification and recommended action.
7. Stores the latest telemetry and result in process memory for the dashboard and landing page.

The Streamlit dashboard adds presentation and demonstration behavior around this API: a five-station synthetic network, a stable three-hour telemetry series, anomaly injection, frozen-reading simulation, visual alerts, and rolling-median replacement values.

## Architecture

```text
AWS device, simulator, or HTTP client
                 |
                 v
       FastAPI POST /api/v1/detect
                 |
       Pydantic request validation
                 |
       +---------+----------+
       |                    |
       v                    v
  Isolation Forest     Dew-point and
  anomaly score        temperature rules
       |                    |
       +---------+----------+
                 v
       Hybrid anomaly decision
                 |
       Classification and action
                 |
       In-memory latest reading
          /                 \
         v                   v
  Streamlit dashboard   Landing-page API checks
```

The intended production direction is a persistent streaming architecture:

```text
AWS sensors -> edge gateway -> message broker -> QC/ML service
            -> time-series database -> alerts -> operations dashboard
```

That production architecture is not implemented in this repository yet.

## Repository structure

```text
skyguard_app/
├── app.py
│   └── Streamlit operations dashboard and demo controls
├── backend.py
│   └── FastAPI application, request model, inference, and latest-state API
├── sensor_stream.py
│   └── Continuous HTTP telemetry simulator
├── landing/
│   └── index.html
│       └── Static product/operations landing page with live API checks
├── ml_engine/
│   ├── anomaly_model.py
│   │   └── Reusable Isolation Forest wrapper
│   ├── physics.py
│   │   └── Dew-point calculation and physics violation helper
│   ├── training_data.py
│   │   └── Generates synthetic normal-weather CSV data
│   ├── weather_normal_data.csv
│   │   └── Bundled 5,000-row synthetic training dataset
│   ├── test_model.py
│   │   └── In-memory model smoke test
│   └── test_real_model.py
│       └── CSV-trained model smoke test
├── requirements.txt
│   └── Runtime Python dependencies
├── render.yaml
│   └── Render definitions for backend and dashboard services
└── .gitignore
    └── Python caches, environments, and local Streamlit secrets
```

## Technology stack

| Layer | Technology | Use in this repository |
|---|---|---|
| Language | Python | Backend, dashboard, simulator, and ML code |
| API | FastAPI + Uvicorn | REST inference service |
| Validation | Pydantic | `SensorInput` request schema |
| ML | scikit-learn | Isolation Forest anomaly detection |
| Data | Pandas + NumPy | Training data, telemetry, and calculations |
| Dashboard | Streamlit | Live monitoring and demonstration UI |
| Charts | Plotly | Three-hour telemetry and contribution charts |
| Map | PyDeck | Synthetic station network view |
| HTTP client | Requests | Dashboard and simulator API calls |
| Refresh | streamlit-autorefresh | Ten-second dashboard reruns |
| Static frontend | HTML, CSS, JavaScript | Landing page and API status view |
| Hosting configuration | Render | Backend and dashboard service definitions |

## ML and quality-control logic

### Isolation Forest

`ml_engine/anomaly_model.py` wraps scikit-learn's `IsolationForest` with:

```python
IsolationForest(
    n_estimators=100,
    contamination=0.05,
    random_state=42,
)
```

The model uses these features, in this order:

```text
temperature, humidity, pressure
```

The bundled `weather_normal_data.csv` contains 5,000 synthetic observations generated around approximate normal conditions. Its values are clipped to these generation ranges:

| Feature | Synthetic generation range |
|---|---:|
| Temperature | 15 °C to 40 °C |
| Humidity | 20% to 95% |
| Pressure | 995 hPa to 1025 hPa |

The model returns `is_anomaly` and scikit-learn's raw `decision_function` value as `anomaly_score`. The score is not a probability, and the model has not been evaluated against a production-labelled fault dataset.

### Backend rule checks

The implemented backend decision is:

```text
is_anomaly = ML anomaly OR dew-point violation OR temperature outside [-10, 50]
```

The backend does not currently implement a temporal comparison against a previous reading or a real peer-station calculation. It returns spatial-consensus wording for the prototype UI, but the current API response does not calculate that comparison from a station network.

### Dashboard checks and recovery display

The dashboard has additional display-side behavior:

- A health score starts at 100 and subtracts points for prototype parameter bounds and an anomaly flag.
- An anomaly reading is marked for replacement by the median of the preceding ten synthetic readings.
- A three-hour window contains 90 two-minute points plus the latest resolved point.
- The sidebar can inject a custom temperature, humidity, or pressure fault.
- The sidebar can hold one parameter constant; after three reruns it displays a frozen-sensor anomaly.
- Feature bars use backend `shap_scores` when present, but no SHAP library or SHAP explainer is implemented. These values are prototype attribution indicators.

The replacement value is data-level imputation for demonstration. It does not repair a physical sensor.

## API reference

### Base URLs

Local development:

```text
http://127.0.0.1:8000
```

Configured deployed backend:

```text
https://skyguard-app-xeak.onrender.com
```

Interactive OpenAPI documentation:

```text
https://skyguard-app-xeak.onrender.com/docs
```

Raw OpenAPI document:

```text
https://skyguard-app-xeak.onrender.com/openapi.json
```

### `POST /api/v1/detect`

Submit one telemetry reading. All four fields are required and must be numeric where applicable.

Request:

```json
{
  "station_id": "AWS-IND-001",
  "temperature": 28.4,
  "humidity": 68.2,
  "pressure": 1012.7
}
```

Typical nominal response:

```json
{
  "station_id": "AWS-IND-001",
  "is_anomaly": false,
  "ml_detected": false,
  "ml_anomaly_score": 0.12,
  "classification": "NOMINAL",
  "confidence_score": 0.995,
  "spatial_buddy_check": "PASSED (Spatial Consensus Match)",
  "action_required": "None",
  "shap_scores": {
    "Temperature Rate-of-Change": 0.02,
    "Dew-Point Violation Score": -0.01,
    "Spatial Residual Error": -0.04,
    "Pressure Shift": -0.03
  }
}
```

The exact ML score varies with the fitted model. `confidence_score` is a fixed prototype value (`0.995` for nominal and `0.942` for anomaly), not a calibrated confidence probability.

An anomalous result can be classified as:

- `Thermal Spike / ADC Surge Fault` when temperature is above 50 °C.
- `Humidity Sensor Fault` when humidity is outside 10% to 95%.
- `Pressure Sensor Drift` when pressure is outside 995 to 1025 hPa.
- `General Sensor Anomaly` for other anomalous readings.

Note that the humidity and pressure classifications are rule-based labels; those bounds do not currently participate in the backend's `is_anomaly` expression unless the ML or dew-point check also flags the reading.

PowerShell example:

```powershell
$body = @{
  station_id = "AWS-IND-001"
  temperature = 58.4
  humidity = 63.5
  pressure = 1011.0
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/detect" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

### `GET /api/v1/latest`

Returns the most recently processed telemetry and result from the current backend process:

```json
{
  "telemetry": {
    "station_id": "AWS-IND-001",
    "temperature": 28.4,
    "humidity": 68.2,
    "pressure": 1012.7
  },
  "result": {
    "station_id": "AWS-IND-001",
    "is_anomaly": false
  }
}
```

Before the first successful detection request, the endpoint returns:

```json
{
  "status": "NO_DATA",
  "message": "Waiting for sensor telemetry..."
}
```

### CORS and state

The API currently allows all origins, methods, headers, and credentials for prototype connectivity. Latest state is held in module-level dictionaries, so it is lost on restart and is not suitable for multi-worker or production use without persistence and a shared state layer.

## Streamlit dashboard

Run `app.py` to open the operations dashboard. It includes:

- Station selector for five configured NCR demo nodes.
- Temperature, humidity, pressure, station status, and health score metrics.
- PyDeck spatial station map.
- Five-stage visual decision pipeline: ingest, ML detection, physics, spatial display, and action.
- Three-hour Plotly history with raw, anomaly, and imputed values.
- Recent telemetry table.
- XAI-style contribution chart and reasoning log.
- Automatic refresh every 10 seconds.

By default the dashboard attempts to read the deployed Render API. Turn off **Connect Live Render API** to use the local synthetic stream without a reachable backend. The dashboard also falls back to synthetic data when the selected station does not match the latest API station.

The **Presentation Mode** controls are intentionally useful for demonstrations:

- **Inject Sensor Anomaly** replaces one selected parameter with a custom value and displays an alert.
- **Simulate Frozen Reading** holds one parameter constant and raises the demo fault after three refresh cycles.

## Telemetry simulator

`sensor_stream.py` continuously sends readings for `AWS-IND-001` to the deployed endpoint every three seconds. It generates:

- Temperature between 24 °C and 32 °C for normal samples.
- Humidity between 50% and 70%.
- Pressure between 1008 hPa and 1014 hPa.
- A 20% chance of replacing temperature with 58.4 °C.

The script currently targets the deployed URL directly. For local testing, change `API_URL` in `sensor_stream.py` to `http://127.0.0.1:8000/api/v1/detect` before running it. Stop the process with `Ctrl+C`.

## Landing page

`landing/index.html` is a self-contained static page. It:

- Presents the SkyGuard AI architecture and feature set.
- Polls the backend latest endpoint every 10 seconds.
- Sends a nominal sample to the detection endpoint every 30 seconds to show API status.
- Opens the deployed dashboard inside a modal iframe or in a new tab.
- Links to Swagger documentation and live latest telemetry.

The landing page is configured for these deployed services:

```text
Backend:   https://skyguard-app-xeak.onrender.com
Dashboard: https://skyguard-dashboard-t737.onrender.com
```

Because it is a static file, it can be opened directly in a browser or served by any static web server. Browser CORS behavior still depends on the backend's CORS configuration and the availability of the deployed services.

## Local setup

### Prerequisites

- Python 3.10 or newer is recommended.
- PowerShell commands below assume Windows.
- `pip` must be available for the selected Python interpreter.
- A network connection is needed only when installing dependencies or using deployed services.

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

The repository's `.gitignore` excludes both `.venv/` and `venv/`.

### 2. Install runtime dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`pytest` is not listed in `requirements.txt`; install it separately if you want to run the smoke-test files through pytest:

```powershell
python -m pip install pytest
```

### 3. Start the backend

From the repository root:

```powershell
python -m uvicorn backend:app --reload --host 127.0.0.1 --port 8000
```

The model is trained from `ml_engine/weather_normal_data.csv` when `backend.py` is imported. Open these local URLs:

```text
API:     http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs
OpenAPI: http://127.0.0.1:8000/openapi.json
Latest:  http://127.0.0.1:8000/api/v1/latest
```

### 4. Start the dashboard

Open a second PowerShell window, activate the same environment, and run:

```powershell
python -m streamlit run app.py
```

Streamlit normally opens:

```text
http://localhost:8501
```

Enable **Connect Live Render API** only when you want to use the deployed backend. For a fully local flow, leave it disabled or update `API_BASE_URL` in `app.py` to the local API URL.

### 5. Send simulator traffic

With the backend running, update `API_URL` in `sensor_stream.py` to the local endpoint if necessary, then run:

```powershell
python sensor_stream.py
```

The simulator is an infinite loop and prints each HTTP result. Start the dashboard after the simulator has posted at least one reading if you want the live backend path to be populated immediately.

## Regenerating the synthetic dataset

To regenerate the bundled dataset:

```powershell
python ml_engine/training_data.py
```

Run this from the `ml_engine` directory if you want the output path to be exactly `ml_engine/weather_normal_data.csv`:

```powershell
Push-Location ml_engine
python training_data.py
Pop-Location
```

The script uses a fixed NumPy seed of 42 and creates 5,000 rows with the columns `temperature`, `humidity`, and `pressure`.

## Demo scenarios

### Nominal observation

```text
Temperature, humidity, and pressure within the learned normal distribution
                         |
                         v
                       NOMINAL
```

### Isolated temperature spike

```text
Station A -> 58.4 °C
Nearby demo nodes -> approximately normal
                         |
                         v
             Thermal Spike / ADC Surge Fault
```

Use either the simulator's 20% temperature-fault injection or the dashboard's manual anomaly control.

### Humidity or pressure fault classification

The dashboard can inject humidity or pressure values outside the configured prototype ranges. The API's classification logic labels those values as humidity or pressure faults when the overall decision is anomalous.

### Frozen reading

Enable **Simulate Frozen Reading** in the dashboard. The selected parameter remains constant across refreshes; after three cycles the dashboard marks it as a frozen sensor and shows an estimated replacement path.

### Regional extreme concept

The project is designed around the distinction between an isolated outlier and a regional event. The current repository does not ingest real peer observations or calculate a live regional consensus, so this remains a design objective and presentation concept rather than a production spatial model.

## Tests

The two files under `ml_engine/` are executable smoke tests rather than pytest test-function suites:

```powershell
Push-Location ml_engine
python test_model.py
python test_real_model.py
Pop-Location
```

`test_model.py` trains on generated in-memory data. `test_real_model.py` trains from `weather_normal_data.csv`. Both print a nominal prediction and a 58.4 °C anomaly prediction.

If using pytest, run from `ml_engine` because the test files import `anomaly_model` as a local module:

```powershell
Push-Location ml_engine
python -m pytest test_model.py test_real_model.py -q
Pop-Location
```

The current project does not include automated API, dashboard, browser, persistence, load, or model-quality evaluation tests.

## Transparency and limitations

This section is important when presenting or extending the project.

### Implemented in the current code

- Isolation Forest anomaly scoring on temperature, humidity, and pressure.
- Dew-point calculation and dew-point violation check.
- Backend temperature bounds check.
- Rule-based classification, action text, and fixed prototype confidence values.
- In-memory latest-reading endpoint.
- Streamlit dashboard with synthetic station network and demo controls.
- Dashboard rolling-median imputation display for the latest anomalous point.
- Static landing page with live endpoint polling.

### Prototype or simulated behavior

- The training CSV is synthetic, not official IMD or field-collected AWS data.
- The five dashboard stations and their coordinates are configured demo records.
- Peer-station/spatial results are text and display behavior; no real peer dataset is loaded by the backend.
- Temporal checks are not implemented in the backend. The dashboard's frozen-reading mode is a presentation simulation.
- The `shap_scores` response field contains hand-authored indicators; SHAP is not a dependency and no SHAP explainer runs.
- `confidence_score` is not calibrated probability.
- Health score is a transparent dashboard heuristic, not a certified sensor-health metric.
- Imputation estimates a replacement data value and does not repair hardware.
- Latest state is process-local and disappears on restart.

### Production gaps

Before operational use, the project would need real station metadata and telemetry, authenticated ingestion, schema/range validation, persistent storage, multi-worker-safe state, structured logging, monitoring, rate limiting, secret management, alert routing, model/version tracking, fault-labelled evaluation data, calibrated uncertainty, and validated meteorological rules.

## Future scope

1. Integrate real AWS observations, station metadata, coordinates, and sensor metadata.
2. Build a true temporal feature store for rate-of-change, stuck-value, drift, noise, and intermittent-failure detection.
3. Replace prototype peer text with real spatial residuals, interpolation, and regional consensus.
4. Compare Isolation Forest with statistical baselines, autoencoders, and time-series models.
5. Add edge-side checks for ESP32 or gateway deployments.
6. Introduce a message broker and time-series database for durable streaming data.
7. Add authentication, role-aware operations views, audit logs, and alert integrations.
8. Evaluate the system using labelled normal and fault cases, with precision, recall, false-alarm rate, detection latency, and calibration measurements.

## Contribution workflow

Potential contribution areas include real AWS datasets, fault labelling, meteorological validation, ML evaluation, temporal analysis, spatial algorithms, edge deployment, persistence, MLOps, dashboard usability, and automated testing.

```text
Clone -> create branch -> make focused change -> run checks
      -> commit -> push -> open a pull request
```

Please keep synthetic/demo behavior clearly labeled when adding new features.

## Project information

| Item | Value |
|---|---|
| Project | SkyGuard AI |
| SIH problem statement | PS 26073 |
| Domain | Disaster Management |
| Category | Software |
| Status | SIH 2026 prototype / demonstration system |
| Core technologies | Python, FastAPI, Streamlit, scikit-learn, Pandas, NumPy |

## 30-second explanation

> SkyGuard AI is an intelligent quality-control layer for Automatic Weather Stations. It combines an Isolation Forest with dew-point and boundary checks to identify suspicious observations, explain the prototype decision, and show an estimated replacement value when a reading is flagged. The key idea is to avoid rejecting every extreme value: an isolated outlier may be a sensor fault, while agreement across real nearby stations could indicate a genuine regional extreme. The current implementation uses synthetic training and demo station data, and is designed to evolve toward validated AWS telemetry, persistent storage, real spatial checks, and production monitoring.

## Terminology

| Term | Meaning |
|---|---|
| AWS | Automatic Weather Station |
| QC | Quality control |
| ML | Machine learning |
| API | Application Programming Interface |
| Isolation Forest | Unsupervised tree-based anomaly detector |
| Telemetry | Measurements transmitted by a device |
| Anomaly | Observation that is unusual under the configured model/rules |
| Imputation | Estimating a replacement value for a missing or rejected value |
| XAI | Explainable artificial intelligence; here, prototype contribution indicators |

> **SkyGuard AI: Detect the anomaly. Understand the cause. Protect the data.**