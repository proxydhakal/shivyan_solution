from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('page/<slug:slug>/', views.page_detail, name='page_detail'),
    path('blog/', views.post_list, name='post_list'),
    path('blog/<slug:slug>/', views.post_detail, name='post_detail'),
    path(
        'newsletter/subscribe/',
        views.newsletter_subscribe,
        name='newsletter_subscribe',
    ),
    path(
        'newsletter/unsubscribe/<str:token>/',
        views.newsletter_unsubscribe,
        name='newsletter_unsubscribe',
    ),
]
