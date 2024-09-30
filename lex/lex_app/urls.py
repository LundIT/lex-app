"""
lex_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/

Examples
--------
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
from django.urls import path, include, re_path
from . import settings
from .ProcessAdminSettings import processAdminSite, adminSite
import os
from react.views import serve_react

url_prefix = os.getenv("DJANGO_BASE_PATH") if os.getenv("DJANGO_BASE_PATH") is not None else ""

print(settings.REACT_APP_BUILD_PATH)
urlpatterns = [
    path(url_prefix + 'admin/', adminSite.urls),
    path(url_prefix, processAdminSite.urls),
    path(url_prefix, include('generic_app.urls')),
    re_path(r"^(?P<path>.*)$", serve_react, {"document_root": settings.REACT_APP_BUILD_PATH}),
]
