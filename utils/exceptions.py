'''
Здесь описаны все кастомные исключения Приложения.
'''
from __future__ import annotations


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Plugin

    from pathlib import Path
    from requests import Response


# ---------------------------------------------------------------------------- #
#                                    Плагины                                   #
# ---------------------------------------------------------------------------- #
class ModuleImportError(Exception):
    def __init__(self, module_path: Path):
        '''
        Исключение, поднимающееся при неудачной попытке загрузки модуля.

        :param module_path: Путь к модулю.
        :type module_path: Path
        '''
        self.module_path = module_path


    def __str__(self): return f'Ошибка при загрузке модуля {self.module_path.stem} ({self.module_path})'


class PluginDependenciesNotLoadedError(Exception):
    def __init__(self, plugin: Plugin, dependencies: dict[str]):
        '''
        Исключение, поднимающееся, если не загружены все зависимости плагина.

        :param plugin: Объект плагина.
        :type plugin: Plugin
        :param dependencies: Зависимости плагина.
        :type dependencies: dict[str]
        '''
        self.plugin = plugin
        self.dependencies = dependencies

    def __str__(self): return f'Загружены не все зависимости плагина {self.plugin.name} {self.plugin.uuid}: {[*self.dependencies]}'


# ---------------------------------------------------------------------------- #
#                                 Прочие ошибки                                #
# ---------------------------------------------------------------------------- #
class ApplicationNotInitializedError(Exception):
    def __init__(self):
        '''
        Исключение, поднимающееся, если Приложение не было инициализировано перед запуском.
        '''

    def __str__(self): return 'Приложение должно быть инициализировано перед запуском!'


__all__ = [
    'ApplicationNotInitializedError',
    'ModuleImportError',
    'PluginDependenciesNotLoadedError',
]