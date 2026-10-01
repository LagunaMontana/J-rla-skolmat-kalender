import urllib.request
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape

RSS_URL = "https://skolmaten.se/api/4/rss/week/jarla-skola?locale=sv"

def clean_html(text):
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()

def escape_ical(text):
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )

# Hämta RSS
with urllib.request.urlopen(RSS_URL) as response:
    rss_data = response.read()

root = ET.fromstring(rss_data)

events = []

for item in root.findall(".//item"):
    title = clean_html(item.findtext("title"))
    description = clean_html(item.findtext("description"))
    pub_date = item.findtext("pubDate")

    # Försök hitta datum i titel eller beskrivning
    combined = f"{title} {description}"

    date_match = re.search(
        r"(\d{4})-(\d{2})-(\d{2})",
        combined
    )

    if date_match:
        event_date = datetime.strptime(
            date_match.group(0), "%Y-%m-%d"
        ).date()
    elif pub_date:
        event_date = parsedate_to_datetime(pub_date).date()
    else:
        continue

    events.append((event_date, title, description))

calendar = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Jarla Skolmat//SV",
    "CALSCALE:GREGORIAN",
    "X-WR-CALNAME:Järla skolmat",
]

for event_date, title, description in events:
    date_string = event_date.strftime("%Y%m%d")
    end_date_string = (event_date + timedelta(days=1)).strftime("%Y%m%d")

    summary = f"🍽 {description.replace(chr(10), ' / ')}" if description else "🍽 Skolmat"
    details = f"{title}\n{description}" if description else title

    calendar.extend([
        "BEGIN:VEVENT",
        f"UID:{date_string}-jarla-skolmat",
        f"DTSTART;VALUE=DATE:{date_string}",
        f"DTEND;VALUE=DATE:{end_date_string}",
        f"SUMMARY:{escape_ical(summary)}",
        f"DESCRIPTION:{escape_ical(details)}",
        "END:VEVENT",
    ])

calendar.append("END:VCALENDAR")

with open("jarla-skolmat.ics", "w", encoding="utf-8") as f:
    f.write("\r\n".join(calendar) + "\r\n")

print(f"Klart! Skapade {len(events)} kalenderposter.")
