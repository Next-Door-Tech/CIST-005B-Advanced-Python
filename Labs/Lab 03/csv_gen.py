import csv
from random import *
from datetime import date


def rand_date(start: date = date(2000, 1, 1), end: date = date.today()) -> date:
    dmin = start.toordinal()
    dmax = end.toordinal()
    return date.fromordinal(randint(dmin, dmax))


def csv_gen(n: int) -> None:
    headers = ("sale_id", "sale_date", "amount", "product")
    products = ("widget", "thingy", "doohickey", "whirligig", "thingamabob", "whatsit", "springamathing", "doodad",
                "gizmo", "thingamajig", "gadget")

    with open(f"testdata_{n}.csv", "w") as fd:
        f = csv.writer(fd)

        f.writerow(headers)

        seed(0)

        for i in range(n):
            f.writerow([i, rand_date(), f'{random() * 200:.2f}', products[randrange(len(products))]])


csv_gen(10)
csv_gen(100)
csv_gen(1000)
csv_gen(10000)
csv_gen(100000)
