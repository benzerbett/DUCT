from django.conf.urls import url
from django.conf.urls import include

from api import views


urlpatterns = [
    url(r'^$', views.welcome, name='api-root'),
    url(r'^indicators/', include('api.indicator.urls', namespace='indicators')),
    url(r'^uploads/', include('api.uploads.urls', namespace='uploads')),
    url(r'^file-source/', include('api.file_source.urls', namespace='file_source')),
    url(r'^validate/', include('api.validate.urls', namespace='validate')),
    url(r'^manual_mapper/', include('api.manual_mapper.urls', namespace='manual_mapper'))
    ]
