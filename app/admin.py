from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Transaction, GiftCardImage, GiftCardTransaction, Notification, CableRequest, ElectricityRequest, Wallet, AirtimeRequest, DataRequest
from django.urls import path
from .views import send_notification


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_filter = ['is_staff', 'is_active']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'full_name', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'full_name', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'username', 'full_name')
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_for_all_users', 'get_users_count')
    list_filter = ('is_for_all_users', 'created_at')
    search_fields = ('title', 'message')
    filter_horizontal = ('users',)

    def get_users_count(self, obj):
        return obj.users.count() if not obj.is_for_all_users else 'All Users'
    get_users_count.short_description = 'Recipients'

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_for_all_users:
            return self.readonly_fields + ('users',)
        return self.readonly_fields

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('send-notification/', self.admin_site.admin_view(send_notification), name='send_notification'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_send_notification'] = True
        return super().changelist_view(request, extra_context=extra_context)

admin.site.add_action(send_notification, 'Send Notification')

class AirtimeRequestInline(admin.StackedInline):
    model = AirtimeRequest
    can_delete = False
    verbose_name_plural = 'Airtime Request'
    fields = ('phone_number', 'network', 'amount')
    readonly_fields = ('phone_number', 'network', 'amount')

class DataRequestInline(admin.StackedInline):
    model = DataRequest
    can_delete = False
    verbose_name_plural = 'Data Request'
    fields = ('phone_number', 'network', 'data_plan', 'amount')
    readonly_fields = ('phone_number', 'network', 'data_plan', 'amount')

class ElectricityRequestInline(admin.StackedInline):
    model = ElectricityRequest
    can_delete = False
    verbose_name_plural = 'Electricity Request'
    readonly_fields = ('operator', 'meter_number', 'plan', 'account_name', 'amount')

class CableRequestInline(admin.StackedInline):
    model = CableRequest
    can_delete = False
    verbose_name_plural = 'Cable Request'
    fields = ('provider', 'smart_card_number', 'package', 'account_name', 'amount')
    readonly_fields = ('provider', 'smart_card_number', 'package', 'account_name', 'amount')


class GiftCardTransactionInline(admin.StackedInline):
    model = GiftCardTransaction
    can_delete = False
    verbose_name_plural = 'Gift Card Transaction'
    fields = ('giftcard_name', 'currency', 'card_type', 'denomination', 'amount')
    readonly_fields = ('giftcard_name', 'currency', 'card_type', 'denomination', 'amount')

class GiftCardImageInline(admin.TabularInline):
    model = GiftCardImage
    extra = 1

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('invoice_id', 'user', 'service', 'amount', 'status', 'date', 'get_phone_number', 'get_request_details')
    list_filter = ('status', 'service', 'transaction_type')
    search_fields = ('invoice_id', 'user__email', 'user__username')
    actions = ['mark_as_completed', 'mark_as_cancelled']
    inlines = [AirtimeRequestInline, DataRequestInline, ElectricityRequestInline, CableRequestInline, GiftCardTransactionInline]

    def get_phone_number(self, obj):
        if obj.service in ['airtime', 'data']:
            request = getattr(obj, f'{obj.service}_request', None)
            if request:
                return str(request.phone_number)
        return '-'
    get_phone_number.short_description = 'Phone Number'

    def get_request_details(self, obj):
        if obj.service == 'airtime':
            request = obj.airtime_request
            if request:
                return f"₦{request.amount}"
        elif obj.service == 'data':
            request = obj.data_request
            if request:
                return f"{request.data_plan} - ₦{request.amount}"
        elif obj.service == 'electricity':
            request = obj.electricity_request
            if request:
                return f"{request.operator} - {request.plan} - ₦{request.amount}"
        return '-'
    get_request_details.short_description = 'Request Details'

    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_as_completed.short_description = "Mark selected transactions as completed"

    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        for transaction in queryset:
            wallet = transaction.wallet
            wallet.balance += transaction.amount
            wallet.save()
    mark_as_cancelled.short_description = "Mark selected transactions as cancelled and refund"

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return [inline(self.model, self.admin_site) for inline in self.inlines]

admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Wallet)
admin.site.register(AirtimeRequest)
admin.site.register(DataRequest)
admin.site.register(ElectricityRequest)
admin.site.register(CableRequest)
admin.site.register(GiftCardTransaction)