#!/usr/bin/env python3
import time

import requests
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

OCTOPRINT_URL = "http://127.0.0.1:5000"
API_KEY = "YOUR_API_KEY"

I2C_PORT = 1
I2C_ADDRESS = 0x3C
WIDTH = 128
HEIGHT = 64
ROTATE = 0

POLL_SECONDS = 2


def fetch_job():
    headers = {"X-Api-Key": API_KEY}
    r = requests.get(
        f"{OCTOPRINT_URL}/api/job",
        headers=headers,
        timeout=5,
    )
    r.raise_for_status()
    return r.json()


def get_display_text(job_data):
    state = str(job_data.get("state", "Unknown"))
    progress = job_data.get("progress", {}) or {}
    completion = progress.get("completion")
    state_lower = state.lower()

    if "printing" in state_lower:
        if completion is None:
            return "--%"
        return f"{completion:.0f}%"

    if "paused" in state_lower:
        if completion is None:
            return "PAUSE"
        return f"{completion:.0f}%"

    if "error" in state_lower:
        return "ERROR"

    if "operational" in state_lower or "ready" in state_lower:
        return "READY"

    return state[:6].upper()


def best_font(text, width, height):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    test_img = Image.new("1", (width, height))
    draw = ImageDraw.Draw(test_img)

    for size in range(72, 7, -2):
        for path in paths:
            try:
                font = ImageFont.truetype(path, size)
                box = draw.textbbox((0,0), text, font=font)
                w = box[2] - box[0]
                h = box[3] - box[1]

                if w <= width and h <= height:
                    return font
            except:
                pass

    return ImageFont.load_default()


def draw(device, text):
    img = Image.new("1", (device.width, device.height))
    d = ImageDraw.Draw(img)

    font = best_font(text, device.width, device.height)

    box = d.textbbox((0,0), text, font=font)
    w = box[2] - box[0]
    h = box[3] - box[1]

    x = (device.width - w) // 2
    y = ((device.height - h) // 2) - box[1]

    d.text((x,y), text, font=font, fill=255)
    device.display(img)


def main():
    serial = i2c(port=I2C_PORT, address=I2C_ADDRESS)
    device = ssd1306(serial, width=WIDTH, height=HEIGHT, rotate=ROTATE)

    draw(device, "BOOT")
    time.sleep(1)

    last = None

    while True:
        try:
            job = fetch_job()
            text = get_display_text(job)

            if text != last:
                draw(device, text)
                last = text

        except Exception as e:
            draw(device, "ERROR")

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
