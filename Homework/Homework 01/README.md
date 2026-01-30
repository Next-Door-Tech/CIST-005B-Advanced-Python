# Homework 1 README

## About Me

I'm a physics and mathematics major here at West Valley – currently preparing to transfer in the fall.

## Goals for This Course

- Have fun!
- Enough said.

## My "First" Python Program

```Python3
deltas = [0x48, 0x1D, 0x07, 0x00, 0x03, -0x4F, 0x37, 0x18, 0x03, -0x06, -0x08, -0x43]
c = 0
chars = list()

for d in deltas:
    c += d
    chars.append(chr(c))
    
print("".join(chars))
```
