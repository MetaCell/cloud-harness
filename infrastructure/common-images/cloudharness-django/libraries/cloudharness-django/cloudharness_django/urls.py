from django.conf import settings
from django.urls import include, path


urlpatterns = []

urlpatterns.append(path('prometheus/', include('django_prometheus.urls')))
urlpatterns.append(path('', include(settings.APP_URLCONF)))
