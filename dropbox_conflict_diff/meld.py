import shutil
import signal

import subprocess


def survive_parent():
    # Don't get killed by your parent
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    # Don't get killed by ^C in the console
    signal.signal(signal.SIGINT, signal.SIG_IGN)


meld_running = False


def ensure_meld_in_background():
    """
    Ensure meld is already running, or launch it in the background in other case.

    Successive calls to meld --newtab will use the current running process.
    """
    global meld_running

    if not meld_running:
        # This process will end immediately if meld is already running.
        # In any case, this function will not wait for meld to be closed.
        subprocess.Popen(["meld", "--newtab"], preexec_fn=survive_parent, close_fds=True)

        # Don't launch it again
        meld_running = True


class MeldError(Exception):
    pass


def meld(path_conflict, path_original):
    if shutil.which("meld") is not None:
        ensure_meld_in_background()
        subprocess.call(["meld", "--newtab", path_original, path_conflict])
    else:
        raise MeldError("meld is not installed")
