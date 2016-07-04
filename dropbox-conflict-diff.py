#!/usr/bin/python3
import os
import re
import subprocess

conflict_strings = [
    "conflicted copy",
    "Copia en conflicto",
]

# First group: file name without the conflict string.
# Second group: extension, if any. Includes the leading period.
re_name = re.compile(r"^(.*) \([^()]*conflict[^()].*\)(\.?.*)$")

default_ignore_dirs = ".git,.idea"

def scan_conflicts(path=".", remove_null_diffs=False, pager="cat", ignore_dirs=default_ignore_dirs):
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

                    if subprocess.call(["cmp", path_original, path_conflict]) == 0:
                        message = "%s is equal to %s." % (path_conflict, path_original)
                        if remove_null_diffs:
                            message += " Removing..."
                        print(message)
                        if remove_null_diffs:
                            os.remove(path_conflict)
                    else:
                        # Files are different, show diff
                        diff_process = subprocess.Popen([
                            "diff", "-u", path_original, path_conflict],
                            stdout=subprocess.PIPE
                        )
                        subprocess.call([pager], stdin=diff_process.stdout)
                else:
                    print("Warning: Could not find '%s', but there is a conflicted copy: %s"
                          % (unconflicted_name, name))


if __name__ == '__main__':
    from argparse import ArgumentParser
    
    parser = ArgumentParser(description=
        "Scan a directory computing diffs of Dropbox conflicted copies.")
    
    parser.add_argument("path", default=".", type=str, help=
        "Directory to scan (default is current working directory)")
    parser.add_argument("--pager", default="cat", type=str, help=
        "Pager to use (e.g. less)")
    parser.add_argument("--ignore-dirs", default=default_ignore_dirs, type=str, help=
        "List of directory names that will be pruned during the exploration. By default: " +
        default_ignore_dirs)
    parser.add_argument("--remove-null-diffs", dest="remove_null_diffs", action="store_true", help=
        "Automatically delete conflicted copies that match byte to byte the original files.")

    args = parser.parse_args()

    scan_conflicts(
        path=args.path,
        remove_null_diffs=args.remove_null_diffs,
        pager=args.pager,
        ignore_dirs=args.ignore_dirs
    )
