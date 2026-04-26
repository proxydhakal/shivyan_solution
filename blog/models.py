import secrets

from django.conf import settings
from django.db import models
from django.db.models import Avg, Count
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from ckeditor_uploader.fields import RichTextUploadingField


class SitePage(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    content = RichTextUploadingField()
    show_in_header = models.BooleanField(default=False)
    show_in_footer = models.BooleanField(default=False)
    menu_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True, db_index=True)
    meta_description = models.TextField(blank=True, help_text='Optional SEO description')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['menu_order', 'title']

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse('blog:page_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title)[:200]
        super().save(*args, **kwargs)


class BlogCategory(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=130, unique=True, db_index=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Blog categories'

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return f"{reverse('blog:post_list')}?category={self.slug}"


class BlogTag(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return f"{reverse('blog:post_list')}?tag={self.slug}"


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_posts',
    )
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
    )
    tags = models.ManyToManyField(BlogTag, blank=True, related_name='posts')
    excerpt = models.TextField(blank=True, max_length=500, help_text='Short summary for list view')
    content = RichTextUploadingField()
    cover = models.ImageField(upload_to='blog/covers/%Y/%m', blank=True, null=True)
    is_published = models.BooleanField(default=True, db_index=True)
    published_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    allow_comments = models.BooleanField(default=True)
    allow_rating = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ['-published_at', '-id']

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.title)[:200]
        super().save(*args, **kwargs)

    def approved_comments(self):
        return self.comments.filter(is_approved=True).order_by('created_at')

    @property
    def rating_stats(self) -> dict:
        agg = self.ratings.aggregate(avg=Avg('value'), c=Count('id'))
        avg = agg['avg']
        return {
            'average': float(round(avg, 1)) if avg is not None else None,
            'count': agg['c'] or 0,
        }


class BlogComment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=120)
    email = models.EmailField()
    body = models.TextField(max_length=4000)
    is_approved = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip = models.GenericIPAddressField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'comment'
        verbose_name_plural = 'comments'

    def __str__(self) -> str:
        return f'{self.name} on {self.post_id}'


class PostRating(models.Model):
    """One row per (post, voter_key); voter_key is derived from IP + session in the view."""
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='ratings')
    value = models.PositiveSmallIntegerField(choices=[(i, f'{i} star(s)') for i in range(1, 6)])
    voter_key = models.CharField(max_length=64, db_index=True, editable=False)
    ip = models.GenericIPAddressField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('post', 'voter_key')]

    def __str__(self) -> str:
        return f'{self.value} for post {self.post_id}'


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True, db_index=True, max_length=254)
    name = models.CharField(max_length=120, blank=True, help_text='Optional')
    is_active = models.BooleanField(
        default=True, db_index=True, help_text='Deselect to stop sending; use unsubscribe to self-remove.'
    )
    unsubscribe_token = models.CharField(max_length=64, unique=True, db_index=True, editable=False)
    subscribed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    ip = models.GenericIPAddressField(null=True, blank=True, editable=False)
    user_agent = models.TextField(blank=True, default='', editable=False)

    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = 'newsletter subscriber'
        verbose_name_plural = 'newsletter subscribers'

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs) -> None:
        if not self.unsubscribe_token:
            self.unsubscribe_token = secrets.token_urlsafe(48)[:64]
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)
