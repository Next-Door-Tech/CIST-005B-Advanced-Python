import csv
from typing import NamedTuple, TypeAlias
from datetime import date
import decimal
from decimal import Decimal

decimal.setcontext(decimal.Context(rounding=decimal.ROUND_HALF_UP))

headers = ("sale_id", "sale_date", "amount", "product")


class SaleDB:
    """Database of sales records."""

    class Record(NamedTuple):
        """Sales record."""

        sale_id: int
        sale_date: date
        amount: Decimal
        product: str

    _records: dict[int, Record]  # hashmap of sales records
    _ids: dict[int, list[int]]  # maps sales ids to hashes for fast search
    _dates: dict[date, list[int]]  # maps dates to hashes for fast search


def main() -> None:
    database = SaleDB()

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
