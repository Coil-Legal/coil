"""Independent recurrence expansion with timezone data read from the feed itself."""
from datetime import datetime, date, timezone
from io import StringIO
from zoneinfo import ZoneInfo
import pytest
from dateutil.rrule import rrulestr
from dateutil.tz import tzical
from app.blueprints.calendar import build_ics
from app.models import CalendarEvent
from tests.test_phase1_independent import app


def expand(body):
    text=body.replace('\r\n ','')
    event=text.split('BEGIN:VEVENT\r\n')[1].split('END:VEVENT')[0]
    lines=event.splitlines()
    start=next(l for l in lines if l.startswith('DTSTART'))
    rule=next(l.split(':',1)[1] for l in lines if l.startswith('RRULE:'))
    key,value=start.split(':',1)
    if ';TZID=' in key:
        tzid=key.split('=',1)[1]
        component=text.split('BEGIN:VTIMEZONE')[1].split('END:VTIMEZONE')[0]
        zone=tzical(StringIO('BEGIN:VTIMEZONE'+component+'END:VTIMEZONE\r\n')).get(tzid)
        start=datetime.strptime(value,'%Y%m%dT%H%M%S').replace(tzinfo=zone)
    else:
        start=datetime.strptime(value,'%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
    return rrulestr(rule, dtstart=start)


@pytest.mark.parametrize('zone,recurrence,start,until',[
 ('America/Chicago','weekly',datetime(2026,10,25,9),date(2026,11,8)),
 ('America/Chicago','monthly',datetime(2027,1,31,9),date(2027,4,30)),
 ('America/Chicago','yearly',datetime(2024,2,29,9),date(2028,3,1)),
 ('Asia/Tokyo','monthly',datetime(2027,1,31,0,30),date(2027,4,30)),
 ('Australia/Lord_Howe','daily',datetime(2026,10,3,9),date(2026,10,5)),
 ('UTC','monthly',datetime(2027,1,31,9),date(2027,4,30)),
 ('America/Chicago','weekly',datetime(2040,10,28,9),date(2040,11,11)),
])
def test_timed_series_matches_ui_with_embedded_zone(zone,recurrence,start,until):
 e=CalendarEvent(id=1,uid='qa-recurrence',title='QA recurrence',starts_at=start,
                 all_day=False,recurrence=recurrence,recurrence_until=until)
 expected=list(e.occurrences(start,datetime(until.year+1,1,1)))
 actual=[d.astimezone(ZoneInfo(zone)).replace(tzinfo=None) for d in expand(build_ics([e],tz_name=zone))]
 assert actual==expected


@pytest.mark.parametrize('key', ['America/Chicago','Asia/Tokyo','Europe/Dublin','Australia/Lord_Howe',
                                'Africa/Casablanca','Asia/Gaza','America/Nuuk','Pacific/Auckland','UTC'])
def test_embedded_timezone_matches_iana_history_and_far_future(key):
 from app.calendar_timezone import timezone_lines
 exported=tzical(StringIO('\r\n'.join(timezone_lines(key))+'\r\n')).get(key)
 for year in (1800,1900,2026,2040,2100,2400,2800,9998):
  for month in (1,3,4,7,10,11,12):
   instant=datetime(year,month,15,12,tzinfo=timezone.utc)
   assert instant.astimezone(exported).replace(tzinfo=None)==instant.astimezone(ZoneInfo(key)).replace(tzinfo=None), (key,instant)


def test_open_series_timezone_rules_survive_2038():
 e=CalendarEvent(id=1,uid='qa-open',title='QA open',starts_at=datetime(2026,10,25,9),
                 all_day=False,recurrence='weekly')
 body=build_ics([e],tz_name='America/Chicago')
 series=expand(body)
 actual=series.between(datetime(2040,10,1,tzinfo=timezone.utc),datetime(2040,12,1,tzinfo=timezone.utc))
 assert actual and all(d.astimezone(ZoneInfo('America/Chicago')).hour==9 for d in actual)
 assert len(body)<20000


@pytest.mark.parametrize('recurrence,start,until',[
 ('weekly','2026-10-25T09:00','2026-11-08'),
 ('monthly','2027-01-31T09:00','2027-04-30'),
])
def test_saved_series_in_firm_and_owner_feed(app,recurrence,start,until):
 from app.extensions import db
 from app.models import Firm
 from app.blueprints.calendar import feed_secret
 from tests.test_phase1_independent import staff
 with app.app_context():
  Firm.get().timezone='America/Chicago';db.session.commit()
  urls=[f'/calendar/feed/{feed_secret()}.ics',f'/calendar/feed/u/1/{feed_secret(1)}.ics']
 client,csrf=staff(app)
 assert client.post('/calendar/new',data={'_csrf':csrf,'title':'QA saved recurrence','starts_at':start,
  'recurrence':recurrence,'recurrence_until':until,'user_id':'1'}).status_code==302
 with app.app_context():
  e=CalendarEvent.query.one();expected=list(e.occurrences(datetime.fromisoformat(start),datetime(2028,1,1)))
 for url in urls:
  response=client.get(url);assert response.status_code==200
  actual=[d.astimezone(ZoneInfo('America/Chicago')).replace(tzinfo=None) for d in expand(response.get_data(as_text=True))]
  assert actual==expected
