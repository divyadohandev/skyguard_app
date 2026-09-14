from anomaly_model import WeatherAnomalyModel


model = WeatherAnomalyModel()

# Train using our CSV dataset
model.train_from_csv("weather_normal_data.csv")


# Test normal weather
normal_result = model.predict(
    28.0,
    62.0,
    1011.0
)

print("\nNORMAL READING")
print(normal_result)


# Test abnormal weather
anomaly_result = model.predict(
    58.4,
    63.5,
    1011.0
)

print("\nANOMALOUS READING")
print(anomaly_result)