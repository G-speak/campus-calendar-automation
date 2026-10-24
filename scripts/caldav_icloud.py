# -*- coding: utf-8 -*-
"""Course upload/backup tool. Configure APPLE_ID, APP_PWD and COURSE_CALENDAR_URL in .env.
Commands: list | backup PATH | put JSON_PATH.
Uploads create independent course events with a 15 minute reminder.
Do not repeat an upload: the legacy importer generates fresh event identifiers.
"""
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
import xml.etree.ElementTree as ET
import os
import sys
import re
import json
import uuid
import datetime
from collections import Counter

import niquests
from icalendar import Calendar, Event, Alarm

USER = os.environ["APPLE_ID"]
PW = os.environ["APP_PWD"]
CAL = os.environ["COURSE_CALENDAR_URL"].rstrip("/")
AUTH = (USER, PW)
XML_H = {"Connection": "close", "Content-Type": "application/xml; charset=utf-8", "Depth": "1"}
PUT_H = {"Connection": "close", "Content-Type": "text/calendar; charset=utf-8"}

REPORT = """<?xml version="1.0" encoding="utf-8" ?>
<c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
 <d:prop><c:calendar-data/></d:prop>
 <c:filter><c:comp-filter name="VCALENDAR"><c:comp-filter name="VEVENT"/></c:comp-filter></c:filter>
</c:calendar-query>"""


def sess():
    return niquests.Session(disable_http2=True)


def fetch():
    """返回 (list[Calendar], 原始xml)"""
    r = sess().request("REPORT", CAL + "/", headers=XML_H, data=REPORT.encode(), auth=AUTH, timeout=90)
    if r.status_code != 207:
        raise SystemExit("REPORT failed %s: %s" % (r.status_code, r.text[:300]))
    cals = []
    for response in ET.fromstring(r.content).findall('{DAV:}response'):
        raw = response.findtext('.//{urn:ietf:params:xml:ns:caldav}calendar-data')
        if raw:
            cals.append(Calendar.from_ical(raw))
    return cals, r.text


def cmd_list():
    cals, _ = fetch()
    c = Counter()
    for cal in cals:
        for ev in cal.walk("VEVENT"):
            c[str(ev.get("SUMMARY") or "")] += 1
    print("TOTAL:", sum(c.values()))
    for k, v in sorted(c.items()):
        print("  %-46s %d" % (k, v))


def cmd_backup(path):
    cals, _ = fetch()
    out = Calendar()
    out.add("prodid", "-//hermes course-timetable//CN")
    out.add("version", "2.0")
    n = 0
    for cal in cals:
        for ev in cal.walk("VEVENT"):
            out.add_component(ev)
            n += 1
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(out.to_ical())
    print("backup events=%d -> %s" % (n, path))


def cmd_put(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    ok = 0
    for e in spec["events"]:
        day = datetime.date.fromisoformat(e["day"])
        h0, m0 = [int(x) for x in e["start"].split(":")]
        h1, m1 = [int(x) for x in e["end"].split(":")]
        cal = Calendar()
        cal.add("prodid", "-//hermes course-timetable//CN")
        cal.add("version", "2.0")
        ev = Event()
        uid = str(uuid.uuid4()) + "@hermes-timetable"
        ev.add("uid", uid)
        ev.add("summary", e["summary"])
        ev.add("dtstart", datetime.datetime.combine(day, datetime.time(h0, m0)))
        ev.add("dtend", datetime.datetime.combine(day, datetime.time(h1, m1)))
        if e.get("location"):
            ev.add("location", e["location"])
        if e.get("description"):
            ev.add("description", e["description"])
        al = Alarm()
        al.add("action", "DISPLAY")
        al.add("description", e["summary"])
        al.add("trigger", datetime.timedelta(minutes=-15))
        ev.add_component(al)
        cal.add_component(ev)
        r = sess().request("PUT", CAL + "/" + uid + ".ics", headers=PUT_H,
                           data=cal.to_ical(), auth=AUTH, timeout=60)
        print("%s %s %s" % (r.status_code, e["day"], e["summary"]))
        if r.status_code in (201, 204):
            ok += 1
    print("created=%d/%d" % (ok, len(spec["events"])))


if __name__ == "__main__":
    a = sys.argv[1:] or ["list"]
    {"list": cmd_list,
     "backup": lambda: cmd_backup(a[1]),
     "put": lambda: cmd_put(a[1])}[a[0]]()
