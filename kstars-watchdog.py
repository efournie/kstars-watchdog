import argparse
import os
from pathlib import Path
from pydbus import SessionBus
import subprocess
import time

# TODO:
# trigger() toggles the Ekos window on/off, only call it if the window is not opened
# replace all time.sleep() calls with status checks

home = Path.home()
default_sched_job = os.path.join(home, 'default.esl')
max_retries = 10

# Read command line arguments
parser = argparse.ArgumentParser(description='KStars / Ekos watchdog program, automatically resuming in case of a crash.')
parser.add_argument('-k', '--kstars_executable', type=str, default='/usr/bin/kstars', help='Full path to the kstars executable.')
parser.add_argument('-s', '--sched_job', type=str, default=default_sched_job, help='Path to the default Ekos scheduler job file to be resumed in case of a crash.')
args = parser.parse_args()

# Initialize DBus
bus = SessionBus()

# Main loop
while True:
    # Check if KStars is running, try to start it otherwise
    cnt = 0
    while True:
        try:
            ekos = bus.get('org.kde.kstars','/KStars/Ekos')
        except:
            time.sleep(1)
            cnt += 1
            if cnt <= max_retries:
                print(f'Unable to accesss KStars, attempting to start it (attempt #{cnt} of {max_retries})...')
                proc = subprocess.Popen([args.kstars_executable], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                time.sleep(5)
                continue
            else:
                print(f'KStars could not be started after {max_retries} attempts, giving up...')
                exit(-1)
        break

    print('KStars is running.')

    # Show main Ekos window
    ekos.start()
    show_ekos_action = bus.get('org.kde.kstars', '/kstars/MainWindow_1/actions/show_ekos')
    show_ekos_action.trigger()

    # INDI devices should be up and running by now
    if os.path.exists(args.sched_job):
        print('Scheduler job file present, unparking telescope')
        # Unpark mount
        cnt = 0
        while True:
            try:
                mount = bus.get('org.kde.kstars','/KStars/Ekos/Mount')
                mount.unpark()
            except:
                time.sleep(1)
                cnt += 1
                if cnt <= max_retries:
                    print(f'Unparking failed, retrying ((attempt #{cnt} of {max_retries})...')
                    continue
                else:
                    print('Could not unpark mount after {max_retries} attempts')
            break

        # (Re-)start scheduler jobs : load and start scheduler file
        cnt = 0
        print('Loading scheduler job')
        while True:
            try:
                scheduler = bus.get('org.kde.kstars','/KStars/Ekos/Scheduler')
                scheduler.loadScheduler(args.sched_job)
                print('Starting scheduler job')
                scheduler.start()
            except:
                time.sleep(1)
                cnt += 1
                if cnt <= max_retries:
                    print(f'Loading scheduler job failed, retrying ((attempt #{cnt} of {max_retries})...')
                    continue
                else:
                    print('Could not reload scheduler job after {max_retries} attempts')
            break

    # Watchdog loop, restart everything if Kstars crashes or is closed
    print('Everything is up and running, initiating watchdog.')
    while True:
        try:
            ekos = bus.get('org.kde.kstars','/KStars/Ekos')
        except:
            print('Kstars has been closed or crashed, restarting in 5 seconds...')
            time.sleep(5)
            break
        time.sleep(1)
