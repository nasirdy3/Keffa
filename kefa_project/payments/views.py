from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import uuid
import requests
from .models import Payment
from kefa_project.tournaments.models import Tournament, TournamentRegistration


@login_required
def initiate_payment(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    try:
        player = request.user.player_profile
        team = player.team
    except:
        messages.error(request, 'You must have a team to register for tournaments.')
        return redirect('tournaments_list')
    
    if tournament.status != 'registration':
        messages.error(request, 'Registration is closed for this tournament.')
        return redirect('tournament_detail', tournament_id=tournament_id)
    
    if tournament.is_full:
        messages.error(request, 'This tournament is full.')
        return redirect('tournament_detail', tournament_id=tournament_id)
    
    registration, created = TournamentRegistration.objects.get_or_create(
        tournament=tournament,
        team=team
    )
    
    if registration.payment_verified:
        messages.info(request, 'You are already registered for this tournament.')
        return redirect('tournament_detail', tournament_id=tournament_id)
    
    if tournament.registration_fee == 0:
        registration.payment_verified = True
        registration.save()
        messages.success(request, 'Registration successful! Tournament is free.')
        return redirect('tournament_detail', tournament_id=tournament_id)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        if payment_method == 'offline':
            payment = Payment.objects.create(
                registration=registration,
                amount=tournament.registration_fee,
                payment_method='offline',
                transaction_reference=f'OFFLINE-{uuid.uuid4().hex[:12].upper()}',
                status='pending'
            )
            messages.success(request, 'Offline payment initiated. Please contact admin with proof of payment.')
            return redirect('payment_proof_upload', payment_id=payment.id)
        
        elif payment_method == 'paystack':
            return initiate_paystack_payment(request, registration, tournament)
        
        elif payment_method == 'flutterwave':
            return initiate_flutterwave_payment(request, registration, tournament)
        
        else:
            messages.error(request, 'Invalid payment method selected.')
    
    return render(request, 'payments/initiate_payment.html', {
        'tournament': tournament,
        'team': team,
        'registration': registration
    })


def initiate_paystack_payment(request, registration, tournament):
    paystack_secret = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
    
    if not paystack_secret:
        messages.error(request, 'Paystack is not configured. Please use offline payment.')
        return redirect('initiate_payment', tournament_id=tournament.id)
    
    transaction_ref = f'PAYSTACK-{uuid.uuid4().hex[:12].upper()}'
    
    payment = Payment.objects.create(
        registration=registration,
        amount=tournament.registration_fee,
        payment_method='paystack',
        transaction_reference=transaction_ref,
        status='pending'
    )
    
    headers = {
        'Authorization': f'Bearer {paystack_secret}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'email': request.user.email,
        'amount': int(float(tournament.registration_fee) * 100),
        'reference': transaction_ref,
        'callback_url': request.build_absolute_uri(f'/payments/paystack/callback/')
    }
    
    try:
        response = requests.post('https://api.paystack.co/transaction/initialize', json=data, headers=headers)
        result = response.json()
        
        if result.get('status'):
            authorization_url = result['data']['authorization_url']
            return redirect(authorization_url)
        else:
            messages.error(request, 'Failed to initialize Paystack payment.')
            payment.status = 'failed'
            payment.save()
    except Exception as e:
        messages.error(request, f'Payment initialization error: {str(e)}')
        payment.status = 'failed'
        payment.save()
    
    return redirect('initiate_payment', tournament_id=tournament.id)


def initiate_flutterwave_payment(request, registration, tournament):
    flutterwave_public = getattr(settings, 'FLUTTERWAVE_PUBLIC_KEY', None)
    flutterwave_secret = getattr(settings, 'FLUTTERWAVE_SECRET_KEY', None)
    
    if not flutterwave_public or not flutterwave_secret:
        messages.error(request, 'Flutterwave is not configured. Please use offline payment.')
        return redirect('initiate_payment', tournament_id=tournament.id)
    
    transaction_ref = f'FLW-{uuid.uuid4().hex[:12].upper()}'
    
    payment = Payment.objects.create(
        registration=registration,
        amount=tournament.registration_fee,
        payment_method='flutterwave',
        transaction_reference=transaction_ref,
        status='pending'
    )
    
    headers = {
        'Authorization': f'Bearer {flutterwave_secret}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'tx_ref': transaction_ref,
        'amount': str(float(tournament.registration_fee)),
        'currency': 'NGN',
        'redirect_url': request.build_absolute_uri(f'/payments/flutterwave/callback/'),
        'customer': {
            'email': request.user.email,
            'name': request.user.player_profile.full_name,
        },
        'customizations': {
            'title': 'KEFA Tournament Registration',
            'description': f'Registration fee for {tournament.name}',
            'logo': request.build_absolute_uri('/static/images/logo.png'),
        }
    }
    
    try:
        response = requests.post('https://api.flutterwave.com/v3/payments', json=data, headers=headers)
        result = response.json()
        
        if result.get('status') == 'success':
            payment_link = result['data']['link']
            return redirect(payment_link)
        else:
            messages.error(request, 'Failed to initialize Flutterwave payment.')
            payment.status = 'failed'
            payment.save()
    except Exception as e:
        messages.error(request, f'Payment initialization error: {str(e)}')
        payment.status = 'failed'
        payment.save()
    
    return redirect('initiate_payment', tournament_id=tournament.id)


@login_required
def flutterwave_callback(request):
    transaction_id = request.GET.get('transaction_id')
    tx_ref = request.GET.get('tx_ref')
    status = request.GET.get('status')
    
    if status == 'successful' and transaction_id and tx_ref:
        flutterwave_secret = getattr(settings, 'FLUTTERWAVE_SECRET_KEY', None)
        
        if not flutterwave_secret:
            messages.error(request, 'Payment verification failed. Please contact support.')
            return redirect('player_dashboard')
        
        headers = {
            'Authorization': f'Bearer {flutterwave_secret}',
            'Content-Type': 'application/json'
        }
        
        try:
            verify_url = f'https://api.flutterwave.com/v3/transactions/{transaction_id}/verify'
            response = requests.get(verify_url, headers=headers)
            result = response.json()
            
            if result.get('status') == 'success' and result['data']['status'] == 'successful':
                try:
                    payment = Payment.objects.get(transaction_reference=tx_ref)
                    
                    if payment.status != 'verified':
                        payment.status = 'verified'
                        payment.verified_at = timezone.now()
                        payment.save()
                        
                        payment.registration.payment_verified = True
                        payment.registration.save()
                        
                        messages.success(request, 'Payment successful! You are now registered for the tournament.')
                    else:
                        messages.info(request, 'Payment already verified.')
                    
                    return redirect('tournament_detail', tournament_id=payment.registration.tournament.id)
                except Payment.DoesNotExist:
                    messages.error(request, 'Payment record not found.')
            else:
                messages.error(request, 'Payment verification failed.')
        except Exception as e:
            messages.error(request, f'Verification error: {str(e)}')
    else:
        messages.error(request, 'Payment was not successful.')
    
    return redirect('player_dashboard')


@csrf_exempt
def flutterwave_webhook(request):
    if request.method == 'POST':
        flutterwave_secret_hash = getattr(settings, 'FLUTTERWAVE_SECRET_HASH', None)
        
        if not flutterwave_secret_hash:
            return JsonResponse({'status': 'error', 'message': 'Not configured'}, status=400)
        
        signature = request.headers.get('verif-hash', '')
        
        if signature != flutterwave_secret_hash:
            return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=401)
        
        try:
            data = json.loads(request.body)
            
            if data.get('event') == 'charge.completed' and data.get('data', {}).get('status') == 'successful':
                tx_ref = data['data']['tx_ref']
                
                try:
                    payment = Payment.objects.get(transaction_reference=tx_ref)
                    
                    if payment.status != 'verified':
                        payment.status = 'verified'
                        payment.verified_at = timezone.now()
                        payment.save()
                        
                        payment.registration.payment_verified = True
                        payment.registration.save()
                    
                    return JsonResponse({'status': 'success'})
                except Payment.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Payment not found'}, status=404)
            
            return JsonResponse({'status': 'received'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@csrf_exempt
def paystack_webhook(request):
    import hmac
    import hashlib
    
    if request.method == 'POST':
        paystack_secret = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
        
        if not paystack_secret:
            return JsonResponse({'status': 'error', 'message': 'Not configured'}, status=400)
        
        signature = request.headers.get('X-Paystack-Signature', '')
        
        computed_signature = hmac.new(
            paystack_secret.encode('utf-8'),
            request.body,
            hashlib.sha512
        ).hexdigest()
        
        if not hmac.compare_digest(signature, computed_signature):
            return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=401)
        
        try:
            data = json.loads(request.body)
            
            if data.get('event') == 'charge.success':
                transaction_ref = data['data']['reference']
                
                try:
                    payment = Payment.objects.get(transaction_reference=transaction_ref)
                    
                    if payment.status != 'verified':
                        payment.status = 'verified'
                        payment.verified_at = timezone.now()
                        payment.save()
                        
                        payment.registration.payment_verified = True
                        payment.registration.save()
                    
                    return JsonResponse({'status': 'success'})
                except Payment.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Payment not found'}, status=404)
            
            return JsonResponse({'status': 'received'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
def payment_proof_upload(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    try:
        player = request.user.player_profile
        team = player.team
    except:
        messages.error(request, 'Access denied.')
        return redirect('player_dashboard')
    
    if payment.registration.team != team:
        messages.error(request, 'Access denied.')
        return redirect('player_dashboard')
    
    if request.method == 'POST':
        payment_proof = request.FILES.get('payment_proof')
        
        if payment_proof:
            payment.payment_proof = payment_proof
            payment.save()
            messages.success(request, 'Payment proof uploaded! Admin will verify it soon.')
            return redirect('player_dashboard')
        else:
            messages.error(request, 'Please select an image to upload.')
    
    return render(request, 'payments/upload_proof.html', {'payment': payment})


@staff_member_required
def verify_offline_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            payment.status = 'verified'
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.save()
            
            payment.registration.payment_verified = True
            payment.registration.save()
            
            messages.success(request, 'Payment verified successfully!')
        
        elif action == 'reject':
            payment.status = 'failed'
            payment.notes = request.POST.get('notes', 'Payment rejected')
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.save()
            
            messages.success(request, 'Payment rejected.')
        
        return redirect('admin_payment_queue')
    
    return render(request, 'payments/verify_offline.html', {'payment': payment})


@staff_member_required
def payment_verification_queue(request):
    pending_payments = Payment.objects.filter(
        payment_method='offline',
        status='pending'
    ).select_related('registration__team', 'registration__tournament').order_by('created_at')
    
    return render(request, 'payments/verification_queue.html', {
        'payments': pending_payments
    })
