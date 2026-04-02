from dataclasses import dataclass
from random import randint, choice, seed, random
from collections.abc import Generator
from itertools import islice

from common_lib.containers import LinkedQueue
from bst import BST
from hash_table import HashTable

seed(0)  # deterministic random generation for debugging


@dataclass
class Animal:
    name: str
    species: str
    care_level: int


def gen_animals() -> Generator[Animal, None, None]:
    # AI generated default animal names and species names
    names = (
        "Leo", "Bella", "Max", "Luna", "Charlie", "Lucy", "Cooper", "Daisy", "Rocky", "Molly", "Buddy", "Sadie", "Toby",
        "Chloe", "Bear", "Lola", "Duke", "Zoe", "Oliver", "Ruby", "Jack", "Rosie", "Tucker", "Penny", "Jasper", "Lilly",
        "Murphy", "Nala", "Buster", "Ellie", "Winston", "Roxy", "Louie", "Stella", "Zeus", "Gracie", "Henry", "Coco",
        "Sam", "Mia", "Oscar", "Abby", "Gizmo", "Sasha", "Shadow", "Pepper", "Simba", "Izzy", "Dexter", "Athena",
        "Scout", "Layla", "Thor", "Sophie", "Bruno", "Hazel", "Finn", "Kona", "Riley", "Willow", "Apollo", "Maddie",
        "Ace", "Harley", "Bandit", "Nova", "Rusty", "Olive", "Cash", "Mocha", "Blue", "Piper", "Tank", "Remy", "Koda",
        "Ember", "Chance", "Freya", "Hunter", "Skye", "Marley", "Sugar", "Boomer", "Peanut", "Otis", "Honey", "Rufus",
        "Maple", "Archie", "Cleo", "Benji", "Ginger", "Hank", "Sunny", "Ollie", "Princess", "Chester", "Angel", "Monty",
        "Pixie"
    )
    assert len(set(names)) == len(names), "names must be unique"

    species = (
        "African Elephant", "Bengal Tiger", "Gray Wolf", "Red Fox", "Bald Eagle", "Emperor Penguin", "Giant Panda",
        "Koala", "Komodo Dragon", "Cheetah", "Snow Leopard", "Blue Whale", "Great White Shark", "Orangutan",
        "Chimpanzee", "Hippopotamus", "Rhinoceros", "Giraffe", "Zebra"
    )

    for name in names:
        yield Animal(name, choice(species), randint(1, 10))


class CarePriorityQueue(BST[int, LinkedQueue[Animal]]):
    def __init__(self) -> None:
        super().__init__()

        for level in range(1, 10 + 1):
            self[level] = LinkedQueue()

    def insert_animal(self, animal: Animal) -> None:
        if animal in self[animal.care_level]:
            pass
        else:
            self[animal.care_level].push(animal)

    def remove_animal(self, animal: Animal) -> None:
        try:
            self[animal.care_level].remove(animal)
        except ValueError:
            for level in self:
                if animal in self[level]:
                    self[level].remove(animal)
                    return
            else:
                raise

    def pop_basic(self) -> Animal:
        for level in reversed(range(1, 3 + 1)):
            try:
                return self[level].pop()
            except IndexError:
                continue

        raise IndexError

    def pop_advanced(self) -> Animal:
        for level in reversed(range(1, 7 + 1)):
            try:
                return self[level].pop()
            except IndexError:
                continue

        raise IndexError

    def pop_intensive(self) -> Animal:
        for level in reversed(range(1, 10 + 1)):
            try:
                return self[level].pop()
            except IndexError:
                continue

        raise IndexError


class ZooManager:
    def __init__(self, num_animals: int = 10, basic_pens: int = 4, advanced_pens: int = 3,
                 intensive_pens: int = 2) -> None:
        self.animals: HashTable[str, Animal] = HashTable()
        self.care_queue: CarePriorityQueue = CarePriorityQueue()
        self.basic_pens: int = basic_pens
        self.advanced_pens: int = advanced_pens
        self.intensive_pens: int = intensive_pens

        for animal in islice(gen_animals(), num_animals):
            self.animals[animal.name] = animal
            self.care_queue[animal.care_level].append(animal)

    def next_day(self) -> None:
        """Treats as many animals as there are pens available for each treatment level.
        Additionally, all animals also have a chance to worsen in condition, whether or not they have been treated."""

        try:
            for _ in range(self.basic_pens):
                animal = self.care_queue.pop_basic()
                print(f'Treating {animal!r} in a basic pen.')
                self.treat_animal(animal)
                print(f'Care level improved to {animal.care_level}.')
        except IndexError:  # all animals are treated
            pass

        try:
            for _ in range(self.advanced_pens):
                animal = self.care_queue.pop_advanced()
                print(f'Treating {animal!r} in an advanced pen.')
                self.treat_animal(animal)
                print(f'Care level improved to {animal.care_level}.')
        except IndexError:  # all animals are treated
            pass

        try:
            for _ in range(self.intensive_pens):
                animal = self.care_queue.pop_intensive()
                print(f'Treating {animal!r} in an intensive pen.')
                self.treat_animal(animal)
                print(f'Care level improved to {animal.care_level}.')
        except IndexError:  # all animals are treated
            pass

        for animal in self.animals.values():
            if random() < 0.10:  # 10% chance for condition to worsen
                if animal.care_level > 0:
                    self.care_queue.remove_animal(animal)
                new_level = min(animal.care_level + randint(1, 3), 10)  # worsen 1-3 levels, but not past 10
                print(f'Care level of {animal!r} is increasing to {new_level}.')
                animal.care_level = new_level
                self.care_queue.insert_animal(animal)

    def treat_basic(self) -> None:
        animal = self.care_queue.pop_basic()
        self.treat_animal(animal)

    def treat_advanced(self) -> None:
        animal = self.care_queue.pop_advanced()
        self.treat_animal(animal)

    def treat_intensive(self) -> None:
        animal = self.care_queue.pop_intensive()
        self.treat_animal(animal)

    def treat_animal(self, animal) -> None:
        animal.care_level -= randint(1, animal.care_level)
        if animal.care_level > 0:
            self.care_queue.insert_animal(animal)


zoo = ZooManager(num_animals=10, basic_pens=4, advanced_pens=3, intensive_pens=2)

for day in range(10):
    print(f"\n\nDay {day + 1}:")
    zoo.next_day()
