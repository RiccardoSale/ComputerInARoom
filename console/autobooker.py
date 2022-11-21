from common import *
import time
import sys
from datetime import datetime, timedelta
import requests


def autobooker(delta: int, sync=False):
    log("Autobooker started...")
    log(f"Booking a session every {delta} hours...")
    if sync:
        log("Syncing enabled: map and objectives will be downloaded")

    close = False
    while not close:

        # Wait for booked session.
        current_slot = None
        while current_slot is None:
            log("Waiting for next booked session...")
            time.sleep(60)
            try:
                current_slot = get_current_slot()
            except requests.exceptions.ConnectionError:
                log("Failed to check slots...")

        log("Reached session start time, checking connection...")

        booked_slots = get_booked_slots()
        # Check if connection to MELVIN works.
        if try_connect(f"http://{MELVIN_API}/observation", 3, 20, 5):
            log("Connection established")

            # Downaload new objectives and map if required.
            if sync:
                ssh = ssh_connect(MELVIN_SSH, "user", "user")
                sync_map(ssh, callback=log)
                sync_objectives(ssh, callback=log)
                ssh.close()

            # Only book a new slot if there aren't any already booked.
            if not len(booked_slots) > 1:
                # Session is ok book another one in `delta` hours.
                t_target = datetime.utcnow() + timedelta(hours=delta)
                log(f"Booking new session near {t_target}...")
                book_slot_near(t_target)
            else:
                log("Slots already booked. Nothing to do.")
        else:
            # MELVIN connection failed book the next available slot.
            log("Failed to connect to MELVIN, booking next available slot...")
            next_slot_id = int(current_slot["id"]) + 1
            set_slot(next_slot_id, True)

        next_slot_start = parse_slot_time(get_booked_slots()[1]["start"])
        log(f"Next slot booked at: {next_slot_start}")

        # Wait for the current session to end.
        session_ended = False
        while not session_ended:
            log("Waiting for session to end...")
            time.sleep(60)
            try:
                session_ended = not in_booked_slot()
            except requests.exceptions.ConnectionError:
                log("Failed to check slots...")
        log("Session ended")


if __name__ == "__main__":
    exit_code = 0
    match sys.argv[1:]:
        case [delta, ("--sync" | "--nosync") as sync]:
            if int(delta) <= 2:
                print("Error: delta too small, only >2 accepted")
                exit_code = 1
            else:
                autobooker(int(delta), sync == "--sync")
        case _:
            print("Usage: autobooker <delta> [--sync|--nosync]")
            exit_code = 1
    exit(exit_code)
