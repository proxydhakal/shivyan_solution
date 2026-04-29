import re
from typing import Iterable

from django import forms

from .models import ContactInquiry
from .text_security import validate_plain_text
from .models import CompanyRegistrationApplication

SERVICE_CHOICES = [
    ('', 'Select a service'),
    ('कम्पनी दर्ता सेवा', 'कम्पनी दर्ता सेवा'),
    ('PAN / VAT दर्ता', 'PAN / VAT दर्ता'),
    ('शेयर खरिद-बिक्री प्रक्रिया', 'शेयर खरिद-बिक्री प्रक्रिया'),
    ('लेखा सम्बन्धि सेवा', 'लेखा सम्बन्धि सेवा'),
    ('व्यवसायिक परामर्श', 'व्यवसायिक परामर्श'),
    ('शेयर लगत', 'शेयर लगत'),
    ('कर परामर्श', 'कर परामर्श'),
    ('अध्यावधिक / नियमित अपडेट', 'अध्यावधिक / नियमित अपडेट'),
]

INPUT_CLASS  = 'finput w-full px-4 py-3 rounded-xl text-sm text-slate-800 placeholder-slate-400'
SELECT_CLASS = 'finput w-full px-4 py-3 rounded-xl text-sm text-slate-800 cursor-pointer'
TEXTAREA_CLASS = 'finput w-full px-4 py-3 rounded-xl text-sm text-slate-800 placeholder-slate-400 resize-none'

class ContactForm(forms.ModelForm):
    service = forms.ChoiceField(choices=SERVICE_CHOICES, required=False,
        widget=forms.Select(attrs={'class': SELECT_CLASS}))

    class Meta:
        model = ContactInquiry
        fields = ['name', 'email', 'phone', 'service', 'message']
        widgets = {
            'name':    forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Your full name', 'autocomplete': 'name', 'maxlength': '200'}),
            'email':   forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'you@email.com', 'autocomplete': 'email', 'maxlength': '254'}),
            'phone':   forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '98XXXXXXXX', 'autocomplete': 'tel', 'maxlength': '20', 'inputmode': 'numeric'}),
            'message': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 4, 'maxlength': '4000',
                                             'placeholder': 'आफ्नो आवश्यकता लेख्नुहोस्…'}),
        }

    def clean_name(self) -> str:
        v = (self.cleaned_data.get('name') or '').strip()
        if not v:
            raise forms.ValidationError('Name is required.', code='required')
        return validate_plain_text(v, field_name='Name')

    def clean_email(self) -> str:
        v = (self.cleaned_data.get('email') or '').strip()
        if not v:
            return ''  # model allows blank
        return v

    def clean_phone(self) -> str:
        v = (self.cleaned_data.get('phone') or '').strip()
        if not v:
            raise forms.ValidationError('Phone is required.', code='required')
        validate_plain_text(v, field_name='Phone number')
        phone_re = re.compile(r'^[\d\-\s\+\(\)\\.]+$')
        if not phone_re.match(v) or len(re.sub(r'\D', '', v)) < 6:
            raise forms.ValidationError(
                'Enter a valid phone number (digits, spaces, and + ( ) - only; at least 6 digits).',
                code='invalid_phone',
            )
        if len(v) > 20:
            raise forms.ValidationError('Phone number is too long.', code='max_length')
        return v

    def clean_message(self) -> str:
        v = self.cleaned_data.get('message') or ''
        if not (v and str(v).strip()):
            return ''
        return validate_plain_text(v, field_name='Message')


ALLOWED_DOC_EXTS = {'jpg', 'jpeg', 'png', 'pdf'}
MAX_UPLOAD_BYTES = 1 * 1024 * 1024  # 1 MB


def validate_uploads(files: Iterable) -> None:
    for f in files:
        name = (getattr(f, 'name', '') or '').lower()
        if '.' not in name:
            raise forms.ValidationError('Each document must have a file extension (jpg, png, pdf).')
        ext = name.rsplit('.', 1)[-1]
        if ext not in ALLOWED_DOC_EXTS:
            raise forms.ValidationError('Only JPG, JPEG, PNG, and PDF documents are allowed.')
        size = int(getattr(f, 'size', 0) or 0)
        if size <= 0:
            raise forms.ValidationError('One of the uploaded documents is empty.')
        if size > MAX_UPLOAD_BYTES:
            raise forms.ValidationError('Each document must be smaller than 1 MB.')


class CompanyRegistrationApplicationForm(forms.ModelForm):
    class Meta:
        model = CompanyRegistrationApplication
        fields = [
            'full_name',
            'email',
            'phone',
            'desired_company_name',
            'company_type',
            'business_nature',
            'registered_address',
            'kitta_number',
            'notes',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Full name'}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'you@email.com'}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '98XXXXXXXX'}),
            'desired_company_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Proposed company name'}),
            'company_type': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'e.g. Pvt. Ltd., Partnership'}),
            'business_nature': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Nature of business'}),
            'registered_address': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Registered address'}),
            'kitta_number': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Kitta number (if applicable)'}),
            'notes': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 4, 'placeholder': 'Any extra details…'}),
        }

    def clean_full_name(self) -> str:
        v = (self.cleaned_data.get('full_name') or '').strip()
        if not v:
            raise forms.ValidationError('Full name is required.')
        return validate_plain_text(v, field_name='Full name')

    def clean_phone(self) -> str:
        v = (self.cleaned_data.get('phone') or '').strip()
        if not v:
            raise forms.ValidationError('Phone is required.')
        validate_plain_text(v, field_name='Phone')
        phone_re = re.compile(r'^[\d\-\s\+\(\)\\.]+$')
        if not phone_re.match(v) or len(re.sub(r'\D', '', v)) < 6:
            raise forms.ValidationError('Enter a valid phone number.')
        return v

    def clean_desired_company_name(self) -> str:
        v = (self.cleaned_data.get('desired_company_name') or '').strip()
        if not v:
            raise forms.ValidationError('Desired company name is required.')
        return validate_plain_text(v, field_name='Company name')

    def clean_company_type(self) -> str:
        v = (self.cleaned_data.get('company_type') or '').strip()
        return validate_plain_text(v, field_name='Company type') if v else v

    def clean_business_nature(self) -> str:
        v = (self.cleaned_data.get('business_nature') or '').strip()
        return validate_plain_text(v, field_name='Nature of business') if v else v

    def clean_registered_address(self) -> str:
        v = (self.cleaned_data.get('registered_address') or '').strip()
        return validate_plain_text(v, field_name='Registered address') if v else v

    def clean_kitta_number(self) -> str:
        v = (self.cleaned_data.get('kitta_number') or '').strip()
        return validate_plain_text(v, field_name='Kitta number') if v else v

    def clean_notes(self) -> str:
        v = (self.cleaned_data.get('notes') or '').strip()
        return validate_plain_text(v, field_name='Notes') if v else v
