import pymysql
from flask import Flask, request, jsonify

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


@app.route('/test', methods=['POST'])
def test():
    global dat
    val = request.get_data().decode()
    res = val.split(',')
    temperature = res[0]
    humidity = res[1]
    gas=res[2]
    noise=res[3]
    lat=res[4]
    long=res[5]
    print("temperature", temperature)
    print("humidity", humidity)
    print("gas", gas)
    print("noise", noise)
    print("lat", lat)
    print("long", long)


    # Pass values as a tuple for the placeholders
    query = "INSERT INTO readings (null, temp, hum, gas,noise,lat,long,curdate(),curtime()) VALUES (null, %s, %s, %s,%s,%s,%s)"
    cmd.execute(query, (temperature, humidity, gas,noise,lat,long))
    con.commit()

    result = "ok"
    if dat:
        result = dat
        dat = ""
    return result


app.run(port=5000, host='0.0.0.0')