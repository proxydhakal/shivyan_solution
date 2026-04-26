import re

from django import forms

from .models import ContactInquiry
from .text_security import validate_plain_text

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
