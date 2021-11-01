from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "W.A.G.M.I. - systematic trade execution"

urlpatterns = [
    path("wagmi/", admin.site.urls),
]
