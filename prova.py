y_scan = {i: [] for i in range(10800)}  # 8027

for i in range(8027 - 300, 8027 + 300 + 1):
    if i <= 8027:
        y_scan[i].append([16000, 17500])
        y_scan[i].append([2500, 10000])
    else:
        if i == 8028:
            y_scan[i].append([5000, 15000])
            y_scan[i].append([16000, 20000])
        else:
            y_scan[i].append([4000, 11000])
            y_scan[i].append([17000, 18000])



























def see_if_takephoto(y_center):
    y_start = y_center - 300 if y_center - 300 > 0 else 10800 + (y_center - 300)
    y_end = (y_center + 300) % 10800

    tmp = None
    l = []
    for i in range(y_start, y_end):
        if y_scan[i] != tmp:

            tmp = y_scan[i]
            if tmp == []:
                return []
            l.append(tmp)

    # c'è il caso lista vuota ??? CONTROLLARE

    if len(l) == 1:  # ho un unico intervallo posso returnare quello
        return l[0]  # vedere se funzia tramite pop

    new = []
    print("llll",l)
    for x in l[0]:
        new.append(x)
    for i in range(1, len(l)):
        temp_n = []
        for x in l[i]:
            for y in new:
                print("x", x)
                print("y", y)
                if y[0] <= x[0] and x[1] <= y[1]:
                    temp_n.append(x)
                elif x[0] <= y[0] and y[1] <= x[1]:
                    temp_n.append(y)
                elif y[0] <= x[0] and y[1] <= x[1] and y[1] >= x[0]:
                    temp_n.append([x[0], y[1]])
                elif y[0] >= x[0] and y[1] >= x[1] and y[0] <= x[1]:
                    temp_n.append([y[0], x[1]])
                print("tttt",temp_n)

        new = temp_n
    print("NEW: ", new)
    return new


see_if_takephoto(8027)
