"""Select helpers for notebooks."""

import sys

from colorama import Fore, Style


def cecho():
    """Print formatted text.

    Entrypoint to print formatted text:

        cecho error This message is printed in red

    Valid formats are: 'error', 'warning', 'ok', 'success'
    """
    style, *text = sys.argv[1:]
    text = ' '.join(text)
    if style == 'error':
        print(error(text))
    elif style == 'warning':
        print(warning(text))
    elif style == 'ok':
        print(ok(text))
    elif style == 'success':
        print(success(text))
    else:
        print(text)


def error(text):
    """Format text as heavy red."""
    return Fore.RED + Style.BRIGHT + text + Style.RESET_ALL


def warning(text):
    """Format text as heavy magenta."""
    return Fore.MAGENTA + Style.BRIGHT + text + Style.RESET_ALL


def ok(text):
    """Format text as heavy blue."""
    return Fore.BLUE + Style.BRIGHT + text + Style.RESET_ALL


def success(text):
    """Format text as heavy green."""
    return Fore.GREEN + Style.BRIGHT + text + Style.RESET_ALL
