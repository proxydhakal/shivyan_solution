import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models import ContactInquiry, SiteSettings

logger = logging.getLogger(__name__)


def _company_name() -> str:
    try:
        return SiteSettings.get().company_name
    except Exception:
        return 'Shivyan Solutions'


def send_contact_inquiry_emails(inquiry: ContactInquiry) -> dict:
    """
    Notify the business inbox and optionally confirm to the inquirer.
    Returns {'staff': bool, 'inquirer': bool|None} so callers can log partial failures.
    """
    out = {'staff': False, 'inquirer': None}
    inbox = (getattr(settings, 'CONTACT_INBOX_EMAIL', None) or '') or (
        getattr(settings, 'CONTACT_EMAIL', None) or ''
    )
    if not inbox.strip():
        logger.error('CONTACT_INBOX_EMAIL is not set; skipping staff notification for inquiry %s', inquiry.pk)
    else:
        out['staff'] = _send_staff_email(inquiry, inbox.strip())

    if inquiry.email and inquiry.email.strip():
        out['inquirer'] = _send_inquirer_email(inquiry)
    return out


def _send_staff_email(inquiry: ContactInquiry, to_email: str) -> bool:
    company = _company_name()
    subject = f'[Website] New contact: {inquiry.name} (#{inquiry.pk})'
    ctx = {
        'inquiry': inquiry,
        'company': company,
        'received': timezone.localtime(inquiry.created_at) if inquiry.created_at else None,
    }
    text_body = render_to_string('core/emails/staff_inquiry.txt', ctx)
    html_body = render_to_string('core/emails/staff_inquiry.html', ctx)

    reply_to = [inquiry.email] if (inquiry.email and inquiry.email.strip()) else None
    from_email = settings.DEFAULT_FROM_EMAIL
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[to_email],
            reply_to=reply_to,
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        return True
    except (SMTPException, OSError):
        logger.exception('Failed to send staff contact email for inquiry %s', inquiry.pk)
    except Exception:  # noqa: BLE001 — surface unexpected mail backend issues
        logger.exception('Failed to send staff contact email for inquiry %s', inquiry.pk)
    return False


def _send_inquirer_email(inquiry: ContactInquiry) -> bool:
    company = _company_name()
    inbox = (getattr(settings, 'CONTACT_INBOX_EMAIL', None) or '') or (
        getattr(settings, 'CONTACT_EMAIL', None) or ''
    )
    subject = f'Thank you for contacting {company}'
    ctx = {
        'inquiry': inquiry,
        'company': company,
        'inbox': inbox,
    }
    text_body = render_to_string('core/emails/inquirer_confirmation.txt', ctx)
    html_body = render_to_string('core/emails/inquirer_confirmation.html', ctx)

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[inquiry.email.strip()],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        return True
    except (SMTPException, OSError):
        logger.exception('Failed to send inquirer confirmation for inquiry %s', inquiry.pk)
    except Exception:  # noqa: BLE001
        logger.exception('Failed to send inquirer confirmation for inquiry %s', inquiry.pk)
    return False
