# import pdb; pdb.set_trace()
import os
import sys
import json
import logging
import requests
import datetime as dt
import smtplib
from dotenv import load_dotenv
from tinydb import TinyDB, where

load_dotenv()

def log_setup():
    log_level = os.getenv('RAIN_SENSOR_LOG', 'INFO').lower()
    log_format = '%(asctime)s - %(levelname)s: %(message)s'
    date_format = '%c'
    if log_level in ['debug', 'info', 'warning', 'error', 'critical']:
        if log_level == 'debug':
            logging.basicConfig(format=log_format, datefmt=date_format, stream=sys.stdout, level=logging.DEBUG)
        elif log_level == 'info':
            logging.basicConfig(format=log_format, datefmt=date_format, stream=sys.stdout, level=logging.INFO)
        elif log_level == 'warning':
            logging.basicConfig(format=log_format, datefmt=date_format, stream=sys.stdout, level=logging.WARNING)
        elif log_level == 'error':
            logging.basicConfig(format=log_format, datefmt=date_format, stream=sys.stdout, level=logging.ERROR)
        else:
            logging.basicConfig(format=log_format, datefmt=date_format, stream=sys.stdout, level=logging.CRITICAL)
    else:
        print('Logging level set to invalid value; defaulting to INFO.')
        logging.basicConfig(format=log_format, datefmt=date_format, stream=sys.stdout, level=logging.INFO)
    logging.info(f'Logging set to level: {log_level}')
    return

log_setup()

db = TinyDB(os.getenv('OWM_DB_FILE', 'db.json'))
logging.info(f'Opened DB {os.getenv("OWM_DB_FILE", "db.json")}')
logging.debug(f'Old DB data: {db.all()}')
db.drop_tables()
logging.info('Flushed old DB data.')


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
    old_forecast = db.search(where('forecast_data').exists())
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
logging.debug(f'Global variables: {globals()}')


def current_utc():
    return dt.datetime.now(dt.timezone.utc)


def convert_dt_string(input):
    return dt.datetime.fromisoformat(input)


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
    logging.debug(f'{result.headers}')
    logging.debug(f'{result.json()}')
    if result.status_code != 200:
        logging.error(f'API error encountered, code: {result.status_code}.')
        logging.error(f'Response: {result.text}')
        sys.exit(1)
    else:
        return result.json()


def eval_forecast(data):
    forecast_list = []
    irr_state = True
    for forecast in data['list'][0:intervals]:
        forecast_list.append([forecast['pop'], f'{forecast["dt_txt"]} +0000'])
        if forecast['pop'] > precip_thresh:
            irr_state = False
        logging.info(f'Forecast Interval: {forecast["dt_txt"]} UTC')
        logging.info(f'Forecast Probability of Precipitation: {100 * forecast["pop"]}%')
    db.insert({'forecast_data': forecast_list})
    logging.debug(f'Inserting forecast data into DB: {forecast_list}')
    return irr_state


def eval_override_logic(irr_state):
    # params irr_state: Boolean settings for state of Normally Closed Relay
    # return irr_state: Evaluated and possibly updated state setting
    # Evaluates whether rain has occurred within 12 hours of the next irrigation event, sets status accordingly
    # If evaluated forecast calls for rain and irrigation should be bypassed, proceed.
    if irr_state is False:
        return irr_state

    # Get current UTC time
    time_now = dt.datetime.now(dt.timezone.utc)

    # Check if this is even or odd day
    if irr_even_odd is None: # If NO even/odd scheduling specified (if we irrigate every day), proceed
        # Check if irrigation hour has passed
        if time_now.hour < irr_hour:
            # Check for old forecast data, evalute if it rained during the last stored forecast
            if old_forecast is not None:
                for item in old_forecast:
                    dt_stamp = convert_dt_string(item[1])
                    time_now = current_utc()
                    delta = (time_now - dt_stamp).seconds
                    # Check if precip_threshold was crossed and if the time of that forecast event was less than 12 hours ago
                    if int(item[0]) >= precip_thresh and delta <= 43200:
                        logging.info(f'Overriding irrigation status based on old forecast data: {item}(UTC)')
                        return False
                return True
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
                        dt_stamp = convert_dt_string(item[1]) 
                        time_now = current_utc()
                        delta = (time_now - dt_stamp).seconds
                        # Check if precip_threshold was crossed and if the time of that forecast event was less than 12 hours ago
                        if int(item[0]) >= precip_thresh and delta <= 43200:
                            logging.info(f'Overriding irrigation status based on old forecast data: {item}(UTC)')
                            return False
                    return True
                else:
                    return irr_state
            else:
                return irr_state
        else:
            logging.warning(f'Today is not an irrigation day, bypass logic was skipped.')
            return irr_state


def db_set_irr_state(irr_state):
    date_time = str(dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f %z"))
    result = [irr_state, date_time]
    db.insert({'irr_state': result})
    logging.debug(f'Forecast bypass state result: {result}')


def change_sensor_state(irr_state):
    # params irr_state: Boolean setting for state of Normally Closed Relay
    # return Boolean: True if successful, False if unsuccessful
    
    # Check the Relay Normally Open state; 0 is off (irrigation on), 1 is on (irrigation off)
    # current = rain_sensor.check_state(rain_sensor.relay_no)
    base_url = f'http://{os.getenv("FLASK_RUN_HOST")}:{os.getenv("FLASK_RUN_PORT")}'
    check_url = f'{base_url}/check-state'
    change_url = f'{base_url}/change-state'

    global current
    current = check_api(check_url)
    if irr_state:
        if current == 'ON':
            return True
        elif current == 'OFF':
            current = change_api(change_url, True)
            if current == 'ON':
                return True
            else:
                logging.critical(f'Relay state failed to change, current state is: {current}')
                return False
        else:
            logging.critical(f'Relay state failed to change, current state is: {current}')
            return False
    else:
        if current == 'ON' or current == 'UNKNOWN':
            current = change_api(change_url, False)
            if current == 'ON' or current == 'UNKNOWN':
                logging.critical(f'Relay state failed to change, current state is: {current}')
                return False
            else:
                return True
        else:
            return True


def check_api(url):
    response = requests.get(url)
    if response.status_code != 200:
        logging.error(f'Check State REST API call to sensor failed with code {response.status_code}: {response.text}')
        sys.exit(1)
    else:
        return response.text


def change_api(url, state):
    payload = {"status": state}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    if response.status_code != 200:
        logging.error(f'Change State REST API call to sensor failed with code {response.status_code}: {response.text}')
        sys.exit(1)
    else:
        return response.text


def send_email(override_state, bypass_result):
    # Skip sending email if nothing has changed, and no relay change failure is detected
    if (current == 'ON' and override_state is True) or (current == 'OFF' and override_state is False):
        logging.info(f'No change between requested state ({override_state}) and current state ({current}).')
        logging.info(f'Bypass result was: {bypass_result}')
        return
        
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    try:
        smtp.starttls()
    except Exception as e:
        logging.warning(f'SMTP StartTLS failed: {e}')
        return
    try:
        smtp.login(os.getenv('OWM_GMAIL_USER'), os.getenv('OWM_GMAIL_APP_PASSWORD'))
    except Exception as e:
        logging.warning(f'SMTP Login failed: {e}')
        return
    forecast = db.search(where('forecast_data').exists())[0]['forecast_data']
    message = f'Subject: Irrigation Bypass Results\n\n' \
        f'Forecast-predicted irrigation state: {irr_state}\n' \
        f'Evaluated override irrigation state: {bypass_result}\n\n' \
        f'Forecast weather data was: \n{json.dumps(forecast, indent=4)}'
    for dest in json.loads(os.getenv('OWM_GMAIL_RECIPIENT')):
        send_result = smtp.sendmail(os.getenv('OWM_GMAIL_USER'), dest, message)
        logging.info(f'Email send result was: {send_result}')
    smtp.close()
    return


if __name__ == '__main__':
    data = get_forecast()
    irr_state = eval_forecast(data)
    override_state = eval_override_logic(irr_state)
    # If state is False, disable irrigation is requested
    if not override_state:
        logging.info(f'**** Irrigation Bypass Requested ****')
    else:
        logging.info(f'**** Irrigation Enable Requested ****')
    db_set_irr_state(override_state)
    result = change_sensor_state(override_state)
    if result:
        logging.info(f'#### Irrigation State Changed ####')
    else:
        logging.info(f'!!!! Irrigation State Failed To Change !!!!')
    send_email(override_state, result)
    db.close()
