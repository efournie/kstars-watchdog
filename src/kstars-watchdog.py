import argparse
import os
from pathlib import Path
from pydbus import SessionBus
import subprocess
import time

# TODO:
# trigger() toggles the Ekos window on/off, only call it if the window is not opened
# replace all time.sleep() calls with status checks

# Helper functions
def start_kstars():
    print('Starting KStars...')
    proc = subprocess.Popen([args.kstars_executable], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(8)

def attempt_bus_connect(bus, service_name, path, max_retries=10, error_callback=None):
    cnt = 0
    while True:
        try:
            result = bus.get(service_name, path)
        except:
            time.sleep(1)
            cnt += 1
            if cnt <= max_retries:
                print(f'Loading {service_name} {path} failed, retrying (attempt #{cnt} of {max_retries})...')
                if error_callback is not None:
                    error_callback()
                continue
            else:
                print(f'Could not reload scheduler job after {max_retries} attempts')
                return None
            break
        break
    print(f'{service_name} {path} connected successfully.')
    return result

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
    ekos = attempt_bus_connect(bus, 'org.kde.kstars', '/KStars/Ekos', error_callback=start_kstars)
    if ekos == None:
        print(f'KStars could not be started, giving up...')
        exit(-1)
    print('KStars is running.')

    # Show main Ekos window
    ekos.start()
    show_ekos_action = bus.get('org.kde.kstars', '/kstars/MainWindow_1/actions/show_ekos')
    show_ekos_action.trigger()

    # INDI devices should be up and running by now
    if os.path.exists(args.sched_job):
        print('Scheduler job file present, unparking telescope')
        # Unpark mount
        mount = attempt_bus_connect(bus, 'org.kde.kstars','/KStars/Ekos/Mount')
        if mount is not None:
            if mount.status != 4:
                # Mount is not parked, park it before unparking it otherwise job may not restart correctly
                mount.park()
                time.sleep(20)
            mount.unpark()
        else:
            print('Could not unpark mount')

        # (Re-)start scheduler jobs : load and start scheduler file
        scheduler = attempt_bus_connect(bus, 'org.kde.kstars','/KStars/Ekos/Scheduler')
        if scheduler is not None:
            scheduler.loadScheduler(args.sched_job)
            scheduler.start()
        else:
            print('Could not reload scheduler job')

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
