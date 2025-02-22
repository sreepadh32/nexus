import pymysql as pymysql
from flask import *
from werkzeug.utils import secure_filename
import requests

task = Flask(__name__)
task.secret_key = "abc"
con =pymysql.connect(host="localhost", user="root", password="root", port=3307, db="smartcitydb",charset='utf8')
cmd = con.cursor()


@task.route('/')
def login():
    return render_template('login.html')
<<<<<<< HEAD
# ------------- LOgin And Signup
=======

@task.route('/logout')
def logout():
    session.clear()
    return redirect('/')
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


# ------------------------------------------------ LOgin And Signup ---------------------------------------------
>>>>>>> 6de2068 (geolocation api set)
@task.route('/logincheck', methods=['post'])
def logincheck():
    user = request.form['email']
    psd = request.form['password']
    cmd.execute("select * from logintable where username='" + user + "' and password='" +psd+ "'")
    result = cmd.fetchone()
    usertype=result[3]
    if result is None:
        return '''<script>alert("INVALID USERNAME AND PASSWORD");windows.locations='/'</script>'''
    elif usertype=="admin":
         session['logid']=result[0]
         return render_template('adminsettings.html')


<<<<<<< HEAD
# ------Dash -----
@task.route('/dash')
def dashboard():
    return render_template('dash.html')
    
# ---------- Map ----------------
=======
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
>>>>>>> 6de2068 (geolocation api set)
@task.route('/map')
def showHeatmap():
    data_points = [
       {'lon': 75.231870, 'lat': 12.240140, 'weight': 0.8},
       {'lon': 75.233870, 'lat': 12.242140, 'weight': 0.6},
       {'lon': 75.229870, 'lat': 12.238140, 'weight': 0.9},
       {'lon': 75.235870, 'lat': 12.241140, 'weight': 0.7}
        ]
    return render_template('heatmap.html', data_points=data_points)


#----------- Heatmap ----------
@task.route('/heatmap')
def heatmap():

    data_points = [
       {'lon': 75.231870, 'lat': 12.240140, 'weight': 0.8},
       {'lon': 75.233870, 'lat': 12.242140, 'weight': 0.6},
       {'lon': 75.229870, 'lat': 12.238140, 'weight': 0.9},
       {'lon': 75.235870, 'lat': 12.241140, 'weight': 0.7}
        ]

    return render_template('heatmap.html', data_points=data_points)

# -------- Settings -----
@task.route('/changeusername')
def changeusername():
    return render_template('change-username.html')

@task.route('/changepassword')
def changepassword():
    return render_template('change-password.html')



# ------------ Admin -----------
@task.route("/admin")
def Admin():
    return render_template("adminsettings.html")


@task.route('/showuser')
def showuser():
    return render_template('usermg.html')

@task.route("/sensormg")
def sensormg():
    return render_template("sensormg.html")


@task.route("/alertmg")
def alertmg():
    return render_template("alertmg.html")


@task.route("/notifmg")
def notifmg():
    return render_template("notifmg.html")


@task.route("/addUser", methods=["POST"])
def add_user():
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    usertype = request.form["role"]

    # Insert the user into the database
    cmd.execute("INSERT INTO logintable (username, email, password, usertype) VALUES (%s, %s, %s, %s)", (username, email, password, usertype))
    con.commit()
    return "User added successfully!"

@task.route("/deleteUser", methods=["POST"])
def delete_user():
    username = request.form["username"]

    # Delete the user from the database
    cmd.execute("DELETE FROM logintable WHERE username = %s", (username))
    con.commit()

    return "User deleted successfully!"




task.run(debug=True)