# 52pi-mini-tower-octoprint-status
Script for octopi and raspberry pi mini tower lcd screen

# 52Pi ZP-0128 OLED OctoPrint Progress Display

Displays the **current OctoPrint print progress as a large percentage** on the OLED screen included with the **52Pi ZP-0128-4wire Raspberry Pi case**.

The percentage is rendered using the **largest font that fits the 128×64 OLED**, making it readable across the room.

---

## Example Display

Printing:

```
34%
```

Idle:

```
READY
```

Paused:

```
PAUSE
```

Error:

```
ERROR
```

---

## Hardware

- Raspberry Pi
- 52Pi **ZP-0128-4wire case**
- Built-in **SSD1306 OLED display**
- OLED connected over **I²C**

OLED I²C address:

```
0x3C
```

---

## Enable I²C

Enable I²C support:

```bash
sudo raspi-config
```

Navigate to:

```
Interface Options → I2C → Enable
```

Verify the OLED is detected:

```bash
i2cdetect -y 1
```

You should see:

```
3c
```

---

## Install Dependencies

```bash
sudo apt update
sudo apt install \
python3 python3-pip python3-pil \
libjpeg-dev zlib1g-dev libfreetype6-dev \
liblcms2-dev libopenjp2-7 libtiff-dev
```

---

## Create Python Environment

```bash
python3 -m venv ~/luma-venv
source ~/luma-venv/bin/activate
```

Install required libraries:

```bash
pip install luma.oled luma.core pillow requests
```

---

## Script Location

Save the OLED display script as:

```
/home/octopi/octoprint_oled.py
```

The script queries the OctoPrint API:

```
http://127.0.0.1:5000/api/job
```

and extracts:

```
progress.completion
```

This value is displayed as a **large full-screen percentage**.

---

## Run Manually

```bash
source ~/luma-venv/bin/activate
python3 ~/octoprint_oled.py
```

---

## Run Automatically at Boot

Create the systemd service:

```bash
sudo nano /etc/systemd/system/octoprint-oled.service
```

Service configuration:

```
[Unit]
Description=OctoPrint OLED Display
After=network.target

[Service]
ExecStart=/home/octopi/luma-venv/bin/python /home/octopi/octoprint_oled.py
Restart=always
User=octopi

[Install]
WantedBy=multi-user.target
```

Enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable octoprint-oled.service
sudo systemctl start octoprint-oled.service
```

View logs:

```bash
journalctl -u octoprint-oled.service -f
```

---

## Result

The OLED display automatically shows the **current OctoPrint print progress**.

Example:

```
18%
```

The display updates every **2 seconds** and starts automatically whenever the Raspberry Pi boots.
