from django.core.management import call_command
from django.core.mail import send_mail
from django_q.tasks import schedule
from .utils import send_unsent_messages, process_mails, process_incoming_sms

# get and process incoming mails, sms
def fetch_mails():
    call_command('getmail')
    process_mails()
    process_incoming_sms()

# send outgoing mails, sms
def mail_sender_task():
    send_unsent_messages()

