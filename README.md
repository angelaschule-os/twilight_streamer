# The Twitching Allsky Twilight Streamer

You can use the following python script to stream images from the Allsky camera
to Twitch during twilight.


## Setting up Systemd Service

You can use systemd to manage your Python script as a service, which helps
ensure the script keeps running even if the system restarts or encounters any
issues. Here are the steps to create a systemd service for your Python script:


```bash
python3 -m venv my_venv
source my_venv/bin/activate
pip install ephem pytz schedule
```

Create a systemd service file named `twilight_recorder.service` in the
`/etc/systemd/system` directory:

```ini
[Unit]
Description=Twilight Recorder Service
After=network.target

[Service]
Type=simple
User=<your_user>
WorkingDirectory=<path_to_your_script_directory>
ExecStart=<path_to_your_venv>/bin/python3 <path_to_your_script>/twilight_recorder.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Replace `<your_user>` with your username, `<path_to_your_script_directory>` with
the directory containing your script, and `<path_to_your_venv>` with the path to
your virtual environment.

Reload the systemd daemon and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl start twilight_recorder.service
```

Enable the service to run at startup:

```bash
sudo systemctl enable twilight_recorder.service
```

Check the status of the service:

```bash
sudo systemctl status twilight_recorder.service
```

Now your Python script will run as a systemd service, which will help ensure
that it keeps running even if the system restarts or encounters any issues. The
service will also restart automatically if the script fails.
