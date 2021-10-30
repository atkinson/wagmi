from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    #path("trade/", include("execution.urls")),
    path('wagmi/', admin.site.urls),
]
