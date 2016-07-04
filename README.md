#dropbox-conflict-diff

A script to easily find the difference between Dropbox conflicted copies and their original files.

<img src="https://i.imgur.com/Nk87lAU.png" width="710">

##Requirements

* Python 3.3+
* diff
* A working terminal
* Optional: [colordiff](http://www.colordiff.org/)
* Optional: [Meld](http://meldmerge.org/)

## Usage

```
usage: dropbox-conflict-diff.py [-h] [-p] [-i IGNORE_DIRS] [-r] [-m] path

Scan a directory computing diffs of Dropbox conflicted copies.

positional arguments:
  path                  Directory to scan (default is current working
                        directory)

optional arguments:
  -h, --help            show this help message and exit
  -p, --pager           Use less to display the differences.
  -i IGNORE_DIRS, --ignore-dirs IGNORE_DIRS
                        List of directory names that will be pruned during the
                        exploration. By default: .git,.idea
  -r, --remove-equal    Automatically delete conflicted copies that match byte
                        to byte the original files.
  -m, --merge           Interactively present options to keep one of the files
                        in conflict or merge them using meld.
```