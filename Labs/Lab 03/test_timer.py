import csv
from pprint import pprint

from csv_gen import csv_write_records
from record_manager import SalesDB, SaleRecord, USD
import tempfile
from time import perf_counter_ns
from datetime import date


def test_timer() -> dict[str, dict[int, list[int]]]:
    repetitions = 10
    sizes = [10, 100, 1_000, 10_000, 100_000]
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

                # load records from file
                start = perf_counter_ns()
                load_file()
                end = perf_counter_ns()
                timings["load file"][n].append(end - start)

        # time finding latest record
        db.get_latest()
        for i in range(repetitions):
            db.clear_date_cache()

            start = perf_counter_ns()
            db.get_latest()
            end = perf_counter_ns()
            timings["latest"][n].append(end - start)

        # time finding latest record with date index cached
        db.get_latest()
        for i in range(repetitions):
            start = perf_counter_ns()
            db.get_latest()
            end = perf_counter_ns()
            timings["latest with index"][n].append(end - start)

        # time finding total revenue
        db.total_revenue()
        for i in range(repetitions):
            start = perf_counter_ns()
            db.total_revenue()
            end = perf_counter_ns()
            timings["total revenue"][n].append(end - start)

        # time finding duplicate ids
        db.get_duplicates()
        for i in range(repetitions):
            db.clear_id_cache()
            start = perf_counter_ns()
            db.get_duplicates()
            end = perf_counter_ns()
            timings["duplicates"][n].append(end - start)

        # time finding duplicate ids with id index cached
        db.get_duplicates()
        for i in range(repetitions):
            start = perf_counter_ns()
            db.get_duplicates()
            end = perf_counter_ns()
            timings["duplicates with index"][n].append(end - start)

        # time retrieving records by id
        db.get_by_id(-1)
        for i in range(repetitions):
            db.clear_id_cache()
            start = perf_counter_ns()
            db.get_by_id(-1)
            end = perf_counter_ns()
            timings["by id"][n].append(end - start)

        db.get_by_id(-1)
        for i in range(repetitions):
            start = perf_counter_ns()
            db.get_by_id(-1)
            end = perf_counter_ns()
            timings["by id with index"][n].append(end - start)

    return timings


pprint(test_timer(), compact=True, width=240)
