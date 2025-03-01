import pymysql as pymysql
from flask import *
from werkzeug.utils import secure_filename
import requests
import numpy as np

task = Flask(__name__)
task.secret_key = "abc"
con =pymysql.connect(host="localhost", user="root", password="root", port=3306, db="smartcitydb",charset='utf8')
cmd = con.cursor()

# --------------------------------------------------Functions-------------------------------------------------
def heat_index(t, rh):
    """
    Calculate Heat Index using the Steadmans Heat Index formula.
    
    :param t: Temperature in Celsius
    :param rh: Relative Humidity in %
    :return: Heat Index in Celsius
    """
    hi = t + 0.5555 * (6.11 * np.exp((17.27 * t) / (237.7 + t)) * rh / 100 - 10)
    return round(hi, 2)

def min_max_normalize(value, min=0, max=50):
    """
    Min-Max Normalization (scales values between 0 and 1).
    
    :param value: Heat Index value
    :param min: Minimum expected HI (default: 0°C)
    :param max: Maximum expected HI (default: 50°C)
    :return: Normalized Heat Index (0 to 1)
    """
    return round((value - min) / (max - min), 3)

def heat_status_calculation():
    cmd.execute("SELECT * FROM readings WHERE id = (SELECT MAX(id) FROM readings)")
    result=cmd.fetchall()
    print(result)
    for row in result:
        temp_c = heat_index(row[1],row[2])
    if temp_c <= 20:
        heat_status="Good"
    elif 21 <= temp_c <= 35:
        heat_status="Moderate"
    else:
        heat_status="Bad"
    session["heat_status"]  = heat_status

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
    
#------------------------------------------------- Header -------------------------------------------------------


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
@task.route('/dashboard')
def dashboard():
    if session["logid"] is not None:

        return render_template('dashboard.html')
    else:
        return redirect("/")


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
# @task.route('/map')
# def showHeatmap():
#     data_points = [
#        {'lon': 75.231870, 'lat': 12.240140, 'weight': 0.8},
#        {'lon': 75.233870, 'lat': 12.242140, 'weight': 0.6},
#        {'lon': 75.229870, 'lat': 12.238140, 'weight': 0.9},
#        {'lon': 75.235870, 'lat': 12.241140, 'weight': 0.7}
#         ]
#     return render_template('heatmap.html', data_points=data_points)

@task.route('/map/heat')
def chartheat():
    cmd.execute("SELECT * FROM readings WHERE id = (SELECT MAX(id) FROM readings)")
    result=cmd.fetchall()
    print(result)
    # Prepare data_points in the required format
    data_points = []
    for row in result:
        #calculate the effective temerature using heat index
        temp_c = heat_index(row[1],row[2])
        # Assuming the database has latitude in row[1], longitude in row[2], and weight in row[4]
        data_point = {
            'lat': 12.2429,  # Replace with the correct column index for latitude
            'lon': 75.2346,  # Replace with the correct column index for longitude
            'weight': min_max_normalize(temp_c,min=0, max=50)  #min max normalised for 0-50 degrees
        }
        data_points.append(data_point)
        print(data_points)
    if temp_c <= 20:
        heat_status="Good"
    elif 21 <= temp_c <= 35:
        heat_status="Moderate"
    else:
        heat_status="Bad"
    return render_template('heatmap.html', data_points=data_points ,map="Effective Heat", heat_status=heat_status)

@task.route('/map/noise')
def chartnoise():
    # cmd.execute("SELECT * FROM readings WHERE id = (SELECT MAX(id) FROM readings)")
    # result=cmd.fetchall()
    # print(result)
    # # Prepare data_points in the required format
    # data_points = []
    # for row in result:
    #     # Assuming the database has latitude in row[1], longitude in row[2], and weight in row[4]
    #     data_point = {
    #         'lat': 12.2429,  # Replace with the correct column index for latitude
    #         'lon': 75.2346,  # Replace with the correct column index for longitude
    #         'weight': row[1]/40  # Replace with the correct column index for weight
    #     }
    #     data_points.append(data_point)
    #     print(data_points)
    # # Pass data_points to the template
    return render_template('heatmap.html', data_points=None,map="Noise Pollution",)

@task.route('/map/air')
def chartair():
    # cmd.execute("SELECT * FROM readings WHERE id = (SELECT MAX(id) FROM readings)")
    # result=cmd.fetchall()
    # print(result)
    # # Prepare data_points in the required format
    # data_points = []
    # for row in result:
    #     # Assuming the database has latitude in row[1], longitude in row[2], and weight in row[4]
    #     data_point = {
    #         'lat': 12.2429,  # Replace with the correct column index for latitude
    #         'lon': 75.2346,  # Replace with the correct column index for longitude
    #         'weight': row[1]/40  # Replace with the correct column index for weight
    #     }
    #     data_points.append(data_point)
    #     print(data_points)
    # # Pass data_points to the template
    return render_template('heatmap.html', data_points=None,map="Air Pollution")

# -------------------------------------------------- Admin -----------------------------------------------------
@task.route("/admin-settings")
def admin_settings():
    return render_template("adminsettings.html")

#----------------USer management-------------------
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