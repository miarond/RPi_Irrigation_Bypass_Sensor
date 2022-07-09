import os
import time
import logging

import RPi.GPIO as gpio

signal = int(os.getenv('RAIN_SENSOR_SIGNAL_PIN', '4'))
relay_no = int(os.getenv('RAIN_SENSOR_RELAY_NO_PIN', '23'))

def gpio_setup():
    # Use Broadcom pinout
    gpio.setwarnings(False)
    gpio.setmode(gpio.BCM)
    gpio.cleanup((signal, relay_no))
    logging.debug('Setting GPIO mode to BCM.\n')
    # Setup relay signal pin as 3.3v output
    gpio.setup(signal, gpio.OUT)
    logging.debug(f'Setting GPIO BCM pin {signal} to Output mode.\n')
    # Setup relay Normally Open pin as input with small voltage signal (False = open circuit, True = closed circuit)
    gpio.setup(relay_no, gpio.IN, pull_up_down=gpio.PUD_UP)
    logging.debug(f'Setting GPIO BCM pin {relay_no} to Input mode with Pull-Up-Down set to UP.\n')


def set_relay_no_state(state):
    logging.info(f'Requesting Relay Normally Open (NO) state set to {state}.\n')
    if state:
        gpio.output(signal, True)
    else:
        gpio.output(signal, False)
    logging.info(f'Signal pin ({signal}) state is: {gpio.input(signal)} (0 is Off/Low, 1 is On/High)\n')


def check_state(pin):
    state = gpio.input(pin)
    logging.info(f'Checking state for pin {pin}; state is {state}\n')
    return state


def cleanup():
    logging.info('Requesting GPIO cleanup.\n')
    gpio.cleanup()