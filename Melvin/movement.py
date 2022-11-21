import init


def f_dec_x(vel_x=10):
    """
    Decelerate x'velocity down to vel_x

    :param vel_x: veolcity target
    """

    print("Decelerate x",init.datetime.now())
    init.requests.put(init.url + "control", json={"state": "active", "camera_angle": "wide", "vel_x": vel_x, "vel_y": init.real_vy})
    init.sched.remove_job('decx')
    init.real_vx = vel_x


def f_dec_y(vel_y=0):
    """
    Decelerate y'velocity down to vel_y

    :param vel_y: veolcity target
    """

    print("Decelerate y",init.datetime.now())
    init.requests.put(init.url + "control", json={"state": "active", "camera_angle": "wide", "vel_x": init.real_vx, "vel_y": vel_y})
    init.sched.remove_job('decy')
    init.real_vy = vel_y


def cruise_charge():
    """
    Set Melvin's state to charge

    """

    print('Start cruise_or charge', init.datetime.now())
    init.requests.put(init.url + "control",json={"state": "charge", "camera_angle": "wide", "vel_x": init.real_vx, "vel_y": init.real_vy})
    init.sched.remove_job('cruisecharge')


def descent(time, idx_row):
    """
    Manages the timing for the accelerations and decelerations during the multi-layer objective two point descent

    :param time: descent's time
    :param idx_row: number of row it's in
    """

    init.real_vx = 0
    init.real_vy = 8
    init.requests.put(init.url + "control", json={"state": 'active', "camera_angle": 'wide', "vel_x": 0, "vel_y": 8})
    init.sched.add_job(cruise_charge, 'interval', seconds=42, id='cruisecharge', max_instances=1)

    if idx_row % 2 == 1:
        init.sched.add_job(f_dec_x, args=[-10], trigger='interval', seconds=time - 22, id='decx', max_instances=1)
    else:
        init.sched.add_job(f_dec_x, args=[10], trigger='interval', seconds=time - 22, id='decx', max_instances=1)
    init.sched.add_job(f_dec_y, 'interval', seconds=time - 16, id='decy', max_instances=1)
