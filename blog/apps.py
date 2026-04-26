from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
    verbose_name = 'Pages & blog'

    def ready(self) -> None:
        import blog.signals  # noqa: F401 — newsletter emails on new published posts
