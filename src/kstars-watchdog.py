import argparse
from datetime import datetime
import os
from pathlib import Path
from pydbus import SessionBus
import subprocess
import time

# TODO:
# trigger() toggles the Ekos window on/off, only call it if the window is not opened
# replace all time.sleep() calls with status checks

# Helper functions
def log(string, output=None):
    print(f'{datetime.now()}: {string}')
    if output is not None:
        with open(output, 'a') as f:
            f.write(f'{datetime.now()}: {string}\n')

def start_kstars(kstars_executable, output):
    log('Starting KStars...', output=output)
    proc = subprocess.Popen([kstars_executable], stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    time.sleep(8)

def attempt_bus_connect(bus, service_name, path, max_retries=10, error_callback=None, callback_arg=None, output=None):
    cnt = 0
    while True:
        try:
            result = bus.get(service_name, path)
        except:
            time.sleep(1)
            cnt += 1
            if cnt <= max_retries:
                log(f'Loading {service_name} {path} failed, retrying (attempt #{cnt} of {max_retries})...', output)
                if error_callback is not None:
                    error_callback(callback_arg, output)
                continue
            else:
                log(f'Could not reload scheduler job after {max_retries} attempts', output)
                return None
            break
        break
    log(f'{service_name} {path} connected successfully.', output)
    return result

def main():
    home = Path.home()
    default_sched_job = os.path.join(home, 'default.esl')
    max_retries = 10

    # Read command line arguments
    parser = argparse.ArgumentParser(description='KStars / Ekos watchdog program, automatically resuming in case of a crash.')
    parser.add_argument('-k', '--kstars_executable', type=str, default='/usr/bin/kstars', help='Full path to the kstars executable.')
    parser.add_argument('-s', '--sched_job', type=str, default=default_sched_job, help='Path to the default Ekos scheduler job file to be resumed in case of a crash.')
    parser.add_argument('-o', '--output', type=str, default=None, help='Log file. If not set, outptut will be only be printed sent to stdout.')
    args = parser.parse_args()

    # Initialize DBus
    bus = SessionBus()

    # Main loop
    while True:
        # Check if KStars is running, try to start it otherwise
        ekos = attempt_bus_connect(bus, 'org.kde.kstars', '/KStars/Ekos', error_callback=start_kstars, callback_arg=args.kstars_executable, output=args.output)
        if ekos == None:
            log(f'KStars could not be started, giving up...', args.output)
            exit(-1)
        log('KStars is running.', args.output)

        # Show main Ekos window
        ekos.start()
        show_ekos_action = bus.get('org.kde.kstars', '/kstars/MainWindow_1/actions/show_ekos')
        show_ekos_action.trigger()

        # INDI devices should be up and running by now
        if os.path.exists(args.sched_job):
            log('Scheduler job file present, unparking telescope', args.output)
            # Unpark mount
            mount = attempt_bus_connect(bus, 'org.kde.kstars','/KStars/Ekos/Mount', output=args.output)
            if mount is not None:
                if mount.status != 4:
                    # Mount is not parked, park it before unparking it otherwise job may not restart correctly
                    mount.park()
                    time.sleep(20)
                mount.unpark()
            else:
                log('Could not unpark mount', args.output)

            # (Re-)start scheduler jobs : load and start scheduler file
            scheduler = attempt_bus_connect(bus, 'org.kde.kstars','/KStars/Ekos/Scheduler', output=args.output)
            if scheduler is not None:
                scheduler.loadScheduler(args.sched_job)
                scheduler.start()
            else:
                log('Could not reload scheduler job', args.output)

        # Watchdog loop, restart everything if Kstars crashes or is closed
        log('Everything is up and running, initiating watchdog.', args.output)
        while True:
            try:
                ekos = bus.get('org.kde.kstars','/KStars/Ekos')
            except:
                log('Kstars has been closed or crashed, restarting in 5 seconds...', args.output)
                time.sleep(5)
                break
            time.sleep(1)

if __name__ == '__main__':
    main()
