import os
import sys
import re
import logging
from xml.dom.expatbuilder import FILTER_ACCEPT
from dotenv import load_dotenv
import requests

load_dotenv()

# def filter_appid(record):
#     msg = re.sub('appid=[A-Za-z0-9]+', 'appid=<<REDACTED>>', record)
#     return msg


if os.getenv('OWM_DEBUG', 'False').lower() == 'true':
    isdebug = True
else:
    isdebug = False

if isdebug:
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')  
else:
    pass
    logging.basicConfig(level=logging.CRITICAL, format='%(asctime)s - %(levelname)s - %(message)s')

err_state = False
appid = os.getenv('OWM_APPID')
units = os.getenv('OWM_UNITS', 'imperial') #'standard', 'metric', or 'imperial'
lat = os.getenv('OWM_LAT')
lon = os.getenv('OWM_LON')
intervals = int(os.getenv('OWM_3H_INTERVALS', '8'))
cnt = os.getenv('OWM_CNT', '40')
base_url = os.getenv('OWM_URL', 'https://api.openweathermap.org/')

try:
    precip_thresh = float(os.getenv('OWM_THRESHOLD'))
except Exception:
    precip_thresh = 0.50 #Assigning default value upon exception

for item in [appid, lat, lon]:
    if item is None:
        sys.stderr.write(f'Environment Variable OWM_{item}.upper() is required.')
        err_state = True
if err_state:
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
    if isdebug is True:
        logging.debug(f'{result.headers}\n')
        logging.debug(f'{result.json()}\n')
    if result.status_code != 200:
        sys.stderr.write(f'API error encountered, code: {result.status_code}.\n')
        sys.stderr.write(f'Response: {result.text}\n')
        return None
    else:
        return result.json()


def eval_forecast(data):
    if data is None:
        return False
    
    # if not isinstance(data, dict) or not isinstance(data['list'], list):
    #     return False
    
    for forecast in data['list'][0:intervals]:
        if forecast['pop'] > precip_thresh:
            sys.stdout.write(f'Forecast Interval: {forecast["dt_txt"]} UTC\n')
            sys.stdout.write(f'Forecast Probability of Precipitation: {100 * forecast["pop"]}%\n')
            return True
        else:
            sys.stdout.write(f'Forecast Interval: {forecast["dt_txt"]} UTC\n')
            sys.stdout.write(f'Forecast Probability of Precipitation: {100 * forecast["pop"]}%\n')
    return False


if __name__ == '__main__':
    data = get_forecast()
    bypass = eval_forecast(data)
    if bypass:
        sys.stdout.write('******** Irrigation Bypass Enabled! ********\n')
