"""laumproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, include

from web import views

urlpatterns = i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('web.urls', namespace='web')),
    prefix_default_language=False
)

handler400 = views.bad_request
handler403 = views.permission_denied
handler404 = views.page_not_found
handler500 = views.server_error


def switch_lang_code(path_, language):
    lang_codes = [c for (c, name) in settings.LANGUAGES]

    if path_ == '':
        raise Exception('URL path for language switch is empty')
    elif path_[0] != '/':
        raise Exception('URL path for language switch does not start with "/"')
    elif language not in lang_codes:
        raise Exception('%s is not a supported language code' % language)

    parts = path_.split('/')
    if parts[1] in lang_codes:
        parts[1] = language
    else:
        parts[0] = '/' + language
    return '/'.join(parts)
