
from __future__ import annotations


import os


def set_console_title(title: str) -> None:
    '''
    Изменяет название консоли для Windows.
    '''
    try:
        if os.name == 'nt':  # Windows
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(title)

    except: ...


    return


__all__ = [
    'set_console_title',
]