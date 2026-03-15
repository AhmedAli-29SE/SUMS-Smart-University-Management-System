from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls', namespace='accounts')),
    path('academics/', include('academics.urls', namespace='academics')),
    path('enrollment/', include('enrollment.urls', namespace='enrollment')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
    path('results/', include('results.urls', namespace='results')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = 'accounts.views.error_403'
handler404 = 'accounts.views.error_404'
handler500 = 'accounts.views.error_500'
