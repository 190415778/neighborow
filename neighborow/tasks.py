from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from .models import (
    Transaction,
    Messages,
    ReminderType,
    MessageType,
)
from .utils import generate_unique_message_code

# look for all open transactions to send reminders
def process_transaction_reminders():

    # Retrieve the admin user (it is assumed that a user with the username "admin-user" exists)
    admin_user = User.objects.get(username="admin")
    now = timezone.now()
    
    # All transactions where no return date has been set
    transactions = Transaction.objects.filter(return_date__isnull=True)
    
    for trans in transactions:
        due_date = trans.borrowed_until
        # If no due date is present, skip
        if due_date is None:
            continue

        # Case 1: Due in less than 1 day and reminder is STANDARD
        if due_date > now and due_date - now <= timedelta(days=1) and trans.reminder == ReminderType.STANDARD:
            Messages.objects.create(
                sender_member_id=trans.lender_member_id,
                receiver_member_id=trans.borrower_member_id,
                title=f"Reminder: please return {trans.items_for_loan_id.label} tomorrow",
                body=(
                    f"Hi {trans.borrower_member_id.nickname}, \n\n"
                    f"just a friendly reminder about the {trans.items_for_loan_id.label} you borrowed on {trans.borrowed_on}. "
                    "If possible, could you please bring it back tomorrow? Thanks a bunch! \n\n"
                    f"Your neighbour {trans.lender_member_id.nickname} from {trans.lender_member_id.flat_no}"
                ),
                message_code=generate_unique_message_code(),
                inbox=False,
                outbox=True,
                internal=True,
                is_sent_email=False,
                is_sent_sms=False,
                is_sent_whatsApp=False,
                message_type=MessageType.REMINDER,
                created_by=admin_user,
            )
            trans.reminder = ReminderType.REMINDER_DAY
            trans.save()

        # Case 2: Due in less than 1 hour and reminder is STANDARD or REMINDER_DAY
        elif due_date > now and due_date - now <= timedelta(hours=2) and trans.reminder in [ReminderType.STANDARD, ReminderType.REMINDER_DAY]:
            Messages.objects.create(
                sender_member_id=trans.lender_member_id,
                receiver_member_id=trans.borrower_member_id,
                title=f"Reminder: please return {trans.items_for_loan_id.label} today",
                body=(
                    f"Hi {trans.borrower_member_id.nickname}, \n\n"
                    f"just a friendly reminder about the {trans.items_for_loan_id.label} you borrowed on {trans.borrowed_on}. "
                    f"If possible, could you please bring it back today, the borrowing time ends on {due_date}? Thanks a bunch! \n\n"
                    f"Your neighbour {trans.lender_member_id.nickname} from {trans.lender_member_id.flat_no}"
                ),
                message_code=generate_unique_message_code(),
                inbox=False,
                outbox=True,
                internal=True,
                is_sent_email=False,
                is_sent_sms=False,
                is_sent_whatsApp=False,
                message_type=MessageType.REMINDER,
                created_by=admin_user,
            )
            trans.reminder = ReminderType.REMINDER_HOURS
            trans.save()

        # Case 3: Overdue for at least 3 hours and reminder is STANDARD, REMINDER_DAY or REMINDER_HOURS
        elif due_date < now and now - due_date >= timedelta(hours=3) and trans.reminder in [ReminderType.STANDARD, ReminderType.REMINDER_DAY, ReminderType.REMINDER_HOURS]:
            Messages.objects.create(
                sender_member_id=trans.lender_member_id,
                receiver_member_id=trans.borrower_member_id,
                title=f"Reminder: please return {trans.items_for_loan_id.label} as soon as possible",
                body=(
                    f"Hi {trans.borrower_member_id.nickname}, just a friendly reminder that the loan period for {trans.items_for_loan_id.label} "
                    f"has ended on {due_date}. Could you please return it as soon as possible? Thanks!\n\n"
                    f"Your neighbour {trans.lender_member_id.nickname} from {trans.lender_member_id.flat_no}"
                ),
                message_code=generate_unique_message_code(),
                inbox=False,
                outbox=True,
                internal=True,
                is_sent_email=False,
                is_sent_sms=False,
                is_sent_whatsApp=False,
                message_type=MessageType.REMINDER,
                created_by=admin_user,
            )
            trans.reminder = ReminderType.OVERDUE
            trans.save()

        # Case 4: Overdue for at least 1 day and reminder is STANDARD, REMINDER_DAY, REMINDER_HOURS or OVERDUE
        elif due_date < now and now - due_date >= timedelta(days=1) and trans.reminder in [ReminderType.STANDARD, ReminderType.REMINDER_DAY, ReminderType.REMINDER_HOURS, ReminderType.OVERDUE]:
            Messages.objects.create(
                sender_member_id=trans.lender_member_id,
                receiver_member_id=trans.borrower_member_id,
                title=f"Urgently: please return {trans.items_for_loan_id.label} overdue",
                body=(
                    f"Hi {trans.borrower_member_id.nickname}, the loan period for the {trans.items_for_loan_id.label} is over. "
                    f"Return {trans.items_for_loan_id.label} immediately.\n\n"
                    f"Your neighbour {trans.lender_member_id.nickname} from {trans.lender_member_id.flat_no}"
                ),
                message_code=generate_unique_message_code(),
                inbox=False,
                outbox=True,
                internal=True,
                is_sent_email=False,
                is_sent_sms=False,
                is_sent_whatsApp=False,
                message_type=MessageType.REMINDER,
                created_by=admin_user,
            )
            trans.reminder = ReminderType.OVERDUE_ESC
            trans.save()


