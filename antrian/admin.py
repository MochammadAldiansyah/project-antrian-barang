from django.contrib import admin
from .models import ServiceType, Counter, Officer, QueueTicket, DummyResi


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ['name', 'number', 'is_active']
    list_filter = ['is_active']


@admin.register(Officer)
class OfficerAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'counter']
    list_filter = ['counter']
    search_fields = ['user__first_name', 'user__last_name', 'employee_id']


@admin.register(QueueTicket)
class QueueTicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'tracking_code', 'customer_name', 'service_type', 'status', 'counter', 'created_at']
    list_filter = ['status', 'service_type', 'counter', 'created_at']
    search_fields = ['ticket_number', 'tracking_code', 'customer_name', 'customer_phone']
    readonly_fields = ['ticket_number', 'tracking_code', 'created_at', 'called_at', 'served_at', 'completed_at']
    date_hierarchy = 'created_at'
