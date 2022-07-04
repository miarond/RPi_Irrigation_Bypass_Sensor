import os
import time
import sys
import logging

import RPi.GPIO as gpio

log_level = os.getenv('RAIN_SENSOR_LOG', 'INFO').lower()
signal = int(os.getenv('RAIN_SENSOR_SIGNAL_PIN', '4'))
relay_no = int(os.getenv('RAIN_SENSOR_RELAY_NO_PIN', '23'))
api_key = os.getenv('RAIN_SENSOR_API_KEY', '')

# Use Broadcom pinout
gpio.setmode(gpio.BCM)
# Setup relay signal pin as 3.3v output
gpio.setup(signal, gpio.OUT)
# Setup relay Normall Open pin as input with small voltage signal (False = open circuit, True = closed circuit)
gpio.setup(relay_no, gpio.IN, pull_up_down=gpio.PUD_UP)

def log_setup(log_level):
    logging.basicConfig(format='%(asctime)s: %(message)s', datefmt='%c')
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
        sys.stderr.write('Logging level set to invalid value; defaulting to ERROR.\n')
        logging.basicConfig(level=logging.ERROR)


def set_relay_state(state):
    if state:
        gpio.output(signal, True)
    else:
        gpio.output(signal, False)
    logging.info(f'Signal pin ({signal}) state is: {gpio.input(signal)} (0 is Off/Low, 1 is On/High)\n')


def check_state(pin):
    return gpio.input(pin)

