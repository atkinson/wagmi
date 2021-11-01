from django.contrib import admin

# Register your models here.

from sizing.models import (
    Strategy,
    StrategyPositionRequest,
    TargetPosition,
    Exchange,
    Security,
)


class StrategyAdmin(admin.ModelAdmin):
    list_display = ["name", "exchange", "max_position_size_usd", "command"]


admin.site.register(Strategy, StrategyAdmin)


class StrategyPositionRequestAdmin(admin.ModelAdmin):
    list_display = [
        "strategy",
        "exchange",
        "security",
        "weight",
        "arrival_price_usd",
    ]


admin.site.register(StrategyPositionRequest, StrategyPositionRequestAdmin)


class TargetPositionAdmin(admin.ModelAdmin):
    list_display = [
        "exchange",
        "security",
        "size",
    ]


admin.site.register(TargetPosition, TargetPositionAdmin)


class ExchangeAdmin(admin.ModelAdmin):
    list_display = ["name"]


admin.site.register(Exchange, ExchangeAdmin)


class SecurityAdmin(admin.ModelAdmin):
    list_display = ["name"]


admin.site.register(Security, SecurityAdmin)
