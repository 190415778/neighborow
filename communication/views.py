from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from twilio.rest import Client
from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.messaging_response import MessagingResponse

# Create your views here.
# views.py

def internal_only(view_func):
    def _wrapped_view(request, *args, **kwargs):
        allowed_ips = ['127.0.0.1', '::1']  # Add additional internal IPs here
        if request.META.get('REMOTE_ADDR') not in allowed_ips:
            return HttpResponseForbidden("Access Denied")
        return view_func(request, *args, **kwargs)
        print("IP allowed")
    return _wrapped_view

@internal_only
def send_sms(request):
    # Twilio client initialization
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    # Create and send SMS message
    # message = client.messages.create(
    #     body="This is a test message from Django App!",
    #     from_=settings.TWILIO_PHONE_NUMBER,
    #     to='NUMBER'  # Recipient, must be verified in Trial mode
    # )
    
    #return HttpResponse(f"Nachricht gesendet! SID: {message.sid}")
    return HttpResponse(f"Nachricht gesendet!")

@csrf_exempt
def receive_sms(request):

# still missing: only works with external address
# Configure Webhook in Twilio:
# configure "A MESSAGE COMES IN" for the relevant phone number 

    if request.method == 'POST':
        # Read incoming SMS data
        from_number = request.POST.get('From')
        message_body = request.POST.get('Body')
        # process the message
        print(f"message from {from_number}: {message_body}")
        
        # Create a response, if desired
        response = MessagingResponse()
        response.message("Thank you for your mesasage!")
        return HttpResponse(str(response), content_type='text/xml')
    else:
        return HttpResponse("Invalid request", status=400)