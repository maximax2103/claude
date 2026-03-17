"""Terminal color helpers (ANSI codes)."""

import sys

_USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def bold(text: str) -> str:    return _c("1", text)
def green(text: str) -> str:   return _c("32", text)
def red(text: str) -> str:     return _c("31", text)
def yellow(text: str) -> str:  return _c("33", text)
def cyan(text: str) -> str:    return _c("36", text)
def gray(text: str) -> str:    return _c("90", text)


def ok(msg: str) -> None:    print(green("✓ " + msg))
def warn(msg: str) -> None:  print(yellow("⚠ " + msg))
def info(msg: str) -> None:  print(cyan("ℹ " + msg))
def skip(msg: str) -> None:  print(gray("⏸ " + msg))
def err(msg: str) -> None:   print(red("✗ " + msg))
