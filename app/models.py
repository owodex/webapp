from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models, transaction
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth import get_user_model
from django.conf import settings
import uuid
from django.db.models.signals import pre_save
from django.dispatch import receiver

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    username = models.CharField(max_length=150, unique=True)
    referral_code = models.CharField(max_length=10, unique=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def generate_referral_code(self):
        return uuid.uuid4().hex[:8].upper()

    def __str__(self):
        return self.email

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username}'s Wallet - {self.balance} Naira"

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )

    SERVICE_TYPES = (
        ('giftcard', 'Giftcard Purchase'),
        ('bill_payment', 'Bill Payment'),
        ('money_transfer', 'Money Transfer'),
        ('signup_bonus', 'Signup Bonus'),
        ('airtime', 'Airtime Purchase'),
        ('data', 'Data Purchase'),
        ('cable', 'Cable TV'),
        ('electricity', 'Electricity Bill'),
        ('bank transfer', 'Bank Transfer')
    )

    STATUS_TYPES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    service = models.CharField(max_length=50, choices=SERVICE_TYPES)
    invoice_id = models.CharField(max_length=20, unique=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions', null=True)
    status = models.CharField(max_length=20, choices=STATUS_TYPES, default='pending')

    def __str__(self):
        return f"{self.invoice_id} - {self.service} - ₦{self.amount} - {self.status}"

    class Meta:
        ordering = ['-date']

    def update_wallet_on_completion(self):
        if self.status == 'completed' and self.service == 'giftcard':
            wallet, created = Wallet.objects.get_or_create(user=self.user)
            wallet.balance += self.amount
            wallet.save()

@receiver(pre_save, sender=Transaction)
def transaction_pre_save(sender, instance, **kwargs):
    if instance.id:  # Check if this is an existing instance
        old_instance = Transaction.objects.get(id=instance.id)
        if old_instance.status != 'completed' and instance.status == 'completed':
            instance.update_wallet_on_completion()

class AirtimeRequest(models.Model):
    NETWORK_CHOICES = (
        ('mtn', 'MTN'),
        ('airtel', 'Airtel'),
        ('glo', 'Glo'),
        ('9mobile', '9mobile'),
    )

    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='airtime_request')
    phone = PhoneNumberField()
    network = models.CharField(max_length=10, choices=NETWORK_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def __str__(self):
        return f"Airtime Request for {self.phone} ({self.network})"

    def save(self, *args, **kwargs):
        if not self.amount:
            self.amount = self.transaction.amount
        super().save(*args, **kwargs)

class DataRequest(models.Model):
    NETWORK_CHOICES = (
        ('mtn', 'MTN'),
        ('airtel', 'Airtel'),
        ('glo', 'Glo'),
        ('9mobile', '9mobile'),
    )

    DATA_PLAN_CHOICES = (
        ('1gb', '1GB'),
        ('2gb', '2GB'),
        ('5gb', '5GB'),
        ('10gb', '10GB'),
    )

    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='data_request')
    phone = PhoneNumberField()
    network = models.CharField(max_length=10, choices=NETWORK_CHOICES)
    data_plan = models.CharField(max_length=10, choices=DATA_PLAN_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Data Request for {self.phone} ({self.network}) - {self.data_plan}"

    def save(self, *args, **kwargs):
        if not self.amount:
            self.amount = self.transaction.amount
        super().save(*args, **kwargs)

class CableRequest(models.Model):
    PROVIDER_CHOICES = [
        ('dstv', 'DSTV'),
        ('gotv', 'GOtv'),
        ('startimes', 'StarTimes'),
    ]

    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='cable_request')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    smart_card_number = models.CharField(max_length=20)
    package = models.CharField(max_length=50)
    account_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.provider} - {self.smart_card_number}"
    
class ElectricityRequest(models.Model):
    OPERATOR_CHOICES = [
        ('ekedc', 'EKEDC'),
        ('ikedc', 'IKEDC'),
        ('aedc', 'AEDC'),
    ]
    PLAN_CHOICES = [
        ('prepaid', 'Prepaid'),
        ('postpaid', 'Postpaid'),
    ]
    operator = models.CharField(max_length=10, choices=OPERATOR_CHOICES)
    meter_number = models.CharField(max_length=50)
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES)
    account_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    token = models.CharField(max_length=50, null=True, blank=True)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name= 'electricity_request', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.operator} - {self.meter_number} - {self.amount}"
    
class GiftCardTransaction(models.Model):
    CURRENCY_CHOICES = [
        ('us', '🇺🇸 United States'),
        ('gb', '🇬🇧 United Kingdom'),
        ('ca', '🇨🇦 Canada'),
    ]
    TYPE_CHOICES = [
        ('ecode', 'E-code'),
        ('physical', 'Physical'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    transaction = models.OneToOneField('Transaction', on_delete=models.CASCADE, related_name='giftcard_transaction')
    giftcard_name = models.CharField(max_length=100)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True)
    currency = models.CharField(max_length=2, choices=CURRENCY_CHOICES)
    card_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    denomination = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.giftcard_name} - {self.amount} ({self.status})"

class GiftCardImage(models.Model):
    transaction = models.ForeignKey(GiftCardTransaction, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='giftcard_images/')

    def __str__(self):
        return f"Image for {self.transaction}"
    
class Notification(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_for_all_users = models.BooleanField(default=False)
    users = models.ManyToManyField(CustomUser, related_name='notifications', blank=True)

    def __str__(self):
        return self.title or f"Notification {self.id}"

    class Meta:
        ordering = ['-created_at']

class Beneficiary(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.bank_name}"

    class Meta:
        verbose_name_plural = "Beneficiaries"