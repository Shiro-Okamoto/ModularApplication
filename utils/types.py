'''
Здесь описаны кастомные классы, датаклассы и абстрактные классы Приложения.
'''
from __future__ import annotations


from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Literal, Callable


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from application import ModularApplication


# ---------------------------------------------------------------------------- #
#                                  Датаклассы                                  #
# ---------------------------------------------------------------------------- #

@dataclass
class Plugin:
    '''
    Класс, описывающий плагин Приложения.

    :param uuid: Уникальный айди плагина.
    :type uuid: str
    :param name: Имя плагина.
    :type name: str
    :param version: Версия плагина.
    :type version: str
    :param description: Описание плагина.
    :type description: str
    :param credits: Автор плагина.
    :type credits: str
    :param dir: Путь к папке плагина.
    :type dir: :class:`Path`
    :param dependencies: Список зависимостей плагина.
    :type dependencies: dict
    :param raw_info: Хэш и прочая информация о плагине.
    :type raw_info: dict
    :param module: Объект модуля `plugin.py`, по умолчанию — None.
    :type module: :class:`ModuleType` | None, опционально
    :param handlers: Список хендлеров плагина.
    :type handlers: dict[str, list[:class:`Handler`]]
    '''
    uuid: str
    name: str
    version: str
    description: str
    credits: str
    dir: Path
    dependencies: dict
    raw_info: dict
    module: ModuleType | None = None
    handlers: dict[
        Literal[''] | str,
        list[Handler]
    ] = field(default_factory=dict)


@dataclass
class Handler:
    '''
    Класс, описывающий хендлер Приложения.

    :param uuid: Айди связанного плагина.
    :type uuid: str
    :param type: Тип (триггер) хендлера.
    :type type: str
    :param priority: Приоритет загрузки хендлера.
    :type priority: int
    :param func: Вызываемая  хендлером функция.
    :type func: :obj:`Callable`
    '''
    plugin_uuid: str
    type: Literal[''] | str
    priority: int
    func: Callable[..., None]


__all__ = [
    'Plugin',
    'Handler',
]