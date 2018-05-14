from typing import Tuple

__all__ = ['Red', 'Green', 'Yellow', 'Blue', 'Purple', 'LightBlue']


class _Colored:
    Red = '\033[31m'
    Green = '\033[32m'
    Yellow = '\033[33m'
    Blue = '\033[34m'
    Purple = '\033[35m'
    LightBlue = '\033[36m'
    Clear = '\033[39m'
    Purple2 = '\033[95m'


def _wrap_color(colored: str):
    def func(*strings: str, sep=''):
        strings = map(lambda each: f'{colored}{each}', strings)
        return f'{sep.join(strings)}{_Colored.Clear}'

    return func


Red = _wrap_color(_Colored.Red)
Green = _wrap_color(_Colored.Green)
Yellow = _wrap_color(_Colored.Yellow)
Blue = _wrap_color(_Colored.Blue)
Purple = _wrap_color(_Colored.Purple)
LightBlue = _wrap_color(_Colored.LightBlue)
