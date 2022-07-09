#!/bin/sh
# RPi Irrigation Bypass Sensor - Developed by Aron Donaldson

cd /home/pi

# Retrieve user-specific values that will be written to the webexapp.service file for use with systemd
echo "Beginning setup. See https://github.com/miarond/RPi_Irrigation_Bypass_Sensor for full instructions."

# Update service file with creds using 'sed' to find & replace 'foo' and 'bar' placeholders with user's credentials.
sed -i "s/foo/$accessToken/" webexapp.service
sed -i "s/bar/$person/" webexapp.service

# Copy the service's unit file out to systemd, then register app as a service
sudo mv rain-sensor.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable rain-sensor.service

# Install external dependencies
sudo pip3 install -r requirements.txt

# Finally, reboot
echo "Install complete. Rebooting..."
sleep 5
sudo reboot now