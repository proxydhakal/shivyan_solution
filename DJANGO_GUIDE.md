# Shivyan Solutions — Django Full-Stack Web App
## Complete Developer Guide

---

## PROJECT STRUCTURE

```
shivyan_project/
├── manage.py
├── requirements.txt
├── db.sqlite3                        ← auto-generated
├── .env                              ← create this (see below)
│
├── shivyan/                          ← Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── core/                             ← Main app
│   ├── models.py                     ← All database models
│   ├── views.py                      ← Page & AJAX views
│   ├── forms.py                      ← Contact form
│   ├── admin.py                      ← Admin panel config
│   ├── context_processors.py         ← Global site settings
│   ├── migrations/
│   └── fixtures/
│       └── initial_data.json         ← Seed data
│
├── templates/
│   └── core/
│       └── home.html                 ← Full Django template
│
└── static/                           ← CSS/JS/images
```

---

## QUICK START (5 Commands)

```bash
# 1. Clone / unzip project, then:
cd shivyan_project

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up database + seed data
python manage.py migrate
python manage.py loaddata core/fixtures/initial_data.json

# 5. Create admin user + run server
python manage.py createsuperuser
python manage.py runserver
```

Visit: http://127.0.0.1:8000/
Admin: http://127.0.0.1:8000/admin/

---

## ENVIRONMENT VARIABLES (.env file)

Create `.env` in the project root:

```env
SECRET_KEY=your-very-secret-key-change-this
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email (for contact form notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Shivyan Solutions <your@gmail.com>
CONTACT_EMAIL=Shivyansolutions259@gmail.com
```

---

## DATABASE MODELS

### 1. SiteSettings (Singleton)
Controls all editable site content from admin.

| Field | Type | Purpose |
|---|---|---|
| company_name | CharField | Navbar & footer name |
| tagline | CharField | Nepali tagline in hero badge |
| hero_headline | CharField | Hero section H1 |
| hero_subtext | TextField | Hero subtitle paragraph |
| hero_cta_label | CharField | CTA button text |
| phone | CharField | Clickable phone everywhere |
| email | EmailField | Contact email |
| address | TextField | Office address |
| office_hours | CharField | Footer hours |
| about_text_nepali | TextField | About section Nepali para |
| about_text_en | TextField | About section English para |
| clients_count | IntegerField | Animated stat counter |
| experience_years | IntegerField | Animated stat counter |
| retention_percent | IntegerField | Stat + progress bar % |
| services_count | IntegerField | Animated stat counter |
| facebook_url | URLField | Footer social link |
| linkedin_url | URLField | Footer social link |
| instagram_url | URLField | Footer social link |
| meta_description | TextField | SEO meta tag |

### 2. ServiceCategory
Groups services by color theme (emerald / gold / blue).

### 3. Service
Each service card on the site.

| Field | Purpose |
|---|---|
| title_nepali | Nepali heading (Devanagari font) |
| title_en | English subtitle |
| description | Card body text |
| icon_svg | SVG path(s) — paste from heroicons.com |
| tags | Comma-separated tag pills |
| category | Links to color theme |
| is_cta_card | If True, renders as dark blue CTA card |
| is_active | Toggle visibility |
| order | Display order (drag in admin) |

### 4. WhyChooseUs
Feature grid points in "Why Choose Us" section.

### 5. ProcessStep
The 4-step process workflow. step_number controls order.

### 6. Testimonial
Client reviews for the auto-carousel.

### 7. ContactInquiry
Every form submission saved here.
- Status: New → In Progress → Resolved
- Tracks IP address
- Read-only in admin (prevents editing client data)

---

## HOW TEMPLATE TAGS WORK

The template uses Django template tags throughout:

```django
{# Site-wide settings (from context processor) #}
{{ site.company_name }}
{{ site.phone }}
{{ site.email }}

{# Loop over services from DB #}
{% for service in services %}
  {{ service.title_nepali }}
  {{ service.title_en }}
  {{ service.description }}
  {{ service.icon_svg|safe }}        ← |safe renders raw SVG HTML
  {{ service.color }}                ← 'emerald' | 'gold' | 'blue'
  {% for tag in service.get_tags_list %}
    {{ tag }}
  {% endfor %}
  {% if service.is_cta_card %}
    ...dark card layout...
  {% else %}
    ...regular card layout...
  {% endif %}
{% empty %}
  No services found.
{% endfor %}

{# Testimonials passed to Alpine.js as JSON #}
items: [
  {% for t in testimonials %}
  { name: '{{ t.client_name|escapejs }}', q: '{{ t.quote|escapejs }}' }
  {% endfor %}
]

{# Contact form rendered by Django #}
{{ form.name }}        ← renders <input> with CSS classes
{{ form.email }}
{{ form.service }}     ← renders <select>
{{ form.message }}     ← renders <textarea>

{# CSRF token for AJAX #}
{% csrf_token %}
'X-CSRFToken': '{{ csrf_token }}'

{# URL reversals #}
{% url 'home' %}
{% url 'contact_ajax' %}

{# Auto copyright year #}
{% now "Y" %}
```

---

## ADMIN PANEL FEATURES

Go to http://127.0.0.1:8000/admin/ → login with superuser credentials.

**Site Settings** — Edit everything from one screen:
- Company name, phone, email, address
- Hero headline, subtext, CTA button label
- About section text (Nepali + English)
- All stat counters
- Social media URLs

**Services** — Add/edit/delete service cards:
- Reorder by changing the `order` field
- Toggle `is_active` to show/hide
- Set `is_cta_card=True` for the dark blue CTA card
- SVG icons: copy path(s) from https://heroicons.com

**Why Choose Us** — Add feature points with icon + color

**Process Steps** — Edit the 4-step workflow

**Testimonials** — Add client reviews, toggle active/inactive

**Contact Inquiries** — View all form submissions:
- Filter by status (New / In Progress / Resolved)
- Change status via list view dropdown
- Search by name, phone, email
- Cannot add/delete (read-only protection)

---

## CONTACT FORM — HOW IT WORKS

The form uses AJAX (fetch API) so the page never reloads:

1. User fills form → clicks submit
2. Alpine.js intercepts click, sets `sending=true` (shows spinner)
3. `fetch()` POSTs to `/contact/submit/` with CSRF token
4. Django view validates, saves to `ContactInquiry` model
5. Returns `{"success": true}` JSON
6. Alpine sets `sent=true` → success screen animates in

**To add email notifications**, edit `core/views.py`:

```python
from django.core.mail import send_mail
from django.conf import settings

# After inquiry.save():
send_mail(
    subject=f'New Inquiry from {inquiry.name}',
    message=f'Name: {inquiry.name}\nPhone: {inquiry.phone}\nService: {inquiry.service}\n\n{inquiry.message}',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[settings.CONTACT_EMAIL],
    fail_silently=True,
)
```

---

## ADDING A NEW SERVICE (Step-by-Step)

1. Go to Admin → Services → Add Service
2. Set **title_nepali** (e.g., "अडिट रिपोर्टिङ")
3. Set **title_en** (e.g., "Audit Reporting")
4. Write **description** paragraph
5. Go to https://heroicons.com → find icon → click "Copy SVG"
6. Paste only the `<path .../>` part into **icon_svg**
7. Set **tags**: "Statutory,Internal,Tax Audit"
8. Choose **category** (sets color theme)
9. Set **order** number
10. Check **is_active**
11. Save → Refresh site ✓

---

## COLORS EXPLAINED

| Category Color | Icon BG | Tag Color | Border Bar |
|---|---|---|---|
| `emerald` | green-50 | emerald text | green gradient |
| `gold` | yellow-50 | amber text | gold gradient |
| `blue` | blue-50 | blue text | navy gradient |

The template maps color strings to CSS classes automatically:
```django
class="svc-icon-{{ service.color }}"    → svc-icon-emerald / svc-icon-gold / svc-icon-blue
class="tag-{{ service.color }}"         → tag-emerald / tag-gold / tag-blue
stroke="{{ service.color }}"            → mapped in template to hex value
```

---

## DEPLOYMENT (Production Checklist)

```bash
# 1. Set environment variables
DEBUG=False
SECRET_KEY=<strong-random-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# 2. Collect static files
python manage.py collectstatic --noinput

# 3. Switch to PostgreSQL (recommended)
# In settings.py, replace DATABASES with:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'shivyan_db',
        'USER': 'db_user',
        'PASSWORD': 'db_password',
        'HOST': 'localhost',
    }
}

# 4. Install gunicorn
pip install gunicorn
gunicorn shivyan.wsgi:application --bind 0.0.0.0:8000

# 5. Nginx config (reverse proxy to gunicorn)
# Point yourdomain.com → localhost:8000
```

**Recommended hosting**: Railway.app, Render.com, or DigitalOcean App Platform (all support Django natively).

---

## FREQUENTLY ASKED

**Q: How do I change the Nepali tagline?**
Admin → Site Settings → `tagline` field

**Q: How do I update the phone number everywhere?**
Admin → Site Settings → `phone` field (updates navbar, hero, footer, CTA, contact)

**Q: How do I add more services?**
Admin → Services → Add Service (see step-by-step above)

**Q: How do I view contact form submissions?**
Admin → Contact Inquiries → filter by "New" status

**Q: How do I hide a service temporarily?**
Admin → Services → uncheck `is_active` → Save

**Q: How do I change the animated counter numbers?**
Admin → Site Settings → `clients_count`, `experience_years`, `retention_percent`

---

## DEFAULT ADMIN CREDENTIALS

```
URL:      http://127.0.0.1:8000/admin/
Username: admin
Password: admin123
```
⚠️ Change immediately in production!

---

*Built with Django 4.2 · Tailwind CSS CDN · Alpine.js 3.x*
