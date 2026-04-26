import hashlib

from django.utils.crypto import get_random_string


def get_client_ip(request) -> str | None:
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip() or None
    ip = request.META.get('REMOTE_ADDR')
    return str(ip) if ip else None


def make_voter_key(request) -> str:
    if not request.session.session_key:
        request.session.cycle_key()
    ip = get_client_ip(request) or '0.0.0.0'
    sk = request.session.session_key or get_random_string(32)
    raw = f'{ip}|{sk}'.encode('utf-8')
    return hashlib.sha256(raw).hexdigest()
