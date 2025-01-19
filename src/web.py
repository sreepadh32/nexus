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
# ------------- LOgin And Signup
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