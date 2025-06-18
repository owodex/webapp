from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from django.urls import path
from .views import send_notification
from django.db import models
from django.db import transaction as db_transaction
from django.contrib import messages
from django.utils.html import format_html

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_filter = ['is_staff', 'is_active']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
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

@admin.register(DepositRequest)
class DepositRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'status', 'created_at')
    actions = ['approve_deposit', 'reject_deposit']

    def approve_deposit(self, request, queryset):
        for deposit in queryset.filter(status='pending'):
            wallet, _ = Wallet.objects.get_or_create(user=deposit.user)
            wallet.balance += deposit.amount
            wallet.save()
            deposit.status = 'approved'
            deposit.save()
            # Update transaction status to completed
            invoice_id = f'DEP{deposit.id}{int(deposit.created_at.timestamp())}'
            transaction = Transaction.objects.filter(
                user=deposit.user,
                amount=deposit.amount,
                service='deposit',
                invoice_id=invoice_id
            ).first()
            if transaction:
                transaction.status = 'completed'
                transaction.save()
            else:
                # Fallback: create if not found
                Transaction.objects.create(
                    user=deposit.user,
                    wallet=wallet,
                    amount=deposit.amount,
                    service='deposit',
                    status='completed',
                    transaction_type='credit',
                    invoice_id=invoice_id
                )
        self.message_user(request, "Selected deposits approved, wallet credited, and transactions updated.")

    def reject_deposit(self, request, queryset):
        for deposit in queryset.filter(status='pending'):
            deposit.status = 'rejected'
            deposit.save()
            # Update transaction status to cancelled
            invoice_id = f'DEP{deposit.id}{int(deposit.created_at.timestamp())}'
            transaction = Transaction.objects.filter(
                user=deposit.user,
                amount=deposit.amount,
                service='deposit',
                invoice_id=invoice_id
            ).first()
            if transaction:
                transaction.status = 'cancelled'
                transaction.save()
            else:
                # Fallback: create if not found
                Transaction.objects.create(
                    user=deposit.user,
                    amount=deposit.amount,
                    service='deposit',
                    status='cancelled',
                    transaction_type='credit',
                    invoice_id=invoice_id
                )
        self.message_user(request, "Selected deposits rejected and transactions updated.")

class AirtimeRequestInline(admin.StackedInline):
    model = AirtimeRequest
    can_delete = False
    verbose_name_plural = 'Airtime Request'
    fields = ('phone', 'network', 'amount')
    readonly_fields = ('phone', 'network', 'amount')

class DataRequestInline(admin.StackedInline):
    model = DataRequest
    can_delete = False
    verbose_name_plural = 'Data Request'
    fields = ('phone', 'network', 'data_plan', 'amount')
    readonly_fields = ('phone', 'network', 'data_plan', 'amount')

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
    fields = ('giftcard_name', 'currency', 'card_type', 'denomination', 'amount', 'status')
    readonly_fields = ('giftcard_name', 'currency', 'card_type', 'denomination', 'amount', 'status')

@admin.register(GiftCardTransaction)
class GiftCardTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'giftcard_name', 'user', 'currency', 'card_type', 'denomination', 'amount', 'status', 'show_submitted_images'
    )
    readonly_fields = ('show_submitted_images','created_at', 'updated_at')
    fields = (
        'giftcard_name', 'user', 'currency', 'card_type', 'denomination', 'amount', 'status',
        'show_submitted_images'
    )

    def show_submitted_images(self, obj):
        images = obj.images.all()
        if not images:
            return "No images submitted."
        return format_html(''.join(
            f'<img src="{img.image.url}" style="max-width:100px;max-height:100px;margin:2px;" />'
            for img in images
        ))
    show_submitted_images.short_description = "Submitted Images"

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('invoice_id', 'user', 'service', 'amount', 'status', 'date', 'get_phone', 'get_request_details')
    list_filter = ('status', 'service', 'transaction_type')
    search_fields = ('invoice_id', 'user__email', 'user__username')
    actions = ['mark_as_completed', 'mark_as_cancelled']
    inlines = [AirtimeRequestInline, DataRequestInline, ElectricityRequestInline, CableRequestInline, GiftCardTransactionInline]

    def get_phone(self, obj):
        if obj.service in ['airtime', 'data']:
            request = getattr(obj, f'{obj.service}_request', None)
            if request:
                return str(request.phone)
        return '-'
    get_phone.short_description = 'Phone Number'

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj and obj.service == 'buy_giftcard':
            if 'email' not in fields:
                fields = list(fields) + ['email']
        else:
            fields = [f for f in fields if f != 'email']
        return fields

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
        elif obj.service == 'giftcard':
            giftcard = obj.giftcard_transaction
            if giftcard:
                return f"{giftcard.giftcard_name} - {giftcard.currency} - {giftcard.amount}"
        elif obj.service == 'deposit':
            deposit = obj.deposit_request
            if deposit:
                return f"₦{deposit.amount}"
        return '-'
    get_request_details.short_description = 'Request Details'

    @db_transaction.atomic
    def mark_as_completed(self, request, queryset):
        completed_count = 0
        for trans in queryset:
            if trans.status != 'completed':
                trans.status = 'completed'
                trans.save()
                completed_count += 1

                if trans.service == 'giftcard':
                    giftcard_trans = trans.giftcard_transaction
                    if giftcard_trans:
                        giftcard_trans.status = 'completed'
                        giftcard_trans.save()

                        # Update wallet balance for gift card transactions
                        wallet, created = Wallet.objects.get_or_create(user=trans.user)
                        wallet.balance += trans.amount
                        wallet.save()

                elif trans.service == 'deposit':
                    deposit_request = trans.deposit_request
                    if deposit_request:
                        deposit_request.status = 'approved'
                        deposit_request.save()

                        # Update wallet balance for deposit transactions
                        wallet, created = Wallet.objects.get_or_create(user=trans.user)
                        wallet.balance += trans.amount
                        wallet.save()

            # Send notification
            notify_user_transaction_status(trans.user, trans, 'completed')

        if completed_count:
            messages.success(request, f"{completed_count} transaction(s) marked as completed.")
        else:
            messages.info(request, "No transactions were updated.")

    mark_as_completed.short_description = "Mark selected transactions as completed"

    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        for transaction in queryset:
            wallet = transaction.wallet
            wallet.balance += transaction.amount
            wallet.save()
            notify_user_transaction_status(transaction.user, transaction, 'cancelled')
    mark_as_cancelled.short_description = "Mark selected transactions as cancelled and refund"

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return [inline(self.model, self.admin_site) for inline in self.inlines]
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            service_display=models.Case(
                models.When(service='bank transfer', then=models.Value('Bank Transfer')),
                default=models.F('service'),
                output_field=models.CharField(),
            )
        )
        return queryset

    def service(self, obj):
        return obj.service_display
    service.admin_order_field = 'service_display'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # --- Deposit wallet credit logic ---
        is_newly_completed = False
        if change:
            old_obj = Transaction.objects.get(pk=obj.pk)
            if old_obj.status != 'completed' and obj.status == 'completed':
                is_newly_completed = True
        elif obj.status == 'completed':
            is_newly_completed = True

        if (
            is_newly_completed and
            obj.service == 'deposit' and
            obj.transaction_type == 'credit'
        ):
            wallet = obj.wallet or Wallet.objects.get_or_create(user=obj.user)[0]
            wallet.balance += obj.amount
            wallet.save()
            obj.wallet = wallet
            obj.save(update_fields=['wallet'])
            
            # Update associated GiftCardTransaction if it exists
            if obj.service == 'giftcard':
                try:
                    giftcard_trans = GiftCardTransaction.objects.get(transaction=obj)
                    if giftcard_trans.status != obj.status:
                        giftcard_trans.status = obj.status
                        giftcard_trans.save()
                        messages.info(request, f"Gift Card Transaction status updated to {obj.status}.")
                except GiftCardTransaction.DoesNotExist:
                    pass  # No associated GiftCardTransaction

@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'account_number', 'bank_name')
    search_fields = ('user__username', 'user__email', 'name', 'account_number', 'bank_name')

class GiftCardCurrencyInline(admin.TabularInline):
    model = GiftCardCurrency
    extra = 1

class GiftCardTypeInline(admin.TabularInline):
    model = GiftCardType
    extra = 1

class GiftCardDenominationInline(admin.TabularInline):
    model = GiftCardDenomination
    extra = 1

@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    inlines = [GiftCardCurrencyInline, GiftCardTypeInline, GiftCardDenominationInline]

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

from django.contrib import admin
from .models import Category, Tag, Post

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at', 'status')
    list_filter = ('status', 'created_at', 'category')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    ordering = ('status', '-created_at')
    filter_horizontal = ('tags',)

    fieldsets = (
        ('Main Content', {
            'fields': (
                'title', 'slug', 'author', 'category', 'tags',
                'image', 'status', 'content'
            )
        }),
        ('SEO Information', {
            'classes': ('collapse',),
            'fields': (
                'meta_title', 'meta_description', 'meta_keywords'
            )
        }),
    )


# Optionally, you can also register these models individually
admin.site.register(GiftCardCurrency)
admin.site.register(GiftCardType)
admin.site.register(GiftCardDenomination)
admin.site.register(GiftCardRate)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Wallet)
admin.site.register(AirtimeRequest)
admin.site.register(DataRequest)
admin.site.register(ElectricityRequest)
admin.site.register(CableRequest)
