from django import forms

from core.text_security import validate_plain_text, validate_search_query

from .models import BlogComment, NewsletterSubscriber


class BlogCommentForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)  # honeypot

    class Meta:
        model = BlogComment
        fields = ['name', 'email', 'body']
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm',
                    'placeholder': 'Your name',
                }
            ),
            'email': forms.EmailInput(
                attrs={
                    'class': 'w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm',
                    'placeholder': 'email@example.com',
                }
            ),
            'body': forms.Textarea(
                attrs={
                    'class': 'w-full rounded-xl border border-slate-200 px-4 py-3 text-sm',
                    'rows': 4,
                    'placeholder': 'Write your comment...',
                }
            ),
        }

    def clean_name(self) -> str:
        v = (self.cleaned_data.get('name') or '').strip()
        if not v:
            raise forms.ValidationError('Name is required.', code='required')
        return validate_plain_text(v, field_name='Name')

    def clean_body(self) -> str:
        v = (self.cleaned_data.get('body') or '').strip()
        if not v:
            raise forms.ValidationError('Please enter a comment.', code='required')
        return validate_plain_text(v, field_name='Comment')

    def clean(self):
        data = super().clean()
        if self.cleaned_data.get('website'):
            raise forms.ValidationError('Invalid submission.')
        return data


class NewsletterSubscribeForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email', 'name']
        labels = {
            'email': 'Email',
            'name': 'Name (optional)',
        }
        widgets = {
            'email': forms.EmailInput(
                attrs={
                    'class': 'w-full rounded-lg border border-white/15 bg-white/5 px-3 py-2 text-sm text-white placeholder-slate-500',
                    'placeholder': 'you@email.com',
                    'autocomplete': 'email',
                }
            ),
            'name': forms.TextInput(
                attrs={
                    'class': 'w-full rounded-lg border border-white/15 bg-white/5 px-3 py-2 text-sm text-white placeholder-slate-500',
                    'placeholder': 'Name',
                    'autocomplete': 'name',
                }
            ),
        }

    def clean_email(self) -> str:
        e = (self.cleaned_data.get('email') or '').strip().lower()
        if not e:
            raise forms.ValidationError('Enter a valid email.')
        return e

    def clean_name(self) -> str:
        v = (self.cleaned_data.get('name') or '').strip()
        if v:
            return validate_plain_text(v, field_name='Name')
        return v


class BlogSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        max_length=200,
        strip=True,
        label='',
        widget=forms.TextInput(
            attrs={
                'class': 'w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm',
                'placeholder': 'Type keywords…',
                'maxlength': '200',
            }
        ),
    )

    def clean_q(self) -> str:
        raw = self.cleaned_data.get('q') or ''
        if not raw:
            return ''
        return validate_search_query(raw)


class PostRatingForm(forms.Form):
    value = forms.TypedChoiceField(
        label='',
        choices=[(i, f'{i}') for i in range(1, 6)],
        coerce=int,
        widget=forms.Select(
            attrs={'class': 'rounded-xl border border-slate-200 px-3 py-2 text-sm min-w-[8rem]'}
        ),
    )
