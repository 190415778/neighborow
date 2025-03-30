import os
import logging
from django.apps import AppConfig
from django.core.signals import request_started
from django.conf import settings  

logger = logging.getLogger(__name__)
setup_done = False

class CommunictionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'communication'

    def ready(self):
        request_started.connect(setup_schedules_once)

# setup schedule once at startup
def setup_schedules_once(sender, **kwargs):
    global setup_done
    if not setup_done:
        setup_schedules()
        setup_done = True

# create schedule for email, twilio and reminders
def setup_schedules():
    from django_q.models import Schedule  
    from django_q.tasks import schedule
    from django_mailbox.models import Mailbox

    #Schedule.objects.all().delete()
    logger.info("Starting Setup: Delete mail_sender_task Schedules.")
    # delete existing mail sender schedule
    Schedule.objects.filter(name='mail_sender_task').delete()
    
    # create schedule for mail sender
    schedule(
        'communication.tasks.mail_sender_task',  # Pfad zur Task-Funktion
        name='mail_sender_task',
        schedule_type=Schedule.MINUTES,     
        minutes=1,
        repeats=-1,
    )
    logger.info("Mail Sender Schedule created!")

    # delete existing fetch mail schedule
    logger.info("Starting Setup: Delete fetch_mails Schedules.")
    Schedule.objects.filter(name='fetch_mails').delete()

    # create fetch mail schedule
    schedule(
        'communication.tasks.fetch_mails',  # Pfad zur Task-Funktion 
        name='fetch_mails',      
        schedule_type=Schedule.MINUTES,     
        minutes=1,
        repeats=-1,
    )
    logger.info("Mail Receiver Schedule created!")

    # delete all existing mailbox configuration entries
    logger.info("Deleting all Mailbox entries.")
    Mailbox.objects.all().delete()

    # create mailbox configuration entry
    logger.info("Creating dynamic mailbox from settings.")
    mailbox_uri = getattr(settings, "NEIGHBOROW_MAILBOX_URI", None)
    if mailbox_uri is None:
        logger.error("NEIGHBOROW_MAILBOX_URI is not defined in settings!")
    else:
        Mailbox.objects.create(
            name="Neighborow Mailbox",
            uri=mailbox_uri,
        )
        logger.info("Dynamic mailbox created with URI: %s", mailbox_uri)

    logger.info("Setup completed.")
