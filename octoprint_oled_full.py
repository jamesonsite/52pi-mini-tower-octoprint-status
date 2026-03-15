#!/usr/bin/env python3
import time
import socket
from datetime import timedelta

import requests
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

# =========================
# OctoPrint settings
# =========================
OCTOPRINT_URL = "http://127.0.0.1:5000"
API_KEY = "API_KEY"

# =========================
# OLED settings
# =========================
I2C_PORT = 1
I2C_ADDRESS = 0x3C
WIDTH = 128
HEIGHT = 64
ROTATE = 0

POLL_SECONDS = 2


def get_hostname():
    return socket.gethostname()


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "No IP"
    finally:
        s.close()


def format_temp(section):
    if not isinstance(section, dict):
        return "--/--"

    actual = section.get("actual")
    target = section.get("target")

    if actual is None and target is None:
        return "--/--"

    if actual is None:
        actual = 0
    if target is None:
        target = 0

    return f"{actual:.0f}/{target:.0f}"


def format_eta(seconds):
    if seconds is None:
        return "--:--"
    try:
        seconds = int(seconds)
        return str(timedelta(seconds=seconds))
    except Exception:
        return "--:--"


def fetch_octoprint():
    headers = {"X-Api-Key": API_KEY}

    printer = requests.get(
        f"{OCTOPRINT_URL}/api/printer?history=false&limit=1",
        headers=headers,
        timeout=5,
    )
    job = requests.get(
        f"{OCTOPRINT_URL}/api/job",
        headers=headers,
        timeout=5,
    )

    printer.raise_for_status()
    job.raise_for_status()

    return printer.json(), job.json()


def build_lines(printer_data, job_data):
    state_text = printer_data.get("state", {}).get("text", "Unknown")

    temp_data = printer_data.get("temperature", {}) or {}
    tool0 = temp_data.get("tool0", {}) or {}
    bed = temp_data.get("bed", {}) or {}

    nozzle = format_temp(tool0)
    bedtemp = format_temp(bed)

    progress = job_data.get("progress", {}) or {}
    completion = progress.get("completion")
    if completion is None:
        completion_text = "--%"
    else:
        completion_text = f"{completion:.0f}%"

    print_time_left = progress.get("printTimeLeft")
    eta = format_eta(print_time_left)

    job_info = job_data.get("job", {}) or {}
    file_info = job_info.get("file", {}) or {}
    filename = file_info.get("name", "No file")

    if filename is None:
        filename = "No file"

    filename = str(filename)

    if len(filename) > 18:
        filename = filename[:18]

    line1 = f"{str(state_text)[:18]}"
    line2 = f"N:{nozzle} | B:{bedtemp}"
    line3 = f"P:{completion_text} ETA:{eta[:8]}"
    line4 = filename

    return [line1, line2, line3, line4]


def draw_screen(device, font, lines):
    image = Image.new("1", (device.width, device.height))
    draw = ImageDraw.Draw(image)

    y = 0
    line_height = 15 if device.height >= 64 else 8

    for line in lines:
        draw.text((0, y), str(line), font=font, fill=255)
        y += line_height

    device.display(image)


def draw_error(device, font, message):
    image = Image.new("1", (device.width, device.height))
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), "OctoPrint OLED", font=font, fill=255)
    draw.text((0, 16), "Error:", font=font, fill=255)
    draw.text((0, 32), str(message)[:20], font=font, fill=255)
    device.display(image)


def main():
    serial = i2c(port=I2C_PORT, address=I2C_ADDRESS)
    device = ssd1306(serial, width=WIDTH, height=HEIGHT, rotate=ROTATE)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except Exception:
        font = ImageFont.load_default()

    splash = [
        "OctoPrint OLED",
        get_hostname(),
        get_ip(),
        "Starting..."
    ]
    draw_screen(device, font, splash)
    time.sleep(2)

    while True:
        try:
            printer_data, job_data = fetch_octoprint()
            lines = build_lines(printer_data, job_data)
            draw_screen(device, font, lines)
        except Exception as e:
            print("ERROR:", repr(e))
            draw_error(device, font, str(e))
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
