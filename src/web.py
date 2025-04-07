import pymysql as pymysql
from flask import *
import datetime
from werkzeug.utils import secure_filename
import requests
import numpy as np
import joblib
import sklearn
from sklearn.preprocessing import MinMaxScaler
import pandas as pd

task = Flask(__name__)
# Session Configuration
task.config['SESSION_COOKIE_NAME'] = 'my_session'
task.config['SESSION_COOKIE_HTTPONLY'] = True
task.config['SESSION_PERMANENT'] = False

task.secret_key = "abc"
con =pymysql.connect(host="localhost", user="root", password="root", port=3307, db="smartcitydb",charset='utf8')
cmd = con.cursor()

#-----------------------------------------------model---------------------------------------------------------
#predict AQI
model = joblib.load("aqi_model.pkl")


scaler = joblib.load("scaler.pkl")

def predict_aqi(temp, hum, gas, noise):
    input_data = np.array([[temp, hum, gas, noise]])

    print(f"Raw input data: {input_data}")

    #MinMaxScaler transformation
    input_data_scaled = scaler.transform(np.clip(input_data, scaler.data_min_, scaler.data_max_))
    print(f"Scaled input data: {input_data_scaled}")

    predicted_aqi = model.predict(input_data_scaled)[0]
    print(f"Predicted AQI: {predicted_aqi}")

    return round(predicted_aqi, 2)


# --------------------------------------------------Functions-------------------------------------------------
def heat_index(t, rh):
    """
    Calculate Heat Index using the Steadmans Heat Index formula.
    
    :param t: Temperature in Celsius
    # Predict the AQI using the pre-trained model
    :param rh: Relative Humidity in %
    :return: Heat Index in Celsius
    """
    t = float(t)
    rh = float(rh)
    hi = t + 0.5555 * (6.11 * np.exp((17.27 * t) / (237.7 + t)) * rh / 100 - 10)
    return round(hi, 2)

def min_max_normalize(value, min=0, max=50):
    """
    Min-Max Normalization (scales values between 0 and 1).
    
    :param value: Value to normalise
    :param min: Minimum expected HI (default: 0°C)
    :param max: Maximum expected HI (default: 50°C)
    :return: Normalized Heat Index (0 to 1)
    """
    return round((value - min) / (max - min), 3)


#------------------------------------------------- GEOLOCATION -------------------------------------------------
@task.route('/location', methods=['POST'])
def handle_location():
    data = request.get_json()
    latitude = data['latitude']
    longitude = data['longitude']
    print("Received latitude: %s" % latitude)
    print("Received longitude: %s" % longitude)

    # Use the latitude and longitude to get the location
    mapapi = "678e6b7153e80080651781qpn13b068"  # Replace with your actual API key
    url = f"https://geocode.maps.co/reverse?lat={latitude}&lon={longitude}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        
        if "display_name" in data:
            location_name = data["display_name"]
            print("Received location name: %s" % location_name)
            session["location"] = location_name
            return jsonify({'message': 'Location received successfully', 'location': location_name})
        else:
            return jsonify({'error': 'Could not fetch location data'}), 500

    except requests.RequestException as e:
        print(f"Error fetching location: {e}")
        return jsonify({'error': 'Failed to connect to the location service'}), 500
    
#------------------------------------------------- Notifications -------------------------------------------------------


@task.route('/notifications', methods=['GET'])
def get_notifications():
    cmd.execute("SELECT * FROM notification ORDER BY timestamp DESC;")
    notifications = cmd.fetchall()
    
    print("Fetched notifications:", notifications)  # Debugging line to check fetched notifications
    return render_template('notification_log.html', notifications=notifications)


# ------------------------------------------------ LOgin And Signup --------------------------------------------- 
@task.route('/')
def login():
    return render_template('login.html')

@task.route('/logout')
def logout():
    session.clear()
    return redirect('/')
@task.route('/logincheck', methods=['post'])
def logincheck():
    user = request.form['email']
    psd = request.form['password']
    cmd.execute("select * from logintable where username='" + user + "' and password='" +psd+ "'")
    result = cmd.fetchone()
    if result is not None:
        session['logid'] = result[0]
        session['usertype']=result[3]
        session["username"]=result[1]
        session["email"]=result[4]
        session["lon"]=75.2346
        session["lat"]=12.2429
        return redirect('/dashboard')
    else:
        return '''<script>alert("INVALID USERNAME AND PASSWORD");window.location.replace("/");</script>'''

@task.route('/signupcheck', methods=['post'])
def signupcheck():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    usertype = 'user'  # default user type, can be changed later

    # Check if username or email already exists
    cmd.execute("SELECT * FROM logintable WHERE username=%s OR email=%s", (username, email))
    result = cmd.fetchone()
    if result is not None:
        return '''<script>alert("USERNAME OR EMAIL ALREADY EXISTS");window.location.replace("/");</script>'''

    # Insert the user into the database
    cmd.execute("INSERT INTO logintable (username, email, password, usertype) VALUES (%s, %s, %s, %s)", (username, email, password, usertype))
    con.commit()
    return '''<script>alert("SIGNUP SUCCESSFUL");window.location.replace("/");</script>'''

# ------------------------------------------------- Dashboard ------------------------------------------------------------

def heat_status_calculation():
    lon = session.get("lon")
    lat = session.get("lat")
    coord_margin = 0.005
    print("Looking for coordinates:", lon, lat)
    try:
        cmd.execute("""
            SELECT * FROM readings 
            WHERE lon BETWEEN %s - %s AND %s + %s 
            AND lat BETWEEN %s - %s AND %s + %s 
            ORDER BY id DESC LIMIT 1
        """, (lon, coord_margin, lon, coord_margin, lat, coord_margin, lat, coord_margin))

        result = cmd.fetchone()
        
        if result is None:
            print("No data found for the specified coordinates.")
            session["heat_status"] = "Unknown"
            return
        
        temp_c = heat_index(result[1], result[2])
        
        if temp_c <= 20:
            heat_status = "Good"
        elif 21 <= temp_c <= 35:
            heat_status = "Moderate"
        else:
            heat_status = "Bad"
        
        session["heat_status"] = heat_status
        print("Heat Status:", heat_status)
        
    except Exception as e:
        print(f"An error occurred during heat status calculation: {e}")
        session["heat_status"] = "Error"

def noise_status_calculation():
    lon = session.get("lon")
    lat = session.get("lat")
    coord_margin = 0.005
    print("Looking for coordinates:", lon, lat)
    try:
        cmd.execute("""
            SELECT * FROM readings 
            WHERE lon BETWEEN %s - %s AND %s + %s 
            AND lat BETWEEN %s - %s AND %s + %s 
            ORDER BY id DESC LIMIT 1
        """, (lon, coord_margin, lon, coord_margin, lat, coord_margin, lat, coord_margin))

        result = cmd.fetchone()
        noise=result[4]
        
        if result is None:
            print("No data found for the specified coordinates.")
            session["noise_status"] = "Unknown"
            return
                
        if noise <= 20:
            noise_status = "Good"
        elif 21 <= noise <= 50:
            noise_status = "Moderate"
        else:
            noise_status = "Bad"
        
        session["noise_status"] = noise_status
        print("Noise Status:", noise_status)
        
    except Exception as e:
        print(f"An error occurred during noise status calculation: {e}")
        session["noise_status"] = "Error"

def air_status_calculation():
    lon = session.get("lon")
    lat = session.get("lat")
    coord_margin = 0.005
    print("Looking for coordinates:", lon, lat)
    try:
        cmd.execute("""
            SELECT * FROM readings 
            WHERE lon BETWEEN %s - %s AND %s + %s 
            AND lat BETWEEN %s - %s AND %s + %s 
            ORDER BY id DESC LIMIT 1
        """, (lon, coord_margin, lon, coord_margin, lat, coord_margin, lat, coord_margin))

        result = cmd.fetchone()
        
        if result is None:
            print("No data found for the specified coordinates.")
            session["air_status"] = "Unknown"
            return
        air=result[3]
        if air <= 200:
            air_status = "Good"
        elif 201 <= air <= 350:
            air_status = "Moderate"
        else:
            air_status = "Bad"
        
        session["air_status"] = air_status
        print("Air Status:", air_status)
        
    except Exception as e:
        print(f"An error occurred during air status calculation: {e}")
        session["air_status"] = "Error"

@task.route('/dashboard')
def dashboard():
    if session["logid"] is not None:
        heat_status_calculation()
        noise_status_calculation()
        air_status_calculation()
        return render_template('dashboard.html')
    else:
        return redirect("/")
    
@task.route('/get_trend_data')
def get_trend_data():
    # Get coordinates from session
    lon = session.get("lon")
    lat = session.get("lat")
    coord_margin = 0.005
    
    # Calculate date for 7 days ago
    current_date = datetime.datetime.now().date()
    seven_days_ago = current_date - datetime.timedelta(days=7)
    
    
    try:
        # Query to get aggregated data for the past 7 days
        cmd.execute("""
            SELECT 
                date,
                AVG(temp) as avg_temp,
                AVG(hum) as avg_hum,
                AVG(gas) as avg_gas,
                AVG(noise) as avg_noise
            FROM readings
            WHERE 
                lon BETWEEN %s - %s AND %s + %s
                AND lat BETWEEN %s - %s AND %s + %s
                AND date >= %s
            GROUP BY date
            ORDER BY date ASC
            LIMIT 7
        """, (lon, coord_margin, lon, coord_margin, lat, coord_margin, lat, coord_margin, seven_days_ago))
        
        results = cmd.fetchall()

        print(f"trend chart results: {results}")
        
        # Prepare the data for the chart
        dates = []
        temps = []
        hums = []
        gases = []
        noises = []
        
        for row in results:
            # Format date as day name (Mon, Tue, etc.)
            date_obj = row[0]
            day_name = date_obj.strftime('%a')
            dates.append(day_name)
            temps.append(float(row[1]))
            hums.append(float(row[2]))
            gases.append(float(row[3]))
            noises.append(float(row[4]))
        
        return jsonify({
            'dates': dates,
            'temps': temps,
            'hums': hums,
            'gases': gases,
            'noises': noises
        })
    
    except Exception as e:
        print(f"Error fetching trend data: {e}")
        return jsonify({'error': str(e)}), 500
    
@task.route('/get_pollution_data')
def get_pollution_data():
    lon = session.get("lon")
    lat = session.get("lat")
    coord_margin = 0.01

    # Create a list of all month names in order
    all_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    aqi_by_month = {month: 0 for month in all_months}  # Default AQI as 0

    try:
        # Query to get average AQI per month
        cmd.execute("""
            SELECT 
                MONTH(date) AS month_num,
                AVG(aqi) AS avg_aqi
            FROM readings
            WHERE 
                lon BETWEEN %s - %s AND %s + %s
                AND lat BETWEEN %s - %s AND %s + %s
            GROUP BY MONTH(date)
            ORDER BY MONTH(date)
        """, (lon, coord_margin, lon, coord_margin, lat, coord_margin, lat, coord_margin))

        results = cmd.fetchall()

        # Fill the AQI data into the dictionary
        for row in results:
            month_index = row[0] - 1  # Convert 1-based SQL month to 0-based Python index
            avg_aqi = float(row[1]) if row[1] is not None else 0
            aqi_by_month[all_months[month_index]] = avg_aqi

        # Convert dict to lists for JSON
        months = list(aqi_by_month.keys())
        aqi_values = list(aqi_by_month.values())

        return jsonify({
            'months': months,
            'aqi': aqi_values
        })

    except Exception as e:
        print(f"Error fetching pollution data: {e}")
        return jsonify({'error': str(e)}), 500



@task.route("/change-password", methods=["POST", "GET"])
def change_password():
    if request.method == "POST":
        current_password = request.form["current-password"]
        new_password = request.form["new-password"]
        confirm_password = request.form["confirm-password"]

        # Find the user
        cmd.execute("SELECT password FROM logintable WHERE username=%s", (session["username"],))
        user_password = cmd.fetchone()[0]

        # Check if the current password is correct
        if user_password != current_password:
            return '''<script>alert("Invalid current password");window.location.replace("/change-password");</script>'''

        # Check if the new password and confirmation match
        if new_password != confirm_password:
            return '''<script>alert("New password and confirmation do not match");window.location.replace("/change-password");</script>'''

        # Update the user's password
        cmd.execute("UPDATE logintable SET password=%s WHERE username=%s", (new_password, session["username"]))
        con.commit()

        # Return a success response
        return '''<script>alert("Password changed successfully");window.location.replace("/dashboard");</script>'''

    return render_template("change-password.html")

@task.route("/change-username", methods=["POST", "GET"])
def change_username():
    if request.method == "POST":
        new_username = request.form["new-username"]

        # Find the user
        cmd.execute("SELECT username FROM logintable WHERE username=%s", (session["username"],))
        user_username = cmd.fetchone()[0]

        # Check if the new username is available
        cmd.execute("SELECT username FROM logintable WHERE username=%s", (new_username,))
        existing_username = cmd.fetchone()

        if existing_username is not None:
            return '''<script>alert("Username already exists");window.location.replace("/change-username");</script>'''

        # Update the user's username
        cmd.execute("UPDATE logintable SET username=%s WHERE username=%s", (new_username, session["username"]))
        con.commit()

        # Update the session username
        session["username"] = new_username

        # Return a success response
        return '''<script>alert("Username changed successfully");window.location.replace("/dashboard");</script>'''

    return render_template("change-username.html")

# ---------------------------------------------------- Map ------------------------------------------------------------

@task.route('/map/heat/date')
def heat_by_date():
    date = request.args.get('date')
    
    if not date:
        return jsonify({"error": "Date parameter is required"}), 400
    
    date_parts = date.split('/')
    sql_date_format = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
    
    cmd.execute("""
    SELECT 
    r1.lat, 
    r1.lon, 
    r1.date, 
    AVG(r1.temp) AS avg_temp, 
    AVG(r1.hum) AS avg_hum
FROM readings r1 
INNER JOIN (
    SELECT lat, lon, date
    FROM readings 
    WHERE date = %s
    GROUP BY lat, lon, date
) r2 
ON r1.lat = r2.lat AND r1.lon = r2.lon AND r1.date = r2.date
GROUP BY r1.lat, r1.lon, r1.date
    """, (sql_date_format,))

    result = cmd.fetchall()
    data_points = []
    for row in result:
        # Calc the effective temperature using heat index
        temp_c = heat_index(row[3], row[4])
        
        # Create data point
        data_point = {
            'lat': row[0],
            'lon': row[1],
            'weight': min_max_normalize(temp_c, min=0, max=50)  # min-max normalized for 0-50 degrees
        }
        data_points.append(data_point)
    
    return jsonify({"data_points": data_points})

@task.route('/map/heat')
def chartheat():
    cmd.execute("SELECT r1.lat, r1.lon, r1.temp, r1.hum FROM readings r1 INNER JOIN (SELECT lat, lon, MAX(DATE) AS max_date, MAX(TIME) AS max_time FROM readings GROUP BY lat, lon) r2 ON r1.lat = r2.lat AND r1.lon = r2.lon AND r1.date = r2.max_date AND r1.time = r2.max_time;")
    result=cmd.fetchall()
    print(result)
    # Prepare data_points in the required format
    data_points = []
    for row in result:
        #calculate the effective temerature using heat index
        temp_c = heat_index(row[2],row[3])
        # Assuming the database has latitude in row[1], longitude in row[2], and weight in row[4]
        data_point = {
            'lat': row[0],  # Replace with the correct column index for latitude
            'lon': row[1],  # Replace with the correct column index for longitude
            'weight': min_max_normalize(temp_c,min=0, max=50)  #min max normalised for 0-50 degrees
        }
        data_points.append(data_point)
        print(data_points)
    return render_template('heatmap.html', data_points=data_points ,map="Effective Heat")

@task.route('/map/noise')
def chartnoise():
    cmd.execute("""
    SELECT r1.lat, r1.lon, r1.noise 
    FROM readings r1 
    INNER JOIN (
        SELECT lat, lon, MAX(DATE) AS max_date, MAX(TIME) AS max_time 
        FROM readings 
        GROUP BY lat, lon
    ) r2 
    ON r1.lat = r2.lat 
    AND r1.lon = r2.lon 
    AND r1.date = r2.max_date 
    AND r1.time = r2.max_time
    ORDER BY r1.lat, r1.lon
""")
    result=cmd.fetchall()
    # # Prepare data_points in the required format
    data_points = []
    for row in result:
        # Assuming the database has latitude in row[1], longitude in row[2], and weight in row[4]
        data_point = {
            'lat': row[0],  # Replace with the correct column index for latitude
            'lon': row[1],  # Replace with the correct column index for longitude
            'weight': min_max_normalize(row[2],min=0, max=100)  # Replace with the correct column index for weight
        }
        data_points.append(data_point)
    # Pass data_points to the template
    print(data_points)
    return render_template('heatmap.html', data_points=data_points,map="Noise Pollution",)

@task.route('/map/air')
def chartair():
    cmd.execute("""
    SELECT r1.lat, r1.lon, r1.gas 
    FROM readings r1 
    INNER JOIN (
        SELECT lat, lon, MAX(DATE) AS max_date, MAX(TIME) AS max_time 
        FROM readings 
        GROUP BY lat, lon
    ) r2 
    ON r1.lat = r2.lat 
    AND r1.lon = r2.lon 
    AND r1.date = r2.max_date 
    AND r1.time = r2.max_time
    ORDER BY r1.lat, r1.lon
""")
    result=cmd.fetchall()
    print(result)
    # Prepare data_points in the required format
    data_points = []
    for row in result:
        # Assuming the database has latitude in row[1], longitude in row[2], and weight in row[4]
        data_point = {
            'lat': row[0],  # Replace with the correct column index for latitude
            'lon': row[1],  # Replace with the correct column index for longitude
            'weight': min_max_normalize(row[2],min=300, max=2000)  # weight of data point
        }
        data_points.append(data_point)
        print(data_points)
    # Pass data_points to the template
    return render_template('heatmap.html', data_points=data_points,map="Air Pollution")

# ----------------------------------------- Heatmap Prediction Routes --------------------------------------------

@task.route('/map/aqipredict', methods=['GET'])
def aqi_heatmapday():
    cmd.execute("SELECT * FROM readings r1 INNER JOIN (SELECT lat, lon, MAX(DATE) AS max_date, MAX(TIME) AS max_time FROM "
    "readings GROUP BY lat, lon) r2 ON r1.lat = r2.lat AND r1.lon = r2.lon AND r1.date = r2.max_date AND r1.time = r2.max_time;")
    results = cmd.fetchall()

    aqi_data = []
    for row in results:
        temp = row[1]  # Temperature column
        hum = row[2]   # Humidity column
        gas = row[3]   # Gas level column
        noise = row[4] # Noise level column
        lat = row[7]   # Latitude
        lon = row[8]   # Longitude

        # Predict AQI using the trained model
        aqi_value = predict_aqi(temp, hum, gas, noise)

        # Normalize AQI for heatmap visualization
        weight = min_max_normalize(aqi_value, min=0, max=300)

        aqi_data.append({
            "lat": lat,
            "lon": lon,
            "weight": weight  # Include AQI value for coloring
        })
    
    # Check if requesting JSON format (based on Accept header or json parameter)
    if request.args.get('format') == 'json' or request.headers.get('Accept') == 'application/json':
        return jsonify({"data_points": aqi_data})
    else:
        return render_template('heatmap.html', data_points=aqi_data, map="Predicted Air Quality Index")

@task.route('/map/aqipredictweek', methods=['GET'])
def aqi_heatmapweek():
    # Optimized query to get the most recent reading for each unique location
    cmd.execute("""
    SELECT 
            ROUND(AVG(temp), 2) AS avg_temperature,
            ROUND(AVG(hum), 2) AS avg_humidity,
            ROUND(AVG(gas), 2) AS avg_gas,
            ROUND(AVG(noise), 2) AS avg_noise,
            lat,
            lon
        FROM readings
        WHERE date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY lat, lon
    """)
    
    results = cmd.fetchall()
    
    aqi_data = []
    for row in results:
        temp = row[0]      # Temperature 
        hum = row[1]       # Humidity
        gas = row[2]       # Gas level
        noise = row[3]     # Noise level
        lat = row[4]       # Latitude
        lon = row[5]       # Longitude
        
        # Predict AQI using the trained model
        aqi_value = predict_aqi(temp, hum, gas, noise)
        
        # Normalize AQI for heatmap visualization
        weight = min_max_normalize(aqi_value, min=0, max=300)
        
        aqi_data.append({
            "lat": lat,
            "lon": lon,
            "weight": weight  # Include AQI value for coloring
        })
    
    # Check if requesting JSON format (based on Accept header or json parameter)
    if request.args.get('format') == 'json' or request.headers.get('Accept') == 'application/json':
        return jsonify({"data_points": aqi_data})
    else:
        return render_template('heatmap.html', data_points=aqi_data, map="Predicted Air Quality Index")

# -------------------------------------------------- Admin -----------------------------------------------------
@task.route("/admin-settings")
def admin_settings():
    return render_template("adminsettings.html")

#--------------------------------------------------User management-----------------------------------------------
@task.route("/usermanagement")
def usermanagement():
    cmd.execute("SELECT * FROM logintable")
    users = cmd.fetchall()
    return render_template("usermg.html", users=users)


@task.route("/addUser", methods=["POST"])
def add_user():
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    usertype = request.form["role"]

    # Insert the user into the database
    cmd.execute("INSERT INTO logintable (username, email, password, usertype) VALUES (%s, %s, %s, %s)", (username, email, password, usertype))
    con.commit()
    return redirect(url_for("usermanagement", message="User added successfully!"))


@task.route("/deluser/<uid>", methods=["GET"])
def delete_user(uid):
    try:
        # Delete the user from the database
        cmd.execute("DELETE FROM logintable WHERE id= %s;", (uid))
        con.commit()
        return redirect(url_for("usermanagement", message="User deleted successfully!"))
    except Exception as e:
        return redirect(url_for("usermanagement", message="Error deleting user: " + str(e)))
    
# ---------- Sensor Management ------------
@task.route("/sensormanagement")
def sensor_management():
    cmd.execute("SELECT * FROM readings")
    sensors = cmd.fetchall()
    return render_template("sensormg.html", sensors=sensors)

@task.route("/delete_sensor/<sid>", methods=["GET"])
def delete_sensor(sid):
    try:
        cmd.execute("DELETE FROM sensor_table WHERE id= %s;", (sid))
        con.commit()
        return redirect(url_for("sensor_management", message="Sensor deleted successfully!"))
    except Exception as e:
        return redirect(url_for("sensor_management", message="Error deleting sensor: " + str(e)))
    

task.run(debug=True)
