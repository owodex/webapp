from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import make_password, check_password
from .models import CustomUser, Transaction, Notification, GiftCardImage, GiftCardTransaction, ElectricityRequest, CableRequest, AirtimeRequest, DataRequest, Wallet, Beneficiary
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.core.paginator import Paginator
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db import transaction
from decimal import Decimal, InvalidOperation
from django.views.decorators.csrf import csrf_protect
import uuid
from django.http import HttpResponseBadRequest


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

        if password == confirm_password:
            user = CustomUser.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                first_name=full_name.split()[0],
                last_name=' '.join(full_name.split()[1:]),
                phone_number=phone_number,
            )

            # Create the signup bonus transaction
            Transaction.objects.create(
                user=user,
                service='Signup Bonus',
                invoice_id=f'SB{user.id}{int(timezone.now().timestamp())}',
                amount=2000,
                transaction_type='credit',
                date=timezone.now()
            )

            # Log the user in
            login(request, user)
            return redirect('dashboard')  # Redirect to dashboard after successful signup
        else:
            # Handle password mismatch error
            return render(request, 'signup.html', {'error': 'Passwords do not match'})
    return render(request, 'signup.html')


def index(request):
    return render(request, 'index.html')

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
                return redirect('dashboard')  # Redirect to dashboard after successful login
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please provide both email and password.')
        
        # For debugging: print the POST data
        print("POST data:", request.POST)
    
    return render(request, 'login.html')

def rate_calculator(request):
    return render(request, "rate_calculator.html")

def terms(request):
    return render(request, "terms.html")

def privacy_policy(request):
    return render(request, "privacy_policy.html")

def dashboard(request):
    # Get the 5 most recent transactions for the current user
    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:5]

    context = {
        'recent_transactions': recent_transactions,
    }

    return render(request, 'dashboard/index.html', context) 


def services(request):
    return render(request, "dashboard/services.html")

@login_required
def transactions(request):
    transactions_list = Transaction.objects.filter(user=request.user)
    paginator = Paginator(transactions_list, 10)  # Show 10 transactions per page

    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    return render(request, 'dashboard/transaction.html', {'transactions': transactions})

def profile(request):
    return render(request, "dashboard/profile.html")

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

def giftcards(request):
    return render(request, "dashboard/giftcards.html")

def airtime_data(request):
    return render(request, 'dashboard/airtime-data.html')

def pay_bills(request):
    return render(request, 'dashboard/pay-bills.html')

def bonus(request):
    return render(request, 'dashboard/bonus.html')

def trade_giftcard(request):
    return render(request, 'dashboard/trade_giftcards.html')

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
        return JsonResponse({'status': 'error', 'message': 'Invalid input'}, status=400)

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
            service='money_transfer',
            invoice_id=f'OT{Transaction.objects.count() + 1:06d}',
        )
        Transaction.objects.create(
            user=recipient,
            wallet=recipient_wallet,
            amount=amount,
            transaction_type='credit',
            service='money_transfer',
            invoice_id=f'OT{Transaction.objects.count() + 1:06d}',
        )

    return JsonResponse({'status': 'success', 'message': 'Transfer successful'})

@login_required
@require_POST
@csrf_protect
def bank_transfer(request):
    amount = request.POST.get('amount')
    account_number = request.POST.get('account_number')
    bank_name = request.POST.get('bank_name')
    save_beneficiary = request.POST.get('save_beneficiary') == 'true'

    if not amount or not account_number or not bank_name:
        return JsonResponse({'status': 'error', 'message': 'Invalid input'}, status=400)

    try:
        amount = Decimal(amount)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid amount'}, status=400)

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if wallet.balance < amount:
        return JsonResponse({'status': 'error', 'message': 'Insufficient balance'}, status=400)

    with transaction.atomic():
        wallet.balance -= amount
        wallet.save()

        Transaction.objects.create(
            user=request.user,
            wallet=wallet,
            amount=amount,
            transaction_type='debit',
            service='money_transfer',
            invoice_id=f'BT{Transaction.objects.count() + 1:06d}',
        )

        if save_beneficiary:
            Beneficiary.objects.create(
                user=request.user,
                account_number=account_number,
                bank_name=bank_name,
                name=f"Beneficiary {account_number[-4:]}"
            )

    # Here you would typically integrate with a payment gateway to complete the bank transfer
    # For this example, we'll assume the transfer is successful

    return JsonResponse({'status': 'success', 'message': 'Transfer successful'})

@login_required
def get_beneficiaries(request):
    beneficiaries = Beneficiary.objects.filter(user=request.user).values('id', 'name', 'account_number', 'bank_name')
    return JsonResponse(list(beneficiaries), safe=False)


@login_required
@transaction.atomic
def submit_airtime_request(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        network = request.POST.get('network')
        amount = request.POST.get('amount')

        # Generate a unique invoice ID
        invoice_id = str(uuid.uuid4().hex)[:20]

        # Create a new transaction
        new_transaction = Transaction.objects.create(
            user=request.user,
            service='airtime',
            invoice_id=invoice_id,
            amount=amount,
            transaction_type='debit',
            status='pending'
        )

        # Create a new airtime request
        AirtimeRequest.objects.create(
            transaction=new_transaction,
            phone_number=phone_number,
            network=network
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Airtime request submitted successfully',
            'transaction_id': new_transaction.invoice_id
        })

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)

@require_POST
def submit_data_request(request):
    phone_number = request.POST.get('phone_number')
    network = request.POST.get('network')
    data_plan = request.POST.get('data_plan')
    amount = request.POST.get('amount')

    # Generate a unique invoice ID
    invoice_id = str(uuid.uuid4().hex)[:20]
    
    try:
        transaction = Transaction.objects.create(
            user=request.user,
            service='data',
            invoice_id=invoice_id,
            amount=amount,
            transaction_type='debit',
            status='pending'
        )

        DataRequest.objects.create(
            transaction=transaction,
            phone_number=phone_number,
            network=network,
            data_plan=data_plan,
            amount=amount
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Data request submitted successfully',
            'transaction_id': transaction.invoice_id
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
    

@require_POST
@csrf_protect
def submit_cable_request(request):
    provider = request.POST.get('provider')
    smart_card_number = request.POST.get('smart_card_number')
    package = request.POST.get('package')
    account_name = request.POST.get('account_name')
    amount = request.POST.get('amount')

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

    with transaction.atomic():
        wallet.balance -= amount
        wallet.save()

        new_transaction = Transaction.objects.create(
            user=request.user,
            wallet=wallet,
            amount=amount,
            transaction_type='debit',
            service='cable',
            invoice_id=invoice_id,
            status='pending'
        )

        CableRequest.objects.create(
            transaction=new_transaction,
            provider=provider,
            smart_card_number=smart_card_number,
            package=package,
            account_name=account_name,
            amount=amount
        )

    return JsonResponse({'status': 'success', 'message': 'Cable subscription successful', 'transaction_id': new_transaction.invoice_id})

@require_POST
@csrf_protect
def submit_electricity_request(request):
    meter_number = request.POST.get('meter_number')
    account_name = request.POST.get('account_name')
    operator = request.POST.get('operator')
    plan = request.POST.get('plan')
    amount = request.POST.get('amount')

     # Generate a unique invoice ID
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

    with transaction.atomic():
        wallet.balance -= amount
        wallet.save()

        new_transaction = Transaction.objects.create(
            user=request.user,
            wallet=wallet,
            amount=amount,
            transaction_type='debit',
            service='electricity',
            invoice_id=invoice_id,
            status='pending'
        )

        ElectricityRequest.objects.create(
            transaction=new_transaction,
            meter_number=meter_number,
            plan=plan,
            operator=operator,
            account_name=account_name,
            amount=amount
        )

    return JsonResponse({'status': 'success', 'message': 'Electricity bill payment successful', 'transaction_id': new_transaction.invoice_id})

@login_required
def trade_giftcard(request):
    if request.method == 'POST':
        giftcard_name = request.POST.get('giftcard_name')
        currency = request.POST.get('giftCardCurrency')
        card_type = request.POST.get('giftCardType')
        denomination = request.POST.get('denomination')
        amount = request.POST.get('amount')
        images = request.FILES.getlist('giftCardImages')

        # Convert amount to Decimal
        try:
            amount = Decimal(amount)
        except InvalidOperation:
            return render(request, 'dashboard/trade_giftcards.html', {
                'error_message': 'Invalid amount provided. Please enter a valid number.',
                'form_data': request.POST
            })

        # Generate a unique invoice ID
        invoice_id = str(uuid.uuid4().hex)[:20]

        # Create a new Transaction
        transaction = Transaction.objects.create(
            user=request.user,
            amount=amount,
            service='giftcard',
            status='pending',
            transaction_type='credit',
            invoice_id=invoice_id
        )

        # Create a new GiftCardTransaction
        giftcard_transaction = GiftCardTransaction.objects.create(
            user=request.user,
            transaction=transaction,
            giftcard_name=giftcard_name,
            currency=currency,
            card_type=card_type,
            denomination=denomination,
            amount=amount
        )

        # Save the uploaded images
        for image in images:
            GiftCardImage.objects.create(
                transaction=giftcard_transaction,
                image=image
            )

        # Pass success message to the template
        return render(request, 'dashboard/trade_giftcards.html', {
            'success_message': 'Gift card trade request submitted successfully!',
        })

    return render(request, 'dashboard/trade_giftcards.html')
