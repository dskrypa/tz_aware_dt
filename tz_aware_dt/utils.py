"""
Datetime-related misc utilities

:author: Doug Skrypa
"""

__all__ = ['format_duration', 'timedelta_to_str']


def format_duration(seconds):
    """
    Formats time in seconds as (Dd)HH:MM:SS (time.stfrtime() is not useful for formatting durations).

    :param float seconds: Number of seconds to format
    :return: Given number of seconds as (Dd)HH:MM:SS
    """
    x = '-' if seconds < 0 else ''
    m, s = divmod(abs(seconds), 60)
    h, m = divmod(int(m), 60)
    d, h = divmod(h, 24)
    x = '{}{}d'.format(x, d) if d > 0 else x

    if isinstance(s, int):
        return '{}{:02d}:{:02d}:{:02d}'.format(x, h, m, s)
    return '{}{:02d}:{:02d}:{:05.2f}'.format(x, h, m, s)


def timedelta_to_str(delta):
    m, s = divmod(delta.seconds, 60)
    h, m = divmod(m, 60)
    td_str = '{:d}:{:02d}:{:02d}'.format(h, m, s)
    if delta.days != 0:
        td_str = '{:d}d, {}'.format(delta.days, td_str)
    return td_str
