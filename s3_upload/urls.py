"""s3_upload URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path
from core import views
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name="layout.html")),
    path('login/', views.login),
    path('logout/', views.logout),
    path('register/', views.register),
    path('upload/', login_required(views.DocumentCreateView.as_view())),

    path("videos/", views.DocumentListView.as_view()),
    
    path('draftVideos/', views.draftVideos),
    path('disApproveVideo/<int:id>/', views.disApproveVideo),
    path('approvevideo/<int:id>/', views.approveVideo),
    path("approvedVideos/",views.ApprovedDocumentListView.as_view()),
    path("unPublishedVideos/",views.UnPublishedDocumentListView.as_view()),
    path("disapprovedvideos/",views.DisApprovedDocumentListView.as_view()),
    path('unPublishVideo/<int:id>/', views.unPublishVideo),
    path("allVideos/", views.allVideos),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)