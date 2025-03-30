import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import (Borrowing_Request_Recipients, Borrowing_Request, 
                     Messages, Member, Communication, Channels, 
                     Invitation, Items_For_Loan, Transaction)
from django.contrib.auth.models import User
from .utils import generate_unique_message_code

logger = logging.getLogger(__name__)

# create messages for borrowing requests
@receiver(post_save, sender=Borrowing_Request_Recipients)
def create_messages(sender, instance, created, raw, **kwargs):
    
    if created:
        # Retrieve the related Borrowing_Request
        # If instance.borrowing_request_id is not already a Borrowing_Request instance,
        # use the foreign key id directly
        #borrowing_request_instance = instance.borrowing_request_id
        borrowing_request_instance = instance.borrowing_request

        # Retrieve receiver and sender Member objects
        # If instance.member_id is already a Member instance use it
        receiver_member_instance = instance.member_id
        sender_member_instance = borrowing_request_instance.member_id

        # Retrieve the User from the sender Member
        user_instance = sender_member_instance.user_id

        # Generate a unique message code.
        message_code = generate_unique_message_code()


        # Append borrowing period information if set
        new_body = borrowing_request_instance.body
        if borrowing_request_instance.required_from or borrowing_request_instance.required_until:
            new_body += (
                f"\nRequired borrowing period from {borrowing_request_instance.required_from} "
                f"to {borrowing_request_instance.required_until}"
            )

        # Create the new Message record
        Messages.objects.create(
            sender_member_id=sender_member_instance,
            receiver_member_id=receiver_member_instance,
            title=borrowing_request_instance.title,
            body=new_body,
            message_code=message_code,
            outbox=True,
            is_sent_email=False,
            is_sent_sms=False,
            is_sent_whatsApp =False,
            message_type='3',
            message_type_id=instance.pk,
            created_by=user_instance
        )
        # Create the new Message record
        Messages.objects.create(
            sender_member_id=sender_member_instance,
            receiver_member_id=receiver_member_instance,
            title=borrowing_request_instance.title,
            body=new_body,
            message_code=message_code,
            outbox=False,
            inbox=True,
            internal=True,
            is_sent_email=True,
            is_sent_sms=True,
            is_sent_whatsApp =True,
            message_type='3',
            message_type_id=instance.pk,
            created_by=user_instance
        )

# When a new Member instance is created, set default communication channel
@receiver(post_save, sender=Member)
def create_default_communication(sender, instance, created, raw, **kwargs):

    if raw:
        # Do not run the signal if the instance is loaded from fixtures
        return

    if created:
        try:
            Communication.objects.create(
                member_id=instance,
                channel=Channels.BUILTIN,  # Set channel to built-in messages
                identification=instance.nickname, 
                is_active=True,
                created_by=instance.user_id,
                modified_by=instance.user_id
            )
        except Exception as e:
            logger.error(f"Error creating Default Communication Channel for Member {instance.pk}: {e}", exc_info=True)

# When a new Invitation is created create a corresponding message record
@receiver(post_save, sender=Invitation)
def create_invitation_message(sender, instance, created, raw, **kwargs):
    if raw:
        # Do not run signal if the instance is loaded from fixtures
        return

    if created:
        # Use the Invitation.created_by field as the user who creates the message
        user_instance = instance.created_by

        # Construct the message title using the relationship display value.
        title = "Access Code for invitee " + instance.get_relationship_display()

        # Construct the body. Use the invitee's nickname if available.
        greeting = "Dear Member,"
        body = (
            greeting + "\n" + "\n" +
            "this is the new Access Code for a " + instance.get_relationship_display() + "\n" +
            "Access Code: " + instance.access_code_id.code + "\n" + "\n" +
            "Best Regards,\nYour Neighborow Team"
        )

        # Create the new Message record with the specified fields.
        Messages.objects.create(
            sender_member_id=instance.invitor_member_id,
            receiver_member_id=instance.invitor_member_id,
            title=title,
            body=body,
            message_code=generate_unique_message_code(),
            inbox=False,
            outbox=False,
            internal=True,
            is_sent_email=True,
            message_type='2',
            created_by=user_instance
        )

# when an item for loan is returned update status
@receiver(pre_save, sender=Items_For_Loan)
def update_available_from(sender, instance, **kwargs):
    if instance.pk:
        old_instance = Items_For_Loan.objects.get(pk=instance.pk)
        # interchnage currently_borowed flag
        if old_instance.currently_borrowed and not instance.currently_borrowed:
            instance.available_from = timezone.now()
    else:
        # and set timestamp to now
        if not instance.currently_borrowed:
            instance.available_from = timezone.now()


# When a transaction record chnges set new borrowed_on date based on future transactiosn
@receiver(post_save, sender=Transaction)
def update_item_availability(sender, instance, **kwargs):
    # get corresponding Items
    item = instance.items_for_loan_id  
    now_time = timezone.now() 
    threshold = now_time + timezone.timedelta(hours=5)

    # open transaction for this item with denen borrowed_on > threshold
    open_transactions = Transaction.objects.filter(
        items_for_loan_id=item,
        return_date__isnull=True,
        borrowed_on__gt=threshold
    )

    if open_transactions.exists():
        # smallest borrowed_on-date 
        min_date = open_transactions.order_by('borrowed_on').first().borrowed_on
    else:
        min_date = now_time

    # Updatethe  Items: available_from and currently_borrowed based on compariosn to now
    item.available_from = min_date
    item.currently_borrowed = min_date > now_time
    item.save(update_fields=['available_from', 'currently_borrowed'])