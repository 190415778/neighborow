import logging
import re
import email
import uuid
from email import policy
import base64
import quopri
from bs4 import BeautifulSoup
from django.http import HttpResponse
from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from email_reply_parser import EmailReplyParser
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from neighborow.models import Messages, MessageType, Borrowing_Request_Recipients, Communication, Channels, AppSettings, ApplicationSettings
from django_mailbox.models import Message as MailboxMessage
from neighborow.utils import generate_unique_message_code

logger = logging.getLogger(__name__)

# send unsent messages
def send_unsent_messages():
    # get al´l unsent messages
    unsent_messages = Messages.objects.filter(
        Q(is_sent_email=False) | Q(is_sent_sms=False) | Q(is_sent_whatsApp=False),
        outbox=True,
        inbox=False
    )
    # loop through unsent messages using all communication channels
    for message in unsent_messages:
        recipient = message.receiver_member_id

        if message.is_sent_email == False:
            # 1. send emails
            email_comms = Communication.objects.filter(
                member_id=recipient,
                channel=Channels.EMAIL,
                is_active=True
            )
            if email_comms.exists():
                email_addresses = [comm.identification for comm in email_comms]
                subject = f"{message.title} (Code: {message.message_code})"
                try:
                    send_mail(
                        subject=subject,
                        message=message.body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=email_addresses,
                        fail_silently=False,
                        html_message=None,
                    )
                    message.is_sent_email = True
                    message.save(update_fields=['is_sent_email'])
                except Exception as e:
                    logger.error(f"Error sending email messages {message.id} an {email_addresses}: {e}")
            else:
                message.is_sent_email = True
                message.save(update_fields=['is_sent_email'])

        if message.is_sent_sms == False:
            # 2. send sms via Twilio
            sms_comms = Communication.objects.filter(
                member_id=recipient,
                channel=Channels.SMS,
                is_active=True
            )
            if sms_comms.exists():
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                sms_sent = False
                for comm in sms_comms:
                    sms_body = f"{message.title} (Code: {message.message_code}) {message.body}"
                    trimmed_body = sms_body[:420] # send only first 420 charachters - 3 sms messages
                    try:
                        sms_response = client.messages.create(
                            body=trimmed_body,
                            from_=settings.TWILIO_PHONE_NUMBER,
                            to=comm.identification  # Twilio Trial-Modus: only registered snder phone numbers
                        )
                        logger.info(f"SMS sent to {comm.identification}. SID: {sms_response.sid}")
                        sms_sent = True
                    except Exception as e:
                        logger.error(f"Error sending sms messages {message.id} an {comm.identification}: {e}")
                if sms_sent:
                    message.is_sent_sms = True
                    message.save(update_fields=['is_sent_sms'])
            else:
                message.is_sent_sms = True
                message.save(update_fields=['is_sent_sms'])

        if message.is_sent_whatsApp == False:
            # 3. send WhatsApp via Twilio
            # whatsapp_comms = Communication.objects.filter(
            #     member_id=recipient,
            #     channel=Channels.WHATSAPP,
            #     is_active=True
            # )
            # if whatsapp_comms.exists():
            #     client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            #     whatsapp_sent = False
            #     for comm in whatsapp_comms:
            #         whatsapp_body = f"{message.title} {message.body}"
            #         try:
            #
            #             whatsapp_response = client.messages.create(
            #                 body=whatsapp_body,
            #                 from_="whatsapp:" + settings.TWILIO_WHATSAPP_NUMBER,
            #                 to="whatsapp:" + comm.identification
            #             )
            #             logger.info(f"WhatsApp sent to {comm.identification}. SID: {whatsapp_response.sid}")
            #             whatsapp_sent = True
            #         except Exception as e:
            #             logger.error(f"Error sending WhatsApp messagest {message.id} an {comm.identification}: {e}")
            #     if whatsapp_sent:
            #         message.is_sent_whatsApp = True
            #         message.save(update_fields=['is_sent_whatsApp'])
            # else:
            message.is_sent_whatsApp = True
            message.save(update_fields=['is_sent_whatsApp'])            


        # update corresponding Borrowing_Request_Recipients if typs is BORREQ
        if message.message_type == MessageType.BORREQ.value:
            Borrowing_Request_Recipients.objects.filter(
                member_id=recipient,
                pk=message.message_type_id,
                message_id__isnull=True
            ).update(message_id=message)

# process incoming messages
def gmx_processing(body):
    try:
        app_setting = AppSettings.objects.filter(key=ApplicationSettings.REPLY_MAIL_GMX).first()
        if app_setting:
            # reply patterns from app_settings
            reply_values = [v.strip() for v in app_setting.value.split(",")]
            new_body_lower = body.lower()
            for reply in reply_values:
                reply_lower = reply.lower()
                index = new_body_lower.find(reply_lower)
                if index != -1:
                    # Strip return message
                    substring = body[index + len(reply):]
                    new_body = body[:index]

                    # search for substring in EMAIL_HOST_USER case-insensitive
                    if (settings.EMAIL_HOST_USER.lower() in substring.replace(" ", "").lower()):
                        # delete from reply_value
                        new_body = body[:index]
                        # skip agter first hit
                        break
                    else:
                        new_body = new_body
                else:
                    new_body = body                       
    except Exception as e:
        logger.error(f"Error in additional filtering: {e}")

    return new_body

# process incoming mails
def process_mails():
    # get admin user
    try:
        admin_user = User.objects.get(username="admin")
    except User.DoesNotExist:
        raise Exception("Admin user not found.")

    # only filter outgoing=False emails
    mails = MailboxMessage.objects.filter(outgoing=False)

    valid_mails = []
    # loop through all messages and search for message code
    for mail in mails:
        match = re.search(r"\(Code:\s*(\w{16})\)", mail.subject)
        if match:
            code = match.group(1)
            valid_mails.append((mail, code))
        else:
            # delete emails without messgage code
            mail.delete()

    for mail, code in valid_mails:
        # Search for original message to identify sender
        original_messages = Messages.objects.filter(
            message_code=code,
            is_sent_email=True,
            outbox=True,
            inbox=False
        ).order_by('-created')
        if not original_messages.exists():
            mail.delete()
            continue
        original_message = original_messages.first()

        # strip title to 150 characters
        new_title = re.sub(r"\(Code:\s*(\w{16})\)", "", mail.subject).strip()[:150]

        plaintext_body = ""
        html_body = ""

        # --- PROCESS EMAIL BODY ---
        # get email.message.Message-Object 
        email_object = mail.get_email_object()

        if email_object.is_multipart():
            for part in email_object.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                # extract message text
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        plaintext_body += part.get_payload(decode=True).decode(charset, errors='ignore')
                    except Exception as e:
                        logger.error(f"Error decoding text/plain: {e}")
                # extract html-content
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        html_body += part.get_payload(decode=True).decode(charset, errors='ignore')
                    except Exception as e:
                        logger.error(f"Error decoding text/html: {e}")
        else:
            content_type = email_object.get_content_type()
            if content_type == 'text/plain':
                try:
                    charset = email_object.get_content_charset() or 'utf-8'
                    plaintext_body = email_object.get_payload(decode=True).decode(charset, 'ignore')
                except Exception as e:
                    logger.error(f"Error decoding (not multipart, text/plain): {e}")
            elif content_type == 'text/html':
                try:
                    charset = email_object.get_content_charset() or 'utf-8'
                    html_body = email_object.get_payload(decode=True).decode(charset, 'ignore')
                except Exception as e:
                    logger.error(f"Error decoding (not multipart, text/html): {e}")
            else:
                plaintext_body = mail.body  # Fallback

        # If plain text is missing but HTML content is available,
        # convert the HTML content to plain text.
        if not plaintext_body and html_body:
            soup = BeautifulSoup(html_body, 'html.parser')
            plaintext_body = soup.get_text(separator=" ", strip=True)

        # Remove the original message using python-email-reply-parser,
        # so that only the reply text remains.
        reply_text = EmailReplyParser.parse_reply(plaintext_body)
        new_body = reply_text[:2100]

        # --- NEW BLOCK: Processing of reply based on app-settings ---
        if "gmx" in mail.from_header.lower() and new_body != '':
            new_body = gmx_processing(new_body)
        # --- END NEW BLOCK ---

        # create record in message table with interchnaged sender/receiver
        new_message = Messages(
            sender_member_id=original_message.receiver_member_id,  # interchnaged
            receiver_member_id=original_message.sender_member_id,  # interchnaged
            title=new_title,
            body=new_body,
            message_code=code,
            inbox=True,
            is_sent_email=True,
            created_by=admin_user,
        )
        new_message.save()
        # delete processed message from mail table
        mail.delete()

# Retrieves all incoming SMS messages from Twilio that were sent to the central TWILIO_PHONE_NUMBER
def process_incoming_sms():

    admin_user = User.objects.get(username="admin")
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    # Retrieve all SMS messages sent to the central TWILIO_PHONE_NUMBER
    incoming_sms = client.messages.list(
        to=settings.TWILIO_PHONE_NUMBER
    )
    
    logger.info(f"{len(incoming_sms)} SMS found for number {settings.TWILIO_PHONE_NUMBER}.")
    for sms in incoming_sms:
        # Process only messages that have an inbound direction.
        if sms.direction.lower() != "inbound":
            deletion_success = client.messages(sms.sid).delete()
            if deletion_success:
                logger.info(f"Outgoing SMS SID {sms.sid} successfully deleted from Twilio.")
            else:
                logger.warning(f"Outgoing SMS SID {sms.sid} could not be deleted from Twilio.")            
            logger.info(f"Skipping outgoing SMS SID {sms.sid} because its direction is '{sms.direction}'.")
            continue

        try:
            # Try to extract a 16-digit code from the SMS body using regex
            code_match = re.search(r"Code:\s*(\w{16})", sms.body)
            if code_match:
                code = code_match.group(1)
                # Search for the original message in the Messages table (outbox message)
                original_message = Messages.objects.filter(
                    message_code=code,
                    outbox=True,
                    inbox=False
                ).order_by("-created").first()
                
                if not original_message:
                    logger.error(f"No original message found with code {code}. SMS SID {sms.sid} skipped.")
                    continue
                
                # Compose new SMS body with details from the original message
                new_message = Messages(
                    sender_member_id=original_message.receiver_member_id,  # Reply is sent from the original recipient
                    receiver_member_id=original_message.sender_member_id,  # Reply is sent to the original sender
                    title="Re: " + original_message.title,
                    body=original_message.body,
                    message_code=code,
                    inbox=True,
                    outbox=False,
                    internal=False,
                    is_sent_email=True,
                    is_sent_sms=True,
                    is_sent_whatsApp=True,
                    message_type=MessageType.INCOMING_SMS.value,
                    created_by=admin_user,
                )
                new_message.save()
                logger.info(f"New reply message (ID: {new_message.id}) created for code {code}.")
            else:
                # No code found – fallback via SMS identification
                sms_identification = Communication.objects.filter(
                    channel=Channels.SMS,
                    identification=sms.from_,
                    is_active=True
                ).first()
                if not sms_identification:
                    logger.error(f"No SMS Communication entry found for number {sms.from_}. SMS SID {sms.sid} skipped.")
                    continue
                
                # Generate a unique fallback code
                fallback_code = generate_unique_message_code()
                appended_text = "\nThis message could not be assigned to any sender because the code was missing."
                new_sms_body = sms.body + appended_text
                new_message = Messages(
                    sender_member_id=sms_identification.member_id,  # Use the member from the SMS communication
                    receiver_member_id=sms_identification.member_id,  # Association via SMS communication
                    title="Fallback SMS:" + sms.titel,
                    body=new_sms_body,
                    message_code=fallback_code,
                    inbox=True,
                    outbox=False,
                    internal=False,
                    is_sent_email=True,
                    is_sent_sms=True,
                    is_sent_whatsApp=True,
                    message_type=MessageType.INCOMING_SMS.value,
                    created_by=admin_user,
                )
                new_message.save()
                logger.info(f"New fallback message (ID: {new_message.id}) created for number {sms.from_} (no code found).")
            
            # Delete the SMS from Twilio after successful processing to ensure it is only handled once
            deletion_success = client.messages(sms.sid).delete()
            if deletion_success:
                logger.info(f"SMS SID {sms.sid} successfully deleted from Twilio.")
            else:
                logger.warning(f"SMS SID {sms.sid} could not be deleted from Twilio.")
        except Exception as e:
            logger.error(f"Error processing SMS SID {sms.sid}: {e}")
            
    logger.info("Processing of incoming SMS completed.")


