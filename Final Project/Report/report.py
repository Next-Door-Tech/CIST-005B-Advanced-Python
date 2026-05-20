from time import sleep
import webbrowser


def print_baud(*values: object, sep: str = " ", end: str = "\n", baud: int = 300) -> None:
    string = sep.join(str(val) for val in values) + end
    for char in string:
        print(char, sep='', end='')
        sleep(8 / baud)


print_baud("I don't know about you, but I feel like having ChatGPT write this report for me is kinda lame.", baud=150,
           end='')
print_baud('...', baud=8)
print_baud('\n', baud=30)
print_baud("So, I let the internet write it for me instead.", baud=150, end='\n\n')
sleep(2)
print_baud("Accessing Wikipedia...", baud=150)
sleep(1)
webbrowser.open_new(r"https://en.wikipedia.org/wiki/A*_search_algorithm")
