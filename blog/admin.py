from django.contrib import admin
from .models import (
    SitePage,
    BlogCategory,
    BlogTag,
    BlogPost,
    BlogComment,
    NewsletterSubscriber,
    PostRating,
)


@admin.register(SitePage)
class SitePageAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'is_published',
        'show_in_header',
        'show_in_footer',
        'menu_order',
        'updated_at',
    ]
    list_filter = ['is_published', 'show_in_header', 'show_in_footer']
    list_editable = ['menu_order', 'is_published', 'show_in_header', 'show_in_footer']
    search_fields = ['title', 'slug', 'content']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    list_editable = ['order']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'category',
        'author',
        'is_published',
        'published_at',
    ]
    list_filter = ['is_published', 'category', 'tags', 'published_at']
    search_fields = ['title', 'excerpt', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    filter_horizontal = ['tags']
    raw_id_fields = ['author']
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'author', 'category', 'tags')}),
        (
            'Content',
            {
                'fields': ('excerpt', 'content', 'cover'),
            },
        ),
        (
            'Publish',
            {
                'fields': (
                    'is_published',
                    'published_at',
                    'allow_comments',
                    'allow_rating',
                )
            },
        ),
    )
    save_on_top = True

    def save_model(self, request, obj, form, change) -> None:
        if not change and not obj.author_id and request.user.is_authenticated:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'post', 'is_approved', 'created_at', 'ip']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['name', 'email', 'body', 'post__title']
    list_editable = ['is_approved']
    date_hierarchy = 'created_at'


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'is_active', 'subscribed_at', 'ip']
    list_filter = ['is_active', 'subscribed_at']
    list_editable = ['is_active']
    search_fields = ['email', 'name']
    readonly_fields = ['unsubscribe_token', 'subscribed_at', 'updated_at', 'ip', 'user_agent']


@admin.register(PostRating)
class PostRatingAdmin(admin.ModelAdmin):
    list_display = ['post', 'value', 'ip', 'created_at']
    list_filter = ['value']
    readonly_fields = ['voter_key', 'ip', 'post', 'value', 'created_at', 'updated_at']

    def has_add_permission(self, request):
        return False
