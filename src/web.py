import pymysql as pymysql
from flask import *
from werkzeug.utils import secure_filename

task = Flask(__name__)
task.secret_key = "abc"
con =pymysql.connect(host="localhost", user="root", password="root", port=3306, db="smartcitydb",charset='utf8')
cmd = con.cursor()

@task.route('/')
def login():
    return render_template('login.html')

@task.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ------------------------------------------------ LOgin And Signup ---------------------------------------------
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
@task.route("/dashboard")
def dashboard():
    if session.get("logid") is not None:
        cmd.execute("SELECT AVG(temp) as avg_temp,AVG(hum) as avg_hum,CAST(date AS DATE) as date1 FROM readings GROUP BY CAST(date AS DATE)")
        data = cmd.fetchall()
        return render_template("dashboard.html",trenddata=data)
    else :
        return redirect("/")

# ---------------------------------------------------- Map ------------------------------------------------------------
@task.route('/map')
def showHeatmap():
    return render_template('map.html')



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