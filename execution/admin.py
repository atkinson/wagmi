from django.contrib import admin

# Register your models here.
from execution.models import (
    Order,
    Fill
)

class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "security",
        "exchange",
        "size",
        "created_at",
    ]

class FillAdmin(admin.ModelAdmin):
    list_display = [
        "market",
        "side",
        "type",
        "size",
        "status",
        "createdAt",
    ]

admin.site.register(Fill, FillAdmin)
admin.site.register(Order, OrderAdmin)
