'''
Здесь описан класс модулярного приложения.
'''
from __future__ import annotations


from subprocess import Popen
import importlib.util


from configs import Config, APPLICATION_CONFIG_DIR, PLUGINS_DIR


from utils import exceptions, Handler, Plugin



import json
from time import time, sleep
import hashlib
from math import inf


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType
    from importlib._bootstrap import ModuleSpec
    from typing import Self, NoReturn, Any, Literal
    from pathlib import Path
    from logging import Logger
    from _hashlib import HASH as Hash


from logging import getLogger


log = getLogger('Application')


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


        self.plugins_load_order: list[str] = []
        'Порядок загрузки плагинов.'

        self.plugins: dict[str, Plugin] = {}
        'Список загруженных плагинов.'


        self.event_var_names = [
            'PRE_INIT', # Функции, выполняемые до инициализации Приложения (после загрузки плагинов).
            'POST_INIT', # Функции, выполняемые после инициализации Приложения.
            'PRE_START', # Функции, выполняемые перед запуском основного цикла Приложения (выполняются первыми).
            'POST_START', # Функции, выполняемые перед запуском основного цикла Приложения (после `PRE_START`).
        ]
        'Имена событий для привязки хендлеров.'

        self.handlers: dict[Literal[
            'PRE_INIT',
            'POST_INIT',
            'PRE_START',
            'POST_START',
        ] | str, list[Handler]] = {}
        'Список загруженных хендлеров.'


        self.start_time = int(time())


    def init(self) -> Self:
        '''
        Инициализирует Приложение.

        Инициализирует конфиг, загружает плагины, регистрирует хэндлеры.
        '''
        log.info(f'Инициализирую Приложение.')

        if not (APPLICATION_CONFIG_DIR / f'{self.name}.toml').exists(): self.create_config()


        self.get_plugins()
        self.load_plugins()
        self.init_plugins()
        self.add_handlers_from_plugins()


        self.run_handlers(self.handlers.get('PRE_INIT', []))

        ...

        self.run_handlers(self.handlers.get('POST_INIT', []))


        self.initialized = True

        return self


    def start(self) -> NoReturn:
        '''
        Запускает Приложение.

        :raises :class:`exceptions.ApplicationNotInitializedError`: Приложение не было инициализировано перед запуском.
        '''
        log.info(f'Запускаю Приложение.')

        if not self.initialized: raise exceptions.ApplicationNotInitializedError()


        self.start_time = int(time())

        self.run_id += 1


        self.run_handlers(self.handlers.get('PRE_START', []))


        ...


        self.run_handlers(self.handlers.get('POST_START', []))


        self.run()


    def run(self) -> NoReturn:
        while True:
            ...
            sleep(5)


    # ---------------------------------------------------------------------------- #
    #                                    Плагины                                   #
    # ---------------------------------------------------------------------------- #

    # ---------------------- Получение информации о плагинах --------------------- #
    @staticmethod
    def get_plugin_hash(plugin_dir: Path) -> Hash:
        '''
        Возвращает sha256 хеш плагина.

        :param plugin_dir: Путь к плагину.
        :type plugin_dir: :class:`Path`
        :return: Хеш файлов плагина.
        :rtype: dict[str, :obj:`hashlib.HASH`]
        '''
        def hash_update_from_file(file_path: Path, hash: Hash):
            hash.update(file_path.read_bytes())


            return hash


        def hash_update_from_dir(directory: Path, hash: Hash):
            for path in sorted(directory.iterdir(), key=lambda p: str(p).lower()):
                if '__pycache__' in str(directory): continue

                hash.update(path.name.encode())


                if path.is_file(): hash = hash_update_from_file(path, hash)

                elif path.is_dir(): hash = hash_update_from_dir(path, hash)


            return hash


        log.debug(f'Получаю хеш файлов плагина {plugin_dir}.')

        result = hashlib.sha256()

        result = hash_update_from_dir(plugin_dir, result)


        return result


    @staticmethod
    def get_plugin_raw_info(plugin_dir: Path) -> tuple[str, dict[str, Any]]:
        '''
        Возвращает информацию о плагине.

        :param plugin_dir: Путь к плагину.
        :type plugin_dir: :class:`Path`
        :return: Информация о плагине.
        :rtype: dict[str, Any]
        '''
        log.debug(f'Получаю информацию о плагине {plugin_dir}.')

        plugin_info_path = plugin_dir / 'plugin_info.json' # TODO Добавить разные типы файлов документации плагина (PluginInfoLoaders)
        plugin_dependencies_path = plugin_dir / 'dependencies.json' # TODO Добавить разные типы файлов списка зависимостей (PluginDependenciesLoaders)


        with open(plugin_info_path, encoding='utf-8') as fp: plugin_info = json.load(fp)

        if plugin_dependencies_path.exists():
            with open(plugin_dependencies_path, encoding='utf-8') as fp: plugin_dependencies = json.load(fp)
        else: plugin_dependencies = {}


        plugin_hash = ModularApplication.get_plugin_hash(plugin_dir)


        return plugin_info['UUID'], {
            'NAME': plugin_info['NAME'],
            'VERSION': plugin_info['VERSION'],
            'DESCRIPTION': plugin_info['DESCRIPTION'],
            'CREDITS': plugin_info['CREDITS'],
            'dependencies': plugin_dependencies,
            'plugin_dir': plugin_dir,
            'plugin_hash': plugin_hash
        }


    # -------------------- Получение порядка загрузки плагинов ------------------- #
    @staticmethod
    def set_plugin_load_order(plugin_uuid: str, plugins_raw_info: dict[str, dict]) -> dict[str, dict]:
        '''
        Присваивает плагину порядок загрузки, исходя из его зависимостей.

        :param plugin_uuid: UUID плагина.
        :type plugin_uuid: str
        :param plugins_raw_info: Список плагинов.
        :type plugins_raw_info: dict
        :return: Список плагинов.
        :rtype: dict
        '''
        plugin_raw_info = plugins_raw_info[plugin_uuid]


        # ---------- Если плагину уже присвоен порядок загрузки - пропустить --------- #
        if hasattr(plugin_raw_info, 'load_order'): return plugins_raw_info


        # ------------ Если у плагина нет зависимостей - загружать первым ------------ #
        if not plugin_raw_info['dependencies']:
            plugin_raw_info['load_order'] = 0
            plugins_raw_info[plugin_uuid] = plugin_raw_info


        # ----- Если у плагина есть зависимости - присвоить каждой из них порядок ---- #
        # ------------------ загрузки, а плагин загрузить после них ------------------ #
        else:
            load_order = 0

            for dependency in plugin_raw_info['dependencies']:
                if not hasattr(plugins_raw_info[dependency], 'load_order'): plugins_raw_info = ModularApplication.set_plugin_load_order(dependency, plugins_raw_info)

                load_order = max(load_order, plugins_raw_info[dependency]['load_order']+1)


            plugin_raw_info['load_order'] = load_order


        return plugins_raw_info


    @staticmethod
    def set_plugins_load_order(plugins_raw_info: dict[str, dict]) -> dict[str, dict]:
        '''
        Присваивает плагинам порядок загрузки.

        :param plugins_raw_info: Список плагинов.
        :type plugins_raw_info: dict
        :return: Список плагинов с порядком загрузки.
        :rtype: dict
        '''
        result = plugins_raw_info.copy()

        for plugin_uuid in plugins_raw_info:
            result = ModularApplication.set_plugin_load_order(plugin_uuid, result)


        return result


    def get_plugins_load_order(self, plugins_raw_info: dict[str, dict]) -> None:
        '''
        Получает порядок загрузки плагинов из информации о плагинах.

        :param plugins_raw_info: Информация о плагинах.
        :type plugins_raw_info: dict
        '''
        log.debug('Получаю порядок загрузки плагинов.')

        self.plugins_load_order = list(plugins_raw_info)

        self.plugins_load_order.sort(key=lambda u: plugins_raw_info[u]['load_order'])


        log.debug(f'Порядок загрузки плагинов успешно получен: {self.plugins_load_order}')

        return


    # ----------------------------- Загрузка плагинов ---------------------------- #
    @staticmethod
    def get_module(module_path: Path) -> tuple[ModuleSpec, ModuleType]:
        '''
        Загружает модуль по указанному пути.

        :param module_path: Путь к модулю.
        :type module_path: :class:`Path`
        :raises :class:`exceptions.ModuleImportError`: Ошибка при загрузке модуля.
        :return: Модуль.
        :rtype: tuple[:class:`ModuleSpec`, :class:`ModuleType`]
        '''
        try:
            spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except: raise exceptions.ModuleImportError(module_path)


        return spec, module


    def get_plugins(self) -> None:
        '''
        Получает все плагины из папки plugins.

        -----------------------------------

        **ВАЖНО!!!** Не импортирует модули.
        '''
        log.debug('Получаю плагины.')

        plugins_count = 0
        plugin_dirs = PLUGINS_DIR.iterdir()

        for plugin_dir in plugin_dirs:
            # ---------- Если нет plugin_info.json или plugin.py - это не плагин --------- #
            if not all([
                (plugin_dir / 'plugin.py').exists(),
                (plugin_dir / 'plugin_info.json').exists()
            ]): continue


            plugin_uuid, plugin_raw_info = self.get_plugin_raw_info(plugin_dir)


            plugin = Plugin(
                uuid=plugin_uuid,
                name=plugin_raw_info['NAME'],
                version=plugin_raw_info['VERSION'],
                description=plugin_raw_info['DESCRIPTION'],
                credits=plugin_raw_info['CREDITS'],
                dir=plugin_dir,
                dependencies=plugin_raw_info['dependencies'],
                raw_info=plugin_raw_info
            )


            self.plugins[plugin.uuid] = plugin

            plugins_count+=1


        log.debug(f'Плагины ({plugins_count}) успешно получены.')

        return


    def load_plugin(self, plugin_uuid: str) -> None: # TODO Доверенные плагины
        '''
        Загружает модуль плагина.

        :param module: Модуль.
        :type module: :class:`ModuleType`
        :param module_path: Путь к модулю.
        :type module_path: :class:`Path`
        :raises :class:`~exceptions.PluginDependenciesNotLoadedError`: Не загружены все зависимости плагина.
        '''
        plugin = self.plugins[plugin_uuid]


        log.debug(f'Загружаю плагин {plugin.name} ({plugin.uuid}).')

        # ------ Вызывать ошибку, если плагины из зависимостей не были загружены ----- #
        if any([not self.plugins[dependency].module for dependency in plugin.dependencies]): raise exceptions.PluginDependenciesNotLoadedError(plugin, plugin.dependencies)


        plugin_path = plugin.dir / 'plugin.py'

        plugin.spec, plugin.module = self.get_module(plugin_path)


        # ------------------- Запуск хендлеров при загрузке плагина ------------------ #
        if hasattr(plugin.module, 'LOAD_PLUGIN'):
            log.debug(f'Запускаю хендлеры при загрузке плагина {plugin.name} ({plugin.uuid}).')

            load_plugin_handlers = [Handler(plugin.uuid, 'LOAD_PLUGIN', 0, func) for func in getattr(plugin.module, 'LOAD_PLUGIN')]

            self.run_handlers(load_plugin_handlers)


        log.debug(f'Плагин {plugin.name} ({plugin.uuid}) успешно загружен.')

        return


    def load_plugins(self) -> None:
        '''
        Загружает плагины, полученные через :meth:`get_plugins`.
        '''
        log.debug('Загружаю плагины.')

        plugins_raw_info = {plugin.uuid: plugin.raw_info for plugin in self.plugins.values()}

        plugins_raw_info = self.set_plugins_load_order(plugins_raw_info)

        self.get_plugins_load_order(plugins_raw_info)


        plugins_count = 0

        for plugin_uuid in self.plugins_load_order:
            try:
                self.load_plugin(plugin_uuid)

                plugins_count+=1


            except exceptions.PluginDependenciesNotLoadedError:
                log.error(f'Плагин {plugin_uuid} не будет загружен, так как загружены не все его зависимости.')
                log.debug('TRACEBACK', exc_info=True)

                del self.plugins[plugin_uuid]


            except:
                log.error(f'Не удалось загрузить плагин {plugin_uuid}.')
                log.debug('TRACEBACK', exc_info=True)

                del self.plugins[plugin_uuid]


        log.debug(f'Плагины ({plugins_count}) успешно загружены.')

        return


    # ---------------------------------------------------------------------------- #
    #                                   Хендлеры                                   #
    # ---------------------------------------------------------------------------- #
    def run_handler(self, handler: Handler, *args, **kwargs) -> None:
        '''
        Запускает хендлер с указанными аргументами.

        :param handler: Хендлер.
        :type handler: :class:`Handler`
        '''
        log.debug(f'Запускаю хендлер {getattr(handler.func, __name__, handler.plugin_uuid)}.')

        try: handler.func(self, *args, **kwargs)


        except:
            log.warning(f'Ошибка при выполнении хендлера {getattr(handler.func, __name__, handler.plugin_uuid)}.')
            log.debug('TRACEBACK', exc_info=True)

            self.run_handlers(self.handlers.get('HANDLER_ERROR', []), handler, args, kwargs)


        return


    def run_handlers(self, handlers: list[Handler], *args, **kwargs) -> None:
        '''
        Запускает все хендлеры из списка с указанными аргументами

        :param handlers: Список хендлеров.
        :type handlers: list[:class:`Handler`]
        '''
        if not handlers: return


        handlers.sort(key=lambda h: h.priority if h.priority >= 0 else inf)


        log.debug(f'Запускаю хендлеры {handlers}.')

        for handler in handlers: self.run_handler(handler, *args, **kwargs)


        return


    # ---------------------------- Загрузка хендлеров ---------------------------- #
    def init_plugin(self, plugin: Plugin, event_var_names: list[str]) -> None:
        '''
        Загружает хендлеры из плагина.

        :param plugin: Плагин.
        :type plugin: :class:`Plugin`
        :param event_var_names: Список алиасов хендлеров.
        :type event_var_names: list[str]
        '''
        log.debug(f'Инициализирую плагин {plugin.name} ({plugin.uuid}).')

        if hasattr(plugin.module, 'INIT_PLUGIN'):
            log.debug(f'Запускаю хендлеры при инициализации плагина {plugin.name} ({plugin.uuid}).')

            init_plugin_handlers = [
                Handler(
                    plugin.uuid,
                    'INIT_PLUGIN',
                    0,
                    func
                ) for func in getattr(plugin.module, 'INIT_PLUGIN')
            ]

            self.run_handlers(init_plugin_handlers)


        for event_name in event_var_names:
            if hasattr(plugin.module, event_name):
                log.debug(f'Получаю хендлеры {event_name}: {getattr(plugin.module, event_name)} ({plugin.uuid}).')

                for handler_value in getattr(plugin.module, event_name):
                    handler = Handler(
                        plugin.uuid,
                        event_name,
                        handler_value['priority'],
                        handler_value['handler']
                    )

                    plugin.handlers[event_name] = [*plugin.handlers.get(event_name, []), handler]


        return


    def init_plugins(self) -> None:
        '''
        Инициализирует все загруженные плагины.
        '''
        log.debug(f'Инициализирую плагины ({len(self.plugins)}).')

        for plugin in self.plugins.values():
            try: self.init_plugin(plugin, self.event_var_names)


            except:
                log.error(f'Ошибка при инициализации плагина {plugin.name} ({plugin.uuid}).')
                log.debug('TRACEBACK', exc_info=True)


        log.info('Все плагины инициализированы.')

        return


    def add_handler(self, handler: Handler, event_var_name: str) -> None:
        '''
        Добавляет хендлер в Приложение.

        :param handler: Хендлер.
        :type handler: :class:`Handler`
        :param event_var_name: Алиас события хендлера.
        :type event_var_name: str
        '''
        log.debug(f'Добавляю хендлер {handler.func.__name__} ({handler.plugin_uuid}) в хендлеры {event_var_name}.')

        self.handlers[event_var_name] = [*self.handlers.get(event_var_name, []), handler]


        return

    def add_handlers_from_plugin(self, plugin: Plugin) -> None:
        '''
        Добавляет хендлеры из плагина в Приложение.

        :param plugin: Плагин.
        :type plugin: :class:`Plugin`
        '''
        log.debug(f'Загружаю хендлеры из плагина {plugin.name} ({plugin.uuid}).')

        for event_name, handlers in plugin.handlers.items():
            log.debug(f'Добавляю хендлеры {event_name}: {handlers} ({plugin.uuid}).')

            for handler in handlers: self.add_handler(handler, event_name)


        return


    def add_handlers_from_plugins(self) -> None:
        '''
        Добавляет хендлеры из всех загруженных плагинов.
        '''
        log.debug(f'Загружаю хендлеры из плагинов ({len(self.plugins)}).')

        for plugin in self.plugins.values(): self.add_handlers_from_plugin(plugin)


        return


    # ---------------------------------------------------------------------------- #
    #                                   Настройки                                  #
    # ---------------------------------------------------------------------------- #
    @property
    def config(self): return Config(self.name)


    def create_config(self):
        '''
        Создает конфиг с именем экземпляра.
        '''
        Config('DEFAULT_CONFIG').copy_section(APPLICATION_CONFIG_DIR / f'{self.name}.toml', self.name) # TODO переделать под метод Config.save
        Config().init_config()


__all__ = [
    'ModularApplication',
]