"""
Datetime-related misc utilities

:author: Doug Skrypa
"""

__all__ = ['format_duration', 'timedelta_to_str']


def format_duration(seconds: float) -> str:
    """
    Formats time in seconds as (Dd)HH:MM:SS (time.stfrtime() is not useful for formatting durations).

    :param seconds: Number of seconds to format
    :return: Given number of seconds as (Dd)HH:MM:SS
    """
    x = '-' if seconds < 0 else ''
    m, s = divmod(abs(seconds), 60)
    h, m = divmod(int(m), 60)
    d, h = divmod(h, 24)
    x = f'{x}{d}d' if d > 0 else x
    return f'{x}{h:02d}:{m:02d}:{s:02d}' if isinstance(s, int) else f'{x}{h:02d}:{m:02d}:{s:05.2f}'


def timedelta_to_str(delta):
    m, s = divmod(delta.seconds, 60)
    h, m = divmod(m, 60)
    td_str = f'{h:d}:{m:02d}:{s:02d}'
    return f'{delta.days:d}d, {td_str}' if delta.days != 0 else td_str
