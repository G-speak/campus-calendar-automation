"""Discover iCloud calendars and shift an existing course without replacing UID."""
import argparse
import os
from datetime import timedelta
from pathlib import Path
import caldav
from dotenv import load_dotenv
load_dotenv()

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('discover')
    shift=sub.add_parser('shift')
    shift.add_argument('--title',required=True)
    shift.add_argument('--from-date',required=True)
    shift.add_argument('--to-date',required=True)
    shift.add_argument('--days',required=True,type=int)
    shift.add_argument('--apply',action='store_true')
    args=p.parse_args()
    client=caldav.DAVClient(url=os.environ['CALDAV_BASE'],username=os.environ['APPLE_ID'],password=os.environ['APP_PWD'],headers={'Connection':'close'})
    if args.command=='discover':
        for c in client.principal().calendars(): print(c.get_display_name(),str(c.url))
        return
    # Exact title/date matching, default read-only preview.
    import requests
    import xml.etree.ElementTree as ET
    from urllib.parse import urljoin
    from icalendar import Calendar
    url=os.environ['COURSE_CALENDAR_URL']
    s=requests.Session(); s.auth=(os.environ['APPLE_ID'],os.environ['APP_PWD']);s.headers['Connection']='close'
    xml='<c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav"><d:prop><d:getetag/><c:calendar-data/></d:prop><c:filter><c:comp-filter name="VCALENDAR"><c:comp-filter name="VEVENT"/></c:comp-filter></c:filter></c:calendar-query>'
    r=s.request('REPORT',url,headers={'Depth':'1','Content-Type':'application/xml'},data=xml,timeout=60);r.raise_for_status()
    changes=[]
    for resp in ET.fromstring(r.content).findall('{DAV:}response'):
        raw=resp.findtext('.//{urn:ietf:params:xml:ns:caldav}calendar-data')
        if not raw: continue
        cal=Calendar.from_ical(raw)
        for ev in cal.walk('VEVENT'):
            if str(ev.get('SUMMARY'))!=args.title:continue
            start=ev.decoded('DTSTART');day=start.date().isoformat()
            if not args.from_date<=day<=args.to_date:continue
            if ev.get('RRULE') or ev.get('RECURRENCE-ID'):raise RuntimeError('仅支持独立单次课程事件')
            for key in ('DTSTART','DTEND'):
                prop=ev[key];value=prop.dt+timedelta(days=args.days);params=dict(prop.params)
                del ev[key];ev.add(key,value,parameters=params)
            ev['SEQUENCE']=int(ev.get('SEQUENCE',0))+1
            changes.append((urljoin(url,resp.findtext('{DAV:}href')),resp.findtext('.//{DAV:}getetag'),raw,cal))
            print(day,'->',ev.decoded('DTSTART').isoformat())
    print('Matched',len(changes),'apply=',args.apply)
    if not args.apply:return
    from datetime import datetime,timezone
    folder=Path('backups')/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder.mkdir(parents=True)
    for i,(href,etag,raw,cal) in enumerate(changes):
        if not etag:raise RuntimeError('Missing ETag; refusing unsafe update')
        (folder/f'{i}.ics').write_text(raw)
        r=s.put(href,data=cal.to_ical(),headers={'Content-Type':'text/calendar','If-Match':etag},timeout=60);r.raise_for_status()
        verify=s.get(href,timeout=60);verify.raise_for_status()
        actual=Calendar.from_ical(verify.content).walk('VEVENT')[0];expected=cal.walk('VEVENT')[0]
        for field in ('UID','DTSTART','DTEND'):
            if actual[field]!=expected[field]:raise RuntimeError('Read-back mismatch; stopped')
    print('Verified',len(changes),'updates; originals saved locally under backups/')

if __name__=='__main__':main()
