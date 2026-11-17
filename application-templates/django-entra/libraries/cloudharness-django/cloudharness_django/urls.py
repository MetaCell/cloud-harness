from django.conf import settings
from django.urls import include, path

from cloudharness_django import views


urlpatterns = []

urlpatterns.append(path('prometheus/', include('django_prometheus.urls')))
urlpatterns.append(path('oidc/login/', views.login, name='oidc_login'))
urlpatterns.append(path('oidc/callback/', views.callback, name='oidc_callback'))
urlpatterns.append(path('oidc/logout/', views.logout, name='oidc_logout'))
urlpatterns.append(path('', include(settings.APP_URLCONF)))
