import init
import melvin
import objective_photo
import utility

TOTAL_X = 21600
TOTAL_Y = 10800


# Distance beetween two coordinates based on module
def dist(one, two, module=1):
    if module != 1:
        return (two - one) % module
    else:
        return two - one


def f_min_xy(value):
    if value > 3:
        return 1
    else:
        if 10 - pow(value, 2) < 0:
            return 1
        else:
            return init.math.trunc(init.math.sqrt(10 - pow(value, 2))) + 1


def filter_matrix(m):
    for i in range(len(m) - 1, 0, -1):
        aux = m[i]
        if m[i][2] == 0: m.remove(aux)
    return m


def generate(tp, max, min, curr, dec, t_to_target, delta, m, negative, multiple=False, ):
    for i in range(0, max - min + 1, 1):
        cand = int(min + i)  # Candidata velocità x

        if (cand < curr):  # Calcolo anche la decelerazione in x
            p_dec_1 = (((curr + cand + 1) / 2) * (curr - dec + 2)) + (
                    ((curr - 1 + cand) / 2) * (curr - cand)) + (
                              0.5 * (curr - cand))  # pixel coperti in decelerazione
            p_dec_2 = (((cand + dec + 1) / 2) * (cand - dec + 2)) + (
                    ((cand - 1 + dec) / 2) * (cand - dec)) + (
                              0.5 * (cand - dec))  # pixel coperti in decelerazione
            t_dec_1 = 2 * abs(curr - cand)
            t_dec_2 = 2 * abs(cand - dec)  # tempo decelerazione
            t_mov = t_dec_1 + t_dec_2
            p_mov = p_dec_1 + p_dec_2
            t_acc = t_dec_1
            t_dec = t_dec_2

            if (p_mov > abs(delta)):
                continue
        if cand > curr:  # Accelero la y
            p_acc = 2 * (((curr + cand - 1) / 2) * (cand - curr)) + (
                    0.5 * (cand - curr))  # pixel coperti in accelerazione
            p_dec = (((cand + dec + 1) / 2) * (cand - dec + 2)) + (
                    ((cand - 1 + dec) / 2) * (cand - dec)) + (
                            0.5 * (cand - dec))  # pixel coperti in decelerazione
            t_acc = 2 * abs(cand - curr)  # tempo accelerazione
            t_dec = 2 * abs(cand - dec)  # tempo decelerazione
            t_mov = t_acc + t_dec
            p_mov = p_acc + p_dec
            if (p_acc + p_dec) > abs(delta):  # Se distanza non copribile, p_acc+p_dec > distanza
                break
        if cand == curr:
            t_acc = t_dec = t_mov = p_mov = 0
        fuel = init.math.sqrt((pow(cand - curr, 2))) / 100 + init.math.sqrt(
            (pow(cand - dec, 2))) / 100  # Fuel consumato per movimento in y

        if delta >= 0:
            cruise = delta - p_mov  # distanza con velocità di crociera y
        else:
            if tp == 'x':
                cruise = 21600 - abs(delta) - p_mov
            else:
                cruise = 10800 - abs(delta) - p_mov
        t_cruise = abs(int(cruise / cand))  # tempo di crociera y
        t_tot = (t_cruise + t_mov)  # tempo totale viaggio in y

        if t_tot <= t_to_target:
            if tp == 'x':
                m.append([cand, t_tot, int(fuel * 100) / 100, t_acc, t_dec, t_cruise])
                if multiple == False:
                    return m
            else:
                if negative == True:
                    if delta < 0:
                        m.append([cand, t_tot, int(fuel * 100) / 100, t_acc, t_dec, t_cruise])
                    else:
                        m.append([-cand, t_tot, int(fuel * 100) / 100, t_acc, t_dec, t_cruise])
                else:
                    m.append([cand, t_tot, int(fuel * 100) / 100, t_acc, t_dec, t_cruise])
    m = filter_matrix(m)
    return m


def calculate_distance_time_fuel(final_x, final_y, t_to_target, curr_x, curr_y, coord_x, coord_y, multiple=False):
    dec_y = 0  # vy finale, verosimilmente useremo quasi sempre 0
    dec_x = 10  # vx finale, non a 0, sfruttiamo movimento lungo paralleli, x sempre attiva
    # Servono per timing
    init.real_vx = curr_x
    init.real_vy = curr_y

    min_y = f_min_xy(curr_x)
    min_x = 10

    max_y = init.math.trunc(init.math.sqrt(4900 - pow(curr_x, 2)))  # Massima y assumibile data vx attuale
    max_x = init.math.trunc(init.math.sqrt(4900 - pow(curr_y, 2)))  # Massima x assumibile data la vy attuale

    delta_y = dist(coord_y, final_y)
    delta_x = dist(coord_x, final_x)

    m_vel_y = []  # create_v(max_y, min_y) #Creo array per movimento y
    m_vel_x = []  # create_v(max_x, min_x) #Creo array per movimento x
    m_vel_y2 = []
    m_multiple = []
    m_vel_x = generate('x', max_x, min_x, curr_x, dec_x, t_to_target, delta_x, m_vel_x, multiple)

    if coord_y > final_y:
        negative = True
    else:
        negative = False
    m_vel_y = generate('y', max_y, min_y, curr_y, dec_y, t_to_target, delta_y, m_vel_y, negative)
    m_vel_y2 = generate('y', max_y, min_y, curr_y, dec_y, t_to_target, - delta_y, m_vel_y2, negative)
    list_y = m_vel_y + m_vel_y2
    list_y.sort(key=lambda el: el[2])
    if multiple:
        for x in m_vel_x:
            for y in list_y:
                if y[1] < x[1]:
                    m_multiple.append([x, y])
                    break
        return m_multiple
    x = m_vel_x[0]
    for i in list_y:
        if i[1] < x[1]:
            y = i
            break

    return [x, y]


def calculator():
    print("Sono entrato in calculator")
    response = init.requests.get(init.url + "observation").content
    data = init.json.loads(response)
    curr_x = int(data['telemetry']['vx'])  # vx attuale
    curr_y = int(data['telemetry']['vy'])  # vy attuale
    # salvo y attuale #Nelle iterazioni succ sarà la coordinata del punto appena fatto
    coord_y = int(data['telemetry']['y'])
    coord_x = int(data['telemetry']['x'])

    init.active_objectives.sort(key=lambda k: dist(curr_y, k['zone']['top'], TOTAL_Y) + dist(curr_x, k['zone']['left'], TOTAL_X),reverse=False)

    vel_arr = [[] for _ in range(len(init.active_objectives))]
    t_route = 0
    count = 0
    limit = float('+inf')
    data_first = None
    tp_first = 's'
    failed = False
    pos_min = float('inf')
    while True and count < limit and len(init.active_objectives) != 0:
        for objective, x in enumerate(init.active_objectives):
            print("sto ciclando")
            zone = x['zone']
            final_x = zone['left']
            final_y = (zone['top'] + zone['bottom']) // 2
            x_end_target = zone['right']

            t_to_target = utility.delta_time(x['end'])
            t_to_target = int(int(t_to_target.total_seconds()) * 0.9)

            if len(init.active_objectives) == 1 and t_to_target > 5400:
                print("Esco da calculator perche ho ancora un solo obb da fare e molto tempo a disposizione")
                return

            lens = x['optic_required'].lower()
            coverage = int(x['coverage_required']) / 100
            pixel_photo = ((zone['bottom'] - zone['top']) % 10800) * coverage
            dic_limit = {'narrow': 550, 'normal': 750, 'wide': 950}

            if pixel_photo > dic_limit[lens]:  # multiple layer photos
                single_layer = False
                photo_data = objective_photo.area(zone, lens, coverage)
                if x == init.active_objectives[0]:  # Se siamo al primo
                    data_first = photo_data
                    tp_first = 'm'
                expected_t = photo_data[4]
                t_to_target -= expected_t
            else:
                single_layer = True
                dist_ = dist(final_x, x_end_target)
                init.t_photo = dist_ / 10
                t_to_target -= init.t_photo

            t_to_target -= t_route  # tolto tempo di viaggio fatto
            if t_to_target < 480:  # Evitiamo velocità troppo consumose
                init.active_objectives.pop(objective)
                print("sono uscito perche avevo meno di 8 minuti")
                break
            if count == 0:
                if single_layer == True:
                    res = calculate_distance_time_fuel(final_x, final_y, t_to_target, curr_x, curr_y, coord_x, coord_y,True)
                    print("SINGLE: ",res)
                else:
                    res = calculate_distance_time_fuel(photo_data[0], photo_data[3][0], t_to_target, curr_x, curr_y,
                                                       coord_x, coord_y,
                                                       True)
                    print("MULTI: ",res)

                if len(res) == 0:  # skippo tale obbiettivo
                    print("HO SKIPPATO OBBIETTIVO PERCHE RES E VUOTO")
                    init.active_objectives.pop(objective)
                    break

                limit = min(limit, len(res))
                pos_min = min(pos_min,objective)
                vel_arr[objective] = res

            if single_layer:
                # Sommato tempo della x (Tempo reale di arrivo all'obiettivo)
                t_route += vel_arr[objective][count][0][1] + init.t_photo
            else:
                # Sommato tempo della x (Tempo reale di arrivo all'obiettivo)
                t_route += vel_arr[objective][count][0][
                               1] + expected_t  # Sommato tempo della x (Tempo reale di arrivo all'obiettivo)

            coord_x = final_x
            coord_y = final_y
        if not failed and len(init.active_objectives) != 0:
            init.vel_route = count
            if tp_first == 's':
                for el in init.data:
                    if el['id'] == init.active_objectives[pos_min]['id']:
                        print("Ho modificato obbiettivo a done -> true")
                        el['done'] = True
                print("Ho cominciato a fare un obbiettivo singolo ( POSSO ROUTE)")
                melvin.go_and_scan_single(vel_arr[pos_min][count][0], vel_arr[pos_min][count][1],
                                          init.active_objectives[pos_min]['optic_required'].lower(), init.active_objectives[pos_min]['id'])

            else:
                for el in init.data:
                    if el['id'] == init.active_objectives[pos_min]['id']:
                        print("Ho modificato obbiettivo a done -> true")
                        el['done'] = True
                print("Ho cominciato a fare un obbiettivo multiplo ( POSSO ROUTE)")
                melvin.go_and_scan_multiple(vel_arr[pos_min][count][0], vel_arr[pos_min][count][1], data_first[3],
                                            init.active_objectives[pos_min]['optic_required'].lower(), data_first[2],
                                            init.active_objectives[pos_min]['id'])

            return
        else:
            failed = False
            count += 1
            t_route = 0
    print("USCITO DA CALCULATOR")
    return
