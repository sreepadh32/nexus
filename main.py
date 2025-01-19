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
    gas = res[2]
    noise = res[3]

    print("temperature:", temperature)
    print("humidity:", humidity)
    print("gas:", gas)
    print("noise:", noise)

    # Insert data into the database
    query = "INSERT INTO readings (temp, hum, gas, noise, date, time) VALUES (%s, %s, %s, %s, CURDATE(), CURTIME())"
    cmd.execute(query, (temperature, humidity, gas, noise))
    con.commit()

    result = "ok"
    if dat:
        result = dat
        dat = ""
    return result

if __name__ == "__main__":
    app.run(port=5000, host='0.0.0.0')
