# Cards: an extensible playing card library

### Running

This library requires either Python 3.12 or later with the `frozendict` package installed from PyPI, or Python 3.15 with
no additional packages (`frozendict` is a built-in type in 3.15).

The demo implementation UI can be started by running `blackjack.py` from this directory.

## Introduction

This project

## Data Structures Used

- Circular queues (a.k.a. cirque) implemented as a container data type
- Linked list container data type (as well as stack and linear queue types subclassing linked list)
- Card type attributes as enum subclasses, including Rank, Suit, and Type (i.e. the cartesian product of Rank and Suit),
  all supporting
- Card as a class supporting a per-instance face up / face down state and appropriate

## Unused Data Structures

- A dict-compliant HashTable class was created, however it was not used in the implementation of cards.py as an
  immutable dictionary type was desired. Python 3.15 introduces a built-in `frozendict` type, however, for 3.14 and
  earlier the `frozendict` package providing the desired functionality can be downloaded from PyPI.
-

## Challenges Faced

- The complexity of the project and my limited time to dedicate to

## Impact Statement

## Conclusions
