import csv
from time import *
from typing import NamedTuple
from datetime import date
import decimal

decimal.setcontext(decimal.Context(rounding=decimal.ROUND_HALF_UP))


class USD(decimal.Decimal):
    """United States Dollars represented as decimal.Decimal"""

    def __str__(self):
        return "$" + super().quantize(decimal.Decimal('0.01')).__str__()


headers = ("sale_id", "sale_date", "amount", "product")


class SaleRecord(NamedTuple):
    """Sales record."""

    sale_id: int
    sale_date: date
    amount: USD
    product: str


class SalesDB:
    """Database of sales records."""

    _records: list[SaleRecord]  # list of sales records

    _ids_initialized: bool
    _ids: dict[int, list[SaleRecord]]  # cache mapping sales ids to hashes for fast search

    _dates_initialized: bool
    _dates: dict[date, list[SaleRecord]]  # cache mapping dates to hashes for fast search

    def __init__(self):
        self._records: list[SaleRecord] = list()  # list of sales records

        self._ids_initialized: bool = False
        self._ids: dict[int, list[SaleRecord]] = dict()  # sorted cache mapping sales ids to hashes for fast search

        self._dates_initialized: bool = False
        self._dates: dict[date, list[SaleRecord]] = dict()  # cache mapping dates to hashes for fast search

    def __len__(self):
        return self._records.__len__()

    def clear(self):
        del self._records, self._ids, self._dates
        self.__init__()

    def insert(self, new_record: SaleRecord):
        self._records.append(new_record)
        self._ids_initialized = False
        self._dates_initialized = False

    def get_by_id(self, search_id: int) -> tuple[SaleRecord, ...]:
        if not self._ids_initialized:
            self._construct_id_cache()

        return tuple(self._ids[search_id])

    def get_by_date(self, search_date: date) -> tuple[SaleRecord, ...]:
        if not self._dates_initialized:
            self._construct_date_cache()

        return tuple(self._dates[search_date])

    def get_latest(self) -> tuple[SaleRecord, ...]:
        if self.__len__() == 0:
            return tuple()

        if not self._dates_initialized:
            self._construct_date_cache()

        return tuple(next(reversed(self._dates.values())))  # return first item of reverse iterator over dates

    def total_revenue(self) -> USD:
        total = USD('0.00')

        for rec in self._records:
            total += rec.amount

        return total

    def get_duplicates(self) -> tuple[SaleRecord, ...]:
        if not self._ids_initialized:
            self._construct_id_cache()

        result = list()

        for rec in self._ids.values():
            if len(rec) > 1:
                result.extend(rec)

        return tuple(result)

    def _construct_id_cache(self):
        self.clear_id_cache()

        # sorted(key) needs to be a function so key=SaleRecord.sale_id does not work
        for rec in sorted(self._records, key=(lambda r: r.sale_id)):
            self._ids.setdefault(rec.sale_id, []).append(rec)

        self._ids_initialized = True

    def clear_id_cache(self):
        self._ids_initialized = False
        self._ids.clear()

    def _construct_date_cache(self):
        self.clear_date_cache()

        # sorted(key) needs to be a function so key=SaleRecord.sale_id does not work
        for rec in sorted(self._records, key=(lambda r: r.sale_date)):
            self._dates.setdefault(rec.sale_date, []).append(rec)

        self._dates_initialized = True

    def clear_date_cache(self):
        self._dates_initialized = False
        self._dates.clear()


def print_menu():
    print(
        """
        Select an option:
            1: Load in sales data from CSV
            2: Retrieve the latest sale
            3: Compute the total revenue
            4: Check for duplicate sale IDs
            5: Search for a sale by its ID

            0: Reprint this menu
            -1: Exit
            -2: Print debug options
        """
    )


def print_debug():
    print_menu()

    print(
        """
            [Debug]
            6: Clear loaded data
            7: Reset caches
        """
    )


def get_option() -> int:
    for i in range(3):
        response = input("Option: ")
        match response.lower():
            case '1' | "load":
                return 1
            case '2' | "retrieve" | "latest":
                return 2
            case '3' | "compute" | "total" | "revenue":
                return 3
            case '4' | "check" | "duplicate":
                return 4
            case '5' | "search" | "id":
                return 5
            case '6' | "clear":
                return 6
            case '7' | "cache":
                return 7
            case '0' | 'h' | '?' | "help":
                return 0
            case '-1' | 'q' | "quit" | "exit":
                return -1
            case '-2' | "debug":
                return -2
            case _:
                print(f'\tError: Unknown option: "{response}"')
    else:
        print("Too many invalid options passed.")
        return -1


def load_file(db: SalesDB) -> int:
    path = input("Enter file path: ")

    try:
        start = perf_counter_ns()
        with open(path, "r") as fd:
            f = csv.DictReader(fd)

            for rec in f:
                sale_id = int(rec["sale_id"])
                sale_date = date.fromisoformat(rec["sale_date"])
                amount = USD(rec["amount"])
                product = rec["product"]

                db.insert(SaleRecord(sale_id, sale_date, amount, product))
        end = perf_counter_ns()

        print(f"\t{len(db)} records loaded.")
        return end - start
    except FileNotFoundError as E:
        print(E)
        return -1


def print_latest_sale(db: SalesDB) -> int:
    start = perf_counter_ns()
    if len(db) == 0:
        print("Error: no sales records loaded.")
        return perf_counter_ns() - start

    print("Most recent sales record(s):")

    start = perf_counter_ns()
    latest = db.get_latest()
    end = perf_counter_ns()

    for rec in latest:
        print('\t', rec)

    print()

    return end - start


def print_total_revenue(db: SalesDB) -> int:
    start = perf_counter_ns()
    rev = db.total_revenue()
    end = perf_counter_ns()

    print(f"Total revenue: {rev}")
    print()

    return end - start


def check_duplicates(db: SalesDB) -> int:
    start = perf_counter_ns()
    duplicates = db.get_duplicates()
    end = perf_counter_ns()

    print(f"{len(duplicates)} records with duplicate ids found:")

    for rec in duplicates:
        print('\t', rec)

    print()

    return end - start


def search_by_id(db: SalesDB) -> int:
    try:
        search_id = int(input("ID to search for: "))
    except ValueError:
        print("\tError: invalid input.")
        return -1

    start = perf_counter_ns()
    results = db.get_by_id(search_id)
    end = perf_counter_ns()

    if len(results) == 0:
        print("No records found.")

    elif len(results) == 1:
        print("One record found:")
        print('\t', results[0])

    else:
        print(f"Warning: multiple records found ({len(results)}):")
        for rec in results:
            print('\t', rec)

    print()
    return end - start


def main() -> None:
    database = SalesDB()

    print_menu()

    while True:
        match get_option():
            case -1:  # Quit
                print("Exiting...")
                return

            case 0:  # Reprint menu
                print_menu()

            case 1:  # Load file to database
                print(f"Elapsed time: {load_file(database)} ns.")

            case 2:  # Load latest sale
                print(f"Elapsed time: {print_latest_sale(database)} ns.")

            case 3:  # Compute total revenue
                print(f"Elapsed time: {print_total_revenue(database)} ns.")

            case 4:  # Check for duplicate IDs
                print(f"Elapsed time: {check_duplicates(database)} ns.")

            case 5:  # Search by ID
                print(f"Elapsed time: {search_by_id(database)} ns.")

            case -2:
                print_debug()

            case 6:  # Clear loaded data
                print("Clearing loaded sales data.")
                database.clear()

            case 7:
                print("Clearing loaded sales data caches.")
                database.clear_id_cache()
                database.clear_date_cache()


main()
