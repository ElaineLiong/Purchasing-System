"""
Definition of views.
"""

from django.shortcuts import render
from django.http import HttpRequest
from django.template import RequestContext
from datetime import datetime

from django.contrib.auth.decorators import login_required

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/index.html',
        {
            'title':'Home Page',
            'year':'2019/2020'
        }
    )

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        {
            'title':'Contact',
            'message':'Dr. Yeoh.',
            'year':'2019/2020'
        }
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {
            'title':'Purchasing System',
            'message':'This application processes purchases of an organization.',
            'year':'2019/2020'
        }
    )

@login_required
def menu(request):
    check_employee = request.user.groups.filter(name='employee').exists()
    check_manager = request.user.groups.filter(name='manager').exists()
    check_finance = request.user.groups.filter(name='finance').exists()

    context = {
            'title':'Main Menu',
            'is_employee': check_employee,
            'is_manager': check_manager,
            'is_finance': check_finance,
            'year':'2019/2020'
        }
    context['user'] = request.user

    return render(request,'app/menu.html',context)