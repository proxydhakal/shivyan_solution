import logging

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import BlogPost
from .newsletter_mail import send_new_post_to_subscribers

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=BlogPost)
def _blogpost_before_save(sender, instance, **kwargs) -> None:
    if not instance.pk:
        instance._prev_is_published = None
    else:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._prev_is_published = old.is_published
        except sender.DoesNotExist:
            instance._prev_is_published = None


@receiver(post_save, sender=BlogPost)
def _blogpost_after_save(sender, instance, created, **kwargs) -> None:
    if not instance.is_published:
        return
    prev = getattr(instance, '_prev_is_published', None)
    should_send = (created and instance.is_published) or (prev is False)
    if not should_send:
        return

    def _on_commit() -> None:
        try:
            n = send_new_post_to_subscribers(instance)
            if n:
                logger.info(
                    'Newsletter: new post %r notified subscribers (%s batch(es))',
                    instance.slug,
                    n,
                )
        except Exception:  # noqa: BLE001
            logger.exception('Newsletter: failed to send for post %s', instance.pk)

    transaction.on_commit(_on_commit)
