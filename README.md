# KStars Watchdog

This is a small batch script that will:
- Start KStars if it is not already running
- Start Ekos with its default profile
- Unpark the telescope
- If an Ekos scheduler file named default.esl is present in the home directory, it will be (re-)started. It can also be a soft or hard link to another file.
- Finally, if KStars crashes or is closed, the script will restart it.

It is a bash script but can probably very easily converted to zsh or sh. 
For now, it uses X and not Wayland. 
By default, no log file is written but changing the value of LOGFILE allows to save the outputs to a file.
