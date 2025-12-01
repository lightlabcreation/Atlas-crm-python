from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone

def send_registration_confirmation_email(user):
    """Send email to user confirming their registration is pending approval."""
    subject = "Registration Confirmation - Pending Approval - Atlas Fulfillment"
    
    html_message = render_to_string('users/emails/registration_pending.html', {
        'user': user,
        'registration_date': timezone.now().strftime('%Y-%m-%d %H:%M'),
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_approval_email(user, approved_by):
    """Send email to user when their account is approved."""
    from django.conf import settings
    
    # Get site URL from settings or use default
    site_url = getattr(settings, 'SITE_URL', 'http://74.241.252.250:3000')
    login_url = f"{site_url}/users/login/"
    
    subject = "تمت الموافقة على حسابك - Account Approved - Welcome to Atlas Fulfillment"
    
    print(f"Attempting to send approval email to {user.email}")
    
    html_message = render_to_string('users/emails/account_approved.html', {
        'user': user,
        'approved_by': approved_by,
        'approval_date': timezone.now().strftime('%Y-%m-%d %H:%M'),
        'login_url': login_url,
    })
    
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"Approval email sent successfully to {user.email}")
    except Exception as e:
        print(f"Failed to send approval email to {user.email}: {e}")
        raise e

def send_verification_code_email(user, verification_code):
    """Send verification code email to user."""
    subject = "Email Verification Code - Atlas Fulfillment"
    
    html_message = render_to_string('users/emails/verification_code.html', {
        'user': user,
        'verification_code': verification_code,
    })
    
    plain_message = f"""
Hello {user.full_name},

Your email verification code is: {verification_code}

This code expires in 15 minutes.

If you didn't request this code, please ignore this email.

Thank you for choosing Atlas Fulfillment!
"""
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_rejection_email(user, rejected_by, reason):
    """Send email to user when their account is rejected."""
    subject = "Registration Request Rejected - Atlas Fulfillment"
    
    html_message = render_to_string('users/emails/account_rejected.html', {
        'user': user,
        'rejected_by': rejected_by,
        'rejection_reason': reason,
        'rejection_date': timezone.now().strftime('%Y-%m-%d %H:%M'),
        'register_url': 'http://74.241.252.250:3000/users/register/',
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    ) 