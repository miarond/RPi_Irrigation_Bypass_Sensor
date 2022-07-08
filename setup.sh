#!/bin/sh
# RPi Irrigation Bypass Sensor - Developed by Aron Donaldson

cd /home/pi

# Retrieve user-specific values that will be written to the webexapp.service file for use with systemd
echo "Beginning setup. See https://github.com/miarond/RPi_Irrigation_Bypass_Sensor for full instructions."

# Download script files
wget -O webexapp.py https://raw.githubusercontent.com/miarond/Webex_Status_Light/main/webexapp.py
wget -O webexapp.service https://raw.githubusercontent.com/miarond/Webex_Status_Light/main/webexapp.service
wget -O ledclean.py https://raw.githubusercontent.com/miarond/Webex_Status_Light/main/ledclean.py
wget -O rgbtest.py https://raw.githubusercontent.com/miarond/Webex_Status_Light/main/rgbtest.py

# Update service file with creds using 'sed' to find & replace 'foo' and 'bar' placeholders with user's credentials.
sed -i "s/foo/$accessToken/" webexapp.service
sed -i "s/bar/$person/" webexapp.service

# Copy the service's unit file out to systemd, then register app as a service
sudo mv webexapp.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable webexapp.service

# Install external dependencies
sudo pip3 install webexteamssdk
sudo pip3 install RPi.GPIO

# Finally, reboot
echo "Install complete. Rebooting..."
sleep 5
sudo reboot now