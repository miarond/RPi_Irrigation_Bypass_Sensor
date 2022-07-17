import os
import logging
import time
from flask import Flask, render_template, request
import rain_sensor
from tinydb import TinyDB, where
from tabulate import tabulate

host = os.getenv('FLASK_APP_HOST', '0.0.0.0')
port = int(os.getenv('FLASK_APP_PORT', '80'))
rain_sensor.gpio_setup()
app = Flask(__name__)

logging.debug(f'GPIO Pins: signal={rain_sensor.signal}, relay_no={rain_sensor.relay_no}')

def log_setup(log_level):
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%c')
    if log_level in ['debug', 'info', 'warning', 'error', 'critical']:
        if log_level == 'debug':
            logging.basicConfig(level=logging.DEBUG)
        elif log_level == 'info':
            logging.basicConfig(level=logging.INFO)
        elif log_level == 'warning':
            logging.basicConfig(level=logging.WARNING)
        elif log_level == 'error':
            logging.basicConfig(level=logging.ERROR)
        else:
            logging.basicConfig(level=logging.CRITICAL)
    else:
        print('Logging level set to invalid value; defaulting to ERROR.\n')
        logging.basicConfig(level=logging.ERROR)


@app.route("/", methods=["GET"])
def index():
    logging.debug('Rendering index.html template.')
    return render_template("index.html")


@app.route("/change-state", methods=["POST"])
def change_state():
    requested_status = request.json.get('status')
    logging.info(f'Requested status is: {requested_status}')
    if requested_status is False:
        rain_sensor.set_relay_no_state(True)
    else:
        rain_sensor.set_relay_no_state(False)
    time.sleep(0.1)
    state = rain_sensor.check_state(rain_sensor.relay_no)
    logging.debug(f'Current relay state for NO pin: {state}')
    if state == 0:
        return 'OFF'
    elif state == 1:
        return 'ON'
    else:
        logging.error('Returned state for relay NO pin was UNKNOWN!')
        return 'UNKNOWN'


@app.route("/check-state", methods=["GET"])
def check_state():
    state = rain_sensor.check_state(rain_sensor.relay_no)
    logging.debug(f'Current NO relay state is: {state}')
    if state == 0:
        # Relay is in NO state, irrigation is off
        return 'OFF'
    elif state == 1:
        # Relay is in NC state, irrigation is on
        return 'ON'


@app.route("/forecast", methods=["GET"])
def forecast_data():
    db = TinyDB('db.json')
    forecast = db.search(where('forecast_data').exists())[0]['forecast_data']
    state = db.search(where('irr_state').exists())[0]['irr_state']
    db.close()
    
    # Convert to percentage
    if len(forecast) > 0:
        result = f'<b>State: </b>{state[0]}</br><b>Date/Time: </b>{state[1]}</br>(Times are in UTC timezone)</br></br>'
        for item in forecast:
            item[0] = item[0] * 100
            #result.append(item)
    else:
        return ''
    data = tabulate(forecast, tablefmt='html', headers=['Precip %', 'Date/Time'], numalign='left', stralign='left')
    result = result + data
    return result


if __name__ == "__main__":
    log_setup(os.getenv('RAIN_SENSOR_LOG', 'ERROR').lower())
    app.run(host=host, port=port, load_dotenv=True)
