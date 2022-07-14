#!/bin/sh
# RPi Irrigation Bypass Sensor - Developed by Aron Donaldson

cd /home/pi

# Retrieve user-specific values that will be written to the webexapp.service file for use with systemd
echo "Beginning setup. See https://github.com/miarond/RPi_Irrigation_Bypass_Sensor for full instructions."

# Install external dependencies
echo "Installing Python dependencies..."
sudo pip3 install -r requirements.txt

# Install and setup Linux utilities
echo "Installing Linux utilities..."
sudo apt-get install wiringpi mlocate python3.9 python3-pip -y
sudo updatedb

# Set up crontab for Forecast script
echo "Setting up cron job to run the forecast.py script. You will need to configure the scheduled hours (in 24hr format) \
when the script should run. Here is an example crontab line that will run the Forecast script every day, every 6 hours: 

0 0,6,12,18 * * * sudo /usr/bin/python3 /home/pi/rain_sensor/forecast.py

The format for this config line is: [minute] [hour (0-23)] [day of month (1-31)] [month (1-12)] [day of week (0-6)] [command to run]"
read -p "Press Enter key to continue."
crontab -e

# Copy the service's unit file out to systemd, then register app as a service
sudo mv rain-sensor.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable rain-sensor.service

# Finally, reboot
echo "Install complete. Rebooting..."
sleep 5
sudo reboot now