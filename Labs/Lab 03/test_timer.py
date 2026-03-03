from time import perf_counter_ns
from datetime import date
import csv
import tempfile
from pprint import pprint
from typing import Callable

import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

from csv_gen import csv_write_records
from record_manager import SalesDB, SaleRecord, USD


def test_timer() -> dict[str, dict[int, list[int]]]:
    repetitions = 10
    sizes = [0, 1, 10, 100, 1_000, 10_000, 100_000, 1_000_000]
    tests = [
        "load file",
        "latest", "latest with index",
        "total revenue",
        "duplicates", "duplicates with index",
        "by id", "by id with index"
    ]
    timings: dict[str, dict[int, list[int]]] = {test: {size: [] for size in sizes} for test in tests}

    def load_file():
        nonlocal fd
        nonlocal db

        with open(fd.name, "r") as fd2:
            f = csv.DictReader(fd2)

            for rec in f:
                sale_id = int(rec["sale_id"])
                sale_date = date.fromisoformat(rec["sale_date"])
                amount = USD(rec["amount"])
                product = rec["product"]

                db.insert(SaleRecord(sale_id, sale_date, amount, product))

    def timing_helper(desc: str, fn: Callable, *args, **kwargs):
        nonlocal timings
        start = perf_counter_ns()
        fn(*args, **kwargs)
        end = perf_counter_ns()
        timings[desc][n].append(end - start)

    for n in sizes:
        db = SalesDB()

        # create temporary file to write/load generated records
        with tempfile.NamedTemporaryFile(mode='w', delete_on_close=False) as fd:
            csv_write_records(n, fd)

            fd.close()

            # time loading records from csv
            load_file()  # prevent first iteration being longer than normal
            for i in range(repetitions):
                db.clear()
                timing_helper("load file", load_file)

        # time finding latest record
        db.get_latest()
        for i in range(repetitions):
            db.clear_date_cache()
            timing_helper("latest", db.get_latest)

        # time finding latest record with date index cached
        db.get_latest()
        for i in range(repetitions):
            timing_helper("latest with index", db.get_latest)

        # time finding total revenue
        db.total_revenue()
        for i in range(repetitions):
            timing_helper("total revenue", db.total_revenue)

        # time finding duplicate ids
        db.get_duplicates()
        for i in range(repetitions):
            db.clear_id_cache()
            timing_helper("duplicates", db.get_duplicates)

        # time finding duplicate ids with id index cached
        db.get_duplicates()
        for i in range(repetitions):
            timing_helper("duplicates with index", db.get_duplicates)

        # time retrieving records by id
        db.get_by_id(-1)
        for i in range(repetitions):
            db.clear_id_cache()
            timing_helper("by id", db.get_by_id, -1)

        # time retrieving records by id with id index cached
        db.get_by_id(-1)
        for i in range(repetitions):
            timing_helper("by id with index", db.get_by_id, -1)

    return timings


pprint(test_timer(), compact=True, width=240, underscore_numbers=True, sort_dicts=False)
