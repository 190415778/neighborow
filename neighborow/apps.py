from django.apps import AppConfig
from django.core.signals import request_started
import os
import logging

logger = logging.getLogger(__name__)
setup_done = False

class NeighborowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'neighborow'

    def ready(self):
        import neighborow.signals
        request_started.connect(setup_schedules_once)

def setup_schedules_once(sender, **kwargs):
    global setup_done
    if not setup_done:
        setup_schedules()
        setup_done = True


def setup_schedules():
    from django_q.models import Schedule  
    from django_q.tasks import schedule

    # Delete existing schedule
    logger.info("Starting Setup: Delete reminders_schedule Schedule.")
    Schedule.objects.filter(name='reminders_schedule').delete()

    # Create new schedule
    schedule(
        'neighborow.tasks.process_transaction_reminders',  
        name='reminders_schedule',       
        schedule_type=Schedule.MINUTES,     
        minutes=10,
        repeats=-1,
    )
    logger.info("reminders_schedule Schedule created!")
