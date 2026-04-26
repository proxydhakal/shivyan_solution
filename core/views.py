from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .contact_mail import send_contact_inquiry_emails
from .models import WhyChooseUs, ProcessStep, Testimonial, ContactInquiry
from .forms import ContactForm


def home(request):
    why_points   = WhyChooseUs.objects.filter(is_active=True)
    steps        = ProcessStep.objects.all()
    testimonials = Testimonial.objects.filter(is_active=True)
    form         = ContactForm()

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            # Capture IP
            x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
            inquiry.ip_address = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')
            inquiry.save()
            send_contact_inquiry_emails(inquiry)

            # AJAX response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'सन्देश पठाइयो!'})

            messages.success(request, 'सन्देश पठाइयो! हाम्रो टोलीले छिटै सम्पर्क गर्नेछ।')
            return redirect('home')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'errors': form.errors.get_json_data()},
                    status=400,
                )

    context = {
        'why_points':   why_points,
        'steps':        steps,
        'testimonials': testimonials,
        'form':         form,
    }
    return render(request, 'core/home.html', context)


@require_POST
def contact_ajax(request):
    """AJAX-only contact endpoint."""
    form = ContactForm(request.POST)
    if form.is_valid():
        inquiry = form.save(commit=False)
        x_fwd = request.META.get('HTTP_X_FORWARDED_FOR')
        inquiry.ip_address = x_fwd.split(',')[0] if x_fwd else request.META.get('REMOTE_ADDR')
        inquiry.save()
        send_contact_inquiry_emails(inquiry)
        return JsonResponse({'success': True})
    return JsonResponse(
        {'success': False, 'errors': form.errors.get_json_data()}, status=400
    )
