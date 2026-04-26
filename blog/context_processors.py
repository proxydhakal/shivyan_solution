from .models import SitePage


def cms_menus(_request) -> dict:
    """Dynamic header/footer pages from the CMS; available on all templates via context_processors."""
    return {
        'header_pages': SitePage.objects.filter(
            is_published=True, show_in_header=True
        ).order_by('menu_order', 'title'),
        'footer_pages': SitePage.objects.filter(
            is_published=True, show_in_footer=True
        ).order_by('menu_order', 'title'),
    }
