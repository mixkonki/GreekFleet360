"""
Billing Views for GreekFleet 360
Subscription management
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def subscription_expired_view(request):
    """
    Subscription Expired Page
    Shows company name, expiry date, and renewal instructions
    """
    company = request.company
    user_role = None
    
    try:
        user_role = request.user.profile.role
    except AttributeError:
        pass
    
    is_admin = user_role == 'ADMIN'
    
    context = {
        'company': company,
        'is_admin': is_admin,
    }
    
    return render(request, 'billing/expired.html', context)
