# RPi_Irrigation_Bypass_Sensor
A project using a Raspberry Pi board and Python, which checks the upcoming weather forecast for rain and can enable a bypass on your irrigation controller.

## Raspberry Pi Setup


### Utilities
1. Install the `wiringpi` utility using the command `sudo apt-get install wiringpi`.  
  1.1. This allows you to run the bash command `gpio readall` to get a current status of the GPIO header pins.