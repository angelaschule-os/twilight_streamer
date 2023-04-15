import datetime
import ephem
import pytz
import schedule
import time
import subprocess
import logging
import argparse
from dotenv import load_dotenv  # Import load_dotenv from python-dotenv library
import os
import git_version

# Load the environment variables from the .env file
load_dotenv()

# Get the RTMP URL from the environment variable
rtmp_url = os.getenv("RTMP_URL")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("twilight_recorder.log"), logging.StreamHandler()],
)


def get_git_version_hash():
    try:
        git_hash = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .decode("utf-8")
            .strip()
        )
        return git_hash
    except Exception as e:
        print("Error getting Git hash:", e)
        return None
    
def load_credentials(dotenv_path):
    load_dotenv(dotenv_path)

    rtmp_url = os.getenv("API_USERNAME")

    return rtmp_url 


def get_astronomical_twilight(observer):
    sun = ephem.Sun()
    observer.date = datetime.datetime.utcnow()
    observer.horizon = "-18"  # Set horizon to -18 degrees for astronomical twilight

    astronomical_twilight_evening = observer.next_setting(
        sun, use_center=True
    ).datetime()
    astronomical_twilight_morning = observer.next_rising(
        sun, use_center=True
    ).datetime()

    return astronomical_twilight_evening, astronomical_twilight_morning


def convert_to_berlin_time(utc_time):
    berlin_tz = pytz.timezone("Europe/Berlin")
    return utc_time.replace(tzinfo=pytz.utc).astimezone(berlin_tz)


def start_ffmpeg_recording():
    command = f"ffmpeg -re -stream_loop -1 -framerate 9 -f image2 -i /home/astroberry/allsky/tmp/image.jpg -vf scale=1280:720 -vcodec libx264 -preset medium -f flv {rtmp_url}"
    process = subprocess.Popen(command, shell=True)
    return process


def stop_ffmpeg_recording(process):
    process.terminate()


def schedule_recording():
    duration = (
        astronomical_twilight_morning - astronomical_twilight_evening
    ).total_seconds()

    process = start_ffmpeg_recording()
    time.sleep(duration)
    stop_ffmpeg_recording(process)


if __name__ == "__main__":
    logging.info("Starting twilight recorder script")

    if not git_version.GIT_HASH:
        git_version.GIT_HASH = get_git_version_hash()

    parser = argparse.ArgumentParser(description="Twitching Allsky Twilight Streamer")
    parser.add_argument(
        "-v", "--version", action="version", version=f"Git version hash: {git_version.GIT_HASH}"
    )
    parser.add_argument(
        "-c","--config", metavar="PATH", default=".env",
        help="Path to the config file (default: .env)"
    )
    args = parser.parse_args()

    observer = ephem.Observer()
    observer.lat, observer.lon, observer.elevation = "52.2799", "8.0472", 62.0

    (
        astronomical_twilight_evening_utc,
        astronomical_twilight_morning_utc,
    ) = get_astronomical_twilight(observer)

    astronomical_twilight_evening = convert_to_berlin_time(
        astronomical_twilight_evening_utc
    )
    astronomical_twilight_morning = convert_to_berlin_time(
        astronomical_twilight_morning_utc
    )

    logging.info(
        "Astronomical twilight starts in the evening at (Berlin Time): %s",
        astronomical_twilight_evening,
    )
    logging.info(
        "Astronomical twilight ends in the morning at (Berlin Time): %s",
        astronomical_twilight_morning,
    )

    schedule.every().day.at(astronomical_twilight_evening.strftime("%H:%M:%S")).do(
        schedule_recording
    )

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping twilight recorder script")
