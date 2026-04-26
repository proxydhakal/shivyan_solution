import logging

from django.conf import settings
from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Avg, Count, F, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from .forms import (
    BlogCommentForm,
    BlogSearchForm,
    NewsletterSubscribeForm,
    PostRatingForm,
)
from .models import (
    SitePage,
    BlogCategory,
    BlogPost,
    BlogTag,
    BlogComment,
    NewsletterSubscriber,
    PostRating,
)
from .newsletter_mail import send_welcome_email
from .utils import get_client_ip, make_voter_key

logger = logging.getLogger(__name__)

PAGE_SIZE = 9


def _post_base_qs():
    return (
        BlogPost.objects.filter(is_published=True)
        .select_related('author', 'category')
        .annotate(
            ratings_count=Count('ratings', distinct=True),
            ratings_avg=Avg('ratings__value'),
        )
    )


def page_detail(request, slug: str):
    page = get_object_or_404(
        SitePage.objects.filter(is_published=True), slug=slug
    )
    return render(request, 'blog/page_detail.html', {'page': page})


def post_list(request):
    qs = _post_base_qs()
    q = ''
    q_error = None
    search_form = BlogSearchForm()
    if 'q' in request.GET:
        search_form = BlogSearchForm(data=request.GET)
        if search_form.is_valid():
            q = (search_form.cleaned_data.get('q') or '').strip()
        else:
            err = search_form.errors.get('q')
            q_error = err[0] if err else 'Invalid search keyword.'
            q = (request.GET.get('q') or '')[:200]
    if q and not q_error:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(excerpt__icontains=q)
            | Q(content__icontains=q)
        )
    cat_slug = (request.GET.get('category') or '').strip()
    if cat_slug:
        qs = qs.filter(category__slug=cat_slug)
    tag_slug = (request.GET.get('tag') or '').strip()
    if tag_slug:
        qs = qs.filter(tags__slug=tag_slug).distinct()
    cat = None
    if cat_slug:
        cat = BlogCategory.objects.filter(slug=cat_slug).first()
    tag = None
    if tag_slug:
        tag = BlogTag.objects.filter(slug=tag_slug).first()
    tags_for_sidebar = (
        BlogTag.objects.annotate(
            c=Count('posts', filter=Q(posts__is_published=True), distinct=True)
        )
        .filter(c__gt=0)
        .order_by('-c', 'name')[:30]
    )
    categories = BlogCategory.objects.all().order_by('order', 'name')
    paginator = Paginator(qs, PAGE_SIZE)
    pnum = request.GET.get('page') or 1
    try:
        posts = paginator.page(pnum)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    return render(
        request,
        'blog/post_list.html',
        {
            'posts': posts,
            'q': q,
            'q_error': q_error,
            'search_form': search_form,
            'active_category': cat,
            'active_tag': tag,
            'categories': categories,
            'tags_for_sidebar': tags_for_sidebar,
        },
    )


def post_detail(request, slug: str):
    post = get_object_or_404(
        BlogPost.objects.filter(is_published=True)
        .select_related('author', 'category')
        .prefetch_related('tags'),
        slug=slug,
    )
    if not (request.user.is_authenticated and request.user.is_staff):
        BlogPost.objects.filter(pk=post.pk).update(view_count=F('view_count') + 1)
        post.view_count = (post.view_count or 0) + 1

    comment_form = BlogCommentForm()
    rating_form = PostRatingForm()
    if post.allow_rating:
        voter_key = make_voter_key(request)
        has_rated = PostRating.objects.filter(
            post=post, voter_key=voter_key
        ).exists()
    else:
        has_rated = True
    if (
        request.method == 'POST'
        and post.allow_comments
        and request.POST.get('form_type') == 'comment'
    ):
        comment_form = BlogCommentForm(request.POST)
        if comment_form.is_valid():
            c = comment_form.save(commit=False)
            c.post = post
            c.ip = get_client_ip(request)
            c.save()
            messages.success(
                request,
                'Thank you. Your comment has been posted.'
                if c.is_approved
                else 'Your comment is awaiting moderation.',
            )
            return HttpResponseRedirect(f'{post.get_absolute_url()}#comments')
    if (
        request.method == 'POST'
        and post.allow_rating
        and request.POST.get('form_type') == 'rating'
    ):
        rating_form = PostRatingForm(request.POST)
        if rating_form.is_valid() and not has_rated:
            ip = get_client_ip(request)
            vkey = make_voter_key(request)
            value = rating_form.cleaned_data['value']
            PostRating.objects.update_or_create(
                post=post,
                voter_key=vkey,
                defaults={'value': value, 'ip': ip},
            )
            has_rated = True
            messages.success(request, 'Thanks for rating this article.')
            return HttpResponseRedirect(f'{post.get_absolute_url()}#rating')
    comments = post.approved_comments()
    rstats = post.rating_stats
    return render(
        request,
        'blog/post_detail.html',
        {
            'post': post,
            'comment_form': comment_form,
            'rating_form': rating_form,
            'comments': comments,
            'has_rated': has_rated,
            'rating_stats': rstats,
        },
    )


@require_POST
def newsletter_subscribe(request):
    form = NewsletterSubscribeForm(request.POST)
    nxt = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'
    if nxt and not nxt.startswith('/'):
        nxt = '/'
    if not form.is_valid():
        request.session['newsletter_form_errors'] = {
            field: str(form.errors[field][0]) for field in form.errors
        }
        request.session['newsletter_prefill'] = {
            'email': (request.POST.get('email') or '')[:254],
            'name': (request.POST.get('name') or '')[:120],
        }
        return HttpResponseRedirect(nxt)
    email = form.cleaned_data['email']
    name = (form.cleaned_data.get('name') or '').strip()
    ip = get_client_ip(request)
    ua = (request.META.get('HTTP_USER_AGENT') or '')[:500]
    sub, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={
            'name': name,
            'is_active': True,
            'ip': ip,
            'user_agent': ua,
        },
    )
    if created:
        if getattr(settings, 'NEWSLETTER_SEND_WELCOME_EMAIL', True):
            if not send_welcome_email(sub):
                logger.warning('Newsletter welcome email not delivered for %s', sub.email)
        messages.success(
            request,
            'You are subscribed! You will get an email when we publish a new blog post.',
        )
    else:
        if not sub.is_active:
            sub.is_active = True
            if name:
                sub.name = name
            sub.ip = ip
            sub.user_agent = ua
            sub.save(
                update_fields=['is_active', 'name', 'ip', 'user_agent', 'updated_at']
            )
            messages.success(
                request,
                'You are subscribed again. Welcome back!',
            )
        else:
            messages.info(
                request,
                'This email is already on the newsletter list.',
            )
    return HttpResponseRedirect(nxt)


@require_GET
def newsletter_unsubscribe(request, token: str):
    sub = get_object_or_404(NewsletterSubscriber, unsubscribe_token=token)
    if sub.is_active:
        sub.is_active = False
        sub.save(update_fields=['is_active', 'updated_at'])
        messages.success(
            request,
            'You have been unsubscribed from the blog newsletter.',
        )
    else:
        messages.info(
            request,
            'This address was already removed from the newsletter list.',
        )
    return render(request, 'blog/newsletter_unsubscribe.html', {'subscriber': sub})
