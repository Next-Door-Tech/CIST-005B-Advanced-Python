from bst import AVLSeq
from itertools import chain

dictionary: AVLSeq[str] = AVLSeq()

with open("dictionary.txt", 'r') as d:
    for line in d:
        dictionary.add(line.lower().strip())

misspelled: AVLSeq[str] = AVLSeq()

with open("check_me.txt", 'r') as f:
    for word in chain(line.split() for line in f):
        if word.lower() not in dictionary:
            misspelled.add(word.lower())

print("Misspelled words:")
print('\t' + word for word in misspelled)
print()

print("Dictionary Tree:")
for node in dictionary.root:
    print(f"\t'{node.value}' skew: {node.skew}")
