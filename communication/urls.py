from django.urls import path
from . import views

urlpatterns = [
     path('sms/send/', views.send_sms, name='send_sms'),
     path('sms/receive/', views.receive_sms, name='sms_reply'),
    ]