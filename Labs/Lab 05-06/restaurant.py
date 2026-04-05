from dataclasses import dataclass
from collections.abc import Generator
from abc import ABC, abstractmethod
from enum import Enum, EnumType
from decimal import Decimal
from datetime import date, time, datetime, timedelta
from random import random, randint, uniform, choice, choices, seed
from typing import Protocol, cast

from common_lib.containers import LinkedList as llist, LinkedQueue as lqueue, LinkedStack as lstack  # noqa


def format_usd(amount: Decimal) -> str:
    return f"${Decimal(amount):.02f}"


type PreparationStepper = Generator[str]


class Preparable(Protocol):
    @abstractmethod
    def prepare(self, task_stack: lstack[PreparationStepper]) -> PreparationStepper:
        ...


@dataclass(frozen=True)
class Ingredient(Preparable, ABC):
    name: str
    # prep_time: timedelta


@dataclass(frozen=True)
class StockedIngredient(Ingredient):
    """An ingredient which is stored in the stockroom and does not need to be prepared."""

    # prep_time: timedelta = timedelta(seconds=15)

    @property
    def verb(self) -> str:  # noqa: PyRedeclarationInspection
        return f"Retrieving {self.name}"

    def prepare(self, task_stack: lstack[PreparationStepper]) -> PreparationStepper:
        task_stack.pop()
        yield self.verb


@dataclass(frozen=True)
class PreparationTask(Preparable):
    """A task required to prepare part of a menu item."""
    verb: str

    # prep_time: timedelta = timedelta(minutes=1)

    def prepare(self, task_stack: lstack[PreparationStepper]) -> PreparationStepper:
        task_stack.pop()
        yield self.verb.title()


@dataclass(frozen=True)
class PreparedIngredient(Ingredient):
    """An ingredient which must be prepared by combining other ingredients or performing other preparation tasks."""
    verb: str
    steps: tuple[Ingredient | PreparationTask, ...]

    # prep_time: timedelta = timedelta(minutes=1)

    def prepare(self, task_stack: lstack[PreparationStepper]) -> PreparationStepper:
        for step in self.steps:
            task_stack.push(step.prepare(task_stack))
            yield f"{self.verb} {self.name}:".capitalize()
        task_stack.pop()
        yield f"Finished {self.verb} {self.name}."


class Ingredients:
    frozen_patty = StockedIngredient("frozen hamburger patty")
    cheese = StockedIngredient("cheese slice")
    bun = StockedIngredient("burger bun")
    paper = StockedIngredient("wrapping paper")

    burger_patty = PreparedIngredient("hamburger patty", "cooking", (
        frozen_patty,
        PreparationTask("grilling patty"),
        PreparationTask("flipping patty"),
        PreparationTask("grilling patty")
    ))

    cheeseburger_patty = PreparedIngredient("cheeseburger patty", "cooking", (
        frozen_patty,
        cheese,
        PreparationTask("grilling patty"),
        PreparationTask("flipping patty"),
        PreparationTask("adding cheese slice"),
        PreparationTask("grilling patty")
    ))

    hamburger = PreparedIngredient("hamburger", "making", (
        bun,
        burger_patty,
        PreparationTask("placing patty on bottom bun"),
        PreparationTask("placing top bun on patty"),
        paper,
        PreparationTask("wrapping burger in paper")
    ))

    cheeseburger = PreparedIngredient("cheeseburger", "making", (
        bun,
        cheeseburger_patty,
        PreparationTask("placing patty on bottom bun"),
        PreparationTask("placing top bun on patty"),
        paper,
        PreparationTask("wrapping burger in paper")
    ))

    double_hamburger = PreparedIngredient("double hamburger", "making", (
        bun,
        burger_patty,
        PreparationTask("placing patty on bottom bun"),
        burger_patty,
        PreparationTask("placing patty on lower patty"),
        PreparationTask("placing top bun on upper patty"),
        paper,
        PreparationTask("wrapping burger in paper")
    ))

    double_cheeseburger = PreparedIngredient("double cheeseburger", "making", (
        bun,
        cheeseburger_patty,
        PreparationTask("placing patty on bottom bun"),
        cheeseburger_patty,
        PreparationTask("placing patty on lower patty"),
        PreparationTask("placing top bun on upper patty"),
        paper,
        PreparationTask("wrapping burger in paper")
    ))

    potato = StockedIngredient("potato")
    onion = StockedIngredient("onion")
    batter = StockedIngredient("batter")
    fries_carton = StockedIngredient("fries carton")

    french_fries = PreparedIngredient("french fries", "making", (
        potato,
        PreparationTask("slicing potato"),
        PreparationTask("placing slices in deep fry basket"),
        PreparationTask("submerging basket"),
        PreparationTask("raising basket"),
        fries_carton,
        PreparationTask("scooping fries")
    ))

    onion_rings = PreparedIngredient("onion rings", "making", (
        onion,
        PreparationTask("slicing onion"),
        batter,
        PreparationTask("dipping slices in batter"),
        PreparationTask("placing slices in deep fry basket"),
        PreparationTask("submerging basket"),
        PreparationTask("raising basket"),
        fries_carton,
        PreparationTask("scooping onion rings")
    ))

    cup = StockedIngredient("cup")
    ice = StockedIngredient("ice")
    lid = StockedIngredient("lid")
    straw = StockedIngredient("straw")

    soda = PreparedIngredient("soft drink w/o ice", "preparing", (
        cup,
        PreparationTask("pouring soda"),
        lid,
        straw,
        PreparationTask("putting lid on soda")
    ))

    iced_soda = PreparedIngredient("soft drink w/ ice", "preparing", (
        cup, ice,
        PreparationTask("pouring ice"),
        PreparationTask("pouring soda"),
        lid,
        straw,
        PreparationTask("putting lid on soda")
    ))

    bag = StockedIngredient("bag")
    tray = StockedIngredient("tray")


@dataclass(frozen=True)
class MenuItem(Preparable):
    """An item on a restaurant menu. """
    name: str
    price: Decimal
    description: str
    item: PreparedIngredient

    def prepare(self, task_stack: lstack[PreparationStepper]) -> PreparationStepper:
        task_stack.push(self.item.prepare(task_stack))
        yield f"Preparing a {self.name}:"
        task_stack.pop()
        yield f"Finished preparing a {self.name}:"


class MenuEnumMeta(EnumType):
    def __getitem__(cls, item) -> MenuItem:
        if isinstance(item, int):
            return list(cls)[item].value
        else:
            return super().__getitem__(item).value


class MenuEnum(Enum, metaclass=MenuEnumMeta):
    pass


class Menu:
    class Entrees(MenuEnum):
        burger = MenuItem(
            "Hamburger", Decimal('10.99'), "A hamburger with no cheese.",
            Ingredients.hamburger
        )

        cheeseburger = MenuItem(
            "Cheeseburger", Decimal('11.99'), "A hamburger with cheese.",
            Ingredients.cheeseburger
        )

        double_burger = MenuItem(
            "Double Hamburger", Decimal('13.99'), "A hamburger with two patties and no cheese.",
            Ingredients.double_hamburger
        )

        double_cheeseburger = MenuItem(
            "Double Cheeseburger", Decimal('14.99'), "A hamburger with two patties no cheese.",
            Ingredients.double_cheeseburger
        )

    class Sides(MenuEnum):
        fries = MenuItem(
            "French Fries", Decimal('3.99'), "A container of french fries.",
            Ingredients.french_fries
        )

        onion_rings = MenuItem(
            "Onion Rings", Decimal('5.99'), "A container of onion rings.",
            Ingredients.onion_rings
        )

    class Drinks(MenuEnum):
        drink_no_ice = MenuItem(
            "Soft Drink", Decimal('3.99'), "A soft drink without ice.",
            Ingredients.soda
        )

        drink_ice = MenuItem(
            "Soft Drink with Ice", Decimal('3.99'), "A soft drink with ice.",
            Ingredients.iced_soda
        )


@dataclass
class Customer:
    name: str


class Order(Preparable, ABC):
    customer: Customer
    items: list[MenuItem]
    subtotal: Decimal
    tip: Decimal
    grand_total: Decimal
    status: Status

    class Status(Enum):
        PLACED = "Placed"
        PREPARING = "Preparing"
        COMPLETED = "Completed"
        DELIVERED = "Delivered"

    def __init__(self, name: str, tip: Decimal, *items: MenuItem) -> None:
        self.name = name
        self.items = list(items)
        self.subtotal = sum((item.price for item in self.items), start=Decimal('0.00'))
        self.tip = Decimal(tip)

        self.total = self.subtotal + self.tip
        self.status = self.Status.PLACED

    def prepare(self, task_stack: lstack[PreparationStepper]) -> PreparationStepper:
        self.status = self.Status.PREPARING

        for item in self.items:
            task_stack.push(item.prepare(task_stack))
            yield f"Preparing order for {self.name}:"

        self.status = self.Status.COMPLETED

        task_stack.pop()
        yield f"Finished preparing order for {self.name}"

        self.deliver()

    @abstractmethod
    def delay_preparation(self, cur_time: datetime) -> bool:
        """Whether the order should be prepared now or delayed for a bit."""
        ...

    @abstractmethod
    def deliver(self) -> None:
        ...


class DineInOrder(Order):
    table: int

    def __init__(self, name: str, table: int, tip: Decimal, *items: MenuItem) -> None:
        super().__init__(name, tip, *items)
        self.table = table

        self.items = cast(list[MenuItem | PreparationTask], self.items)  # type hint
        self.items.append(PreparationTask("placing items on tray"))
        self.items.append(PreparationTask(f"delivering to table {table}"))

    def delay_preparation(self, cur_time: datetime) -> bool:
        return False

    def deliver(self) -> None:
        print(f"Serving order to table {self.table}.")
        self.status = self.Status.DELIVERED


class TakeoutOrder(Order):
    pickup_time: datetime

    def __init__(self, name: str, pickup_time: datetime, tip: Decimal, *items: MenuItem) -> None:
        super().__init__(name, tip, *items)
        self.pickup_time = pickup_time

    def delay_preparation(self, cur_time: datetime) -> bool:
        return self.pickup_time > cur_time + timedelta(minutes=30)

    def deliver(self) -> None:
        print(f"Order ready for {self.name}.")
        self.status = self.Status.DELIVERED


class OrderFinished(Exception):
    pass


class PrepStation:
    def __init__(self) -> None:
        self.current_order: Order | None = None
        self.task_stack = lstack[PreparationStepper]()
        self.task_stack.append(iter(self.idle()))

    def is_working(self) -> bool:
        return self.current_order is not None

    def idle(self) -> Generator[str, None, Order]:
        while True:
            if not self.is_working():
                yield "Not working on any order."
            else:
                assert self.current_order is not None  # typing hint
                self.task_stack.push(self.current_order.prepare(self.task_stack))
                yield f"Starting to prepare order for {self.current_order.name}:"
                return self.current_order

    def current_action(self) -> str:
        return next(self.task_stack.peek())


class Restaurant:
    open_time: time
    close_time: time

    stations: list[PrepStation]
    tables: list[Customer | None]

    completed_orders: list[Order]
    order_queue: lqueue[Order]
    active_orders: llist[Order]

    def __init__(self, num_stations: int = 3, num_tables: int = 10,
                 open_time: time = time(hour=8), close_time: time = time(hour=20)) -> None:
        self.open_time = open_time
        self.close_time = close_time

        self.stations = [PrepStation() for _ in range(num_stations)]
        self.tables = [None for _ in range(num_tables)]

        self.completed_orders = []
        self.order_queue = lqueue()
        self.active_orders = llist()

    def generate_new_order(self, cur_time: datetime) -> Order:
        name = choice([  # AI generated list of names
            "Liam", "Noah", "Oliver", "Elijah", "James", "William", "Benjamin", "Lucas", "Henry", "Alexander", "Mason",
            "Michael", "Ethan", "Daniel", "Jacob", "Logan", "Jackson", "Levi", "Sebastian", "Mateo", "Jack", "Owen",
            "Theodore", "Aiden", "Samuel", "Joseph", "John", "David", "Wyatt", "Matthew", "Luke", "Asher", "Carter",
            "Julian", "Grayson", "Leo", "Jayden", "Gabriel", "Isaac", "Lincoln", "Anthony", "Hudson", "Dylan", "Ezra",
            "Thomas", "Charles", "Christopher", "Jaxon", "Maverick", "Josiah", "Isaiah", "Andrew", "Elias", "Joshua",
            "Nathan", "Caleb", "Ryan", "Adrian", "Miles", "Eli", "Nolan", "Christian", "Aaron", "Cameron", "Ezekiel",
            "Colton", "Luca", "Landon", "Hunter", "Jonathan", "Santiago", "Axel", "Easton", "Cooper", "Jeremiah",
            "Angel", "Roman", "Jordan", "Ian", "Carson", "Jaxson", "Leonardo", "Nicholas", "Connor",  # hey there I am
            "Jameson", "Robert", "Greyson", "Dominic", "Austin", "Everett", "Brooks", "Xavier", "Kai", "Jose", "Parker",
            "Adam", "Jace", "Wesley", "Kayden", "Silas"
        ])

        num_people = randint(1, 3)
        entrees = choices(Menu.Entrees, k=randint(1, num_people))
        sides = choices(Menu.Sides, k=randint(0, num_people + 1))
        drinks = choices(Menu.Drinks, k=randint(0, num_people + 1))

        items = entrees + sides + drinks

        subtotal = sum(item.price for item in items)
        tip = Decimal(subtotal * Decimal.from_float(uniform(0.1, 0.25))).quantize(Decimal('0.01'))

        if random() < 0.5 and None in self.tables:  # DineInOrder, table must be available
            table = choice([i for i, val in enumerate(self.tables) if val is None])
            return DineInOrder(name, table, tip, *items)

        else:  # TakeoutOrder
            pickup_time = cur_time + timedelta(minutes=randint(30, 120))
            return TakeoutOrder(name, pickup_time, tip, *items)

    def start_day(self, today: date) -> None:
        cur_time = datetime.combine(today, self.open_time)
        close_time = datetime.combine(today, self.close_time)

        self.order_queue.enqueue(self.generate_new_order(cur_time))

        while cur_time < close_time:
            if random() < 0.01:
                self.order_queue.enqueue(self.generate_new_order(cur_time))

            for station_no in range(len(self.stations)):
                station: PrepStation = self.stations[station_no]
                if not station.is_working() and not self.order_queue.is_empty():
                    order = self.order_queue.dequeue()
                    self.active_orders.append(order)
                    station.current_order = order

                try:
                    print(
                        f"[{cur_time.strftime("%I:%M:%S %p")}] Station {station_no}:"
                        f"{"":{len(station.task_stack) * 4}}{station.current_action()}"
                    )
                except StopIteration as e:
                    order = e.value
                    self.active_orders.remove(order)
                    self.completed_orders.append(order)
                    station.current_order = None
                    station.task_stack[0] = iter(station.idle())

            cur_time += timedelta(seconds=10)

        print('\n\n\n')
        print(
            "End of shift summary:",
            f"Total customers processed: {sum(map(len, (self.completed_orders, self.active_orders, self.order_queue)))}",
            f"Total completed orders: {len(self.completed_orders)}",
            f"Total dine-in orders: {sum(1 for order in self.completed_orders if isinstance(order, DineInOrder))}",
            f"Total take-out orders: {sum(1 for order in self.completed_orders if isinstance(order, TakeoutOrder))}",
            f"Total revenue: {format_usd(sum((order.total for order in self.completed_orders), Decimal('0.00')))}",
            sep='\n')


seed(0)
restaurant = Restaurant(num_stations=4)
restaurant.start_day(date.today())
