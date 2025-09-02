import os
import json
from dotenv import load_dotenv
from dateutil import tz

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_WHITELIST = [int(x) for x in os.getenv("ADMIN_WHITELIST", "").replace(" ", "").split(",") if x]
SUBJECTS_FILE = os.getenv("SUBJECTS_FILE", "subjects.json")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Yekaterinburg")
HW_RETENTION_DAYS = int(os.getenv("HW_RETENTION_DAYS", "0"))


def load_subjects(path: str = SUBJECTS_FILE):
	try:
		with open(path, "r", encoding="utf-8") as f:
			data = json.load(f)
		id_to_name = {item["id"]: item["name"] for item in data}
		return data, id_to_name
	except Exception:
		default = [
			{"id": "math", "name": "Математика"},
			{"id": "physics", "name": "Физика"},
			{"id": "chemistry", "name": "Химия"},
			{"id": "biology", "name": "Биология"},
			{"id": "history", "name": "История"},
			{"id": "literature", "name": "Литература"},
			{"id": "english", "name": "Английский язык"},
			{"id": "cs", "name": "Информатика"},
			{"id": "geography", "name": "География"},
		]
		return default, {x["id"]: x["name"] for x in default}


def get_tz():
	return tz.gettz(TIMEZONE)
