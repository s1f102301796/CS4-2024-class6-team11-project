from django.urls import path
from .views import SignUpView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', SignUpView.as_view(template_name='account/login.html'), name='login'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
