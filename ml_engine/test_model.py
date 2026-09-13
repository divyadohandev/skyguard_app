from anomaly_model import WeatherAnomalyModel
import numpy as np


# --------------------------------------------------
# Generate realistic normal AWS weather data
# --------------------------------------------------

np.random.seed(42)

normal_data = np.column_stack([
    np.random.normal(28, 3, 1000),      # Temperature
    np.random.normal(60, 8, 1000),      # Humidity
    np.random.normal(1011, 3, 1000)     # Pressure
])


# --------------------------------------------------
# Create and train model
# --------------------------------------------------

model = WeatherAnomalyModel()

model.train(normal_data)


# --------------------------------------------------
# Test NORMAL reading
# --------------------------------------------------

normal_result = model.predict(
    28.0,
    62.0,
    1011.0
)

print("NORMAL READING")
print(normal_result)


# --------------------------------------------------
# Test ANOMALOUS reading
# --------------------------------------------------

anomaly_result = model.predict(
    58.4,
    63.5,
    1011.0
)

print("\nANOMALOUS READING")
print(anomaly_result)