import csv
from typing import NamedTuple
from datetime import date
import decimal
from decimal import Decimal

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
            case '0' | 'h' | '?' | "help":
                return 0
            case '-1' | 'q' | "quit" | "exit":
                return -1
            case _:
                print(f'\tError: Unknown option: "{response}"')
    else:
        print("Too many invalid options passed.")
        return -1


def load_file():
    nonlocal database
    pass


def get_latest():
    pass


def total_revenue():
    pass


def check_duplicates():
    pass


def get_by_id():
    pass


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
                load_file()

            case 2:  # Load latest sale
                get_latest()

            case 3:  # Compute total revenue
                total_revenue()

            case 4:  # Check for duplicate IDs
                check_duplicates()

            case 5:  # Search by ID
                get_by_id()


main()
