from django.contrib import admin

from .models import Clinic, Plan, PlatformAdmin


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'currency', 'interval', 'stripe_price_id', 'is_active')


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'plan', 'subscription_status', 'trial_end', 'current_period_end')
    list_filter = ('status', 'subscription_status', 'plan')
    search_fields = ('name', 'stripe_customer_id')


@admin.register(PlatformAdmin)
class PlatformAdminAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_active', 'last_login')
    exclude = ('password',)
