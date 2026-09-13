import numpy as np
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

    def predict(self, temperature, humidity, pressure):

        if not self.is_trained:
            raise RuntimeError("Model is not trained yet.")

        data = np.array([
            [temperature, humidity, pressure]
        ])

        prediction = self.model.predict(data)

        score = self.model.decision_function(data)[0]

        return {
            "is_anomaly": prediction[0] == -1,
            "anomaly_score": float(score)
        }