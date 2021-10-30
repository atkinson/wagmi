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
    pass


admin.site.register(Strategy, StrategyAdmin)


class StrategyPositionRequestAdmin(admin.ModelAdmin):
    pass


admin.site.register(StrategyPositionRequest, StrategyPositionRequestAdmin)


class TargetPositionAdmin(admin.ModelAdmin):
    pass


admin.site.register(TargetPosition, TargetPositionAdmin)


class ExchangeAdmin(admin.ModelAdmin):
    pass


admin.site.register(Exchange, ExchangeAdmin)


class SecurityAdmin(admin.ModelAdmin):
    pass


admin.site.register(Security, SecurityAdmin)
