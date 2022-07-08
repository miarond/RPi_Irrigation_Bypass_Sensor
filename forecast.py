import os
import sys
import logging
import requests
import datetime as dt
from dotenv import load_dotenv

load_dotenv()

err_state = False
appid = os.getenv('OWM_APPID')
units = os.getenv('OWM_UNITS', 'imperial') #'standard', 'metric', or 'imperial'
lat = os.getenv('OWM_LAT')
lon = os.getenv('OWM_LON')
intervals = int(os.getenv('OWM_3H_INTERVALS', '8'))
cnt = os.getenv('OWM_CNT', '40')
base_url = os.getenv('OWM_URL', 'https://api.openweathermap.org/')
irr_hour = int(os.getenv('OWN_IRR_HOUR', '0'))

try:
    precip_thresh = float(os.getenv('OWM_THRESHOLD'))
except Exception:
    precip_thresh = 0.50 #Assigning default value upon exception

for item in [appid, lat, lon]:
    if item is None:
        logging.critical(f'Environment Variable OWM_{item}.upper() is required.')
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
    logging.debug(f'{result.headers}\n')
    logging.debug(f'{result.json()}\n')
    if result.status_code != 200:
        logging.error(f'API error encountered, code: {result.status_code}.\n')
        logging.error(f'Response: {result.text}\n')
        return None
    else:
        return result.json()


def eval_forecast(data):
    if data is None:
        return False
    
    forcast_list = []
    for forecast in data['list'][0:intervals]:
        forcast_list.append([forecast['pop'], forecast['dt_txt']])
        if forecast['pop'] > precip_thresh:
            logging.info(f'Forecast Interval: {forecast["dt_txt"]} UTC\n')
            logging.info(f'Forecast Probability of Precipitation: {100 * forecast["pop"]}%\n')
            return True
        else:
            logging.info(f'Forecast Interval: {forecast["dt_txt"]} UTC\n')
            logging.info(f'Forecast Probability of Precipitation: {100 * forecast["pop"]}%\n')
    return False


def set_bypass_env(bypass):
    result = f'[{bypass}, {dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")}]'
    os.environ['OWM_BYPASS'] = result




if __name__ == '__main__':
    data = get_forecast()
    bypass = eval_forecast(data)
    if bypass:
        logging.info('******** Irrigation Bypass Enabled! ********\n')
