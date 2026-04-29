import logging
from email.utils import formataddr, parseaddr
from smtplib import SMTPException
from typing import Dict, List, Sequence

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from core.models import SiteSettings

from .models import BlogPost, NewsletterSubscriber

logger = logging.getLogger(__name__)

MAX_RECIPIENTS = 2000  # safety cap per post


def _public_base_url() -> str:
    u = (getattr(settings, 'NEWSLETTER_BASE_URL', None) or '').strip().rstrip('/')
    if u:
        return u
    hosts = list(getattr(settings, 'ALLOWED_HOSTS', []) or [])
    if not hosts or hosts[0] == '*':
        return 'http://127.0.0.1:8000'
    h = hosts[0]
    scheme = 'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'
    return f'{scheme}://{h}'


def _company_name() -> str:
    try:
        return SiteSettings.get().company_name
    except Exception:
        return 'Our team'


def _default_from_addr() -> str:
    return (getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'noreply@example.com').strip()


def _newsletter_from_email() -> str:
    """
    Return RFC 5322 From header value, e.g. "Shivyan Blog <hello@example.com>".
    """
    name = (getattr(settings, 'NEWSLETTER_FROM_NAME', None) or '').strip() or _company_name()
    _, addr = parseaddr(_default_from_addr())
    if not addr:
        _, addr = parseaddr(settings.DEFAULT_FROM_EMAIL)
    if not addr:
        addr = 'noreply@example.com'
    return formataddr((name, addr))


def _reply_to_list() -> Sequence[str]:
    r = (getattr(settings, 'NEWSLETTER_REPLY_TO', None) or '').strip()
    if not r:
        return []
    return [r]


def _list_unsubscribe_headers(unsub_url: str) -> Dict[str, str]:
    """Help Gmail/Apple Mail show a native Unsubscribe action (RFC 2369)."""
    u = (unsub_url or '').strip()
    if not u:
        return {}
    return {'List-Unsubscribe': f'<{u}>'}


def _send_multipart(
    *,
    subject: str,
    text_body: str,
    html_body: str,
    to: List[str],
    from_email: str,
    list_unsubscribe_url: str,
) -> bool:
    headers = _list_unsubscribe_headers(list_unsubscribe_url)
    reply_to = _reply_to_list() or None
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=to,
            reply_to=reply_to,
            headers=headers,
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        return True
    except (SMTPException, OSError) as e:
        logger.exception('Newsletter: SMTP failed to %s: %s', to, e)
    except Exception:  # noqa: BLE001
        logger.exception('Newsletter: send failed to %s (unexpected)', to)
    return False


def send_welcome_email(sub: NewsletterSubscriber) -> bool:
    """
    One-time confirmation after a new row is created. Includes unsubscribe link.
    """
    base = _public_base_url()
    company = _company_name()
    u_path = reverse('blog:newsletter_unsubscribe', kwargs={'token': sub.unsubscribe_token})
    post_list_path = reverse('blog:post_list')
    unsub_url = f'{base}{u_path}'
    subj = f'You’re subscribed — {company} blog'
    ctx = {
        'company': company,
        'base_url': base,
        'post_list_url': f'{base}{post_list_path}',
        'subscriber': sub,
        'unsub_url': unsub_url,
    }
    text = render_to_string('blog/emails/welcome_subscriber.txt', ctx)
    html = render_to_string('blog/emails/welcome_subscriber.html', ctx)
    return _send_multipart(
        subject=subj,
        text_body=text,
        html_body=html,
        to=[sub.email],
        from_email=_newsletter_from_email(),
        list_unsubscribe_url=unsub_url,
    )


def send_new_subscriber_staff_email(sub: NewsletterSubscriber) -> bool:
    """
    Notify staff/business inbox that a new subscriber joined.
    """
    inbox = (getattr(settings, 'NEWSLETTER_INBOX_EMAIL', None) or '').strip()
    if not inbox:
        return False
    company = _company_name()
    base = _public_base_url()
    post_list_path = reverse('blog:post_list')
    ctx = {
        'company': company,
        'subscriber': sub,
        'post_list_url': f'{base}{post_list_path}',
    }
    subject = f'[Website] New newsletter subscriber — {sub.email}'
    text = render_to_string('blog/emails/new_subscriber_staff.txt', ctx)
    html = render_to_string('blog/emails/new_subscriber_staff.html', ctx)
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=_newsletter_from_email(),
            to=[inbox],
        )
        msg.attach_alternative(html, 'text/html')
        msg.send(fail_silently=False)
        return True
    except (SMTPException, OSError) as e:
        logger.exception('Newsletter: staff notify failed: %s', e)
    except Exception:  # noqa: BLE001
        logger.exception('Newsletter: staff notify failed (unexpected)')
    return False


def send_new_post_to_subscribers(post: BlogPost) -> int:
    """
    Send one message per active subscriber (unique unsubscribe link per address).
    Returns number of successfully sent emails.
    """
    if not post.is_published:
        return 0
    base = _public_base_url()
    post_url = f"{base}{post.get_absolute_url()}"
    company = _company_name()
    from_email = _newsletter_from_email()
    subject = f'New article: {post.title} — {company}'

    n_ok = 0
    n_fail = 0
    post_list_path = reverse('blog:post_list')
    subs: List[NewsletterSubscriber] = list(
        NewsletterSubscriber.objects.filter(is_active=True)[:MAX_RECIPIENTS]
    )
    for sub in subs:
        u_path = reverse('blog:newsletter_unsubscribe', kwargs={'token': sub.unsubscribe_token})
        unsub_url = f'{base}{u_path}'
        ctx = {
            'post': post,
            'post_url': post_url,
            'post_list_url': f'{base}{post_list_path}',
            'company': company,
            'base_url': base,
            'subscriber': sub,
            'unsub_url': unsub_url,
        }
        text = render_to_string('blog/emails/new_post_subscribers.txt', ctx)
        html = render_to_string('blog/emails/new_post_subscribers.html', ctx)
        if _send_multipart(
            subject=subject,
            text_body=text,
            html_body=html,
            to=[sub.email],
            from_email=from_email,
            list_unsubscribe_url=unsub_url,
        ):
            n_ok += 1
        else:
            n_fail += 1
    if n_fail:
        logger.warning('Newsletter: %s sent, %s failed for post %s', n_ok, n_fail, post.pk)
    return n_ok
