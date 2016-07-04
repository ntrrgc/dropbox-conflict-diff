from collections import namedtuple

from dropbox_conflict_diff.getch import getch

MenuOption = namedtuple("MenuOption", ["letter", "text"])


def menu(options):
    options_by_letter = {
        option.letter: option
        for option in options
    }
    if len(options) != len(options_by_letter):
        raise RuntimeError("Reused letter in options!")

    for option in options:
        print("%s) %s" % (option.letter, option.text))

    while True:
        print("Select an option: ", end="", flush=True)
        letter = getch()

        if letter == "\x03":
            # ^C
            print("\nAborting due to ^C.")
            raise SystemExit(1)

        print(letter + "\n")
        if letter in options_by_letter:
            return options_by_letter[letter]
        else:
            print("Invalid option.")
