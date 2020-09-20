from importlib import import_module

__attr_module_map = {
    # tz_aware_dt
    'TZ_LOCAL': 'tz_aware_dt',
    'TZ_UTC': 'tz_aware_dt',
    'ISO8601': 'tz_aware_dt',
    'DATETIME_FMT': 'tz_aware_dt',
    'DATE_FMT': 'tz_aware_dt',
    'TIME_FMT': 'tz_aware_dt',
    'now': 'tz_aware_dt',
    'epoch2str': 'tz_aware_dt',
    'str2epoch': 'tz_aware_dt',
    'datetime_with_tz': 'tz_aware_dt',
    'localize': 'tz_aware_dt',
    'as_utc': 'tz_aware_dt',
    # utils
    'format_duration': 'utils',
    'timedelta_to_str': 'utils',
}

# noinspection PyUnresolvedReferences
__all__ = ['__version__', 'tz_aware_dt', 'utils']
__all__.extend(__attr_module_map.keys())


def __dir__():
    return sorted(__all__ + list(globals().keys()))


def __getattr__(name):
    try:
        module_name = __attr_module_map[name]
    except KeyError:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    else:
        module = import_module(f'.{module_name}', __name__)
        return getattr(module, name)
