from ..config import ADMIN_WHITELIST


def is_whitelisted(user_id: int) -> bool:
	return user_id in ADMIN_WHITELIST
