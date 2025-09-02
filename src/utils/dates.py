from datetime import datetime, timedelta, date
from typing import Optional

DATE_INPUT_FORMAT = "%d.%m.%Y"
DATE_ISO_FORMAT = "%Y-%m-%d"


def parse_user_date(text: str) -> Optional[date]:
	try:
		return datetime.strptime(text.strip(), DATE_INPUT_FORMAT).date()
	except Exception:
		return None


def to_iso(d: date) -> str:
	return d.strftime(DATE_ISO_FORMAT)


def from_iso(s: str) -> date:
	return datetime.strptime(s, DATE_ISO_FORMAT).date()


def today_in_tz(tzinfo) -> date:
	return datetime.now(tzinfo).date()


def tomorrow_in_tz(tzinfo) -> date:
	return today_in_tz(tzinfo) + timedelta(days=1)
