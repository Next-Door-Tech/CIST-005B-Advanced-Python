import typing
import csv
from random import *
from datetime import date
from record_manager import headers


def rand_date(start: date = date(2000, 1, 1), end: date = date.today()) -> date:
    dmin = start.toordinal()
    dmax = end.toordinal()
    return date.fromordinal(randint(dmin, dmax))


def csv_gen(n: int, filename: str = None) -> None:
    if filename is None:
        filename = f"testdata_{n}.csv"

    with open(filename, "xw") as fd:
        csv_write_records(n, fd)


def csv_write_records(n: int, fd: typing.IO):
    products = ("widget", "thingy", "doohickey", "whirligig", "thingamabob", "whatsit", "springamathing", "doodad",
                "gizmo", "thingamajig", "gadget")

    f = csv.writer(fd)

    f.writerow(headers)

    seed(0)

    for i in range(n):
        f.writerow([i, rand_date(), f'{random() * 200:.2f}', products[randrange(len(products))]])
