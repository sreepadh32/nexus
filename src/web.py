import pymysql as pymysql
from flask import *
from werkzeug.utils import secure_filename

task = Flask(__name__)
task.secret_key = "abc"
con =pymysql.connect(host="localhost", user="root", password="root", port=3307, db="smartcitydb",charset='utf8')
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


# ------Dash -----
@task.route('/dash')
def dashboard():
    return render_template('dash.html')
    
# ---------- Map ----------------
@task.route('/map')
def showHeatmap():
    return render_template('map.html')

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