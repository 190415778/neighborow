import random, string
from .models import Access_Code, Messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import render

# generate unique access code
def generate_unique_access_code():
    characters = string.ascii_letters + string.digits
    while True:
        # check if code exists
        access_code = ''.join(random.choices(characters, k=16))
        if not Access_Code.objects.filter(code=access_code).exists():
            # code is unique -- end loop
            return access_code
        
# check if request is ajax-request and return relevant rersponse
def ajax_or_render(request, popup_template, fallback_template, context=None):
    if context is None:
        context = {}
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string(popup_template, context=context, request=request)
        return JsonResponse({'html': html})
    else:
        return render(request, fallback_template, context)

# generate unique message code
def generate_unique_message_code():
    characters = string.ascii_letters + string.digits
    while True:
        # check if code exists
        message_code = ''.join(random.choices(characters, k=16))
        if not Messages.objects.filter(message_code=message_code).exists():
            # code is unique -- end loop
            return message_code        
