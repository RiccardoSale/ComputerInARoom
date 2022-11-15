import init


# X deceleration
def f_dec_x(vel_x=10):
    print("Decelera x")
    init.requests.put(init.url + "control",
                      json={"state": "active", "camera_angle": "wide", "vel_x": vel_x, "vel_y": init.real_vy})
    init.sched.remove_job('decx')
    init.real_vx = vel_x
    return


# Y deceleration
def f_dec_y(vel_y=0):
    print("Decelera y")
    init.requests.put(init.url + "control",
                      json={"state": "active", "camera_angle": "wide", "vel_x": init.real_vx, "vel_y": vel_y})
    init.sched.remove_job('decy')
    init.real_vy = vel_y
    return


def charge():
    print('start cruise_or charge', init.datetime.now())
    print("REALI", init.real_vx, init.real_vy)
    init.sched.remove_job('charge')
    init.requests.put(init.url + "control",json={"state": "charge", "camera_angle": "wide", "vel_x": init.real_vx, "vel_y": init.real_vy})
    return

# Start cruise (we reach max speed)
def cruise_charge():
    print('start cruise_or charge', init.datetime.now())
    print("REALI", init.real_vx, init.real_vy)
    init.requests.put(init.url + "control",json={"state": "charge", "camera_angle": "wide", "vel_x": init.real_vx, "vel_y": init.real_vy})
    init.sched.remove_job('cruisecharge')
    return


# Start descent (comando usato per photo a layer multipli )
def descent(time, idx_row):
    print("Scendo foto multipla")
    #init.sched.remove_job('descent' + str(idx_row))
    init.real_vx = 0
    init.real_vy = 8
    init.requests.put(init.url + "control",
                      json={"state": 'active', "camera_angle": 'wide', "vel_x": 0, "vel_y": 8})
    init.sched.add_job(cruise_charge, 'interval', seconds=42, id='cruisecharge', max_instances=1)

    if idx_row % 2 == 1:
        init.sched.add_job(f_dec_x, args=[-10], trigger='interval', seconds=time - 22, id='decx', max_instances=1)
    else:
        init.sched.add_job(f_dec_x, args=[10], trigger='interval', seconds=time - 22, id='decx', max_instances=1)
    init.sched.add_job(f_dec_y, 'interval', seconds=time - 16, id='decy', max_instances=1)
    return
