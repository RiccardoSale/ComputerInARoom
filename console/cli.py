from common import *

import os
import sys

import requests
import pandas
from tabulate import tabulate

HELP = (
    "Available commands:\n"
    "  help                           - show this message\n"
    "  exit                           - leave console\n"
    "  slots                          - list available slots\n"
    "  slots (enable|disable) <id>    - enable/disable slot\n"
    "  objectives [completed]         - list current objectives, specify [completed] to only list\n"
    "                                   completed objectives\n"
    "  sync objectives                - download completed objectives\n"
    "  sync map                       - download stitched map\n"
    "  send objective <id>            - send a specific objective\n"
)


def console():

    current_slot = get_current_slot()
    if current_slot is None:
        print("Connection to MELVIN not available.")
        booked_slots = get_booked_slots()
        if len(booked_slots) > 0:
            next_s = parse_slot_time(booked_slots[0]["start"])
            print(f"Next booked session starts: {next_s}")
    else:
        current_slot_end = parse_slot_time(current_slot["end"])
        if try_connect(f"http://{MELVIN_API}/observation"):
            print(
                f"Connection to MELVIN established.\nSession ends: {current_slot_end}"
            )
        else:
            booked_slots = get_booked_slots()
            print("Connection to MELVIN failed.")
            if len(booked_slots) > 0:
                next_s = parse_slot_time(booked_slots[0]["start"])
                print(f"Next booked session starts: {next_s}")

    close = False
    while not close:
        command = input("operator@melvin ~> ").split()
        match command:
            case ["clear"]:
                os.system("clear")
            case ["exit"]:
                close = True
            case ["slots", ("enable" | "disable") as action, id]:
                try:
                    set_slot(id, action == "enable")
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 400:
                        print("Error: ID does not exists.")
            case ["slots"]:
                df = pandas.DataFrame(get_slots())
                df.rename(
                    columns={
                        "id": "ID",
                        "start": "Start",
                        "end": "End",
                        "enabled": "Booked",
                    },
                    inplace=True,
                )
                print(tabulate(df.to_dict("list"), headers="keys", tablefmt="outline"))
            case ["objectives", *args]:
                if in_booked_slot():
                    objectives = get_objectives()
                    df = pandas.DataFrame(
                        objectives,
                        columns=["id", "name", "start", "end", "max_points", "done"],
                    )
                    df.rename(
                        columns={
                            "id": "ID",
                            "name": "Name",
                            "start": "Start",
                            "end": "End",
                            "max_points": "Max Points",
                            "done": "Done",
                        },
                        inplace=True,
                    )
                    match args:
                        # No additional argumants.
                        case []:
                            print(
                                tabulate(
                                    df.to_dict("list"),
                                    headers="keys",
                                    tablefmt="outline",
                                )
                            )
                        case ["completed"]:
                            completed = df[df["Done"]]
                            if not completed.empty:
                                print(
                                    tabulate(
                                        completed.to_dict("list"),
                                        headers="keys",
                                        tablefmt="outline",
                                    )
                                )
                            else:
                                print("No completed objectives to display")
                        case _:
                            print(HELP)
                else:
                    print("Command not available outside booked sessions.")
            case ["sync", "objectives"]:
                if in_booked_slot():
                    try:
                        ssh = ssh_connect(MELVIN_SSH, "user", "user")
                        sync_objectives(ssh, callback=print)
                        ssh.close()
                    except:
                        print("Error")
                else:
                    print("Command not available outside booked sessions.")
            case ["sync", "map"]:
                if in_booked_slot():
                    try:
                        ssh = ssh_connect(MELVIN_SSH, "user", "user")
                        sync_map(ssh, callback=print)
                        ssh.close()
                    except:
                        print("Error")
                else:
                    print("Not available outside booked sessions.")
            case ["send", "objective", id]:
                if in_booked_slot():
                    try:
                        id = int(id)
                        if os.path.exists(f"obj/objective_{id}.png"):
                            _ = send_image(f"obj/objective_{id}.png", id)
                            print(f"Objective {id} sent.")
                        else:
                            print("Objective image not available")
                    except:
                        print("Error")
                else:
                    print("Not available outside booked sessions.")
            case ["help"] | _:
                print(HELP)


if __name__ == "__main__":
    exit_code = 0
    match sys.argv[1:]:
        case []:
            console()
        case _:
            print("Invalid Arguments")
            exit_code = 1
    exit(exit_code)
