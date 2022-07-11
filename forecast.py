import os
import sys
import json
import logging
import requests
import datetime as dt
import rain_sensor
from dotenv import load_dotenv

load_dotenv()
log_level = os.getenv('RAIN_SENSOR_LOG', 'INFO')

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

appid = os.getenv('OWM_APPID')
units = os.getenv('OWM_UNITS', 'imperial') #'standard', 'metric', or 'imperial'
lat = os.getenv('OWM_LAT')
lon = os.getenv('OWM_LON')
intervals = int(os.getenv('OWM_3H_INTERVALS', '8'))
cnt = os.getenv('OWM_CNT', '40')
base_url = os.getenv('OWM_URL', 'https://api.openweathermap.org/')
irr_hour = int(os.getenv('OWN_IRR_HOUR', '0'))
relay_no = int(os.getenv('RAIN_SENSOR_RELAY_NO_PIN', '23'))
try:
    old_forecast = json.loads(os.getenv('OWM_FORECAST_DATA', None))
except Exception:
    old_forecast = None
try:
    irr_even_odd = int(os.getenv('OWM_IRR_EVEN_ODD'))
except (TypeError, ValueError):
    irr_even_odd = None


try:
    precip_thresh = float(os.getenv('OWM_THRESHOLD'))
except Exception:
    precip_thresh = 0.50 #Assigning default value upon exception

for item in [appid, lat, lon]:
    if item is None:
        logging.critical(f'Environment Variable OWM_{item}.upper() is required.')
        sys.exit(1)

def get_forecast():
    api_endpoint = 'data/2.5/forecast'
    query_params = {
        'appid': appid,
        'units': units,
        'lat': lat,
        'lon': lon,
        'cnt': cnt
    }
    result = requests.get(base_url + api_endpoint, params=query_params)
    logging.debug(f'{result.headers}\n')
    logging.debug(f'{result.json()}\n')
    if result.status_code != 200:
        logging.error(f'API error encountered, code: {result.status_code}.\n')
        logging.error(f'Response: {result.text}\n')
        sys.exit(1)
    else:
        return result.json()


def eval_forecast(data):
    forecast_list = []
    for forecast in data['list'][0:intervals]:
        irr_state = True
        forecast_list.append([forecast['pop'], forecast['dt_txt']])
        if forecast['pop'] > precip_thresh:
            logging.info(f'Forecast Interval: {forecast["dt_txt"]} UTC\n')
            logging.info(f'Forecast Probability of Precipitation: {100 * forecast["pop"]}%\n')
            irr_state = False
        else:
            logging.info(f'Forecast Interval: {forecast["dt_txt"]} UTC\n')
            logging.info(f'Forecast Probability of Precipitation: {100 * forecast["pop"]}%\n')
    os.environ['OWM_FORECAST_DATA'] = str(forecast_list)
    if not irr_state:
        return False
    else:
        return True


def eval_bypass_logic(irr_state):
    # params irr_state: Boolean settings for state of Normally Closed Relay
    # return irr_state: Evaluated and possibly updated state setting
    # Evaluates whether rain has occurred within 12 hours of the next irrigation event, sets status accordingly
    time_now = dt.datetime.now()
    
    # If evaluated forecast calls for rain and irrigation should be bypassed, proceed.
    if irr_state is False:
        return irr_state

    # Check if this is even or odd day
    if irr_even_odd is None: # If NO even/odd scheduling specified (if we irrigate every day), proceed
        # Check if irrigation hour has passed
        if time_now.hour < irr_hour:
            # Check for old forecast data, evalute if it rained during the last stored forecast
            if old_forecast is not None:
                for item in old_forecast:
                    if int(item[0]) >= precip_thresh:
                        logging.info(f'Overriding irrigation status based on old forecast data: {item}(UTC)\n')
                        return False
            else:
                return irr_state
        else:
            return irr_state
    else:
        # If we're on an irrigation day, check if irrigation hour has passed
        if time_now.day % 2 == irr_even_odd:
            if time_now.hour < irr_hour:
                # Check for old forecast data, evalute if it rained during the last stored forecast
                if old_forecast is not None:
                    for item in old_forecast:
                        if int(item[0]) >= precip_thresh:
                            logging.info(f'Overriding irrigation status based on old forecast data: {item}(UTC)\n')
                            return False
                else:
                    return irr_state
        else:
            logging.warning(f'ENV Variable "OWM_IRR_EVEN_ODD" is not set to 0 or 1. Bypass logic not applied.\n')
            return irr_state


def set_bypass_env(irr_state):
    result = f'[{irr_state}, {dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")}]'
    os.environ['OWM_BYPASS'] = result
    logging.debug(f'Forecast bypass state result: {result}\n')
    logging.info(f'Forecast bypass state ENV variable: {os.getenv("OWM_BYPASS")}\n')


def change_bypass_state(irr_state):
    # params irr_state: Boolean setting for state of Normally Closed Relay
    # return Boolean: True if successful, False if unsuccessful
    
    # Check the Relay Normally Open state; 0 is off (irrigation on), 1 is on (irrigation off)
    # current = rain_sensor.check_state(rain_sensor.relay_no)
    base_url = f'http://{os.getenv("FLASK_RUN_HOST")}:{os.getenv("FLASK_RUN_PORT")}'
    check_url = f'{base_url}/check-state'
    change_url = f'{base_url}/change-state'

    current = check_api(check_url)
    if irr_state:
        if current == 0:
            return True
        else:
            change_api(change_url, False)
            current = check_api(check_url)
            if current == 0:
                return True
            else:
                logging.critical(f'Relay state failed to change, current state is: {current}\n')
                return False
    else:
        if current == 0:
            change_api(change_url, True)
            current = check_api(check_url)
            if current == 0:
                logging.critical(f'Relay state failed to change, current state is: {current}\n')
                return False
            else:
                return True
        else:
            return True


def check_api(url):
    response = requests.get(url)
    if response.status_code != 200:
        logging.error(f'Check State REST API call to sensor failed with code {response.status_code}: {response.text}\n')
        sys.exit(1)
    else:
        return response.text


def change_api(url, state):
    payload = '{"status": {state}}'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=payload, headers=headers)
    if response.status_code != 200:
        logging.error(f'Change State REST API call to sensor failed with code {response.status_code}: {response.text}\n')
        sys.exit(1)
    else:
        return response.text


if __name__ == '__main__':
    log_setup()
    data = get_forecast()
    irr_state = eval_forecast(data)
    if not irr_state:
        logging.info(f'**** Irrigation Bypass Requested ****\n')
    else:
        logging.info(f'**** Irrigation Enable Requested ****\n')
    set_bypass_env(irr_state)
    result = change_bypass_state(irr_state)
    if result:
        logging.info(f'#### Irrigation State Changed ####\n')
    else:
        logging.info(f'!!!! Irrigation State Failed To Change !!!!\n')
