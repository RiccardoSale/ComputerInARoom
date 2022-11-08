import init
import movement


def create_change_dir(id):
    dirname = '/obj/objective_' + str(id)
    if not init.os.path.exists(init.cur_dir + dirname):
        init.os.makedirs(init.cur_dir + dirname)
    init.cd = init.cur_dir + dirname


def cruise_dec(x, y):
    print("cruise decel")
    if y[3] > x[3]:  # Se tempo di accelerazione dell y è maggiore
        print("Y",y[3],y[5],init.datetime.now())
        init.sched.add_job(movement.start_cruise, 'interval', seconds=y[3], id='start_cruise', max_instances=1)
    else:
        print("X")
        init.sched.add_job(movement.start_cruise, 'interval', seconds=x[3], id='start_cruise', max_instances=1)
    if y[3]+y[4] != 0:
        init.sched.add_job(movement.f_dec_y, 'interval', seconds=y[3] + y[5], id='f_dec_y', max_instances=1)
    if x[3]+x[4] != 0:
        init.sched.add_job(movement.f_dec_x, 'interval', seconds=x[3] + x[5], id='f_dec_x', max_instances=1)

    print(x[3]+x[4])
    if x[3]+x[4] == 0: #caso y che decelera e x ferma
        print("ziotrenoooo")
        init.sched.add_job(movement.charge, 'interval', seconds=y[1], id='charge',max_instances=1)  # todo chiamare start cruise



def delta_time(e):
    e = e.split('+')[0]
    e = init.datetime.strptime(e, '%Y-%m-%dT%H:%M:%S')
    s = init.datetime.now()
    return e - s


def take_photo(img, type, coordx='', coordy='', row=''):
    response = init.requests.get(init.url + "observation").content
    data = init.json.loads(response)
    coordx = data['telemetry']['x']
    coordy = data['telemetry']['y']

    img_png = init.base64.b64decode(init.json.loads(img)['image'])
    img_np = init.np.frombuffer(img_png, dtype=init.np.uint8)
    img_cv = init.cv2.imdecode(img_np, flags=init.cv2.IMREAD_COLOR)
    #init.cv2.imwrite(init.os.path.join(init.cd, '|' + str(type) + '|' + str(row) + '|' + str(coordx) + "|" + str(coordy) + init.image_format),img_cv)
    #init.cv2.imwrite('|' + str(type) + '|' + str(row) + '|' + str(coordx) + "|" + str(coordy) + init.image_format, img_cv)
    init.cv2.imwrite(init.os.path.join(init.cd, '|' + str(type) + '|' + str(row) + '|' + str(coordx) + "|" + str(coordy) + init.image_format),img_cv)

    #print("NON SONO RIUSCITO A SCATTARE ")

