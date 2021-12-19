from django.contrib import admin

# Register your models here.
from execution.models import (
    Order,
    Fill,
)


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "security",
        "exchange",
        "size",
        "created_at",
        "status",
        "id",
    ]

    readonly_fields = tuple([order.name for order in Order._meta.get_fields()])


class FillAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "market",
        "side",
        "type",
        "size",
        "liquidity",
        "recorded_at",
    ]
    readonly_fields = tuple([fill.name for fill in Fill._meta.get_fields()])


admin.site.register(Fill, FillAdmin)
admin.site.register(Order, OrderAdmin)
