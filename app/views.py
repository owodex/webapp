from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import make_password, check_password
from .models import CustomUser, Transaction, Notification, GiftCard, GiftCardRate, GiftCardCurrency, GiftCardType, GiftCardDenomination, GiftCardImage, GiftCardTransaction, ElectricityRequest, CableRequest, AirtimeRequest, DataRequest, Wallet, Beneficiary
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse, reverse_lazy
from django.core.paginator import Paginator
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db import transaction
from decimal import Decimal, InvalidOperation
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.contrib.auth.forms import PasswordResetForm
import uuid
import json
import logging
import requests
from django.views.decorators.http import require_GET
from django.conf import settings
from django.db.models import Q, Sum
from django.http import HttpResponseBadRequest
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from .vtpass_api import VTPassAPI, VTPassCableAPI
from django.db import IntegrityError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Post, Category, Tag

def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your email has been verified. You can now log in.')
        return redirect('login')
    else:
        messages.error(request, 'The verification link is invalid or has expired.')
        return redirect('signup')


class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset/password_reset_form.html'
    email_template_name = 'password_reset/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    form_class = PasswordResetForm

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        # Check if a user exists with this email
        if not CustomUser.objects.filter(email=email).exists():
            form.add_error('email', ValidationError("No account found with this email address."))
            return self.form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'password_reset/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'password_reset/password_reset_complete.html'

@login_required
def user_settings(request):
    if request.method == 'POST':
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, 'Your password was successfully updated!')
                return redirect('settings')
            else:
                messages.error(request, 'Please correct the error below.')
        else:
            # Existing profile update code
            user = request.user
            user.first_name = request.POST.get('full_name').split()[0]
            user.last_name = ' '.join(request.POST.get('full_name').split()[1:])
            user.email = request.POST.get('email')
            user.phone_number = request.POST.get('phone_number')
            
            if 'profile_image' in request.FILES:
                user.profile_image = request.FILES['profile_image']
            
            user.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('settings')
    else:
        password_form = PasswordChangeForm(request.user)
    
    return render(request, 'dashboard/settings.html', {'password_form': password_form})

@login_required
@require_POST
def delete_account(request):
    password = request.POST.get('password')
    user = request.user

    # Use the email as the username for authentication
    if authenticate(username=user.email, password=password):
        try:
            # Perform any additional cleanup if needed (e.g., deleting related data)
            user.delete()
            logout(request)
            return JsonResponse({
                'success': True, 
                'message': 'Your account has been successfully deleted.',
                'redirect_url': reverse('home')
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred while deleting your account: {str(e)}'})
    else:
        return JsonResponse({'success': False, 'message': 'Incorrect password. Please try again.'})

def signup(request):
    if request.method == 'POST':
        full_name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        referral_code = request.POST.get('referral_code')

        # Phone number validation
        phone_regex = RegexValidator(
            regex=r'^\+?1?\d{10,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )
        try:
            phone_regex(phone_number)
        except ValidationError:
            return render(request, 'signup.html', {'error': 'Invalid phone number format. Please enter a valid phone number.'})

        if password == confirm_password:
            with transaction.atomic():
                # Check if referral code is valid
                referrer = None
                if referral_code:
                    try:
                        referrer = CustomUser.objects.get(referral_code=referral_code)
                    except CustomUser.DoesNotExist:
                        pass

                user = CustomUser.objects.create(
                    username=username,
                    email=email,
                    password=make_password(password),
                    first_name=full_name.split()[0],
                    last_name=' '.join(full_name.split()[1:]),
                    phone_number=phone_number,
                    referred_by=referrer,
                    bonus_amount=2000,  # Sign up bonus
                    is_active=False  # Set user as inactive until email is verified
                )

                # Create the signup bonus transaction
                Transaction.objects.create(
                    user=user,
                    service='Signup Bonus',
                    invoice_id=f'SB{user.id}{int(timezone.now().timestamp())}',
                    amount=2000,
                    transaction_type='credit',
                    date=timezone.now(),
                    status='completed'
                )

                # If user was referred, add referral bonus to referrer
                if referrer:
                    referral_bonus = 500
                    referrer.bonus_amount += referral_bonus
                    referrer.save()

                    Transaction.objects.create(
                        user=referrer,
                        service='Referral Bonus',
                        invoice_id=f'RB{referrer.id}{int(timezone.now().timestamp())}',
                        amount=referral_bonus,
                        transaction_type='credit',
                        date=timezone.now(),
                        status='completed'
                    )

                # Generate email verification token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                verification_link = request.build_absolute_uri(f'/verify-email/{uid}/{token}/')

                # Send verification email using send_mail
                subject = 'Verify your email address'
                html_message = render_to_string('verification_email.html', {
                    'user': user,
                    'verification_link': verification_link,
                })
                plain_message = strip_tags(html_message)
                from_email = 'support@owodex.com'
                to_email = user.email

                send_mail(
                    subject,
                    plain_message,
                    from_email,
                    [to_email],
                    html_message=html_message
                )

                return render(request, 'signup_success.html', {'email': user.email})
        else:
            return render(request, 'signup.html', {'error': 'Passwords do not match'})
    return render(request, 'signup.html')



def index(request):
    latest_posts = Post.objects.order_by('-created_at')[:3]
    context = {
        'latest_posts': latest_posts,
    }
    return render(request, 'index.html', context)

def products(request):
    return render(request, 'service.html')

def support(request):
    return render(request, 'contact.html')

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email and password:
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard') 
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please provide both email and password.')
        
        # For debugging: print the POST data
        print("POST data:", request.POST)
    
    return render(request, 'login.html')

def rate_calculator(request):
    giftcards = GiftCard.objects.filter(is_active=True)
    return render(request, "rate_calculator.html")

def terms(request):
    return render(request, "terms.html")

def privacy_policy(request):
    return render(request, "privacy_policy.html")

from .models import Wallet  

@login_required
def dashboard(request):
    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:5]

    wallet, created = Wallet.objects.get_or_create(user=request.user)

    context = {
        'recent_transactions': recent_transactions,
        'wallet_balance': wallet.balance,
    }

    return render(request, 'dashboard/index.html', context)


def services(request):
    return render(request, "dashboard/services.html")

@login_required
def transactions(request):
    transactions_list = Transaction.objects.filter(user=request.user)
    paginator = Paginator(transactions_list, 20) 

    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    return render(request, 'dashboard/transaction.html', {'transactions': transactions})

def profile(request):
    return render(request, "dashboard/profile.html")

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')


@login_required
def airtime_data(request):
    return render(request, 'dashboard/airtime-data.html')

@login_required
def pay_bills(request):
    return render(request, 'dashboard/pay-bills.html')

@login_required
def bonus(request):
    user = request.user
    
    signup_bonus = Transaction.objects.filter(user=user, service='Signup Bonus').first()
    
    referral_bonuses = Transaction.objects.filter(user=user, service='Referral Bonus').order_by('-date')
    
    total_bonus = user.bonus_amount

    total_referral_bonus = referral_bonuses.aggregate(Sum('amount'))['amount__sum'] or 0

    total_giftcard_transactions = GiftCardTransaction.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    user_eligible = total_giftcard_transactions >= 100000

    context = {
        'total_bonus': total_bonus,
        'signup_bonus': signup_bonus,
        'referral_bonuses': referral_bonuses,
        'total_referral_bonus': total_referral_bonus,
        'user_eligible': user_eligible,
    }
    
    return render(request, 'dashboard/bonus.html', context)

logger = logging.getLogger(__name__)

@require_POST
def withdraw_bonus(request):
    user = request.user
    total_bonus = user.bonus_amount
    
    if total_bonus <= 0:
        return JsonResponse({'success': False, 'error': 'No bonus available for withdrawal.'})

    total_giftcard_transactions = GiftCardTransaction.objects.filter(user=user, status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    
    
    logger.info(f"User {user.id} - Total giftcard transactions: {total_giftcard_transactions}")
    
    if total_giftcard_transactions < 100000:
        error_message = (f"You need to complete a giftcard transaction of at least ₦100,000 to withdraw bonus. "
                         f"Your current total: ₦{total_giftcard_transactions}")
        logger.warning(f"User {user.id} - Withdrawal attempt failed: {error_message}")
        return JsonResponse({'success': False, 'error': error_message})

    with transaction.atomic():
        wallet, created = Wallet.objects.get_or_create(user=user)
        wallet.balance += total_bonus
        wallet.save()

        user.bonus_amount = 0
        user.save()


        Transaction.objects.create(
            user=user,
            service='Bonus Withdrawal',
            invoice_id=f'BW{user.id}{int(timezone.now().timestamp())}',
            amount=total_bonus,
            transaction_type='credit',
            date=timezone.now(),
            status='completed'
        )

    logger.info(f"User {user.id} - Successfully withdrew ₦{total_bonus} bonus")
    return JsonResponse({'success': True, 'message': f'Successfully withdrew ₦{total_bonus} bonus to your wallet.'})

@login_required
def send_notification(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        is_for_all_users = request.POST.get('is_for_all_users') == 'on'
        user_ids = request.POST.getlist('users')

        notification = Notification.objects.create(
            title=title,
            message=message,
            is_for_all_users=is_for_all_users
        )

        if is_for_all_users:
            # If it's for all users, add all users to the notification
            all_users = CustomUser.objects.all()
            notification.users.add(*all_users)
        else:
            # If it's not for all users, add only selected users
            users = CustomUser.objects.filter(id__in=user_ids)
            notification.users.add(*users)

        messages.success(request, 'Notification sent successfully.')
    else:
        messages.error(request, 'Invalid request method.')

    return redirect('admin:app_notification_changelist')

@login_required
@require_POST
@csrf_protect
def owodex_tag_transfer(request):
    amount = request.POST.get('amount')
    tag = request.POST.get('tag')

    if not amount or not tag:
        return JsonResponse({'status': 'error', 'message': 'Amount and tag are required'}, status=400)

    try:
        amount = Decimal(amount)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid amount'}, status=400)

    sender_wallet, _ = Wallet.objects.get_or_create(user=request.user)
    
    if sender_wallet.balance < amount:
        return JsonResponse({'status': 'error', 'message': 'Insufficient balance'}, status=400)

    try:
        recipient = CustomUser.objects.get(username=tag)
    except CustomUser.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Recipient not found'}, status=404)

    recipient_wallet, _ = Wallet.objects.get_or_create(user=recipient)

    with transaction.atomic():
        sender_wallet.balance -= amount
        sender_wallet.save()
        recipient_wallet.balance += amount
        recipient_wallet.save()

        Transaction.objects.create(
            user=request.user,
            wallet=sender_wallet,
            amount=amount,
            transaction_type='debit',
            service='money transfer',
            status='completed',
            invoice_id=f'OT{Transaction.objects.count() + 1:06d}',
        )
        Transaction.objects.create(
            user=recipient,
            wallet=recipient_wallet,
            amount=amount,
            transaction_type='credit',
            service='money_transfer',
            status='completed',
            invoice_id=f'OT{Transaction.objects.count() + 1:06d}',
        )

    return JsonResponse({'status': 'success', 'message': 'Transfer successful'})

@login_required
@require_POST
@csrf_protect
@transaction.atomic
def bank_transfer(request):
    data = json.loads(request.body)
    amount = Decimal(data.get('amount'))
    account_number = data.get('account_number')
    bank_name = data.get('bank_name')
    save_beneficiary = data.get('save_beneficiary')

    wallet = Wallet.objects.get(user=request.user)

     # Generate a unique invoice ID
    invoice_id = str(uuid.uuid4().hex)[:20]

    if wallet.balance < amount:
        return JsonResponse({
            'status': 'error',
            'message': 'Insufficient balance'
        }, status=400)

    try:
        # Deduct amount from wallet
        wallet.balance -= amount
        wallet.save()

        # Create transaction record
        Transaction.objects.create(
            user=request.user,
            service='bank transfer',
            amount=amount,
            transaction_type='debit',
            status='pending',
            invoice_id =  invoice_id,
            account_number=account_number,
            bank_name=bank_name,
        )

        # Save beneficiary if requested
        if save_beneficiary:
            Beneficiary.objects.create(
                user=request.user,
                name=f"{account_number} - {bank_name}",
                account_number=account_number,
                bank_name=bank_name
            )

        return JsonResponse({
            'status': 'success',
            'message': 'Bank transfer completed successfully'
        })
    except Exception as e:
        # If an error occurs, rollback the transaction
        transaction.set_rollback(True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
def get_beneficiaries(request):
    beneficiaries = Beneficiary.objects.filter(user=request.user).values('id', 'name', 'account_number', 'bank_name')
    return JsonResponse(list(beneficiaries), safe=False)

# @login_required
# @transaction.atomic
# def submit_airtime_request(request):
#     if request.method == 'POST':
#         phone = request.POST.get('phone')
#         network = request.POST.get('network')
#         amount = request.POST.get('amount')

#         try:
#             amount = Decimal(amount)
#         except InvalidOperation:
#             return JsonResponse({
#                 'status': 'error',
#                 'message': 'Invalid amount'
#             }, status=400)

#         # Get or create user's wallet
#         wallet, _ = Wallet.objects.get_or_create(user=request.user)

#         # Check if user has sufficient balance
#         if wallet.balance < amount:
#             return JsonResponse({
#                 'status': 'error',
#                 'message': 'Insufficient balance'
#             }, status=400)

#         # Generate a unique invoice ID
#         invoice_id = str(uuid.uuid4().hex)[:20]

#         # Initialize VTPass API
#         vtpass_api = VTPassAPI()

#         # Make API call to VTPass
#         response = vtpass_api.buy_airtime(phone, amount, network)

#         if response.get('code') == '000':
#             # Successful transaction
#             with transaction.atomic():
#                 # Deduct amount from wallet
#                 wallet.balance -= amount
#                 wallet.save()

#                 # Create a new transaction
#                 new_transaction = Transaction.objects.create(
#                     user=request.user,
#                     service='airtime',
#                     invoice_id=invoice_id,
#                     amount=amount,
#                     transaction_type='debit',
#                     status='success'
#                 )

#                 # Create a new airtime request
#                 AirtimeRequest.objects.create(
#                     transaction=new_transaction,
#                     phone_number=phone,
#                     network=network
#                 )

#             return JsonResponse({
#                 'status': 'success',
#                 'message': 'Airtime purchase successful',
#                 'transaction_id': new_transaction.invoice_id
#             })
#         else:
#             # Failed transaction
#             return JsonResponse({
#                 'status': 'error',
#                 'message': 'Airtime purchase failed: ' + response.get('response_description', 'Unknown error')
#             }, status=400)

#     return JsonResponse({
#         'status': 'error',
#         'message': 'Invalid request method'
#     }, status=400)

@login_required
def submit_airtime_request(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        network = request.POST.get('network')
        amount = request.POST.get('amount')

        try:
            amount = Decimal(amount)
        except InvalidOperation:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid amount'
            }, status=400)

        # Get or create user's wallet
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        # Check if user has sufficient balance
        if wallet.balance < amount:
            return JsonResponse({
                'status': 'error',
                'message': 'Insufficient balance'
            }, status=400)

        # Deduct amount from wallet
        wallet.balance -= amount
        wallet.save()

        # Generate a unique invoice ID
        while True:
            invoice_id = f'AIR{uuid.uuid4().hex[:16].upper()}'
            if not Transaction.objects.filter(invoice_id=invoice_id).exists():
                break


        # Make API call to VTPass
        vtpass_api = VTPassAPI()
        api_response = vtpass_api.buy_airtime(phone, str(amount), network)

        try:
            # Create a new transaction
            new_transaction = Transaction.objects.create(
                user=request.user,
                service='airtime',
                amount=amount,
                transaction_type='debit',
                status='pending',
                invoice_id=api_response.get('requestId')
            )
        except IntegrityError:
            # If there's still an IntegrityError, refund the user and return error response
            wallet.balance += amount
            wallet.save()
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to create transaction. Please try again.'
            }, status=500)

        if api_response.get('code') == '000':
            # Successful transaction
            new_transaction.status = 'completed'  # Change this from 'success' to 'completed'
            new_transaction.save()

            # Create a new airtime request
            AirtimeRequest.objects.create(
                transaction=new_transaction,
                phone=phone,
                network=network
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Airtime request submitted successfully',
                'transaction_id': new_transaction.invoice_id,
                'api_response': api_response
            })
        else:
            # Failed transaction
            new_transaction.status = 'failed'
            new_transaction.save()

            # Refund the user
            wallet.balance += amount
            wallet.save()

            return JsonResponse({
                'status': 'error',
                'message': 'Airtime purchase failed: ' + api_response.get('response_description', 'Unknown error'),
                'api_response': api_response
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)

@login_required
@require_POST
@transaction.atomic
def submit_data_request(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        network = request.POST.get('network')
        data_plan = request.POST.get('data_plan')

        logger.debug(f"Received request: phone={phone}, network={network}, data_plan={data_plan}")


        # Initialize VTPass API
        vtpass_api = VTPassAPI()

        # Get variation details
        variations_response = vtpass_api.get_data_variation_codes(network)
        variations = variations_response.get('content', {}).get('variations', [])
        
        logger.debug(f"Received variations from VTPass API: {variations}")

        # Find the exact matching variation
        selected_variation = next((v for v in variations if v['variation_code'] == data_plan), None)

        variation_code = selected_variation['variation_code']
        amount = Decimal(selected_variation['variation_amount'])

        # Get or create user's wallet
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        # Check if user has sufficient balance
        if wallet.balance < amount:
            return JsonResponse({
                'status': 'error',
                'message': 'Insufficient balance'
            }, status=400)

        # Generate a unique invoice ID
        invoice_id = str(uuid.uuid4().hex)[:20]

        # Make API call to VTPass
        api_response = vtpass_api.buy_data(phone, network, variation_code)

        if api_response.get('code') == '000':
            # Successful transaction
            with transaction.atomic():
                # Deduct amount from wallet
                wallet.balance -= amount
                wallet.save()

                # Create a new transaction
                new_transaction = Transaction.objects.create(
                    user=request.user,
                    service='data',
                    invoice_id=api_response.get('requestId'),
                    amount=amount,
                    transaction_type='debit',
                    status='completed'
                )

                # Create a new data request
                DataRequest.objects.create(
                    transaction=new_transaction,
                    phone=phone,
                    network=network,
                    data_plan=selected_variation['name'],
                    amount=amount,
                )

            return JsonResponse({
                'status': 'success',
                'message': 'Data request submitted successfully',
                'transaction_id': new_transaction.invoice_id,
                'api_response': api_response
            })
        else:
            # Failed transaction
            return JsonResponse({
                'status': 'error',
                'api_response': api_response
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)
    
from django.core.serializers.json import DjangoJSONEncoder
from phonenumber_field.phonenumber import PhoneNumber

class PhoneNumberEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, PhoneNumber):
            return str(obj)
        return super().default(obj)

@login_required
@require_POST
@csrf_protect
def submit_cable_request(request):
    provider = request.POST.get('provider')
    smart_card_number = request.POST.get('smart_card_number')
    package = request.POST.get('package')
    account_name = request.POST.get('account_name')
    amount = request.POST.get('amount')
    subscription_type = request.POST.get('subscription_type', 'change')  # Default to 'change' if not provided

    # Generate a unique invoice ID
    invoice_id = str(uuid.uuid4().hex)[:20]

    if not all([provider, smart_card_number, package, account_name, amount]):
        return JsonResponse({'status': 'error', 'message': 'All fields are required'}, status=400)

    try:
        amount = Decimal(amount)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid amount'}, status=400)

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if wallet.balance < amount:
        return JsonResponse({'status': 'error', 'message': 'Insufficient balance'}, status=400)

    vtpass_api = VTPassCableAPI()

    try:
        # Prepare the payload for VTPass API
        if subscription_type == 'renew':
            response = vtpass_api.renew_bouquet(
                request_id=invoice_id,
                service_id=f"{provider}",
                billers_code=smart_card_number,
                amount=str(amount),
                phone=str(request.user.phone_number)
            )
        else:
            response = vtpass_api.purchase_product(
                request_id=invoice_id,
                service_id=f"{provider}",
                billers_code=smart_card_number,
                variation_code=package,
                amount=str(amount),
                phone=str(request.user.phone_number),
                subscription_type='change'
            )

        logger.debug(f"VTPass API Response: {response}")

        if isinstance(response, str):
            raise ValueError(f'Cable subscription failed: {response}')

        if response.get('code') == '000':
            with transaction.atomic():
                wallet.balance -= amount
                wallet.save()

                new_transaction = Transaction.objects.create(
                    user=request.user,
                    wallet=wallet,
                    amount=amount,
                    transaction_type='debit',
                    service='cable',
                    invoice_id=response.get('requestId'),
                    status='completed'
                )

                if new_transaction:
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Cable subscription successful',
                        'transaction_id': new_transaction.invoice_id 
                    })

                CableRequest.objects.create(
                    transaction=new_transaction,
                    provider=provider,
                    smart_card_number=smart_card_number,
                    package=package,
                    account_name=account_name,
                    amount=amount
                )

            return JsonResponse({'status': 'success', 'message': 'Cable subscription successful'})
        else:
            raise ValueError(f'Cable subscription failed: {response.get("response_description")}')

    except Exception as e:
        logger.error(f"Cable subscription error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
@csrf_protect
def submit_electricity_request(request):
    if request.method == 'POST':
        meter_number = request.POST.get('meter_number')
        account_name = request.POST.get('account_name')
        operator = request.POST.get('operator')
        plan = request.POST.get('plan')
        amount = request.POST.get('amount')
        phone = request.user.phone_number

        invoice_id = str(uuid.uuid4().hex)[:20]

        if not all([meter_number, operator, plan, account_name, amount]):
            return JsonResponse({'status': 'error', 'message': 'All fields are required'}, status=400)

        try:
            amount = Decimal(amount)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid amount'}, status=400)

        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        if wallet.balance < amount:
            return JsonResponse({'status': 'error', 'message': 'Insufficient balance'}, status=400)

        vtpass_api = VTPassAPI()
        response = vtpass_api.buy_electricity(meter_number, operator, plan, amount, str(phone))

        if response.get('code') == '000':
            with transaction.atomic():
                wallet.balance -= amount
                wallet.save()

            new_transaction = Transaction.objects.create(
                user=request.user,
                wallet=wallet,
                amount=amount,
                transaction_type='debit',
                service='electricity',
                invoice_id=response.get('requestId'),
                status='completed'
            )

            ElectricityRequest.objects.create(
                transaction=new_transaction,
                meter_number=meter_number,
                plan=plan,
                operator=operator,
                account_name=account_name,
                amount=amount,
                token=response.get('purchased_code', '')
            )

            return JsonResponse({
                    'status': 'success',
                    'message': 'Electricity purchase successful',
                    'transaction_id': new_transaction.invoice_id,
                    'token': response.get('purchased_code', '')
                })
        else:
            return JsonResponse({'status': 'error', 'message': response.get('response_description', 'Transaction failed')}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def giftcards(request):
    giftcards = GiftCard.objects.filter(is_active=True)
    context = {
        'giftcards': giftcards,
    }
    return render(request, 'dashboard/giftcards.html', context)

@login_required
def trade_giftcard(request, giftcard_id):
    giftcard = get_object_or_404(GiftCard, id=giftcard_id)
    currencies = GiftCardCurrency.objects.filter(giftcard=giftcard)
    types = GiftCardType.objects.filter(giftcard=giftcard)
    denominations = GiftCardDenomination.objects.filter(giftcard=giftcard)

    context = {
        'giftcard': giftcard,
        'currencies': currencies,
        'types': types,
        'denominations': denominations,
    }
        
    if request.method == 'POST':
        giftcard_name = request.POST.get('giftcard_name')
        currency = request.POST.get('giftCardCurrency')
        card_type = request.POST.get('giftCardType')
        denomination = request.POST.get('denomination')
        amount = request.POST.get('amount')
        images = request.FILES.getlist('giftCardImages')

        try:
            amount = Decimal(amount)
        except InvalidOperation:
            return render(request, 'dashboard/trade_giftcards.html', {
                'error_message': 'Invalid amount provided. Please enter a valid number.',
                'form_data': request.POST
            })

        invoice_id = str(uuid.uuid4().hex)[:20]

        transaction = Transaction.objects.create(
            user=request.user,
            amount=amount,
            service='giftcard',
            status='pending',
            transaction_type='credit',
            invoice_id=invoice_id
        )

        giftcard_transaction = GiftCardTransaction.objects.create(
            user=request.user,
            transaction=transaction,
            giftcard_name=giftcard_name,
            currency=currency,
            card_type=card_type,
            denomination=denomination,
            amount=amount
        )

        for image in images:
            GiftCardImage.objects.create(
                transaction=giftcard_transaction,
                image=image
            )
        messages.success(request, 'Gift card trade request submitted successfully!')
        return redirect('giftcards')

    return render(request, 'dashboard/trade_giftcards.html', context)

def search(request):
    query = request.GET.get('q', '').lower()
    if query:
        # Define a dictionary mapping search terms to their corresponding URLs
        service_urls = {
            'airtime': reverse('airtime_data'),
            'data': reverse('airtime_data'),
            'cable': reverse('pay_bills'), 
            'tv': reverse('pay_bills'),    
            'electricity': reverse('pay_bills'),  
            'giftcard': reverse('giftcards'),
            'gift card': reverse('giftcards'),
            'transfer': reverse('bank_transfer'),
            'withdraw': reverse('bank_transfer'),
            'transaction': reverse('transactions'),
            'transactions': reverse('transactions'),
            'bonus': reverse('bonus'),
            'reward': reverse('bonus'),
        }

        for key, url in service_urls.items():
            if key in query:
                return redirect(url)

        return render(request, 'dashboard/services.html', {'query': query})

    return redirect('dashboard')

@require_GET
def vtpass_service_variations(request):
    service_id = request.GET.get('serviceID')
    if not service_id:
        return JsonResponse({'error': 'serviceID is required'}, status=400)

    api_url = f"{settings.VTPASS_API_URL}/service-variations"
    headers = {
        'api-key': settings.VTPASS_API_KEY,
        'secret-key': settings.VTPASS_SECRET_KEY,
    }
    params = {'serviceID': service_id}

    try:
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        return JsonResponse(response.json())
    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def get_cable_variations(request, provider):
    url = f"https://vtpass.com/api/service-variations?serviceID={provider}"
    auth = (settings.VTPASS_EMAIL, settings.VTPASS_PASSWORD)
    
    response = requests.get(url, auth=auth)
    
    if response.status_code == 200:
        return JsonResponse(response.json())
    else:
        return JsonResponse({'error': 'Failed to fetch variation codes'}, status=400)


logger = logging.getLogger(__name__)

@require_POST
@csrf_exempt
def validate_smart_card(request):
    data = json.loads(request.body)
    provider = data.get('provider')
    card_number = data.get('smart_card_number')

    logger.debug(f"Validating smart card: provider={provider}, card_number={card_number}")

    if not provider or not card_number:
        return JsonResponse({'status': 'error', 'message': 'Provider and smart card number are required'}, status=400)

    vtpass_api = VTPassAPI()
    validation_result = vtpass_api.verify_smartcard(card_number, f"{provider}")

    logger.debug(f"VTPass API response: {validation_result}")

    if validation_result.get('code') == '000':
        return JsonResponse({
            'status': 'success',
            'customer_name': validation_result['content'].get('Customer_Name'),
            'current_bouquet': validation_result['content'].get('Current_Bouquet_Code'),
            'renewal_amount': validation_result['content'].get('Renewal_Amount')
        })
    else:
        error_message = validation_result.get('response_description')
        logger.error(f"Smart card validation failed: {error_message}")
        return JsonResponse({'status': 'error', 'message': error_message}, status=400)
    
@require_POST
@csrf_exempt
def verify_meter(request):
    operator = request.POST.get('operator')
    meter_number = request.POST.get('meter_number')
    meter_type = request.POST.get('meter_type')

    if not all([operator, meter_number, meter_type]):
        return JsonResponse({'error': 'All fields are required'}, status=400)

    vtpass_api = VTPassAPI()
    response = vtpass_api.verify_meter(operator, meter_number, meter_type)

    logger.debug(f"VTPass API Response: {response}")

    if response.get('code') == '000':
        content = response.get('content', {})
        return JsonResponse({
            'account_name': content.get('Customer_Name') or content.get('customerName') or 'N/A',
            'address': content.get('Address') or content.get('customerAddress') or 'N/A',
            'meter_number': content.get('Meter_Number') or content.get('meterNumber') or meter_number,
            'customer_details': content  
        })
    else:
        error_message = response.get('response_description') or 'Verification failed'
        logger.error(f"Meter verification failed: {error_message}")
        return JsonResponse({
            'error': error_message,
            'details': response  
        }, status=400)

@login_required
def get_notification_count(request):
    count = Notification.objects.filter(users=request.user, is_read=False).count()
    return JsonResponse({'count': count})

@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(users=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

@require_GET
def get_rate(request):
    giftcard_name = request.GET.get('giftcard')
    currency_code = request.GET.get('currency')
    card_type = request.GET.get('type')
    denomination_value = request.GET.get('denomination')

    try:
        giftcard = GiftCard.objects.get(name=giftcard_name)

        currency = GiftCardCurrency.objects.get(giftcard=giftcard, currency=currency_code)
        card_type = GiftCardType.objects.get(giftcard=giftcard, type=card_type)
        denomination = GiftCardDenomination.objects.get(giftcard=giftcard, value=denomination_value)

        rate = GiftCardRate.objects.get(
            giftcard=giftcard,
            currency=currency,
            card_type=card_type,
            denomination=denomination
        )

        return JsonResponse({
            'rate': rate.rate,
            'giftcard': giftcard.name,
            'currency': currency.currency_name,
            'type': card_type.type,
            'denomination': denomination.value
        })
    except (GiftCard.DoesNotExist, GiftCardCurrency.DoesNotExist, 
            GiftCardType.DoesNotExist, GiftCardDenomination.DoesNotExist, 
            GiftCardRate.DoesNotExist) as e:
        return JsonResponse({'error': str(e)}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def get_gift_cards(request):
    """Fetches all available gift cards."""
    gift_cards = GiftCard.objects.values('id', 'name')  
    return JsonResponse(list(gift_cards), safe=False)

def get_currencies(request):
    giftcard_id = request.GET.get('giftcard_id')
    currencies = GiftCardCurrency.objects.filter(giftcard_id=giftcard_id).values('id', 'currency_name')
    return JsonResponse(list(currencies), safe=False)

def get_card_types(request):
    giftcard_id = request.GET.get('giftcard_id')
    card_types = GiftCardType.objects.filter(giftcard_id=giftcard_id).values('id', 'type')
    return JsonResponse(list(card_types), safe=False)

def get_denominations(request):
    giftcard_id = request.GET.get('giftcard_id')
    denominations = GiftCardDenomination.objects.filter(giftcard_id=giftcard_id).values('id', 'value')
    return JsonResponse(list(denominations), safe=False)      

@require_GET
def get_g_rate(request):
    giftcard_name = request.GET.get('giftcard')
    currency_name = request.GET.get('currency') 
    card_type_name = request.GET.get('type')
    denomination_value = request.GET.get('denomination')
    amount = request.GET.get('amount', 1) 

    if not all([giftcard_name, currency_name, card_type_name, denomination_value]):
        return JsonResponse({'error': 'Missing required parameters'}, status=400)

    try:
        amount = float(amount)

        giftcard = GiftCard.objects.get(name=giftcard_name)
        
        # Lookup by currency_name instead of currency
        currency = GiftCardCurrency.objects.get(giftcard=giftcard, currency_name__iexact=currency_name)
        card_type = GiftCardType.objects.get(giftcard=giftcard, type=card_type_name)
        denomination = GiftCardDenomination.objects.get(giftcard=giftcard, value=denomination_value)
        rate_obj = GiftCardRate.objects.get(
            giftcard=giftcard, currency=currency, card_type=card_type, denomination=denomination
        )

        rate = float(rate_obj.rate)
        total_value = round(rate * amount, 2)

        return JsonResponse({
            'rate': rate,
            'total_value': total_value,
            'giftcard': giftcard.name,
            'currency': currency.currency_name, 
            'type': card_type.type,
            'denomination': denomination.value
        })

    except GiftCard.DoesNotExist:
        return JsonResponse({'error': f'GiftCard "{giftcard_name}" not found'}, status=404)

    except GiftCardCurrency.DoesNotExist:
        return JsonResponse({'error': f'Currency "{currency_name}" not found for gift card "{giftcard_name}"'}, status=404)

    except GiftCardType.DoesNotExist:
        return JsonResponse({'error': f'Card type "{card_type_name}" not found for gift card "{giftcard_name}"'}, status=404)

    except GiftCardDenomination.DoesNotExist:
        return JsonResponse({'error': f'Denomination "{denomination_value}" not found for gift card "{giftcard_name}"'}, status=404)

    except GiftCardRate.DoesNotExist:
        return JsonResponse({'error': 'Rate not found for the given parameters'}, status=404)

    except ValueError:
        return JsonResponse({'error': 'Invalid denomination or amount value'}, status=400)

    except Exception as e:
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)


def blog_list(request):
    posts = Post.objects.all().order_by('-created_at')
    paginator = Paginator(posts, 9) 
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    
    context = {
        'posts': posts,
        'categories': Category.objects.all(),
        'tags': Tag.objects.all(),
    }
    return render(request, 'blog_list.html', context)

def blog_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    related_posts = Post.objects.filter(category=post.category).exclude(id=post.id)[:2]
    recent_posts = Post.objects.exclude(id=post.id).order_by('-created_at')[:3]
    
    context = {
        'post': post,
        'related_posts': related_posts,
        'recent_posts': recent_posts,
        'categories': Category.objects.all(),
        'tags': Tag.objects.all(),
    }
    return render(request, 'blog_detail.html', context)
