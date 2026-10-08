'Здесь описан класс модулярного приложения.'
from __future__ import annotations


from subprocess import Popen
import importlib.util


from configs import Config, HOME_DIR, CONFIGS_DIR


from typing import TYPE_CHECKING
from time import time, sleep


from logging import getLogger


if TYPE_CHECKING:
    from typing import Self, NoReturn
    from logging import Logger


class ModularApplication:
    '''
    Класс Модулярного Приложения.

    :param name: Имя экземпляра.
    :type name: str
    :param version: Версия приложения.
    :type version: str
    '''
    instances: dict[str, Self] = {}
    'Список существующих экземпляров Приложения.'


    def __new__(cls, name: str, *args, **kwargs) -> Self:
        if not name in cls.instances: cls.instances[name] = super().__new__(cls)

        return cls.instances[name]


    def __init__(self, name: str, version: str | None = None):
        if hasattr(self, '__initialized'): return

        self.__initialized = True

        self.name = name
        'Имя экземпляра.'

        self.version = version


        self.run_id = 0

        self.initialized = False
        'Флаг инициализации Приложения.'


        self.start_time = int(time())


    def init(self) -> Self:
        '''
        Инициализирует Приложение.
        '''
        if not (CONFIGS_DIR / f'{self.name}.toml').exists(): self.create_config()


        self.initialized = True

        return self


    def start(self) -> NoReturn:
        '''
        Запускает Приложение.

        :raises Exception: Приложение не было инициализировано перед запуском.
        '''
        if not self.initialized: raise Exception('Приложение должно быть инициализировано перед запуском!') # TODO


        self.start_time = int(time())

        self.run_id += 1


        ...


        self.run()


    def run(self) -> NoReturn:
        while True: sleep(5)


    # ---------------------------------------------------------------------------- #
    #                                   Настройки                                  #
    # ---------------------------------------------------------------------------- #
    @property
    def config(self): return Config(self.name)


    def create_config(self):
        '''
        Создает конфиг с именем экземпляра.
        '''
        Config('DEFAULT_CONFIG').copy_section(CONFIGS_DIR / f'{self.name}.toml', self.name) # TODO переделать под метод Config.save
        Config().init_config()


    # ---------------------------------------------------------------------------- #
    #                                    Прочее                                    #
    # ---------------------------------------------------------------------------- #
    def log(self):
        if not hasattr(self, '_log'): self._log = getLogger(self.name)

        return self._log


__all__ = [
    'ModularApplication',
]