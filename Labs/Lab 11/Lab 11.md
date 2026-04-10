# Lab Week 11

Due Apr 14 by 11:59pm | Points 10 | Submitting a file upload | Available until Apr 16 at 11:59pm

---

## Overview

In this lab, you will create a simple spell checker using an AVL Tree and sets. The AVL Tree will serve as your
dictionary, storing a list of valid words for quick searching. The set will store flagged words (misspelled words) from
an input document, ensuring each misspelled word appears only once. You will implement functionality to check each word
in a document against the dictionary, flag misspelled words, and display them in alphabetical order. This lab will give
you hands-on experience with both the efficiency of AVL Trees for search operations and the utility of sets for managing
unique items.

You are required to implement an AVL Tree class, import cannot be used. Sets can be represented as you like.

---

## Requirements

1. **Dictionary AVL Tree Implementation:**

    - Read a dictionary file (a plain text file containing one valid word per line) and insert each word into an AVL
      Tree. Each node in the AVL Tree should contain one word.
    - Implement insertion, search, and removal for the AVL Tree with rotation, ensuring words are sorted alphabetically.
    - You are allowed to simplify, just 15 unique words would be enough.

2. **Spell Checking:**

    - Read a document (another plain text file containing multiple words and sentences) and split it into individual
      words. Ignore punctuation and treat all words as lowercase.
    - For each word in the document, check if it exists in the AVL dictionary.
    - If a word is not found in the dictionary, add it to a set of misspelled words (to avoid duplicates).

3. **Display Misspelled Words and Tree:**

    - Implement functionality to show all misspelled words in the final document.
    - Print your tree with inorder traversal, include balance at each node along with the data stored there

---

## Rubric

* **AVL Tree Implementation (40%):** Correctly implements the AVL Tree with all methods required. Efficiently handles
  the
  dictionary and maintains alphabetical order.
* **Spell Checking (10%):** Correctly identifies all misspelled words and efficiently uses a set to avoid duplicates.
* **Display Functionality (5%):** Correctly displays all misspelled words along with AVL tree inorder with proper
  balance.
* **Code Quality and Documentation (15%)**
* **Demo (30%)**
