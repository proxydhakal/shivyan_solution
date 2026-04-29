"""Build https://wa.me/… for SiteSettings office phone."""


def build_whatsapp_wa_url(phone) -> str:
    if phone is None:
        return ''
    d = ''.join(c for c in str(phone) if c.isdigit())
    if not d:
        return ''
    if d.startswith('977') and len(d) >= 12:
        num = d
    elif len(d) in (9, 10) and d.startswith('9'):
        num = '977' + d
    elif len(d) >= 10:
        num = d
    else:
        return ''
    return f'https://wa.me/{num}'
