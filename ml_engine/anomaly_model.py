import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


class WeatherAnomalyModel:

    def __init__(self):
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42
        )

        self.is_trained = False

    def train(self, normal_data):
        self.model.fit(normal_data)
        self.is_trained = True

    def train_from_csv(self, csv_path):
        data = pd.read_csv(csv_path)

        features = data[
            ["temperature", "humidity", "pressure"]
        ]

        self.train(features)

        print("ML model trained successfully!")
        print(f"Training observations: {len(features)}")

    def predict(self, temperature, humidity, pressure):

        if not self.is_trained:
            raise RuntimeError("Model is not trained yet.")

        data = pd.DataFrame([{
            "temperature": temperature,
            "humidity": humidity,
            "pressure": pressure
        }])

        prediction = self.model.predict(data)

        score = self.model.decision_function(data)[0]

        return {
            "is_anomaly": bool(prediction[0] == -1),
            "anomaly_score": float(score)
        }