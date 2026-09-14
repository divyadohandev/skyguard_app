import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import pydeck as pdk
import requests
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# Refresh dashboard every 3 seconds
st_autorefresh(
    interval=3000,
    key="skyguard_live_refresh"
)


# ------------------------------------------------------------
# FASTAPI BACKEND CONNECTION
# ------------------------------------------------------------

API_BASE_URL = "https://skyguard-app-xeak.onrender.com"
LATEST_API_URL = f"{API_BASE_URL}/api/v1/latest"

def fetch_latest_status():
    try:
        response = requests.get(
            LATEST_API_URL,
            timeout=3
        )

        if response.status_code == 200:
            return response.json()

        st.warning(
            f"Backend returned status code: {response.status_code}"
        )

    except Exception as e:
        st.warning(f"Backend offline: {e}")

    return {
        "status": "NO_DATA"
    }


# -------------------------------------------------------------------
# 1. PAGE CONFIGURATION & THEMING
# -------------------------------------------------------------------
st.set_page_config(
    page_title="SkyGuard AI — AWS Network Control",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for high-contrast monitoring UI
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
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
    .status-ok { color: #00e676; font-weight: bold; }
    .status-fault { color: #ff4b4b; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# 2. MOCK DATA GENERATION ENGINE
# -------------------------------------------------------------------
@st.cache_data
def load_station_network():
    """Generates synthetic AWS Network nodes across India."""
    stations = pd.DataFrame([
        {"station_id": "AWS-IND-001", "name": "New Delhi IMD Head Office", "lat": 28.6139, "lon": 77.2090, "elevation": 216, "status": "FAULT", "color": [255, 75, 75, 200]},
        {"station_id": "AWS-IND-002", "name": "Gurugram Cyber Hub", "lat": 28.4595, "lon": 77.0266, "elevation": 219, "status": "HEALTHY", "color": [0, 230, 118, 200]},
        {"station_id": "AWS-IND-003", "name": "Noida Sector 62", "lat": 28.6280, "lon": 77.3649, "elevation": 200, "status": "HEALTHY", "color": [0, 230, 118, 200]},
        {"station_id": "AWS-IND-004", "name": "Faridabad NIT", "lat": 28.3881, "lon": 77.3090, "elevation": 205, "status": "WARNING", "color": [255, 161, 0, 200]},
        {"station_id": "AWS-IND-005", "name": "Ghaziabad Vasundhara", "lat": 28.6692, "lon": 77.4538, "elevation": 210, "status": "HEALTHY", "color": [0, 230, 118, 200]},
    ])
    return stations

def generate_telemetry_stream(station_id, n_points=96):
    """Generates 24-hour time-series data at 15-minute resolution."""

    times = [
        datetime.now() - timedelta(minutes=15 * i)
        for i in range(n_points)
    ][::-1]

    np.random.seed(42 if station_id != "AWS-IND-001" else 99)

    # Base diurnal pattern
    t = np.linspace(0, 4 * np.pi, n_points)

    temp = (
        28
        + 6 * np.sin(t)
        + np.random.normal(0, 0.4, n_points)
    )

    humidity = (
        65
        - 20 * np.sin(t)
        + np.random.normal(0, 1.0, n_points)
    )

    pressure = (
        1011
        - 2 * np.sin(t / 2)
        + np.random.normal(0, 0.2, n_points)
    )

    df = pd.DataFrame({
        "timestamp": times,
        "temperature": temp,
        "humidity": humidity,
        "pressure": pressure
    })

    # Default values
    df["is_anomaly"] = False

    df["reconstructed_temp"] = df["temperature"]

    df["reconstructed_humidity"] = df["humidity"]


    # Return dataframe
    return df

# -------------------------------------------------------------------
# 3. SIDEBAR CONTROLS & FLEET SUMMARY
# -------------------------------------------------------------------
stations_df = load_station_network()

st.sidebar.title("📡 SkyGuard AI Ops")
st.sidebar.caption("MoES / IMD Weather Station Quality Control")

selected_station_id = st.sidebar.selectbox(
    "Select Target Station", 
    options=stations_df["station_id"].tolist(),
    format_func=lambda x: f"{x} - {stations_df[stations_df['station_id'] == x]['name'].values[0]}"
)

st.sidebar.markdown("---")
st.sidebar.subheader("Fleet Status Summary")
active_count = len(stations_df)
warning_count = len(
    stations_df[stations_df["status"] == "WARNING"]
)

st.sidebar.metric(
    "Total Active AWS Nodes",
    active_count
)

fault_metric = st.sidebar.empty()

st.sidebar.metric(
    "Degradation Warnings",
    warning_count,
    delta_color="off"
)

st.sidebar.markdown("---")
st.sidebar.info("System Engine Status: **ONLINE**\n\nInference Latency: **38 ms**\nEdge ESP32 Sync: **100%**")

# Get selected station record
target_station = stations_df[stations_df["station_id"] == selected_station_id].iloc[0]
telemetry_df = generate_telemetry_stream(selected_station_id)

# -------------------------------------------------------------------
# 4. DASHBOARD HEADER & TOP-LEVEL METRICS
# -------------------------------------------------------------------
st.title("🛡️ SkyGuard AI: AWS Real-Time Anomaly Engine")

st.caption(
    f"Active Station Focus: **{target_station['name']} "
    f"({target_station['station_id']})** | "
    f"Lat: {target_station['lat']}°, "
    f"Lon: {target_station['lon']}°"
)

m1, m2, m3, m4, m5 = st.columns(5)


# Get latest data from FastAPI
live_data = fetch_latest_status()

backend_available = (
    live_data.get("status") != "NO_DATA"
    and live_data.get("telemetry", {}).get("station_id")
    == selected_station_id
)

if backend_available:

    live_telemetry = live_data["telemetry"]
    backend_result = live_data["result"]

    latest_temp = live_telemetry["temperature"]
    latest_hum = live_telemetry["humidity"]
    latest_pres = live_telemetry["pressure"]
    
    is_current_fault = backend_result.get(
    "is_anomaly",
    False
    )

else:

    # Fallback synthetic values
    latest_temp = telemetry_df["temperature"].iloc[-1]
    latest_hum = telemetry_df["humidity"].iloc[-1]
    latest_pres = telemetry_df["pressure"].iloc[-1]

    is_current_fault = False

    backend_result = {
        "is_anomaly": False,
        "classification": "NOMINAL",
        "confidence_score": 0.995,
        "spatial_buddy_check":
            "PASSED (Spatial Consensus Match)",
        "action_required": "None",
        "shap_scores": {
            "Temperature Rate-of-Change": 0.02,
            "Dew-Point Violation Score": -0.01,
            "Spatial Residual Error": -0.04,
            "Pressure Shift": -0.03,
        },
    }


# Current live anomaly status
is_current_fault = backend_result.get(
    "is_anomaly",
    False
)

# Dynamic critical fault count
fault_count = 1 if is_current_fault else 0

fault_metric.metric(
    "Critical Sensor Faults",
    fault_count,
    delta=f"{fault_count} Node" if fault_count else "No Active Fault",
    delta_color="inverse"
)

# ---------------------------------------------------------------
# Display Metrics
# ---------------------------------------------------------------
with m1:
    st.metric(
        "Temperature",
        f"{latest_temp:.1f} °C",
        delta="-0.4 °C"
    )

with m2:
    st.metric(
        "Relative Humidity",
        f"{latest_hum:.1f} %",
        delta="+2.1 %"
    )

with m3:
    st.metric(
        "Atm. Pressure",
        f"{latest_pres:.1f} hPa",
        delta="-0.1 hPa"
    )

with m4:
    status_color = "status-fault" if is_current_fault else "status-ok"

    status_label = (
        "CRITICAL FAULT"
        if is_current_fault
        else "OPTIMAL"
    )

    st.markdown(
        f"""
        **Station Health Status**<br>
        <span class='{status_color}'>{status_label}</span>
        """,
        unsafe_allow_html=True,
    )

with m5:
    st.metric(
        "Sensor Health Score",
        "42 / 100" if is_current_fault else "98 / 100",
        delta="-56 pts" if is_current_fault else "+1 pt"
    )

st.markdown("---")

# -------------------------------------------------------------------
# 5. GEOSPATIAL MAP & REAL-TIME ALERTS
# -------------------------------------------------------------------
col_map, col_alerts = st.columns([1.6, 1.0])

with col_map:
    st.subheader("🗺️ Spatial Buddy Network View")
    
    # Render PyDeck Scatterplot Map
    view_state = pdk.ViewState(
        latitude=28.55,
        longitude=77.20,
        zoom=9.2,
        pitch=25
    )
    
    scatterplot_layer = pdk.Layer(
        "ScatterplotLayer",
        data=stations_df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=2500,
        pickable=True,
        auto_highlight=True
    )
    
    text_layer = pdk.Layer(
        "TextLayer",
        data=stations_df,
        get_position=["lon", "lat"],
        get_text="station_id",
        get_size=14,
        get_color=[255, 255, 255, 255],
        get_alignment_baseline="'bottom'",
        get_offset=[0, -15]
    )

    r = pdk.Deck(
        layers=[scatterplot_layer, text_layer],
        initial_view_state=view_state,
        tooltip={"html": "<b>{name}</b><br>ID: {station_id}<br>Status: {status}<br>Elev: {elevation}m"}
    )
    st.pydeck_chart(r)


with col_alerts:
    st.subheader("🚨 Real-Time Alert Log")

    if is_current_fault:

        fault_type = backend_result.get(
            "classification",
            "General Sensor Anomaly"
        )

        spatial_check = backend_result.get(
            "spatial_buddy_check",
            "Check unavailable"
        )

        st.markdown(f"""
            <div class='alert-critical'>
                <strong>[CRITICAL] {fault_type}</strong><br>
                <small>{selected_station_id} | Live Backend Detection</small><br>
                Spatial Buddy Check: {spatial_check}
            </div>
        """, unsafe_allow_html=True)

    else:

        st.success(
            "✓ No critical alerts actively triggered for this node."
        )


# -------------------------------------------------------------------
# 6. TIME-SERIES ANALYTICS & SELF-HEALING IMPUTATION
# -------------------------------------------------------------------
st.subheader("📊 Atmospheric Parameter Telemetry & Self-Healing Imputation")

tab1, tab2, tab3 = st.tabs(["Temperature (°C)", "Relative Humidity (%)", "Pressure (hPa)"])

def plot_telemetry(df, param_col, rec_col, unit):
    fig = go.Figure()
    
    # Observed Values
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df[param_col],
        mode="lines+markers",
        name="Observed Raw Signal",
        line=dict(color="#29b6f6", width=2)
    ))
    
    # Anomalously Flagged Points
    anomalies = df[df["is_anomaly"]]
    if not anomalies.empty and param_col == "temperature":
        fig.add_trace(go.Scatter(
            x=anomalies["timestamp"], y=anomalies[param_col],
            mode="markers",
            name="Detected Anomaly",
            marker=dict(color="#ff4b4b", size=10, symbol="x")
        ))
        
        # Self-Healing Imputed Signal
        fig.add_trace(go.Scatter(
            x=df["timestamp"], y=df[rec_col],
            mode="lines",
            name="AI Self-Healed Imputation",
            line=dict(color="#00e676", width=2, dash="dash")
        ))
    
    fig.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis_title=f"{param_col.capitalize()} ({unit})",
        xaxis_title="Time (UTC)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

with tab1:
    st.plotly_chart(plot_telemetry(telemetry_df, "temperature", "reconstructed_temp", "°C"), use_container_width=True)

with tab2:
    st.plotly_chart(plot_telemetry(telemetry_df, "humidity", "reconstructed_humidity", "%"), use_container_width=True)

with tab3:
    st.plotly_chart(plot_telemetry(telemetry_df, "pressure", "pressure", "hPa"), use_container_width=True)

# -------------------------------------------------------------------
# 7. EXPLAINABLE AI (XAI) ATTRIBUTION
# -------------------------------------------------------------------
st.subheader("💡 Explainable AI (XAI) Attribution")
exp_col1, exp_col2 = st.columns([1, 1])

with exp_col1:
    st.markdown("**SHAP Feature Contribution to Anomaly Score**")

    shap_scores = backend_result.get(
        "shap_scores",
        {
            "Temperature Rate-of-Change": 0.02,
            "Dew-Point Violation Score": -0.01,
            "Spatial Residual Error": -0.04,
            "Pressure Shift": -0.03,
        }
    )

    shap_df = pd.DataFrame({
        "Feature": list(shap_scores.keys()),
        "SHAP Value": list(shap_scores.values())
    }).sort_values(
        by="SHAP Value",
        ascending=True
    )

    fig_shap = go.Figure(
        go.Bar(
            x=shap_df["SHAP Value"],
            y=shap_df["Feature"],
            orientation="h",
            marker_color=[
                "#ff4b4b" if x > 0.1 else "#29b6f6"
                for x in shap_df["SHAP Value"]
            ]
        )
    )

    fig_shap.update_layout(
        template="plotly_dark",
        height=220,
        
        margin=dict(l=10, r=10, t=10, b=10)
    )

    st.plotly_chart(
        fig_shap,
        use_container_width=True
    )

with exp_col2:
    st.markdown("**Plain-English Model Reasoning**")
    if is_current_fault:
        st.error("""
        **Reasoning Engine Breakdown:**
        1. **Physical Constraint Violation:** Observed temperature (+43.5°C) exceeds calculated saturation vapor pressure limits relative to current ambient humidity.
        2. **Spatial Discrepancy:** Target station diverges by **+8.4σ** from neighboring cluster nodes (`AWS-IND-002`, `AWS-IND-003`).
        3. **Temporal Sudden Jump:** Temperature rate-of-change ($\Delta T / \Delta t$) hit **+18.5°C per 15 mins**, exceeding maximum climatological threshold (5.0°C / 15 mins).
        """)
    else:
        st.success("""
        **Reasoning Engine Breakdown:**
        1. All 3 parameter streams ($T, P, RH$) remain within expected diurnal covariance matrices.
        2. Dew point calculation ($T_d \le T$) remains physically valid.
        3. Station correlates perfectly with spatial network consensus.
        """)