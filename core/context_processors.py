from .models import Service, SiteSettings
from .whatsapp_url import build_whatsapp_wa_url


def site_settings(request):
    """Inject site-wide data for layout (navbar, footer) on all pages."""
    site = SiteSettings.get()
    phone = getattr(site, 'phone', None) or '9744651716'
    return {
        'site': site,
        'services': Service.objects.filter(is_active=True),
        'whatsapp_chat_url': build_whatsapp_wa_url(phone),
    }


def newsletter_flash(request):
    """One-shot form errors / prefill for the footer newsletter form after redirect."""
    return {
        'newsletter_form_errors': request.session.pop('newsletter_form_errors', None) or {},
        'newsletter_prefill': request.session.pop('newsletter_prefill', None) or {},
    }
