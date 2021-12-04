"""
Library to facilitate working with timezone-aware datetimes

.. note::
    If you have a :class:`datetime.datetime` object with a timezone configured, and you modify the date/time via a
    :class:`datetime.timedelta` so that the time is pushed across a DST threshold, then you will need to fix the
    timezone to reflect the new one.

    Example (with ways to fix it) - midnight on 2018-11-04 is in EDT, but 3 hours later is actually 2:00 EST::\n
        >>> pre_dst = datetime_with_tz('2018-11-04 00:00:00 America/New_York')
        >>> pre_dst.strftime(DATETIME_FMT)
        '2018-11-04 00:00:00 EDT'

        >>> post_dst = pre_dst + timedelta(hours=3)
        >>> post_dst.strftime(DATETIME_FMT)
        '2018-11-04 03:00:00 EDT'

        >>> datetime_with_tz('2018-11-04 03:00:00 America/New_York').strftime(DATETIME_FMT)
        '2018-11-04 03:00:00 EST'

        >>> datetime_with_tz(post_dst.timestamp()).strftime(DATETIME_FMT)
        '2018-11-04 02:00:00 EST'
        >>> TZ_LOCAL.normalize(post_dst).strftime(DATETIME_FMT)
        '2018-11-04 02:00:00 EST'
        >>> post_dst.astimezone(TZ_LOCAL).strftime(DATETIME_FMT)
        '2018-11-04 02:00:00 EST'

:author: Doug Skrypa
"""

import logging
import re
from datetime import datetime, tzinfo
from typing import Union, Optional, Any

from tzlocal import get_localzone
from dateutil.tz import gettz, UTC

__all__ = [
    'TZ_LOCAL', 'TZ_UTC', 'ISO8601', 'DATETIME_FMT', 'DATE_FMT', 'TIME_FMT', 'now', 'epoch2str', 'str2epoch',
    'datetime_with_tz', 'localize', 'as_utc'
]
_parse_log = logging.getLogger(__name__ + '.parse')
_parse_log.setLevel(logging.WARNING)

DateTime = Union[str, float, datetime]
TZ = Union[str, tzinfo, None]

# region Globals
TZ_UTC = UTC
TZ_LOCAL = gettz(get_localzone()._key)  # dateutil's tzlocal does not use the IANA TZDB identifier

ISO8601 = '%Y-%m-%dT%H:%M:%SZ'
DATETIME_FMT = '%Y-%m-%d %H:%M:%S %Z'
DATETIME_FMT_NO_TZ = '%Y-%m-%d %H:%M:%S'
DATE_FMT = '%Y-%m-%d'
TIME_FMT = '%H:%M:%S %Z'
TIME_FMT_NO_TZ = '%H:%M:%S'
TZ_ALIAS_MAP = {'HKT': 'Asia/Hong_Kong', 'NYT': 'America/New_York'}
# endregion


def datetime_with_tz(
    dt: DateTime,
    fmt: str = DATETIME_FMT,
    tz: TZ = None,
    use_dateparser: bool = False,
    dp_kwargs: dict[str, Any] = None,
) -> datetime:
    """
    Converts the given timestamp string to a datetime object, and ensures that its tzinfo is set.

    Handles ``%z``=``[+-]\d\d:?[0-5]\d`` (Python's default strptime only supports ``[+-]\d\d[0-5]\d``)\n
    Handles long-form ``%Z`` values provided in ``dt`` (e.g., ``America/New_York``)

    :param dt: A timestamp string/float or datetime object
    :param fmt: Time format used by the given input string
    :param tz: A :class:`datetime.tzinfo` or str timezone name to use if not parsed from dt (or instead of the one that
      is in dt if dt is a string) (default: local)
    :param use_dateparser: Use `dateparser <https://dateparser.readthedocs.io/en/latest/>`_ to parse the given
      timestamp instead of an already known ``fmt`` format string.  Requires the dateparser package to be installed.
    :param dp_kwargs: dateparser keyword arguments to provide to :func:`dateparser.parse`
    :return: A :class:`datetime.datetime` object with tzinfo set
    """
    original_dt = dt
    tokens = {}
    if use_dateparser:
        try:
            import dateparser
        except ImportError:
            raise RuntimeError('Unable to use_dateparser because the dateparser package is not installed.')
        dp_kwargs = dp_kwargs or {}
        dt = dateparser.parse(dt, **dp_kwargs)
    elif isinstance(dt, str):
        dt, tokens = _parse_dt_from_str(dt, fmt, tz)
    elif isinstance(dt, (int, float)):
        dt = datetime.fromtimestamp(dt)

    # From this point forward, type(dt) is (assumed to be) datetime - it will no longer be str or a number
    if not dt.tzinfo:
        if tz is not None:
            tz = _get_tz(tz)
        else:
            if tokens.get('Z'):             # datetime.strptime discards TZ when provided via %Z but retains it via %z
                tz = _get_tz(tokens['Z'])
                _parse_log.debug('Found tz={!r} => {!r} for datetime: {!r}'.format(tokens['Z'], tz, original_dt))
            else:
                _parse_log.debug(f'Defaulting to tz={TZ_LOCAL!r} for datetime without %Z or %z: {original_dt!r}')
                tz = TZ_LOCAL

        dt = dt.replace(tzinfo=tz)
    return dt


def now(fmt: str = DATETIME_FMT, tz: TZ = None, as_datetime: bool = False) -> Union[datetime, str]:
    """
    Returns the current time in the given format, optionally converted to the given timezone.

    :param fmt: The time format to use
    :param tz: A :class:`datetime.tzinfo` or str timezone name (default: local)
    :param as_datetime: If True, return a :class:`datetime.datetime` object instead of a formatted string
    :return: Current time in the requested format
    """
    tz = _get_tz(tz)
    dt = datetime.now(TZ_LOCAL)
    if tz != TZ_LOCAL:
        dt = dt.astimezone(tz)
    return dt if as_datetime else dt.strftime(fmt)


def epoch2str(epoch_ts: float, fmt: str = DATETIME_FMT, millis: bool = False, tz: TZ = None) -> str:
    """
    Returns the given POSIX timestamp as a string with the given format, optionally converted to the given timezone

    :param epoch_ts: Seconds or milliseconds since the Unix epoch
    :param fmt: Time format to use for output
    :param millis: The provided timestamp was in milliseconds instead of seconds (default: False)
    :param tz: A :class:`datetime.tzinfo` or str timezone name (default: local)
    :return: The given time in the given format
    """
    tz = _get_tz(tz)
    dt = datetime.fromtimestamp((epoch_ts // 1000) if millis else epoch_ts, tz)
    return dt.strftime(fmt)


def str2epoch(dt: DateTime, fmt: str = DATETIME_FMT_NO_TZ, millis: bool = False, tz: TZ = None) -> int:
    """
    Convert a string timestamp to a POSIX timestamp (seconds/milliseconds since the Unix epoch of 1970-01-01T00:00:00Z)

    :param dt: A timestamp string/float/int or datetime object
    :param fmt: Time format used by the given input string
    :param millis: Return milliseconds since epoch instead of seconds
    :param tz: A :class:`datetime.tzinfo` or str timezone name (default: from timestamp if available, otherwise local)
    :return: The seconds or milliseconds since epoch that corresponds with the given timestamp
    """
    dt = datetime_with_tz(dt, fmt, tz)
    return int(dt.timestamp() * 1000) // (1 if millis else 1000)


def localize(
    dt: DateTime, in_fmt: str = DATETIME_FMT_NO_TZ, out_fmt: str = DATETIME_FMT, in_tz: TZ = None, out_tz: TZ = None
) -> str:
    """
    Convert the given timestamp string from one timezone to another

    :param dt: A timestamp string/float or datetime object
    :param in_fmt: Time format used by the given input string
    :param out_fmt: Time format to use for output
    :param in_tz: A :class:`datetime.tzinfo` or str timezone name to use if not parsed from dt (default: local)
    :param out_tz: The :class:`datetime.tzinfo` or str timezone name to use for output (default: local)
    :return: The given time in the given timezone and format
    """
    dt = datetime_with_tz(dt, in_fmt, in_tz)
    return dt.astimezone(_get_tz(out_tz)).strftime(out_fmt)


def as_utc(dt: DateTime, in_fmt: str = DATETIME_FMT_NO_TZ, out_fmt: str = DATETIME_FMT, tz: TZ = None) -> str:
    """
    :param dt: A timestamp string/float or datetime object
    :param in_fmt: Time format used by the given input string
    :param out_fmt: Time format to use for output
    :param tz: A :class:`datetime.tzinfo` or str timezone name to use if not parsed from dt (default: local)
    :return: The given time in UTC in the given format
    """
    return localize(dt, in_fmt=in_fmt, out_fmt=out_fmt, in_tz=tz, out_tz=TZ_UTC)


# region Helper Functions


def _get_tz(tz: Union[str, None, tzinfo]) -> Optional[tzinfo]:
    tz_obj = gettz(tz) if isinstance(tz, str) else tz
    if tz_obj is None:
        if isinstance(tz, str) and tz in TZ_ALIAS_MAP:
            return gettz(TZ_ALIAS_MAP[tz])
        elif tz is None:
            return TZ_LOCAL
    return tz_obj


def _parse_dt_from_str(dt: str, fmt: str, tz: Union[str, tzinfo, None]) -> tuple[datetime, dict[str, str]]:
    try:
        dt_fmt_search = _parse_dt_from_str._dt_fmt_search
    except AttributeError:
        # Odd number of preceding % => unescaped %z (i.e., need to tokenize)
        dt_fmt_search = _parse_dt_from_str._dt_fmt_search = re.compile('(?<!%)%(%%)*(?!%)[zZ]').search

    if dt_fmt_search(fmt):  # Trade-off: %z without : won't need this, but more conditions
        tokens = _tokenize_datetime(dt, fmt)  # would be required to tell if tokens should be generated later
        if tz:
            original_dt = dt
            fmt = fmt.replace('%z', '').replace('%Z', '')
            dt = _recompile_datetime(tokens, fmt)  # type(dt) is still str here
            for tok in ('z', 'Z'):
                if tok in tokens:
                    _parse_log.debug(f'Discarding %{tok}={tokens[tok]!r} from {original_dt!r} due to provided {tz=}')
    else:
        tokens = {}

    try:
        dt = datetime.strptime(dt, fmt)
    except ValueError as e:
        if tokens and 'does not match format' in str(e):
            if 'z' in tokens and ':' in tokens['z']:
                tokens['z'] = tokens['z'].replace(':', '')
                dt = datetime.strptime(_recompile_datetime(tokens, fmt), fmt)
            elif 'Z' in tokens:
                alt_fmt = fmt.replace('%Z', '')
                dt = datetime.strptime(_recompile_datetime(tokens, alt_fmt), alt_fmt)
            else:
                raise
        else:
            raise

    return dt, tokens


def _tokenize_datetime(dt: str, fmt: str) -> dict[str, str]:
    try:
        time_re = _tokenize_datetime._time_re
    except AttributeError:
        from _strptime import TimeRE  # Needed to work around timezone handling limitations
        time_re = _tokenize_datetime._time_re = TimeRE()
        time_re['z'] = r'(?P<z>[+-]\d\d:?[0-5]\d)'  # Allow ':' in timezone offset notation
        time_re['Z'] = r'(?P<Z>[0-9A-Za-z_/+-]+)'  # Allow any timezone possibly supported by pytz

    time_rx = time_re.compile(fmt)
    if not (m := time_rx.match(dt)):
        raise ValueError(f'time data={dt!r} does not match format={fmt!r}')
    elif len(dt) != m.end():
        raise ValueError(f'unconverted data remains: {dt[m.end():]}')
    return m.groupdict()


def _recompile_datetime(tokens: dict[str, str], fmt: str) -> str:
    dt_str = fmt
    for token, value in tokens.items():
        dt_str = dt_str.replace('%' + token, value)
    return dt_str

# endregion
