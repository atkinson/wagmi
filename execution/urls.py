from django.urls import path

from . import views

urlpatterns = [
    path("", views.ExecuteTrade.as_view(), name="execute-trade"),
]
