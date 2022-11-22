


from django.urls import include, path
from django.contrib import admin

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('landing.urls')),
    path('note/', include('note.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('accounts.urls')),
]


# ERROR PAGES

handler500 = 'landing.views.custom_error_500'

handler404 = 'landing.views.custom_error_404'

handler403 = 'landing.views.custom_error_403'


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
                          
