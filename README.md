# RPi_Irrigation_Bypass_Sensor
A project using a Raspberry Pi board and Python, which checks the upcoming weather forecast for rain and can enable a bypass on your irrigation controller.

***A Note on Irrigation Systems:***  Not all irrigation controllers are created equal, nor do they all operate in the same way.  I have created this project based on a single example in my own home, which is the "Rain Bird ESP Modular" model.  This controller has a pair of "Sensor" electrical contacts inside, which are devoted to any external rain sensor you might want to connect.  The Rain Bird ESP Module controller sensor system operations on a "Normally Closed" architecture, meaning that the sensor contacts are part of a simple electrical circuit that is normally complete - i.e. the contacts are connected to each other and have continuity.  If the contacts are connected, the irrigation controller follows its normally programmed irrigation cycle.  If that circuit is "broken", it overrides the irrigation cycle programming and your irrigation system will NOT run.  **Please** research the documentation on your irrigation controller before attempting to use this project.  If your irrigation controller sensor system operates on a Normally Closed or Normally Open basis, this project *could* work - though if your controller requires a Normally Open configuration, you will need to swap the pinout on the Relay Output connectors from what is shown in this documentation.  Happy Irrigating!

# Table of Contents

1. [Parts List](#parts-list)
2. [Raspberry Pi Setup](#raspberry-pi-setup)
3. [Relay & Wiring Setup](#relay--wiring-setup)
    1. [Relay Board Preparation](#relay-board-preparation)
    2. [Rasbperry Pi Wiring](#raspberry-pi-wiring)
4. [OpenWeathermap API](#openweathermap-api)
5. [Environment Variables](#environment-variables)
6. [Software Installation](#software-installation)
7. [Web Application](#web-application)
    1. [Web Application Workflow](#web-application-workflow)
8. [Forecast Script](#forecast-script)
    1. [Forecast Script Workflow](#forecast-script-workflow)
9. [Troubleshooting](#troubleshooting)
10. [Directory Structure](#directory-structure)

## Parts List

<b><u>Parts to purchase:</u></b>
- Non-Latching Normally Closed Relay (available from Adafruit)
  - Any relay powered by 3.3v and capable of handling 20+ v DC should suffice.  Adafruit sells a pre-built PCB with relay that requires a minimal amount of soldering.
  - https://www.adafruit.com/product/2895
  - ![Image from www.adafruit.com](/assets/featherwing_relay.jpeg)
- Raspberry Pi Zero WH (Wireless with Headers pre-installed)
  - https://www.adafruit.com/product/3708
  - ![Image from www.adafruit.com](/assets/Pi_Zero_WH.jpeg)
- **OPTIONAL** Raspberry Pi Zero Case (comes with camera ribbon cable, not needed)
  - https://www.adafruit.com/product/3446
  - ![Image from www.adafruit.com](/assets/Pi_Zero_Case.jpeg)
- 16 or 32 GB Micro SDHC card
  - https://www.amazon.com/Sandisk-Ultra-Micro-UHS-I-Adapter/dp/B073K14CVB/
  - https://www.amazon.com/Samsung-MicroSDHC-Adapter-MB-ME32GA-AM/dp/B06XWN9Q99/
  - ![Image from www.sandisk.com](/assets/SDHC.jpeg)
- Female/Female and Female/Male Jumper Wires
  - https://www.amazon.com/dp/B07GD2BWPY?_encoding=UTF8&psc=1&ref_=cm_sw_r_cp_ud_dp_ZHHTD0E41EYNKNG6Z5N3
  - ![Image from www.amazon.com](/assets/jumper_wires.jpeg)
- **OPTIONAL** Splicing wire nuts or lever nuts
  - For combining Ground wires
- 2-wire electrical wire (18 - 22 gauge)
  - For connection to irrigation system

<b><u>Tools needed:</u></b>
- Soldering iron with fine-tipped point
- Low lead (60% tin/40% lead) small gauge rosin-core solder
- Small gauge wire stripper

<b><u>Bring your own:</u></b>
- Micro USB **data transfer** cable. Normally a standard smartphone cable will work as long as it is not a *charging only* cable.
  - ![Image from www.bestbuy.com](/assets/Micro_USB_Cable.jpeg)
- 5v USB charging block (minimum 1 Amp capacity)
- Windows or Mac laptop for SSH and SFTP file transfer
- SD Card reader (if you are creating the bootable SD card on your own)
- WPA2 wireless network with Pre-Shared Key, DHCP/DNS and Internet connectivity

## Raspberry Pi Setup

The Raspberry Pi computing platform most commonly runs a distribution of the Linux operating system, written for ARM processor architectures. In this case I am using the standard Debian Linux distribution recommended by the creators of the RPi. This comes in two versions: Desktop (has a GUI interface) and Lite (CLI only).  I am using the Lite version to save on system resources and because I intend to run the Pi in "**headless**" mode, without a keyboard, mouse or video display.  Let's get started!

1. Insert your Micro SD Card in a card reader and ensure that it is readable.
2. Visit the "Getting Started" guide and follow the instructions [here](https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up/2) to setup your SD card.
    - This requires downloading the Raspberry Pi Imager application, then choosing an installation image to download (you can also download the image manually and pick it from your local machine via the Imager app). **This guide assumes you are choosing the "Lite" version.**
3. Using the Imager application, write the image file to the SD card.
4. Once writing is complete you will need to remove and reinsert the SD card. Next, open the SD card in Finder or Windows Explorer. We will be creating two text files and editing two existing files in the root directory of the SD card, in order to pre-set some basic configuration parameters. The guide on Adafruit's website below mentions a folder named **boot** on the SD card - in testing on Windows I have found that the readable partition of the SD card is labeled **boot**, not a subdirectory on the SD card.
    - This setup process is known as "**headless**" mode and is really well documented on Adafruit's website [here](https://learn.adafruit.com/raspberry-pi-zero-creation).
    - The text file setup process is explained on [this](https://learn.adafruit.com/raspberry-pi-zero-creation/text-file-editing) page of the guide.
5. Create a *blank* text file called `ssh` - there should be **NO** file extension in the filename.  This file tells Debian to enable SSH access permanently on first bootup.
6. Create a text file named `wpa_supplicant.conf` and add the text below. MAKE SURE to replace `YOURSSID` and `YOURPASSWORD` with your actual wireless SSID and PSK (leave the "" surrounding your SSID and PSK). This pre-loads Debian with your wireless network info so it will automatically connect.
  ```
  ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
  update_config=1
  country=US

  network={
    ssid="YOURSSID"
    psk="YOURPASSWORD"
    scan_ssid=1
  }
  ```
7. Edit the `config.txt` file that already exists and add the following lines at the *bottom* of the file.  This setting allows you to use the USB cable for direct console access for emergency troubleshooting.
  ```
  # Enable UART
  enable_uart=1

  # Enable Ethernet over USB
  dtoverlay=dwc2
  ```
8. Edit the `cmdline.txt` file that already exists and add the text `modules-load=dwc2,g_ether` after `rootwait`. This file should contain a single line of text with no line breaks and the text you add should be separated from `rootwait` by a single space. The end result should look like this:
```
console=serial0,115200 console=tty1 root=PARTUUID=eabcf7ff-02 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait modules-load=dwc2,g_ether
```
  - More detailed instructions on how to utilize Ethernet over USB will be covered in the Testing and Troubleshooting section below.
9. Last but not least, safely eject the SD card from your computer.

## Relay & Wiring Setup

If you purchased the Adafruit Featherwing Non-Latching relay board, you will need to solder on a few components.  You will want to attach the 3-pin terminal block and you may want to attach header pins to the appropriate through holes.

### Relay Board Preparation

The non-latching relay on the Featherwing board works by applying 3.3v to one side of the relay switch, through a transistor.  The "Signal" pin activates the transistor when 3.3v is applied to it, and this completes the 3.3v --> Ground circuit.  When this circuit is completed, it powers an electromagnet inside the relay which actuates a larger switch (capable of handling much higher voltage and amperage).  The relay output has two states:

  - Normally Closed (NC): Always connected to "Common" (COM) when the relay is dormant - i.e. NOT activated.
  - Normally Open (NO): Always *dis*connected from "Common" (COM) when the relay is dormant.

1. If you haven't soldered on a Printed Circuit Board (PCB) before, review these resources to learn how: 
    1. https://youtu.be/QKbJxytERvg 
    2. https://learn.adafruit.com/adafruit-guide-excellent-soldering
    3. **NOTE:** The header pins on the PCB are arranged in two sets of matching rows, one on either side of the board.  Each parallel set of through holes is *connected* to the one directly next from it. Typically you will solder header pins to the outermost row and use the innermost row for cross-connecting other pins or through holes on the board.
2. Solder the 3-pin terminal block to the "NC", "COM", and "NO" through holes near the edge of the PCB.  Make sure the block is facing the correct direction, with the insert holes pointing away from the relay.
    1. ![Image from www.adafruit.com](/assets/feather_relayout.jpeg)
3. If you're going to solder header pins, connect them to AT LEAST the "3v" and "GND" through holes, below the "Reset" button.
    1. You may also want to connect the "Signal" through hole to one of the header through holes on the innermost rows - effectively cross-connecting it to one of the header pins you've soldered on.
    2. ![Image from www.adafruit.com](/assets/feather_relaysignal.jpeg)

### Raspberry Pi Wiring

On the Raspberry Pi, we will need to use the following GPIO pin types:

  - (1) 3.3v Power
  - (1) Ground
  - (2) GPIO signal pins

The 3.3v power and Ground pins will provide power to the actuation side of the Relay, one GPIO pin will provide 3.3v power (as needed) to the Relay Signal pin, and the other GPIO pin will track the Normally Open state of the Relay Output.  The Normally Open relay GPIO pin will supply a small amount of voltage at all times, in order to "read" whether the circuit is complete or not.  This gives us the ability to know with certainty - i.e. a sanity check - what the Relay Output state is at any given time.

Here is a sample wiring diagram that depicts one possible way to connect the relay to the Raspberry Pi.  Any set of pins which provide the right capabilities (i.e. power, ground, and GPIO signal) can be used:

![Wiring Diagram](/assets/wiring_diagram.png)

## OpenWeathermap API

This project makes use of the OpenWeathermap API to obtain local weather forecast data.  OpenWeathermap provides a free licensing tier that includes the "3-Hour Forecast 5 Days" API endpoint, which is what this script will use.  Create a free account by clicking on the "Get API Key" button under the Free column on this page: https://openweathermap.org/price  Once you've created your account, you will need to generate your API (called "app-id") key, and add it to the Environment Variable file described in the next section.  You will also need to obtain the Latitude and Longitude coordinates for your location, to a 2 decimal point precision (don't forget any negative (-) symbols for Longitude!) - this can easily be obtained from the Google Maps website.

An example of the API output is located [here](/assets/owm_api_output.json) for reference.  The API documentation can be found here:  https://openweathermap.org/forecast5

## Environment Variables

  - `OWM_UNITS`: Measurement system for units returned by API ("metric", "imperial", "standard")
  - `OWM_LAT`: Latitude for forecast location, measured to 2 decimal points (ex: 44.88)
  - `OWM_LON`: Longitude for forecast location, measured to 2 decimal points (ex: -93.22)
  - `OWM_APPID`: OpenWeathermap API key
  - `OWM_CNT`: Number of timestamps API should return; forecasts are 3 hour periods, so 8 timestamps would equal 24 hours.
  - `OWM_3H_INTERVALS`: Number of forecast intervals to be evaluated by the `forecast.py` script.  Default to 4 which makes the script evaluate 12 hours of forecast data.
  - `OWM_THRESHOLD`: Percentage of precipitation (rain) possibility that will trigger a bypass of the irrigation system.  This value is compared to the `pop` field in the API JSON output and is expressed as a decimal ratio between 0 and 1 (0 = 0%, 1 = 100%, 0.5 = 50%).
  - `OWM_URL`: OpenWeathermap API base URL; currently defaults to "https://api.openweathermap.org/"
  - `OWM_IRR_HOUR`: Hour of the day (expressed in 24h format) that your irrigation system is programmed to start running.  This is used by the `forecast.py` script to determine whether irrigation should be bypassed, based on the date/time stamp of forecast data.
  - `OWM_IRR_EVEN_ODD`: If your local regulations require you to irrigate on **only** even or odd days, set this value to 0 (for even days) or 1 (for odd days).  Leave blank if you irrigate every day.
  - `OWM_GMAIL_USER`: Gmail user account for sending alert emails.
  - `OWM_GMAIL_RECIPIENT`: Email recipients list for alert emails.  This **MUST** be expressed as a Python list in String format, such as this example: '["email1", "email2"]'  (Please note and emulate the placement of both single and double quotation marks)
  - `OWM_GMAIL_APP_PASSWORD`: Application password that you have generated for the sender Gmail account (you can not authenticate using the account's actual password - you MUST generate an application password).
  - `OWM_DB_FILE`: Name of the TinyDB database file used to store forecast data.  Default is 'db.json'.
  - `RAIN_SENSOR_HOST`: The local IP address of your Raspberry Pi board; used for the `flask run` command.  It is highly recommended NOT to set this value to: "0.0.0.0"
  - `RAIN_SENSOR_PORT`: The local port that Flask should bind to when running the applicaiton.  This should always be set to "80".  If you change this port, you may need to alter the `app.py` and/or `forecast.py` scripts to accomodate the change.
  - `RAIN_SENSOR_LOG`:  Logging level for the Python application and `forecast.py` script.  Valid values are: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - `RAIN_SENSOR_SIGNAL_PIN`: GPIO pin connected to the "Signal" pin on the relay board, using the Broadcom (BCM) Pinout mode (see wiring diagram or search Google for details).
  - `RAIN_SENSOR_RELAY_NO_PIN`: GPIO pin connected to the "Normally Open" relay output on the relay board, using the Broadcom (BCM) Pinout mode.

## Software Installation
In this section we'll begin the installation and setup process. We'll start by verifying that Python 3 is installed (the Debian image comes with Python 2 and 3 pre-installed but this script is not fully backward compatible with Python 2) and the necessary Python modules. Then we will install the Python script and configure the background service. Additionally, in the Testing and Troubleshooting section I've given an explanation of the `sudo` command prefix that you'll find in this section.

1. Establish an SSH session to your Pi Zero.
    - Username: `pi`
    - Password: `raspberry`
    - To change the default password, log in via SSH then run the command `passwd`.  Follow the prompts to change the password.
2. Verify Internet connectivity and then ensure that the `git` command line tool is installed:
    - `sudo apt-get update`
    - `sudo apt-get install git -y`
3. Clone this repository to your Raspberry Pi by issuing this command:
    - `git clone https://github.com/miarond/RPi_Irrigation_Bypass_Sensor.git rain_sensor`
    - Change directory into the newly created project folder by issuing the command: `cd rain_sensor`
4. Edit the following files to add your environment-specific information:
    1. Rename the `default.env` file to `.env` with the command: `mv default.env .env`
    2. Edit the `.env` file and update all of the relevant Environment Variable values.
    3. Edit the `rain-sensor.service` file and update the `FLASK_RUN_HOST` environment variable with your Raspberry Pi's local IP address.
5. Verify the file permissions of the newly created `setup.sh` file:
    - Run the command `ls -al | grep setup` to view the file and its attributes.
      - My output looked similar to this:
      ```
      pi@raspberrypi:~ $ ls -al | grep setup
      -rw-r--r-- 1 pi   pi   1848 Dec 23 12:41 setup.sh
      ```
      - File attributes are shown in the format `drwxrwxrwx` where the first letter denotes either a file (`-`) or a directory (`d`). The next groupings of 3 letters denote read (`r`), write (`w`) and execute (`x`) permissions. As you can see, my file is missing the execute permission.
    - Add execute permissions to the file by running the command `chmod +x setup.sh`.  Because the `pi` user account is the owner of the file, we can run this command without adding the `sudo` prefix.
6. Start the setup script to begin installation:
    - `sudo ./setup.sh`
    - The setup script will prompt you to add a "cron" job to the "crontab" configuration file.  Review the example formatting given by the script, and when you're ready press the `Enter` key to continue.
    - You may also receive prompts regarding the installation and configuration of Linux utilities.
7. When finished, the Bash script will force a reboot of the Pi Zero. If the configuration was successful the background service should start automatically on bootup.  The web application should be reachable via `http://<raspberry_pi_IP_address>`.


## Web Application

The core of this project is a Web application and REST API, created using the Flask package in Python.  This application is completely contained in the `app.py` script and `templates/index.html` file, and is run at startup by the `rain-sensor` background service under `systemd`.  You can access this application when the service is running by visiting `http://<raspberry_pi_IP_address>` in any web browser, while you're on your local network.  This page has an **ON/OFF** button which, when clicked, will send a REST API call to the Flask application and will trigger the relay to change from its current state.  The new state will then be reported back to the web page and displayed as "ON", "OFF", or if a fault is encountered "UNKNOWN".  **Please note:** This is a manual change of the relay state but it *can* be overridden automatically by the `forecast.py` script.  Also, any power outage will cause the relay to return to its unpowered, Normally Closed state.

### Web Application Workflow

![Web App Logical Workflow](/assets/webapp_logic_workflow.png)

## Forecast Script

The `forecast.py` script is configured to run periodically via a CRON job that is created during the initial setup phase.  This script will run at the prescribed times, download forecast data, determine if the rain percentage is greater than or equal to the threshold percentage (set in the Environment Variables), and will make REST API calls to the `app.py` Flask application in order to change the Relay state.  The script will also use the TinyDB Python package to create a simple document database for storing the previous forecast data, and the resulting irrigation system state.  This data is stored in a local file named `db.json` and is flushed at the beginning of every run of the `forecast.py` script.

### Forecast Script Workflow

![Forecast Script Logical Workflow](/assets/forecast_logic_workflow.png)

## Troubleshooting

Wait, you mean it *didn't* work right the first time???  It's a well known axiom that code rarely works right on the first try...and if it does, you should be suspicious! There are several places where this setup process could go wrong and its always best to watch the SSH console output carefully as the installation progresses. Detailed error messages or warnings will often be displayed on the console.

Some common spots for trouble could be:
- Installation failures due to insufficient privileges.
    - Most system modifying commands will require the use of the `sudo` prefix.  The `sudo` command stands for "Superuser Do" and it is the equivalent of choosing "Run as Administrator" on Windows operating systems.
    - As mentioned in the previous section, files that need to be executed (like Bash scripts) will require execute permissions which may not be set by default.  To view the permissions of any file or directory you can change directory to where that file or folder exists, then run the `ls -al` command. Running the `chmod +x <filename>` command will add execute permissions - using `+r` or `+w` will add read or write permissions.
- Installation failures due to missing dependencies.
    - Be sure to leverage the Aptitude (`apt-get`) package manager for installing programs.
    - Be sure to use the Pip package manager for installing Python modules.
    - When installing the Python modules listed above, make sure to run the command using `sudo` because this will install the package at the system level, making it available to all users and Python instances.
- Run the script using Python3 - a few of the code conventions used in the script are not backward compatible with Python2. If you aren't sure whether you're using Python3, make sure you're running the script with the command `python3 <script_name>`.
- Background service fails to run.
    - Sometimes a systemd service will fail to run when an error is encountered.  To view status information and logs for the service, use these commands:
      - `service rain-sensor status`
      - `journalctl -u rain-sensor.service -f` (shows the STDOUT and STDERR logs from the service - the "-f" flag follows the log file and displays any new updates) 
    - If your service unit file need to be updated post-installation, you can edit the file directly.  Follow this procedure:
        - `sudo nano /etc/systemd/system/rain-sensor.service`
        - Edit the proper lines
        - Press `Ctrl + O` to save the file, then `Ctrl + X` to exit.
        - Refresh the System Daemon by running the command `sudo systemctl daemon-reload`
        - Restart the service with the command `sudo systemctl start rain-sensor.service`
- Need to view the status of GPIO pins?
  - On the Linux Bash command line, run the command `gpio readall`.  This runs the `wiringpi` package and displays a table of GPIO status information (additional information can be found via the command `man gpio`)
- If all else fails, Google the error message :grin:

If your Pi doesn't come online and connect to your wireless network automatically, you can try connecting a keyboard, mouse and monitor if you have the proper adapters for both Micro USB and Mini HDMI. However, if you don't have those adapters you CAN use the USB data cable to establish an emergency terminal/console session. The process is partially documented on this website [The Polyglot Developer](https://www.thepolyglotdeveloper.com/2016/06/connect-raspberry-pi-zero-usb-cable-ssh/). Windows users will need to install Apple's [Bonjour Print Services](https://support.apple.com/kb/DL999?locale=en_US) application to communicate with the Pi over USB (this is the only method I have personally tested). Mac users should not need this additional step (as documented [here](https://learn.adafruit.com/bonjour-zeroconf-networking-for-windows-and-linux)).

Once setup is complete on your computer, connect the Micro USB cable to the **USB** port on the Pi (NOT the PWR IN port) and to a USB port on your computer. The Pi should power on and establish a network connection to your computer via the USB cable. You can then simply SSH to `raspberrypi.local` from your computer and you should be able to connect to the Pi just like you would over a network connection.

## Directory Structure

The following is a directory tree structure that illustrates the files installed and where they are placed.

```
/
└─── home
|    └─── pi
|        └─── rain_sensor
|             └─── setup.sh
|             └─── app.py
|             └─── forecast.py
|             └─── gpio_cleanup.py
|             └─── db.json
|             └─── .env
|             └─── templates
|                  └─── index.html
└─── etc
     └─── systemd
          └─── system
               └─── rain-sensor.service
```
