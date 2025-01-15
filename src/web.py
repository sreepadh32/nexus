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
         return render_template('dash.html')


task.run(debug=True)