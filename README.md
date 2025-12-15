# KStars Watchdog

This is a python script that will:
- Start KStars if it is not already running
- Start Ekos with its default profile
- Unpark the telescope
- If an Ekos scheduler file named default.esl is present in the home directory, it will be (re-)started. It can also be a soft or hard link to another file.
- Finally, if KStars crashes or is closed, the script will restart it.

The script can be started if KStars is already running. Run it with:

`python kstars-watchdog.py`

or

`python3 kstars-watchdog.py`

Further actions (for example unparking the dome) can easily be added with qdbus. [The KStars API is well described here.](https://api.kde.org/legacy/kstars/html/index.html)

Thanks to https://openastronomy.substack.com/p/automating-kstars-and-ekos-pt-2 for the python DBUS scripting examples.

The kstars-watchdog-ssh.sh initiates X settings in case only ssh remote access is possible. Untested with Wayland yet.

# Requirements

- Python3
- pydbus, installed for example with `pacman -S python-pydbus` or `apt install python3-pydbus`
