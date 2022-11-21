import lzma
import math
import os
import time
from datetime import datetime


from paramiko import SSHClient
import paramiko
import requests


# CIARC interface address.
CIARC_MAIN = "192.168.5.2:12004"
# MELVIN SSH address.
MELVIN_SSH = "192.168.5.30"
# MELVIN telemetry and telecommand address.
MELVIN_API = "192.168.5.2:11004"


def ssh_connect(host: str, user: str, password: str):
    """
    Connect to a remote system with SSH for SFTP transfer. The connection
    must be closed by the caller once unneeded.

    :param host: hostname of the remote server.
    :param user: username for remote server.
    :param password: user password for authentication.

    :return SSHClient connection
    """

    client = SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, 22, user, password)
    return client


def get_objectives():
    """
    Fetch the current objectives.

    :return current objectives
    """

    resp = requests.get(f"http://{MELVIN_API}/objectives")

    resp.raise_for_status()
    return resp.json()["objectives"]


def get_completed_objectives():
    """
    Same as `get_objectives` but only returns completed objectives.

    :return current list of objectives
    """

    objectives = get_objectives()
    return list(filter(lambda o: o["done"], objectives))


def sftp_exists(sftp, path: str):
    """
    Checks if a remote path exists.

    :param sftp: SFTP connection obtained from a `SSHClient` object.
    :param path: the path to check.

    :return True if the path exists False otherwise.
    """

    try:
        # Try to stat the remote path, if it does not exists
        # an `IOError` will be thrown and catched.
        sftp.stat(path)
        return True
    except IOError:
        # The file does not exists.
        return False


def sftp_get_lzma(sftp, remote, local):
    """
    Download, decompress and save a lzma-compressed remote file.

    :param sftp: SFTP connection obtained from a `SSHClient` object.
    :param remote: location of the file in the remote server.
    :param local: path where to save the file.
    """

    with sftp.open(remote, "r") as rf:
        rf.prefetch()
        with open(local, "wb+") as f:
            # Decompress in memory and write to local file.
            f.write(lzma.LZMAFile(rf).read())
            f.close()
        rf.close()


def sync_objectives(ssh: SSHClient, callback=print):
    """
    Downloads all completed objectives from MELVIN.

    :param ssh: `SSHClient` connection.
    :param callback: a function that takes a `str` object.
    """

    if not os.path.exists("obj"):
        os.mkdir("obj")

    sftp = ssh.open_sftp()

    callback("Syncing objectives...")
    completed = os.listdir("obj")
    for e in sftp.listdir("melvin/obj"):
        path = f"melvin/obj/{e}/{e}.png.xz"
        # Only download if available and not already downloaded.
        if sftp_exists(sftp, path) and f"{e}.png" not in completed:
            sftp_get_lzma(sftp, path, f"obj/{e}.png")

    sftp.close()


def sync_map(ssh: SSHClient, callback=print):
    """
    Download stitched map from melvin.

    :param ssh: `SSHClient` connection.
    :param callback: a function that takes a `str` object.
    """

    sftp = ssh.open_sftp()

    busy = True
    while busy:
        callback("MELVIN may be writing the map waiting...")
        minutes = datetime.utcnow().minute
        busy = not 1 < minutes % 10 < 8
        time.sleep(5)

    callback("Syncing map...")
    path = "melvin/map/outs.png.xz"
    if sftp_exists(sftp, path):
        sftp_get_lzma(sftp, "melvin/map/outs.png.xz", "map.png")
        callback("Sync completed")
    else:
        callback("Map not available")

    sftp.close()


def get_slots_info():
    """
    Returns information about available slots.

    :return information about available slots.
    """

    resp = requests.get(f"http://{CIARC_MAIN}/slots")

    resp.raise_for_status()
    return resp.json()


def get_slots():
    """
    Like `get_slots_info` but returns only an array of slots.

    :return array containing slots information.
    """

    slots = get_slots_info()["slots"]
    return list(map(lambda s: slots[s], slots))


def get_booked_slots():
    """
    Like `get_slots` but only returns booked slots.

    :return array containing booked slots information.
    """

    return list(filter(lambda s: s["enabled"], get_slots()))


def parse_slot_time(time: str):
    """
    Returns a `datetime` object converting from the format of
    slots `start` and `end`.

    :param time: time to convert.

    :return `time` converted to a `datetime` object.
    """

    return datetime.strptime(time, "%Y-%m-%dT%H:%M")


def get_current_slot():
    """
    Returns the booked slot with the timeframe that contains
    the current time.

    :return information about the current slot, `None` if not in a slot.
    """

    booked_slots = get_booked_slots()

    for slot in booked_slots:
        start = parse_slot_time(slot["start"])
        end = parse_slot_time(slot["end"])
        if start < datetime.utcnow() < end:
            return slot

    # If no slot is found no session is currently active.
    return None


def book_slot_near(target: datetime):
    """
    Books the slot with the start time closest to the time provided.

    :param target: time
    """

    nearest_slot = None  # Current closest slot found.
    min_delta = math.inf  # Current distance from the target time.

    # Find the slot closest to the time provided.
    for slot in get_slots():
        # Calculate delta between desired time and start of session.
        slot_delta = abs((target - parse_slot_time(slot["start"])).total_seconds())
        if slot_delta < min_delta:
            min_delta = slot_delta
            nearest_slot = slot

    if not nearest_slot["enabled"]:
        set_slot(int(nearest_slot["id"]), True)


def set_slot(id: int, enable: bool):
    """
    Enable/Disable a slot based on the value of `enable`.

    :param id: id of the slot to enable.
    :param enable: set to `True` to enable `False` to disable.
    """

    resp = requests.put(
        f"http://{CIARC_MAIN}/slots",
        json={"id": id, "active": enable},
    )

    resp.raise_for_status()
    return resp.json()


def send_image(image: str, event: int):
    """
    Send the image of a specific objective.

    :param image: path to the image to send.
    :param event: id of the event.
    """

    imageb = open(image, "rb")

    resp = requests.post(
        f"http://{MELVIN_API}/objectives",
        data={"objective_id": event},
        files={"image": imageb},
    )

    resp.raise_for_status()
    return resp.json()


def try_connect(url: str, retry=1, timeout=10, wait=0):
    """
    Check connection to an HTTP url. This is accomplished by
    sending a HEAD HTTP request.

    :param url: location to check.
    :param retry: max retry count.
    :param timeout: request timeout.
    :param wait: time between each try.

    :return `True` if successful `False` otherwise.
    """

    for _ in range(retry):
        try:
            requests.head(url, timeout=timeout)
        except requests.exceptions.ConnectTimeout:
            # Fail, keep tring.
            continue
        else:
            return True
        time.sleep(wait)
    return False


def in_booked_slot():
    """
    Checks if currently in the timeframe of a booked slot.

    :return `True` if currently in a slot `False` otherwise.
    """

    return get_current_slot() is not None


def log(msg: str):
    """
    Logs a message with the current time attached.

    :param msg: message to print.
    """

    t_now = datetime.utcnow()
    print(f"[{t_now}] {msg}")
