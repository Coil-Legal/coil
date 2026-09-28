"""Export the installed IANA TZif history and future rules as VTIMEZONE.

RFC 9636 defines TZif blocks/footers; RFC 5545 defines observances. Reading
both avoids truncating an open-ended calendar's timezone at 2038.
"""
import calendar
import re
import struct
from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache
from importlib import resources
from pathlib import Path
from zoneinfo import TZPATH, ZoneInfo

EPOCH = datetime(1970, 1, 1)
NAME = r'(?:[A-Za-z]{3,}|<[^>]+>)'
TIME = r'[+-]?\d{1,3}(?::\d{1,2}(?::\d{1,2})?)?'
FOOTER = re.compile(rf'({NAME})({TIME})(?:({NAME})({TIME})?,([^,]+),([^,]+))?')


def _tzif(key):
    ZoneInfo(key)  # Validate the key before resolving a filesystem path.
    for root in TZPATH:
        file = Path(root) / key
        if file.is_file():
            return file.read_bytes()
    return resources.files('tzdata.zoneinfo').joinpath(*key.split('/')).read_bytes()


def _block(data, pos, width):
    assert data[pos:pos+4] == b'TZif'
    utc, std, leap, count, types, chars = struct.unpack_from('>6I', data, pos+20)
    pos += 44
    times = struct.unpack_from('>'+('q' if width == 8 else 'l')*count, data, pos)
    pos += width*count
    indices = data[pos:pos+count]; pos += count
    records = [struct.unpack_from('>lBB', data, pos+i*6) for i in range(types)]
    pos += types*6
    names = data[pos:pos+chars]; pos += chars
    records = [(offset, dst, names[index:].split(b'\0', 1)[0].decode('ascii'))
               for offset, dst, index in records]
    pos += leap*(width+4)+std+utc
    return pos, times, indices, records


def _seconds(value):
    sign = -1 if value.startswith('-') else 1
    bits = list(map(int, value.lstrip('+-').split(':')))
    return sign * sum(n*m for n, m in zip(bits, (3600, 60, 1)))


def _rule_date(rule, year):
    rule, _, clock = rule.partition('/')
    seconds = _seconds(clock or '2')
    if rule.startswith('M'):
        month, week, weekday = map(int, rule[1:].split('.'))
        first = datetime(year, month, 1)
        day = 1 + (weekday - (first.weekday()+1)%7)%7 + (week-1)*7
        if day > calendar.monthrange(year, month)[1]:
            day -= 7
        base = datetime(year, month, day)
    else:
        day = int(rule.lstrip('J'))
        if rule.startswith('J'):
            day -= 1
            if calendar.isleap(year) and day >= 59:
                day += 1
        base = datetime(year, 1, 1) + timedelta(days=day)
    return base + timedelta(seconds=seconds)


def _offset(seconds):
    sign = '+' if seconds >= 0 else '-'
    hours, rem = divmod(abs(seconds), 3600); minutes, secs = divmod(rem, 60)
    return f'{sign}{hours:02d}{minutes:02d}' + (f'{secs:02d}' if secs else '')


def _date(value):
    return f'{value.year:04d}{value.month:02d}{value.day:02d}T{value.hour:02d}{value.minute:02d}{value.second:02d}'


def _observance(kind, before, after, name, dates, rule=None):
    lines = ['BEGIN:'+kind, 'DTSTART:'+_date(dates[0]),
             'TZOFFSETFROM:'+_offset(before), 'TZOFFSETTO:'+_offset(after), 'TZNAME:'+name]
    if rule:
        lines.append('RRULE:'+rule)
    elif len(dates) > 1:
        lines.append('RDATE:'+','.join(map(_date, dates[1:])))
    return lines+['END:'+kind]


def _annual_rule(dates):
    """Use a compact annual rule only when it matches a full Gregorian cycle."""
    first = dates[0]
    for ordinal in ((first.day-1)//7+1, -1):
        if all(d.month == first.month and d.weekday() == first.weekday()
               and d.time() == first.time()
               and ((d.day-1)//7+1 == ordinal if ordinal > 0
                    else d.day+7 > calendar.monthrange(d.year, d.month)[1]) for d in dates):
            return f'FREQ=YEARLY;BYMONTH={first.month};BYDAY={ordinal}'+('MO','TU','WE','TH','FR','SA','SU')[first.weekday()]
    if all((d.month,d.day,d.time()) == (first.month,first.day,first.time()) for d in dates):
        return f'FREQ=YEARLY;BYMONTH={first.month};BYMONTHDAY={first.day}'
    return None


@lru_cache(maxsize=64)
def timezone_lines(key):
    data = _tzif(key)
    pos, times, indices, types = _block(data, 0, 4)
    footer = ''
    if data[4:5] in (b'2', b'3', b'4'):
        pos, times, indices, types = _block(data, pos, 8)
        footer = data[pos:].strip(b'\n').decode('ascii')
    groups = defaultdict(list)
    initial = types[0]; previous = initial
    last = datetime(1600, 1, 1)
    for timestamp, index in zip(times, indices):
        current = types[index]
        try:
            instant = EPOCH + timedelta(seconds=timestamp)
            wall = instant + timedelta(seconds=previous[0])
        except OverflowError:
            previous = current
            continue
        if current != previous:
            groups[(current[1], previous[0], current[0], current[2])].append(wall)
        previous = current; last = instant
    lines = ['BEGIN:VTIMEZONE', 'TZID:'+key]
    # An initial standard observance also defines the offset before recorded history.
    lines += _observance('STANDARD', initial[0], initial[0], initial[2], [datetime(1600, 1, 1)])
    for (dst,before,after,name), dates in groups.items():
        lines += _observance('DAYLIGHT' if dst else 'STANDARD', before, after, name, dates)
    if footer:
        match = FOOTER.fullmatch(footer)
        if not match:
            raise ValueError('Unsupported IANA timezone footer for '+key)
        std_name, std, dst_name, dst, start, end = match.groups()
        std = -_seconds(std)
        if dst_name:
            dst = -_seconds(dst) if dst else std+3600
            for name, before, after, rule, kind in ((dst_name,std,dst,start,'DAYLIGHT'),
                                                   (std_name,dst,std,end,'STANDARD')):
                # Evaluate 400 years, the exact Gregorian repeat cycle, including
                # extended POSIX transition times that cross a month boundary.
                year = max(1600, last.year-1)
                while _rule_date(rule, year)-timedelta(seconds=before) <= last:
                    year += 1
                dates = [_rule_date(rule, y) for y in range(year, year+400)]
                annual = _annual_rule(dates)
                if annual:
                    lines += _observance(kind,before,after,name.strip('<>'),dates[:1],annual)
                else:
                    for d in dates:
                        lines += _observance(kind,before,after,name.strip('<>'),[d],
                            f'FREQ=YEARLY;INTERVAL=400;BYMONTH={d.month};BYMONTHDAY={d.day}')
        elif not times:
            # Slim fixed-offset TZif files need not describe their footer in type0.
            lines = ['BEGIN:VTIMEZONE','TZID:'+key] + _observance(
                'STANDARD',std,std,std_name.strip('<>'),[datetime(1600,1,1)])
    return tuple(lines+['END:VTIMEZONE'])
