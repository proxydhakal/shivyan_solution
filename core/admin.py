from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from .models import SiteSettings, Service, ServiceCategory, WhyChooseUs, ProcessStep, Testimonial, ContactInquiry


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            'Brand & website title',
            {
                'fields': (
                    'company_name',
                    'company_name_nepali',
                    'company_name_suffix',
                    'site_title',
                    'tagline',
                    'tagline_en',
                    'logo',
                )
            },
        ),
        (
            'SEO & sharing',
            {
                'fields': (
                    'meta_description',
                    'meta_keywords',
                    'favicon',
                    'apple_touch_icon',
                    'og_image',
                )
            },
        ),
        (
            'Social media (footer & visibility)',
            {
                'description': 'Add URLs to show icons in the site footer. Leave blank to hide that network.',
                'fields': (
                    'facebook_url',
                    'linkedin_url',
                    'instagram_url',
                    'twitter_url',
                    'youtube_url',
                ),
            },
        ),
        ('Hero Section', {'fields': ('hero_headline', 'hero_subtext', 'hero_cta_label')}),
        ('Contact Details', {'fields': ('phone', 'email', 'address', 'office_hours')}),
        ('About Section', {'fields': ('about_text_nepali', 'about_text_en')}),
        ('Stats', {'fields': ('clients_count', 'experience_years', 'retention_percent', 'services_count')}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'order']
    list_display_links = ['name']
    list_editable = ['order']
    list_filter = ['color']
    search_fields = ['name']
    ordering = ['order', 'name']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display  = ['title_en', 'title_nepali', 'category', 'is_featured', 'is_cta_card', 'is_active', 'order']
    list_display_links = ['title_en', 'title_nepali']
    list_editable = ['is_featured', 'is_active', 'order']
    list_filter   = ['is_active', 'category', 'is_featured', 'is_cta_card']
    search_fields = ['title_en', 'title_nepali', 'description', 'tags']
    ordering = ['order', 'title_en']
    list_select_related = ['category']


@admin.register(WhyChooseUs)
class WhyChooseUsAdmin(admin.ModelAdmin):
    list_display  = ['title', 'color', 'is_active', 'order']
    list_display_links = ['title']
    list_editable = ['is_active', 'order']
    list_filter   = ['color', 'is_active']
    search_fields = ['title', 'description']
    ordering = ['order', 'title']


@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display  = ['step_number', 'title', 'color']
    list_display_links = ['title']
    list_editable = ['color']
    list_filter   = ['color']
    search_fields = ['title', 'description']
    ordering      = ['step_number']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display  = ['client_name', 'client_role', 'rating', 'is_active', 'order', 'created_at']
    list_display_links = ['client_name']
    list_editable = ['is_active', 'order']
    list_filter   = ['is_active', 'rating', ('created_at', DateFieldListFilter)]
    search_fields = ['client_name', 'client_role', 'quote']
    ordering = ['order', '-created_at']
    date_hierarchy = 'created_at'


class ServiceInquiryFilter(admin.SimpleListFilter):
    title = 'service type'
    parameter_name = 'inquiry_service'

    def lookups(self, request, model_admin):
        values = (
            model_admin.get_queryset(request)
            .exclude(service='')
            .values_list('service', flat=True)
            .distinct()
        )
        sorted_vals = sorted({v for v in values if v})
        return [(s, s) for s in sorted_vals]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(service=self.value())
        return queryset


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'phone', 'email', 'service', 'status', 'created_at', 'updated_at']
    list_display_links = ['name']
    list_filter   = [
        'status',
        ServiceInquiryFilter,
        ('created_at', DateFieldListFilter),
        ('updated_at', DateFieldListFilter),
    ]
    search_fields = ['name', 'phone', 'email', 'message', 'service']
    list_editable = ['status']
    readonly_fields = ['name','email','phone','service','message','ip_address','created_at','updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False


admin.site.site_header = 'Shivyan Solutions'
admin.site.site_title = 'Shivyan Admin'
admin.site.index_title = 'Dashboard'
