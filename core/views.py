from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .contact_mail import send_contact_inquiry_emails
from .company_registration_mail import (
    send_company_registration_applicant_email,
    send_company_registration_staff_email,
)
from .models import WhyChooseUs, ProcessStep, Testimonial, ContactInquiry
from .forms import ContactForm, CompanyRegistrationApplicationForm, validate_uploads
from .models import ApplicationDocument, CompanyRegistrationApplication


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


def company_registration_apply(request):
    """
    Public online application with unlimited multi-file uploads.
    """
    form = CompanyRegistrationApplicationForm()
    if request.method == 'POST':
        form = CompanyRegistrationApplicationForm(request.POST)
        # grouped uploads (unlimited per doc type)
        electricity_files = request.FILES.getlist('electricity_bill_files')
        lalpurja_files = request.FILES.getlist('lalpurja_files')
        citizenship_files = request.FILES.getlist('citizenship_files')
        photo_files = request.FILES.getlist('photo_files')
        signature_files = request.FILES.getlist('signature_files')
        other_files = request.FILES.getlist('other_files')
        other_label = (request.POST.get('other_label') or '').strip()

        try:
            validate_uploads(electricity_files)
            validate_uploads(lalpurja_files)
            validate_uploads(citizenship_files)
            validate_uploads(photo_files)
            validate_uploads(signature_files)
            validate_uploads(other_files)
        except Exception as e:  # noqa: BLE001
            form.add_error(None, str(e))

        if form.is_valid():
            app = form.save(commit=False)
            x_fwd = request.META.get('HTTP_X_FORWARDED_FOR')
            app.ip_address = x_fwd.split(',')[0] if x_fwd else request.META.get('REMOTE_ADDR')
            app.save()

            def _create_docs(files, doc_type, label=''):
                for f in files:
                    ApplicationDocument.objects.create(
                        application=app,
                        doc_type=doc_type,
                        label=label or '',
                        file=f,
                        original_name=getattr(f, 'name', '') or '',
                        content_type=(getattr(f, 'content_type', '') or '')[:120],
                        size_bytes=int(getattr(f, 'size', 0) or 0),
                    )

            _create_docs(electricity_files, ApplicationDocument.DocType.ELECTRICITY_BILL)
            _create_docs(lalpurja_files, ApplicationDocument.DocType.LALPURJA)
            _create_docs(citizenship_files, ApplicationDocument.DocType.CITIZENSHIP)
            _create_docs(photo_files, ApplicationDocument.DocType.PHOTO)
            _create_docs(signature_files, ApplicationDocument.DocType.SIGNATURE)
            _create_docs(other_files, ApplicationDocument.DocType.OTHER, other_label)

            send_company_registration_staff_email(app)
            send_company_registration_applicant_email(app)
            messages.success(
                request,
                'Your application has been submitted. Our team will contact you soon.',
            )
            return redirect('company_registration_apply')

    return render(
        request,
        'core/company_registration_apply.html',
        {'form': form},
    )
