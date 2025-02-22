import pymysql
from flask import*
dat = ""
data = ""
app = Flask(__name__)

con = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    port=3306,
    db='roadsafety',
    charset='utf8'
)

cmd = con.cursor()



@app.route('/')
def readings():
    # Execute first query
    # cmd.execute("SELECT * FROM readings ORDER BY id DESC LIMIT 1")
    # row = cmd.fetchone()  # Fetch the last entry of readings
    #
    # # Execute second query
    # cmd.execute("SELECT * FROM alert ORDER BY id DESC LIMIT 1")
    # row1 = cmd.fetchone()
    # print(row1)# Fetch the last entry of alert
    # if row:
    #     result = {
    #         "id": row[0],
    #         "depth": row[1],  # Depth is row[1]
    #         "latitude": row[2],  # Latitude is row[2]
    #         "longitude": row[3],
    #         "speed":row1[1]# Longitude is row[3]
    #     }
    # else:
    #     result = None  # If no data exists
    #
    # return render_template("map.html", value=result)
    return render_template("mapajax.html")

#
@app.route('/latest_readings')
def latest_readings():


    # Fetch latest pothole reading
    cmd.execute("SELECT * FROM readings ORDER BY id DESC LIMIT 1")
    row = cmd.fetchone()
    print((row))

    # Fetch latest alert (speed)
    cmd.execute("SELECT * FROM alert ORDER BY id DESC LIMIT 1")
    row1 = cmd.fetchone()
    print(row1)

    # conn.close()

    if row and row1:
        result = {
            "id": row[0],
            "depth": row[1],
            "latitude": row[2],
            "longitude": row[3],
            "speed": row1[1]
        }
    else:
        result = None  # If no data exists

    return jsonify(result)  #
app.run(port=5000,host='0.0.0.0')