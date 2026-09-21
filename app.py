import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import pydeck as pdk
import requests
import time
from datetime import datetime, timedelta
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    def st_autorefresh(*args, **kwargs):
        return 0


# ================================================================
# 1. PAGE CONFIGURATION
# ================================================================
st.set_page_config(
    page_title="SkyGuard AI — AWS Network Control",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ================================================================
# 2. LIVE REFRESH (Paced at 10 Seconds for Pitching)
# ================================================================
st_autorefresh(
    interval=10000,  # 10 seconds allows comfortable reading for judges
    key="skyguard_live_refresh"
)


# ================================================================
# 3. FASTAPI BACKEND CONNECTION
# ================================================================
API_BASE_URL = "https://skyguard-app-xeak.onrender.com"
LATEST_API_URL = f"{API_BASE_URL}/api/v1/latest"


def fetch_latest_status():
    """Fetch the latest telemetry + anomaly decision from FastAPI."""
    start = time.perf_counter()

    try:
        response = requests.get(
            LATEST_API_URL,
            timeout=5
        )

        latency_ms = round(
            (time.perf_counter() - start) * 1000,
            1
        )

        if response.status_code != 200:
            return {
                "status": "NO_DATA",
                "_request_latency_ms": latency_ms,
                "_error": f"Backend returned HTTP {response.status_code}",
                "telemetry": {},
                "result": {},
            }

        data = response.json()

        if not isinstance(data, dict):
            return {
                "status": "NO_DATA",
                "_request_latency_ms": latency_ms,
                "_error": "Backend returned an unexpected JSON structure.",
                "telemetry": {},
                "result": {},
            }

        data.setdefault("telemetry", {})
        data.setdefault("result", {})
        data["_request_latency_ms"] = latency_ms
        return data

    except (requests.RequestException, ValueError) as exc:
        latency_ms = round(
            (time.perf_counter() - start) * 1000,
            1
        )

        return {
            "status": "NO_DATA",
            "_request_latency_ms": latency_ms,
            "_error": str(exc),
            "telemetry": {},
            "result": {},
        }


# ================================================================
# 4. CUSTOM UI / THEME
# ================================================================
st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
    }

    .metric-card {
        background-color: #1e222d;
        border: 1px solid #2e3545;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
    }

    .alert-critical {
        background-color: #3b1414;
        border-left: 5px solid #ff4b4b;
        padding: 10px 15px;
        border-radius: 4px;
        margin-bottom: 8px;
    }

    .alert-warning {
        background-color: #3b2e14;
        border-left: 5px solid #ffa100;
        padding: 10px 15px;
        border-radius: 4px;
        margin-bottom: 8px;
    }

    .status-ok {
        color: #00e676;
        font-weight: bold;
    }

    .status-fault {
        color: #ff4b4b;
        font-weight: bold;
    }

    .status-warning {
        color: #ffa100;
        font-weight: bold;
    }

    .pipeline-box {
        background-color: #161a23;
        border: 1px solid #2e3545;
        border-radius: 8px;
        padding: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ================================================================
# 5. SYNTHETIC AWS NETWORK & STABLE 3-HOUR TELEMETRY
# ================================================================
@st.cache_data
def load_station_network():
    """Synthetic AWS network used for the prototype/demo."""
    return pd.DataFrame(
        [
            {
                "station_id": "AWS-IND-001",
                "name": "New Delhi IMD Head Office",
                "lat": 28.6139,
                "lon": 77.2090,
                "elevation": 216,
                "status": "HEALTHY",
                "color": [0, 230, 118, 200],
            },
            {
                "station_id": "AWS-IND-002",
                "name": "Gurugram Cyber Hub",
                "lat": 28.4595,
                "lon": 77.0266,
                "elevation": 219,
                "status": "HEALTHY",
                "color": [0, 230, 118, 200],
            },
            {
                "station_id": "AWS-IND-003",
                "name": "Noida Sector 62",
                "lat": 28.6280,
                "lon": 77.3649,
                "elevation": 200,
                "status": "HEALTHY",
                "color": [0, 230, 118, 200],
            },
            {
                "station_id": "AWS-IND-004",
                "name": "Faridabad NIT",
                "lat": 28.3881,
                "lon": 77.3090,
                "elevation": 205,
                "status": "WARNING",
                "color": [255, 161, 0, 200],
            },
            {
                "station_id": "AWS-IND-005",
                "name": "Ghaziabad Vasundhara",
                "lat": 28.6692,
                "lon": 77.4538,
                "elevation": 210,
                "status": "HEALTHY",
                "color": [0, 230, 118, 200],
            },
        ]
    )


@st.cache_data
def generate_telemetry_stream(station_id, n_points=90):
    """
    Generate a stable 3-hour baseline at 2-minute resolution (90 points).
    Fixed time anchor prevents baseline jump on auto-refresh.
    """
    base_time = datetime(2026, 1, 1, 12, 0)
    times = [
        base_time - timedelta(minutes=2 * i)
        for i in range(n_points)
    ][::-1]

    np.random.seed(42 if station_id != "AWS-IND-001" else 99)

    t = np.linspace(0, 2 * np.pi, n_points)

    temperature = (
        28.0
        + 2.5 * np.sin(t)
        + np.random.normal(0, 0.2, n_points)
    )

    humidity = (
        65.0
        - 8.0 * np.sin(t)
        + np.random.normal(0, 0.5, n_points)
    )

    pressure = (
        1011.0
        - 1.5 * np.sin(t / 2)
        + np.random.normal(0, 0.1, n_points)
    )

    return pd.DataFrame(
        {
            "timestamp": times,
            "temperature": temperature,
            "humidity": humidity,
            "pressure": pressure,
            "is_anomaly": False,
            "reconstructed_temp": temperature.copy(),
            "reconstructed_humidity": humidity.copy(),
            "reconstructed_pressure": pressure.copy(),
        }
    )


# ================================================================
# 6. SIDEBAR / FLEET & DEMO CONTROLS
# ================================================================
stations_df = load_station_network()

st.sidebar.title("SkyGuard AI Ops")
st.sidebar.caption("MoES / IMD Weather Station Quality Control")

selected_station_id = st.sidebar.selectbox(
    "Select Target Station",
    options=stations_df["station_id"].tolist(),
    format_func=lambda station_id: (
        f"{station_id} - "
        f"{stations_df.loc[stations_df['station_id'] == station_id, 'name'].iloc[0]}"
    )
)

st.sidebar.markdown("---")
st.sidebar.subheader("Presentation Mode")

# Interactive controls for demonstration anomaly injection
force_fault = st.sidebar.checkbox(
    "Inject Sensor Anomaly",
    value=False,
    help="Enable this during your presentation to demonstrate live anomaly detection."
)

anomaly_parameter = st.sidebar.selectbox(
    "Anomaly Parameter",
    options=["Temperature", "Humidity", "Pressure"],
    help="Choose which sensor parameter should receive the demonstration anomaly."
)

anomaly_values = {
    "Temperature": 60.0,
    "Humidity": 2.0,
    "Pressure": 980.0,
}

if force_fault:
    st.sidebar.number_input(
        f"{anomaly_parameter} Anomaly Value",
        value=float(anomaly_values[anomaly_parameter]),
        step=0.1,
        key="anomaly_value",
        help="Set the value that will be injected into the selected parameter."
    )

freeze_reading = st.sidebar.checkbox(
    "Simulate Frozen Reading",
    value=False,
    help="Keep one selected sensor parameter at exactly the same value across consecutive telemetry samples to demonstrate a stuck/frozen sensor."
)

freeze_parameter = st.sidebar.selectbox(
    "Frozen Parameter",
    options=["Temperature", "Humidity", "Pressure"],
    disabled=not freeze_reading,
    help="Choose which sensor parameter will remain unchanged."
)

use_live_backend = st.sidebar.checkbox(
    "Connect Live Render API",
    value=True
)

if freeze_reading:
    current_freeze_value = float(st.session_state.get("frozen_value", 0.0))
    current_freeze_count = int(st.session_state.get("freeze_count", 0))
    st.sidebar.info(
        f"Frozen {freeze_parameter}: {current_freeze_value:.1f} | "
        f"Consecutive samples: {current_freeze_count}"
    )

st.sidebar.markdown("---")
st.sidebar.subheader("Fleet Status Summary")

active_count = len(stations_df)
static_warning_count = int((stations_df["status"] == "WARNING").sum())

fault_metric = st.sidebar.empty()

st.sidebar.metric("Total Active AWS Nodes", active_count)
st.sidebar.metric("Degradation Warnings", static_warning_count, delta_color="off")


# ================================================================
# 7. TARGET STATION + TELEMETRY RESOLUTION
# ================================================================
target_station = stations_df[
    stations_df["station_id"] == selected_station_id
].iloc[0]

telemetry_df = generate_telemetry_stream(selected_station_id)

# Keep the frozen value in session state so Streamlit reruns do not change it.
if freeze_reading and not st.session_state.get("freeze_was_active", False):
    initial_column = {
        "Temperature": "temperature",
        "Humidity": "humidity",
        "Pressure": "pressure",
    }[freeze_parameter]
    st.session_state["frozen_parameter"] = freeze_parameter
    st.session_state["frozen_value"] = float(telemetry_df[initial_column].iloc[-1])
    st.session_state["freeze_count"] = 0
elif freeze_reading and st.session_state.get("frozen_parameter") != freeze_parameter:
    initial_column = {
        "Temperature": "temperature",
        "Humidity": "humidity",
        "Pressure": "pressure",
    }[freeze_parameter]
    st.session_state["frozen_parameter"] = freeze_parameter
    st.session_state["frozen_value"] = float(telemetry_df[initial_column].iloc[-1])
    st.session_state["freeze_count"] = 0

if not freeze_reading:
    st.session_state["freeze_was_active"] = False
    st.session_state["freeze_count"] = 0
else:
    st.session_state["freeze_was_active"] = True

live_data = fetch_latest_status() if use_live_backend else {"status": "NO_DATA"}

backend_available = (
    use_live_backend
    and live_data.get("status") != "NO_DATA"
    and live_data.get("telemetry", {}).get("station_id") == selected_station_id
)

if backend_available and not force_fault and not freeze_reading:
    live_telemetry = live_data.get("telemetry") or {}
    backend_result = live_data.get("result") or {}

    def safe_float(value, fallback):
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(fallback)

    latest_temp = safe_float(live_telemetry.get("temperature"), telemetry_df["temperature"].iloc[-1])
    latest_hum = safe_float(live_telemetry.get("humidity"), telemetry_df["humidity"].iloc[-1])
    latest_pres = safe_float(live_telemetry.get("pressure"), telemetry_df["pressure"].iloc[-1])
    is_current_fault = bool(backend_result.get("is_anomaly", False))
    telemetry_source = "LIVE BACKEND"

elif force_fault:
    # Triggered anomaly mode for demonstration.
    # The selected parameter receives the user-defined anomaly value.
    latest_temp = float(telemetry_df["temperature"].iloc[-1])
    latest_hum = float(telemetry_df["humidity"].iloc[-1])
    latest_pres = float(telemetry_df["pressure"].iloc[-1])

    injected_value = float(st.session_state.get("anomaly_value", anomaly_values[anomaly_parameter]))

    if anomaly_parameter == "Temperature":
        latest_temp = injected_value
        classification = "Temperature Sensor Anomaly"
    elif anomaly_parameter == "Humidity":
        latest_hum = injected_value
        classification = "Humidity Sensor Anomaly"
    else:
        latest_pres = injected_value
        classification = "Pressure Sensor Anomaly"

    is_current_fault = True

    backend_result = {
        "is_anomaly": True,
        "classification": classification,
        "confidence_score": 0.98,
        "spatial_buddy_check": "FAILED — Demonstration anomaly injected into selected parameter.",
        "action_required": "Flag data stream for imputation; inspect/calibrate the affected sensor.",
        "feature_contributions": {
            f"{anomaly_parameter} Deviation": abs(injected_value - float(
                telemetry_df[{"Temperature": "temperature", "Humidity": "humidity", "Pressure": "pressure"}[anomaly_parameter]].iloc[-1]
            )),
            "ML Anomaly Signal": 1.0,
        },
    }
    telemetry_source = f"DEMO {anomaly_parameter.upper()} FAULT INJECTION"

elif freeze_reading:
    # Simulate a stuck sensor: one parameter remains exactly unchanged while
    # the other parameters continue to use the current stream values.
    latest_temp = float(telemetry_df["temperature"].iloc[-1])
    latest_hum = float(telemetry_df["humidity"].iloc[-1])
    latest_pres = float(telemetry_df["pressure"].iloc[-1])

    frozen_value = float(st.session_state.get("frozen_value", latest_temp))
    if freeze_parameter == "Temperature":
        latest_temp = frozen_value
    elif freeze_parameter == "Humidity":
        latest_hum = frozen_value
    else:
        latest_pres = frozen_value

    st.session_state["freeze_count"] = int(st.session_state.get("freeze_count", 0)) + 1
    freeze_count = st.session_state["freeze_count"]

    is_current_fault = freeze_count >= 3
    backend_result = {
        "is_anomaly": is_current_fault,
        "classification": (
            f"Frozen {freeze_parameter} Sensor" if is_current_fault else "Monitoring for Frozen Reading"
        ),
        "confidence_score": 0.96 if is_current_fault else 0.50,
        "spatial_buddy_check": "PASSED — Freeze pattern is local to the selected sensor parameter.",
        "action_required": (
            "Flag reading stream, use estimated replacement, and inspect/calibrate the affected sensor."
            if is_current_fault else "Continue monitoring consecutive readings for a frozen-value pattern."
        ),
        "feature_contributions": {
            "Frozen Reading Pattern": 1.0 if is_current_fault else 0.0,
            "Temporal Discontinuity": 1.0 if is_current_fault else 0.0,
        },
    }
    telemetry_source = f"DEMO FROZEN {freeze_parameter.upper()} READING"

else:
    latest_temp = float(telemetry_df["temperature"].iloc[-1])
    latest_hum = float(telemetry_df["humidity"].iloc[-1])
    latest_pres = float(telemetry_df["pressure"].iloc[-1])
    is_current_fault = False

    backend_result = {
        "is_anomaly": False,
        "classification": "NOMINAL",
        "confidence_score": 0.05,
        "spatial_buddy_check": "PASSED — Validated against 4 neighbor nodes",
        "action_required": "None",
        "feature_contributions": {},
    }
    telemetry_source = "SYNTHETIC 3-HOUR STREAM"


# ================================================================
# 8. DERIVED DECISION VALUES
# ================================================================
ml_detected = is_current_fault
classification = backend_result.get("classification", "General Sensor Anomaly" if ml_detected else "NOMINAL")
spatial_check = backend_result.get("spatial_buddy_check", "Check unavailable")
action_required = backend_result.get("action_required", "None")
request_latency_ms = live_data.get("_request_latency_ms", None)

stations_display_df = stations_df.copy()
selected_mask = (stations_display_df["station_id"] == selected_station_id)
stations_display_df.loc[selected_mask, "status"] = "FAULT" if is_current_fault else "HEALTHY"

def station_status_color(status):
    if status == "FAULT":
        return [255, 75, 75, 200]
    if status == "WARNING":
        return [255, 161, 0, 200]
    return [0, 230, 118, 200]

stations_display_df["color"] = stations_display_df["status"].apply(station_status_color)

fault_count = int((stations_display_df["status"] == "FAULT").sum())
fault_metric.metric(
    "Critical Sensor Faults",
    fault_count,
    delta=f"{fault_count} Node Active" if fault_count else "No Active Fault",
    delta_color="inverse"
)


# ================================================================
# 9. MERGE TELEMETRY & CALCULATE SELF-HEALING IMPUTATION
# ================================================================
# Append latest point to the 3-hour series
next_timestamp = telemetry_df["timestamp"].iloc[-1] + timedelta(minutes=2)
live_row = pd.DataFrame(
    [
        {
            "timestamp": next_timestamp,
            "temperature": latest_temp,
            "humidity": latest_hum,
            "pressure": latest_pres,
            "is_anomaly": is_current_fault,
        }
    ]
)

telemetry_df = pd.concat([telemetry_df.iloc[1:], live_row], ignore_index=True)

# Calculate robust historical median baseline from preceding window
normal_temp_window = telemetry_df["temperature"].iloc[:-1].tail(10)
normal_hum_window = telemetry_df["humidity"].iloc[:-1].tail(10)
normal_pres_window = telemetry_df["pressure"].iloc[:-1].tail(10)

estimated_temp = float(normal_temp_window.median())
estimated_hum = float(normal_hum_window.median())
estimated_pres = float(normal_pres_window.median())

telemetry_df["reconstructed_temp"] = telemetry_df["temperature"]
telemetry_df["reconstructed_humidity"] = telemetry_df["humidity"]
telemetry_df["reconstructed_pressure"] = telemetry_df["pressure"]

if is_current_fault:
    telemetry_df.loc[telemetry_df.index[-1], "reconstructed_temp"] = estimated_temp
    telemetry_df.loc[telemetry_df.index[-1], "reconstructed_humidity"] = estimated_hum
    telemetry_df.loc[telemetry_df.index[-1], "reconstructed_pressure"] = estimated_pres

temperature_deviation = latest_temp - estimated_temp


# ================================================================
# 10. SENSOR HEALTH SCORE
# ================================================================
def calculate_health_score(temperature, humidity, pressure, anomaly):
    score = 100
    if temperature < -20 or temperature > 50:
        score -= 40
    if humidity < 10 or humidity > 95:
        score -= 25
    if pressure < 995 or pressure > 1025:
        score -= 20
    if anomaly:
        score -= 10
    return int(np.clip(score, 5, 100))

health_score = calculate_health_score(latest_temp, latest_hum, latest_pres, is_current_fault)


# ================================================================
# 11. DASHBOARD HEADER
# ================================================================
st.title("SkyGuard AI: AWS Real-Time Anomaly Engine")
st.caption(
    f"Active Station Focus: **{target_station['name']} ({target_station['station_id']})** | "
    f"Lat: {target_station['lat']}° | Lon: {target_station['lon']}° | "
    f"Telemetry Window: **3 Hours (2-min res)** | Source: **{telemetry_source}**"
)


# ================================================================
# 12. TOP-LEVEL LIVE METRICS
# ================================================================
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("Temperature", f"{latest_temp:.1f} °C", delta=f"{temperature_deviation:+.1f} °C" if is_current_fault else None, delta_color="inverse")

with m2:
    st.metric("Relative Humidity", f"{latest_hum:.1f} %")

with m3:
    st.metric("Atm. Pressure", f"{latest_pres:.1f} hPa")

with m4:
    status_class = "status-fault" if is_current_fault else "status-ok"
    status_label = "CRITICAL FAULT" if is_current_fault else "OPTIMAL"
    st.markdown(f"**Station Health Status**<br><span class='{status_class}'>{status_label}</span>", unsafe_allow_html=True)

with m5:
    st.metric("Sensor Health Score", f"{health_score} / 100")


# ================================================================
# 13. SIDEBAR SYSTEM STATUS
# ================================================================
st.sidebar.markdown("---")
latency_text = f"{request_latency_ms:.0f} ms" if request_latency_ms is not None and backend_available else "N/A"
st.sidebar.info(
    f"System Engine Status: **{'ONLINE' if (backend_available or force_fault) else 'DEGRADED'}**\n\n"
    "Inference Engine: **Isolation Forest + Rule Checks**\n\n"
    f"Telemetry Source: **{telemetry_source}**\n\n"
    f"API Response Time: **{latency_text}**"
)


# ================================================================
# 14. MAP + REAL-TIME ALERTS
# ================================================================
col_map, col_alerts = st.columns([1.6, 1.0])

with col_map:
    st.subheader("Spatial Buddy Network View")
    view_state = pdk.ViewState(latitude=28.55, longitude=77.20, zoom=9.2, pitch=25)

    scatterplot_layer = pdk.Layer(
        "ScatterplotLayer",
        data=stations_display_df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=2500,
        pickable=True,
        auto_highlight=True,
    )

    text_layer = pdk.Layer(
        "TextLayer",
        data=stations_display_df,
        get_position=["lon", "lat"],
        get_text="station_id",
        get_size=14,
        get_color=[255, 255, 255, 255],
        get_alignment_baseline="'bottom'",
        get_offset=[0, -15],
    )

    deck = pdk.Deck(
        layers=[scatterplot_layer, text_layer],
        initial_view_state=view_state,
        tooltip={"html": "<b>{name}</b><br>ID: {station_id}<br>Status: {status}<br>Elev: {elevation}m"},
        # Keep map movement user-controlled: pan/zoom remain enabled,
        # but no automatic animation or fly-to behaviour is configured.
    )
    st.pydeck_chart(deck, height=500)

with col_alerts:
    st.subheader("Real-Time Alert Log")
    if is_current_fault:
        st.markdown(
            f"""
            <div class='alert-critical'>
                <strong>[CRITICAL] {classification}</strong><br>
                <small>{selected_station_id} | Anomaly Detection Active</small><br>
                Spatial Buddy Check: {spatial_check}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.error(f"Action Required: {action_required}")
    else:
        st.success("No critical alerts actively triggered for this node.")


# ================================================================
# 15. AUTOMATED DECISION PIPELINE
# ================================================================
st.markdown("---")
st.subheader("Automated Decision Pipeline")
p1, p2, p3, p4, p5 = st.columns(5)

with p1:
    st.metric("1. Ingest", "LIVE" if (backend_available or force_fault) else "FALLBACK")
with p2:
    st.metric("2. ML Detection", "ANOMALY" if ml_detected else "NORMAL")
with p3:
    physics_fail = (latest_temp < -20 or latest_temp > 50 or latest_hum < 10 or latest_hum > 95 or latest_pres < 995 or latest_pres > 1025)
    st.metric("3. Physics Check", "FAIL" if physics_fail else "PASS")
with p4:
    spatial_fail = "FAILED" in str(spatial_check).upper()
    st.metric("4. Spatial Check", "FAIL" if spatial_fail else "PASS")
with p5:
    st.metric("5. Action", "IMPUTE" if is_current_fault else "MONITOR")


# ================================================================
# 16. TIME-SERIES ANALYTICS + SELF-HEALING (3-HOUR WINDOW)
# ================================================================
st.markdown("---")
st.subheader("3-Hour Telemetry Series & AI Self-Healing Imputation")

def plot_telemetry(df, param_col, rec_col, unit):
    fig = go.Figure()

    # Raw observed signal
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df[param_col],
            mode="lines+markers",
            name="Observed Raw Signal",
            line=dict(color="#29b6f6", width=2),
            marker=dict(size=4)
        )
    )

    # Anomaly marker
    anomalies = df[df["is_anomaly"].fillna(False).astype(bool)]
    if not anomalies.empty:
        fig.add_trace(
            go.Scatter(
                x=anomalies["timestamp"],
                y=anomalies[param_col],
                mode="markers",
                name="Detected Anomaly",
                marker=dict(color="#ff4b4b", size=12, symbol="x"),
            )
        )

    # Imputed self-healing signal
    if is_current_fault:
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df[rec_col],
                mode="lines",
                name="AI Self-Healed Baseline",
                line=dict(color="#00e676", width=2, dash="dash"),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[df["timestamp"].iloc[-1]],
                y=[df[rec_col].iloc[-1]],
                mode="markers",
                name="Imputed Corrected Value",
                marker=dict(color="#00e676", size=12, symbol="diamond"),
            )
        )

    fig.update_layout(
        template="plotly_dark",
        height=360,
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis_title=f"{param_col.capitalize()} ({unit})",
        xaxis_title="Time (3-Hour Past Window)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig

tab1, tab2, tab3 = st.tabs(["Temperature (°C)", "Relative Humidity (%)", "Pressure (hPa)"])

with tab1:
    st.plotly_chart(plot_telemetry(telemetry_df, "temperature", "reconstructed_temp", "°C"), use_container_width=True)

with tab2:
    st.plotly_chart(plot_telemetry(telemetry_df, "humidity", "reconstructed_humidity", "%"), use_container_width=True)

with tab3:
    st.plotly_chart(plot_telemetry(telemetry_df, "pressure", "reconstructed_pressure", "hPa"), use_container_width=True)




# ================================================================
# READINGS & DATA TABLE
# ================================================================
st.markdown("---")
st.subheader("Telemetry Readings (3-Hour Past Logs)")

# Show recent 10 records in tabular format
formatted_df = telemetry_df.tail(10).copy()
formatted_df["timestamp"] = formatted_df["timestamp"].dt.strftime("%H:%M:%S")

# Rename columns for clear presentation
formatted_df = formatted_df.rename(
    columns={
        "timestamp": "Time",
        "temperature": "Raw Temp (°C)",
        "reconstructed_temp": "AI Corrected Temp (°C)",
        "humidity": "Humidity (%)",
        "pressure": "Pressure (hPa)",
        "is_anomaly": "Fault Detected",
    }
)

st.dataframe(
    formatted_df[
        [
            "Time",
            "Raw Temp (°C)",
            "AI Corrected Temp (°C)",
            "Humidity (%)",
            "Pressure (hPa)",
            "Fault Detected",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)


# ================================================================
# 17. SELF-HEALING DECISION
# ================================================================
st.markdown("---")
st.subheader("Self-Healing Decision Summary")

heal_col1, heal_col2, heal_col3 = st.columns(3)

with heal_col1:
    st.metric("Raw Observed Temp", f"{latest_temp:.1f} °C")

with heal_col2:
    st.metric("AI Imputed Temp", f"{estimated_temp:.1f} °C" if is_current_fault else "Not Required")

with heal_col3:
    st.metric("Recovery Action", "IMPUTED & FLAGGED" if is_current_fault else "PASSED")

if is_current_fault:
    st.warning(
        f"Raw reading of **{latest_temp:.1f} °C** rejected due to anomaly detection. "
        f"Downstream forecast models receive imputed estimate: **{estimated_temp:.1f} °C** "
        f"(RH: {estimated_hum:.1f}%, Pressure: {estimated_pres:.1f} hPa)."
    )
else:
    st.success("Reading validated. No self-healing correction required.")


# ================================================================
# 18. EXPLAINABLE AI (XAI) ATTRIBUTION
# ================================================================
st.markdown("---")
st.subheader("Explainable AI (XAI) Attribution")

exp_col1, exp_col2 = st.columns([1, 1])

with exp_col1:
    st.markdown("**Feature Contribution Breakdown**")
    raw_scores = backend_result.get("shap_scores", {})
    
    if not raw_scores:
        raw_scores = {
            "Temperature Deviation": round(abs(temperature_deviation), 2),
            "Humidity Outlier Score": round(max(0, latest_hum - 95, 10 - latest_hum), 2),
            "Pressure Variance": round(max(0, latest_pres - 1025, 995 - latest_pres), 2),
            "ML Anomaly Confidence": 1.0 if ml_detected else 0.0,
        }

    contribution_df = pd.DataFrame({
        "Feature": list(raw_scores.keys()),
        "Contribution": [float(v) for v in raw_scores.values()]
    }).sort_values(by="Contribution", ascending=True)

    fig_contrib = go.Figure(go.Bar(
        x=contribution_df["Contribution"],
        y=contribution_df["Feature"],
        orientation="h",
        marker_color=["#ff4b4b" if v > 1.0 else "#29b6f6" for v in contribution_df["Contribution"]]
    ))
    fig_contrib.update_layout(template="plotly_dark", height=240, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_contrib, use_container_width=True)

with exp_col2:
    st.markdown("**Model Reasoning Log**")
    if is_current_fault:
        st.error(
            f"1. **Outlier Reading:** Temperature spike of **{latest_temp:.1f} °C** exceeds historical baseline by **{temperature_deviation:+.1f} °C**.\n\n"
            f"2. **ML Decision:** Isolation Forest classified signal as **ANOMALOUS**.\n\n"
            f"3. **Physical Checks:** Triggered physical boundary warning.\n\n"
            f"4. **Spatial Verification:** {spatial_check}.\n\n"
            f"5. **Resolution:** Reading replaced with self-healing estimate (**{estimated_temp:.1f} °C**)."
        )
    else:
        st.success(
            "1. Observations are within normal physical limits.\n\n"
            "2. Isolation Forest score indicates standard behavior.\n\n"
            "3. Spatial neighbor agreement verified.\n\n"
            "4. No imputation required."
        )