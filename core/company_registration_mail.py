import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import CompanyRegistrationApplication, SiteSettings

logger = logging.getLogger(__name__)


def _company_name() -> str:
    try:
        return SiteSettings.get().company_name
    except Exception:
        return 'Our team'


def _staff_inbox() -> str:
    return (getattr(settings, 'CONTACT_INBOX_EMAIL', None) or getattr(settings, 'CONTACT_EMAIL', None) or '').strip()


def send_company_registration_staff_email(app: CompanyRegistrationApplication) -> bool:
    inbox = _staff_inbox()
    if not inbox:
        return False
    company = _company_name()
    subject = f'[Website] Company registration application: {app.desired_company_name} (#{app.pk})'
    ctx = {'app': app, 'company': company}
    text = render_to_string('core/emails/company_registration_staff.txt', ctx)
    html = render_to_string('core/emails/company_registration_staff.html', ctx)
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[inbox],
            reply_to=[app.email],
        )
        msg.attach_alternative(html, 'text/html')
        msg.send(fail_silently=False)
        return True
    except (SMTPException, OSError):
        logger.exception('Company application: failed staff email for %s', app.pk)
    except Exception:  # noqa: BLE001
        logger.exception('Company application: failed staff email for %s (unexpected)', app.pk)
    return False


def send_company_registration_applicant_email(app: CompanyRegistrationApplication) -> bool:
    if not (app.email and app.email.strip()):
        return False
    company = _company_name()
    subject = f'We received your company registration application — {company}'
    ctx = {'app': app, 'company': company}
    text = render_to_string('core/emails/company_registration_applicant.txt', ctx)
    html = render_to_string('core/emails/company_registration_applicant.html', ctx)
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[app.email.strip()],
        )
        msg.attach_alternative(html, 'text/html')
        msg.send(fail_silently=False)
        return True
    except (SMTPException, OSError):
        logger.exception('Company application: failed applicant email for %s', app.pk)
    except Exception:  # noqa: BLE001
        logger.exception('Company application: failed applicant email for %s (unexpected)', app.pk)
    return False

