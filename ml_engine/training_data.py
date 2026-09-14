import numpy as np
import pandas as pd


np.random.seed(42)

# Number of normal weather observations
n = 5000

# Generate realistic normal weather conditions
temperature = np.random.normal(28, 4, n)
humidity = np.random.normal(60, 10, n)
pressure = np.random.normal(1011, 4, n)

# Keep values within reasonable ranges
temperature = np.clip(temperature, 15, 40)
humidity = np.clip(humidity, 20, 95)
pressure = np.clip(pressure, 995, 1025)

# Create dataframe
data = pd.DataFrame({
    "temperature": temperature,
    "humidity": humidity,
    "pressure": pressure
})

# Save dataset
data.to_csv("weather_normal_data.csv", index=False)

print("Training dataset created successfully!")
print(f"Total observations: {len(data)}")
print(data.head())