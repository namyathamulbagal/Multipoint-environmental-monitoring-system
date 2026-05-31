from flask import Flask, request, render_template_string, jsonify
import csv
import os
import time
import threading
from datetime import datetime

app = Flask(__name__)
filename = "new4.csv" #Name of the excel file(to be changed for each experiment)

ESP_IDS = ["environment","hum_inlet", "hum_outlt", "post_proximal", "y_piece"]

LOG_INTERVAL = 6          # Fixed logging interval
LAG_THRESHOLD = 12        # If no data for 12 sec then it is lagging

# -----------------------
# Store latest readings
# -----------------------
latest_data = {
    sensor: {
        "temp": None,
        "hum": None,
        "pc_time": "--",
        "last_seen": 0
    }
    for sensor in ESP_IDS
}

# -----------------------
# Initialize CSV
# -----------------------
if not os.path.exists(filename):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        header = ["PC_Time"]
        for sensor in ESP_IDS:
            header += [
                f"{sensor}_Temp",
                f"{sensor}_Hum",
                f"{sensor}_Status"
            ]
        writer.writerow(header)

# -----------------------
# 6 SECOND PERIODIC LOGGER
# -----------------------
def periodic_logger():
    while True:
        time.sleep(LOG_INTERVAL)

        pc_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [pc_time]

        for s in ESP_IDS:
            time_gap = time.time() - latest_data[s]["last_seen"]

            if time_gap > LAG_THRESHOLD:
                row += ["NaN", "NaN", 0]   # 0 = Lagging
            else:
                row += [
                    latest_data[s]["temp"],
                    latest_data[s]["hum"],
                    1                      # 1 = Healthy
                ]

        with open(filename, mode='a', newline='') as file:
            csv.writer(file).writerow(row)

        print("Logged snapshot:", pc_time)

threading.Thread(target=periodic_logger, daemon=True).start()

# -----------------------
# DASHBOARD
# -----------------------
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Sensor Parameters Monitor</title>

<style>
body {
    font-family: Arial, sans-serif;
    text-align: center;
    background: #eef2f3;
    margin: 0;
    padding: 20px;
}

h1 {
    margin-bottom: 40px;
}

/* Container for all cards */
.container {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 30px;
    max-width: 1200px;
    margin: 0 auto;
}

/* Individual card */
.card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    width: 240px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.1);
    transition: 0.3s ease;
}

.card h3 {
    margin-top: 0;
    text-transform: capitalize;
}

.value {
    font-size: 1.9em;
    font-weight: bold;
    margin: 8px 0;
}

/* Status styles */
.ok {
    border: 3px solid #2ecc71;
}

.lag {
    border: 3px solid #e74c3c;
}

.status {
    font-weight: bold;
    margin-top: 10px;
    font-size: 1.1em;
}
</style>

<script>
function updateUI(){
    fetch('/ui_data')
    .then(res => res.json())
    .then(data => {
        for(let id in data){

            document.getElementById("temp-"+id).innerHTML =
                data[id].temp ?? "--";

            document.getElementById("hum-"+id).innerHTML =
                data[id].hum ?? "--";

            document.getElementById("time-"+id).innerHTML =
                data[id].pc_time ?? "--";

            let card = document.getElementById("card-"+id);
            let status = document.getElementById("status-"+id);

            if(data[id].lagging){
                card.className = "card lag";
                status.innerHTML = "LAGGING";
                status.style.color = "red";
            } else {
                card.className = "card ok";
                status.innerHTML = "OK";
                status.style.color = "green";
            }
        }
    });
}

setInterval(updateUI, 2000);
window.onload = updateUI;
</script>

</head>

<body>

<h1>Temperature & Humidity Logger</h1>

<div class="container">
{% for sensor in ESP_IDS %}
    <div class="card" id="card-{{sensor}}">
        <h3>{{sensor}}</h3>
        <div class="value">
            <span id="temp-{{sensor}}">--</span> °C
        </div>
        <div class="value">
            <span id="hum-{{sensor}}">--</span> %
        </div>
        <p>Last Update: <span id="time-{{sensor}}">--</span></p>
        <div class="status" id="status-{{sensor}}">--</div>
    </div>
{% endfor %}

</div>

</body>
</html>
"""
@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML, ESP_IDS=ESP_IDS)

@app.route('/ui_data')
def ui_data():
    response = {}

    for s in ESP_IDS:
        lagging = (time.time() - latest_data[s]["last_seen"]) > LAG_THRESHOLD

        response[s] = {
            "temp": latest_data[s]["temp"],
            "hum": latest_data[s]["hum"],
            "pc_time": latest_data[s]["pc_time"],
            "lagging": lagging
        }

    return jsonify(response)


# -----------------------
# RECEIVE DATA
# -----------------------
@app.route('/data', methods=['POST'])
def receive_data():
    try:
        content = request.get_json(force=True)
        sid = content.get("esp_id")

        if sid not in ESP_IDS:
            return "Invalid ESP ID", 400

        temp = float(content.get("temperature"))
        hum = float(content.get("humidity"))

        # Clamp humidity
        hum = max(0, min(100, hum))

        latest_data[sid].update({
            "temp": round(temp,2),
            "hum": round(hum,2),
            "pc_time": datetime.now().strftime("%H:%M:%S"),
            "last_seen": time.time()
        })

        return "OK", 200

    except Exception as e:
        return str(e), 500

# -----------------------
if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000, debug=False)






