from django.db import models


class SiteSettings(models.Model):
    company_name = models.CharField(max_length=200, default="Shivyan Solutions Pvt. Ltd.")
    company_name_nepali = models.CharField(max_length=200, default="शिव्यान सोलुसन्स प्रा.लि.")
    # Shown under the company name in header/footer when no logo, or next to mark on small screens
    company_name_suffix = models.CharField(
        max_length=120,
        default="Pvt. Ltd.",
        blank=True,
        help_text='Short line under the name (e.g. "Pvt. Ltd.") when using text brand.',
    )
    site_title = models.CharField(
        max_length=200,
        blank=True,
        help_text='Default browser tab title. Leave empty to use company name.',
    )
    tagline = models.CharField(max_length=300, default="कौशलम् कार्यसिद्धिनम्")
    tagline_en = models.CharField(max_length=300, default="Nepal's Trusted Tax & Business Consultancy")
    logo = models.ImageField(
        upload_to="site/branding/%Y/%m",
        blank=True,
        null=True,
        help_text="Replaces the text+icon mark in the header and footer when set.",
    )
    favicon = models.FileField(
        upload_to="site/branding/%Y/%m",
        blank=True,
        null=True,
        help_text="Favicon: .ico or .png (32×32 or larger; browsers will scale).",
    )
    apple_touch_icon = models.ImageField(
        upload_to="site/branding/%Y/%m",
        blank=True,
        null=True,
        help_text="Optional 180×180 PNG for iOS “Add to Home Screen”.",
    )
    meta_keywords = models.TextField(
        blank=True,
        help_text="Comma-separated keywords for search engines (optional).",
    )
    og_image = models.ImageField(
        upload_to="site/branding/%Y/%m",
        blank=True,
        null=True,
        help_text="Image for link previews (Open Graph / social). If empty, your logo is used when available.",
    )
    hero_headline = models.CharField(max_length=400, default="Simplifying Tax & Business Compliance")
    hero_subtext = models.TextField(default="Expert guidance in taxation, audit, and business advisory.")
    hero_cta_label = models.CharField(max_length=100, default="आजै सम्पर्क गर्नुहोस्")
    phone = models.CharField(max_length=20, default="9744651716")
    email = models.EmailField(default="Shivyansolutions259@gmail.com")
    address = models.TextField(default="Kathmandu, Nepal")
    office_hours = models.CharField(max_length=200, default="Sunday-Friday: 9:00am - 6:00pm")
    about_text_nepali = models.TextField(default="हामी शिव्यान सोलुसन्स प्रा.लि.मा विशेषज्ञहरूको टोली हौं।")
    about_text_en = models.TextField(default="Our team of certified consultants brings decades of expertise.")
    clients_count = models.PositiveIntegerField(default=500)
    experience_years = models.PositiveIntegerField(default=15)
    retention_percent = models.PositiveIntegerField(default=98)
    services_count = models.PositiveIntegerField(default=9)
    facebook_url = models.URLField(blank=True, verbose_name="Facebook URL")
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn URL")
    instagram_url = models.URLField(blank=True, verbose_name="Instagram URL")
    twitter_url = models.URLField(blank=True, verbose_name="X (Twitter) URL")
    youtube_url = models.URLField(blank=True, verbose_name="YouTube URL")
    meta_description = models.TextField(blank=True, default="Shivyan Solutions - Tax, Audit & Business Advisory Nepal")

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def get_browser_title(self) -> str:
        return (self.site_title or "").strip() or self.company_name

    def has_social_links(self) -> bool:
        return any(
            [
                self.facebook_url,
                self.linkedin_url,
                self.instagram_url,
                self.twitter_url,
                self.youtube_url,
            ]
        )


class ServiceCategory(models.Model):
    COLOR_CHOICES = [('emerald','Emerald Green'),('gold','Gold'),('blue','Navy Blue')]
    name  = models.CharField(max_length=100)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='emerald')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name_plural = "Service Categories"

    def __str__(self):
        return self.name


class Service(models.Model):
    category        = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True)
    title_nepali    = models.CharField(max_length=200)
    title_en        = models.CharField(max_length=200)
    description     = models.TextField()
    icon_svg        = models.TextField(help_text="SVG path(s) e.g. <path d='...'/>", blank=True)
    tags            = models.CharField(max_length=300, help_text="Comma-separated: PAN,VAT,IRD")
    is_featured     = models.BooleanField(default=False)
    is_cta_card     = models.BooleanField(default=False)
    order           = models.PositiveIntegerField(default=0)
    is_active       = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title_en

    def get_tags_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def color(self):
        return self.category.color if self.category else 'emerald'


class WhyChooseUs(models.Model):
    COLOR_CHOICES = [('emerald','Green'),('gold','Gold'),('blue','Blue')]
    title       = models.CharField(max_length=200)
    description = models.TextField()
    icon_svg    = models.TextField(blank=True)
    color       = models.CharField(max_length=20, choices=COLOR_CHOICES, default='emerald')
    order       = models.PositiveIntegerField(default=0)
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name_plural = "Why Choose Us Points"

    def __str__(self):
        return self.title


class ProcessStep(models.Model):
    COLOR_CHOICES = [('blue','Navy Blue'),('gold','Gold'),('green','Green')]
    step_number = models.PositiveIntegerField(unique=True)
    title       = models.CharField(max_length=100)
    description = models.TextField()
    icon_svg    = models.TextField(blank=True)
    color       = models.CharField(max_length=20, choices=COLOR_CHOICES, default='blue')

    class Meta:
        ordering = ['step_number']

    def __str__(self):
        return f"Step {self.step_number}: {self.title}"


class Testimonial(models.Model):
    client_name = models.CharField(max_length=200)
    client_role = models.CharField(max_length=300)
    quote       = models.TextField()
    rating      = models.PositiveSmallIntegerField(default=5)
    is_active   = models.BooleanField(default=True)
    order       = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.client_name} — {self.client_role}"

    def star_range(self):
        return range(self.rating)


class ContactInquiry(models.Model):
    STATUS_CHOICES = [('new','New'),('in_progress','In Progress'),('resolved','Resolved')]
    name       = models.CharField(max_length=200)
    email      = models.EmailField(blank=True)
    phone      = models.CharField(max_length=20)
    service    = models.CharField(max_length=200, blank=True)
    message    = models.TextField(blank=True)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Contact Inquiries"

    def __str__(self):
        return f"{self.name} - {self.phone}"
