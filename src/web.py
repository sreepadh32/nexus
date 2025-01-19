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
# ------------- LOgin And Signup -------------
@task.route('/logincheck', methods=['post'])
def logincheck():
    user = request.form['email']
    psd = request.form['password']
    cmd.execute("select * from logintable where username='" + user + "' and password='" +psd+ "'")
    result = cmd.fetchone()
    if result is not None:
        usertype = result[3]
        if usertype == "admin":
            session['logid'] = result[0]
            return render_template('adminsettings.html')
        else:
            return redirect(url_for("login", error="Student Deletion Succesfull"))
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
    
# ---------- Map ----------------
@task.route('/map')
def showHeatmap():
    return render_template('map.html')

# ------------ Admin -----------
@task.route("/admin")
def Admin():
    return render_template("adminsettings.html")

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