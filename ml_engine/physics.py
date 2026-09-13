import numpy as np

def calculate_dew_point(temp, humidity):
    a, b = 17.27, 237.7
    alpha = ((a * temp) / (b + temp)) + np.log(humidity / 100.0)
    return (b * alpha) / (a - alpha)

def check_physics_violation(temp, humidity):
    dew_point = calculate_dew_point(temp, humidity)
    # Physical Rule: Dew point ambient temperature se bada nahi ho sakta
    return dew_point > temp