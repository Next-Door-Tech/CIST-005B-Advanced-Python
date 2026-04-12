from bst import AVLSeq
from itertools import chain
import re

dictionary: AVLSeq[str] = AVLSeq()

with open("dictionary.txt", 'r') as d:
    for line in d:
        dictionary.add(line.lower().strip())

misspelled: AVLSeq[str] = AVLSeq()

with open("check_me.txt", 'r') as f:
    for match in chain.from_iterable(re.finditer(r'\w+', line) for line in f):
        if match[0] not in dictionary:
            misspelled.add(match[0])

print("Misspelled words:")
print(*('\t' + word for word in misspelled))

print()
print("Dictionary Tree:")
for node in dictionary.root:
    print(f"\t'{node.value}' skew: {node.skew}")

print()
print("Misspelled Tree:")
for node in misspelled.root:
    print(f"\t'{node.value}' skew: {node.skew}")
