import os
import logging
import time
from flask import Flask, render_template, request
import rain_sensor

host = os.getenv('FLASK_APP_HOST', '0.0.0.0')
port = int(os.getenv('FLASK_APP_PORT', '80'))
rain_sensor.gpio_setup()
app = Flask(__name__)

logging.debug(f'GPIO Pins: signal={rain_sensor.signal}, relay_no={rain_sensor.relay_no}\n')

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
    logging.debug('Rendering index.html template.\n')
    return render_template("index.html")


@app.route("/change-state", methods=["POST"])
def change_state():
    requested_status = request.json.get('status')
    logging.info(f'Requested status is: {requested_status}\n')
    if requested_status is False:
        rain_sensor.set_relay_no_state(True)
    else:
        rain_sensor.set_relay_no_state(False)
    time.sleep(0.1)
    state = rain_sensor.check_state(rain_sensor.relay_no)
    logging.debug(f'Current relay state for NO pin: {state}\n')
    if state == 0:
        return 'OFF'
    elif state == 1:
        return 'ON'
    else:
        logging.error('Returned state for relay NO pin was UNKNOWN!\n')
        return 'UNKNOWN'


@app.route("/check-state", methods=["GET"])
def check_state():
    state = rain_sensor.check_state(rain_sensor.relay_no)
    logging.debug(f'Current NO relay state is: {state}\n')
    if state == 0:
        # Relay is in NO state, irrigation is off
        return 'OFF'
    elif state == 1:
        # Relay is in NC state, irrigation is on
        return 'ON'


if __name__ == "__main__":
    log_setup(os.getenv('RAIN_SENSOR_LOG', 'ERROR').lower())
    app.run(host=host, port=port, load_dotenv=True)