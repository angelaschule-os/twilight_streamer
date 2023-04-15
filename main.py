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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/tmp/twilight_streamer.log"), logging.StreamHandler()],
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


def get_twilight(observer):
    sun = ephem.Sun()
    observer.date = datetime.datetime.utcnow()

    # Civil twilight uses the value –6 degrees.
    # Nautical twilight uses the value –12 degrees.
    # Astronomical twilight uses the value –18 degrees.
    observer.horizon = "-12"  # Set horizon to -12 degrees for nautical twilight

    twilight_evening = observer.next_setting(sun, use_center=True).datetime()
    twilight_morning = observer.next_rising(sun, use_center=True).datetime()

    return twilight_evening, twilight_morning


def convert_to_berlin_time(utc_time):
    berlin_tz = pytz.timezone("Europe/Berlin")
    return utc_time.replace(tzinfo=pytz.utc).astimezone(berlin_tz)


def start_ffmpeg_recording(rtmp_url):
    command = f"ffmpeg -re -stream_loop -1 -framerate 9 -f image2 -i /home/astroberry/allsky/tmp/image.jpg -vf scale=1280:720 -vcodec libx264 -preset medium -f flv {rtmp_url}"
    process = subprocess.Popen(command, shell=True)
    logging.info("Started streaming")
    return process


def stop_ffmpeg_recording(process):
    process.terminate()
    logging.info("Stopped streaming")


def schedule_recording(twilight_evening, twilight_morning, rtmp_url):
    duration = (twilight_morning - twilight_evening).total_seconds()
    logging.info("Streaming for %s seconds", duration)

    process = start_ffmpeg_recording(rtmp_url)
    time.sleep(duration)
    stop_ffmpeg_recording(process)


def update_twilight_and_schedule(observer, rtmp_url):
    (
        twilight_evening_utc,
        twilight_morning_utc,
    ) = get_twilight(observer)

    twilight_evening = convert_to_berlin_time(twilight_evening_utc)
    twilight_morning = convert_to_berlin_time(twilight_morning_utc)

    logging.info(
        "Twilight starts in the evening at (Berlin Time): %s",
        twilight_evening,
    )
    logging.info(
        "Twilight ends in the morning at (Berlin Time): %s",
        twilight_morning,
    )

    schedule.every().day.at(twilight_evening.strftime("%H:%M:%S")).do(
        lambda: schedule_recording(twilight_evening, twilight_morning, rtmp_url)
    )


def main():
    logging.info("Starting twilight recorder script")
    rtmp_url = load_credentials(args.config)
    observer = ephem.Observer()
    observer.lat, observer.lon, observer.elevation = "52.2799", "8.0472", 62.0

    update_twilight_and_schedule(observer, rtmp_url)

    #  Function to run every day at a specific time when you expect the twilight
    #  time to have changed, such as 14:00h in the Berlin timezone. 
    schedule.every().day.at("14:00:00").do(
        lambda: update_twilight_and_schedule(observer, rtmp_url)
    )

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping twilight recorder script")


if __name__ == "__main__":
    if not git_version.GIT_HASH:
        git_version.GIT_HASH = get_git_version_hash()

    parser = argparse.ArgumentParser(description="Twitching Allsky Twilight Streamer")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Git version hash: {git_version.GIT_HASH}",
    )
    parser.add_argument(
        "-c",
        "--config",
        metavar="PATH",
        default=".env",
        help="Path to the config file (default: .env)",
    )
    args = parser.parse_args()

    main()
