import pymysql
from flask import Flask, request, jsonify
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import datetime  # Import datetime for time calculations

dat = ""
app = Flask(__name__)
con = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    port=3307,
    db='smartcitydb',
    charset='utf8'
)
cmd = con.cursor()
last_notification_time = None  # Variable to track the last notification time

# Define expected sensor value ranges (same as dataset generation)
temp_range = (20, 60)  # DHT11 - Temperature
hum_range = (10, 100)  # DHT11 - Humidity
gas_range = (10, 2000)  # MQ-135 - Gas
noise_range = (5, 110)  # MZ4466 - Noise

# Initialize MinMaxScaler with predefined feature range
scaler = MinMaxScaler(feature_range=(0, 1))

# Fit scaler using the original feature ranges
scaler.fit([
    [temp_range[0], hum_range[0], gas_range[0], noise_range[0]],  # Min values
    [temp_range[1], hum_range[1], gas_range[1], noise_range[1]]  # Max values
])


# AQI Calculation Function
def calculate_aqi(norm_temp, norm_hum, norm_gas, norm_noise):
    return (0.6 * norm_gas) + (0.15 * norm_temp) + (0.1 * norm_hum) + (0.15 * norm_noise)


@app.route('/test', methods=['POST'])
def test():
    global dat

    val = request.get_data().decode()
    res = val.split(',')
    temperature = float(res[0])
    humidity = float(res[1])
    gas = float(res[2])
    noise = float(res[3])
    lat = float(res[4])
    lon = float(res[5])

    # Normalize sensor values using MinMaxScaler
    normalized_values = scaler.transform([[temperature, humidity, gas, noise]])[0]
    norm_temp, norm_hum, norm_gas, norm_noise = normalized_values

    global last_notification_time
    # Calculate AQI using normalized values
    aqi = calculate_aqi(norm_temp, norm_hum, norm_gas, norm_noise) * 500  # Scale to 0-500

    if aqi > 300:
        notification_message = "AQI crossed 300 at location ({}, {})".format(lat, lon)
        current_time = datetime.datetime.now()

        # Check if 30 minutes have passed since the last notification
        if last_notification_time is None or (current_time - last_notification_time).total_seconds() >= 1800:
            cmd.execute("INSERT INTO notification (Notification, Timestamp, D_id) VALUES (%s, NOW(), %s)",
                        (notification_message, 1))
            con.commit()
            last_notification_time = current_time  # Update the last notification time
    elif aqi > 700:
        notification_message = "AQI crossed 700 at location ({}, {})".format(lat, lon)
        current_time = datetime.datetime.now()

        # Check if 30 minutes have passed since the last notification
        if last_notification_time is None or (current_time - last_notification_time).total_seconds() >= 1800:
            cmd.execute("INSERT INTO notification (Notification, Timestamp, D_id) VALUES (%s, NOW(), %s)",
                        (notification_message, 1))
            con.commit()
            last_notification_time = current_time  # Update the last notification time
    elif aqi > 1000:
        notification_message = "AQI crossed 1000 at location ({}, {})".format(lat, lon)
        current_time = datetime.datetime.now()

        # Check if 30 minutes have passed since the last notification
        if last_notification_time is None or (current_time - last_notification_time).total_seconds() >= 1800:
            cmd.execute("INSERT INTO notification (Notification, Timestamp, D_id) VALUES (%s, NOW(), %s)",
                        (notification_message, 1))
            con.commit()
            last_notification_time = current_time  # Update the last notification time
    else:
        notification_message = "AQI crossed above 1000 at location ({}, {})".format(lat, lon)
        current_time = datetime.datetime.now()

        # Check if 30 minutes have passed since the last notification
        if last_notification_time is None or (current_time - last_notification_time).total_seconds() >= 1800:
            cmd.execute("INSERT INTO notification (Notification, Timestamp, D_id) VALUES (%s, NOW(), %s)",
                        (notification_message, 1))
            con.commit()
            last_notification_time = current_time  # Update the last notification time

    print("temperature:", temperature)
    print("humidity:", humidity)
    print("gas:", gas)
    print("noise:", noise)
    print("latitude:", lat)
    print("longitude:", lon)
    print("AQI:", aqi)

    # Insert data into the database
    query = "INSERT INTO readings (temp, hum, gas, noise , date, time, lat, lon, aqi) VALUES (%s, %s, %s, %s,   CURDATE(), CURTIME(),%s, %s, %s)"
    cmd.execute(query, (temperature, humidity, gas, noise, lat, lon, aqi))

    # Update device status and last seen data
    device_update = """
    UPDATE devices 
    SET status = 'Active', 
        last_seen = NOW(), 
        last_data = CONCAT('Temp:', %s, ' Hum:', %s, ' Gas:', %s, ' Noise:', %s, ' Lat:', %s, ' Lon:', %s, ' AQI:', %s)
    WHERE d_id = 2
    """
    cmd.execute(device_update, (temperature, humidity, gas, noise, lat, lon, aqi))
    con.commit()

    result = "ok"
    if dat:
        result = dat
        dat = ""
    return result


if __name__ == "__main__":
    app.run(port=5000, host='0.0.0.0')
