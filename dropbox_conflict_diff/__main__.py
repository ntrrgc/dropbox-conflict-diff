#!/usr/bin/python3
import os
import re
import shutil
import subprocess
from filecmp import cmp

from dropbox_conflict_diff.meld import meld, MeldError
from dropbox_conflict_diff.menu import menu, MenuOption

conflict_strings = [
    "conflicted copy",
    "Copia en conflicto",
]

# First group: file name without the conflict string.
# Second group: extension, if any. Includes the leading period.
re_name = re.compile(r"^(.*) \([^()]*conflict[^()].*\)(\.?.*)$")

default_ignore_dirs = ".git,.idea"

diff_command = "colordiff" if shutil.which("colordiff") is not None else "diff"

def show_diff(path_original, path_conflict, use_pager):
    diff_process = subprocess.Popen([
        diff_command, "-u", path_original, path_conflict],
        stdout=subprocess.PIPE if use_pager else None
    )
    if use_pager:
        subprocess.call(["less", "-R"], stdin=diff_process.stdout)
    else:
        diff_process.wait()


def meld_retry_not_installed(*args, **kwargs):
    while True:
        try:
            meld(*args, **kwargs)
        except MeldError as err:
            print("Meld is not installed. Please install it to merge files.")

            opt_retry = MenuOption("r", "Retry the merge, I just installed Meld")
            opt_abort = MenuOption("a", "Abort the merge")

            option = menu([opt_retry, opt_abort])

            if option == opt_retry:
                pass
            elif option == opt_abort:
                raise err


def meld_and_ask(path_conflict, path_original):
    while True:
        try:
            meld_retry_not_installed(path_conflict, path_original)
        except MeldError:
            # Meld aborted. User refused to install it, keep both files.
            return

        print("Meld has been closed. Do you want to remove the conflicted copy?")

        opt_remove_conflicted = MenuOption("r", "Remove the conflicted copy")
        opt_keep = MenuOption("k", "Keep the conflicted copy")
        opt_merge_again = MenuOption("m", "Show meld again and retry the merge")

        option = menu([opt_remove_conflicted, opt_keep, opt_merge_again])

        if option == opt_remove_conflicted:
            os.remove(path_conflict)
            print("Removed %s" % path_conflict)
        elif option == opt_keep:
            print("Kept conflicted copy.")
            return
        elif option == opt_merge_again:
            print("Running Meld again...")


def ask_different(path_conflict, path_original):
    opt_keep_original = MenuOption("o", "Keep original file (delete conflicted copy)")
    opt_keep_conflicted = MenuOption("c", "Keep conflicted copy (overwrite original)")
    opt_keep_both = MenuOption("b", "Keep both files")
    opt_merge = MenuOption("m", "Merge both files with Meld")
    opt_quit = MenuOption("q", "Quit and abort the merge")

    option = menu([
        opt_keep_original,
        opt_keep_conflicted,
        opt_keep_both,
        opt_merge,
        opt_quit
    ])

    if option == opt_keep_original:
        os.remove(path_conflict)
        print("Removed %s" % path_conflict)
    elif option == opt_keep_conflicted:
        os.remove(path_original)
        shutil.move(path_conflict, path_original)
        print("Overwritten %s with conflicted copy." % path_original)
    elif option == opt_keep_both:
        print("No changes made.")
    elif option == opt_merge:
        meld_and_ask(path_conflict, path_original)
    elif option == opt_quit:
        raise SystemExit(1)


remove_all_equal = False


def ask_equal(path_conflict, path_original):
    global remove_all_equal

    opt_delete = MenuOption("o", "Delete the conflicted copy")
    opt_keep = MenuOption("k", "Keep the conflicted copy")
    opt_all_delete = MenuOption("a", "Delete all conflicted copies that are equal to their original files")
    opt_quit = MenuOption("q", "Quit and abort the merge")

    if not remove_all_equal:
        option = menu([opt_delete, opt_keep, opt_all_delete, opt_quit])
    else:
        option = opt_delete

    if option == opt_delete or option == opt_all_delete:
        os.remove(path_conflict)
        print("Removed %s" % path_conflict)

        if opt_all_delete:
            remove_all_equal = True
    elif option == opt_keep:
        print("No changes made.")
    elif option == opt_quit:
        raise SystemExit(1)


def scan_conflicts(path=".", remove_equal=False, use_pager=False, ignore_dirs=default_ignore_dirs, merge=False):
    ignore_dirs = ignore_dirs.split(",")
    for root, dirs, files in os.walk(path):
        # Filter ignored directories
        for ignored_dir_name in ignore_dirs:
            if ignored_dir_name in dirs:
                dirs.remove(ignored_dir_name)

        for name in files:
            if any(conflict_string in name
                   for conflict_string in conflict_strings):
                # Strip the conflict part
                try:
                    unconflicted_name = "".join(re_name.match(name).groups())
                except:
                    print("Regex failed for name = '%s'" % name)
                    print(re_name.match(name))
                    print(re_name.match(name).groups())
                    return
                if unconflicted_name in files:
                    path_original = os.path.join(root, unconflicted_name)
                    path_conflict = os.path.join(root, name)

                    if cmp(path_original, path_conflict):
                        message = "%s is equal to %s." % (path_conflict, path_original)
                        if remove_equal:
                            message += " Removing..."
                        print(message)
                        if remove_equal:
                            os.remove(path_conflict)

                        if merge:
                            ask_equal(path_conflict, path_original)
                    else:
                        # Files are different, show diff
                        show_diff(path_original, path_conflict, use_pager=use_pager)

                        if merge:
                            ask_different(path_conflict, path_original)
                else:
                    print("Warning: Could not find '%s', but there is a conflicted copy: %s"
                          % (unconflicted_name, name))


def main():
    from argparse import ArgumentParser
    
    parser = ArgumentParser(description=
        "Scan a directory computing diffs of Dropbox conflicted copies.")
    
    parser.add_argument("path", default=".", type=str, help=
        "Directory to scan (default is current working directory)")
    parser.add_argument("-p", "--pager", action="store_true", help=
        "Use less to display the differences.")
    parser.add_argument("-i", "--ignore-dirs", default=default_ignore_dirs, type=str, help=
        "List of directory names that will be pruned during the exploration. By default: " +
        default_ignore_dirs)
    parser.add_argument("-r", "--remove-equal", action="store_true", help=
        "Automatically delete conflicted copies that match byte to byte the original files.")
    parser.add_argument("-m", "--merge", action="store_true", help=
        "Interactively present options to keep one of the files in conflict or merge them using meld.")

    args = parser.parse_args()

    global remove_all_equal
    remove_all_equal = args.remove_equal

    scan_conflicts(
        path=args.path,
        remove_equal=args.remove_equal,
        use_pager=args.pager,
        ignore_dirs=args.ignore_dirs,
        merge=args.merge
    )
