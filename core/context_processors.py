from .models import Service, SiteSettings


def site_settings(request):
    """Inject site-wide data for layout (navbar, footer) on all pages."""
    return {
        'site': SiteSettings.get(),
        'services': Service.objects.filter(is_active=True),
    }


def newsletter_flash(request):
    """One-shot form errors / prefill for the footer newsletter form after redirect."""
    return {
        'newsletter_form_errors': request.session.pop('newsletter_form_errors', None) or {},
        'newsletter_prefill': request.session.pop('newsletter_prefill', None) or {},
    }
