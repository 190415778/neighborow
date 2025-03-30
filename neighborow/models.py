import datetime
from django.db import models
from django.db.models import UniqueConstraint
from django.contrib.auth.models import User
from django.db import connection


# Create your models here.

class ApplicationSettings(models.TextChoices):
    DISTANCE = '0', 'Invitor distance'
    REPLY_MAIL_GMX = '1', 'GMX Reply to Mail Processing'

class Channels(models.TextChoices):
    BUILTIN = '0', 'built-in messages'
    EMAIL = '1', 'email'
    SMS = '2', 'text messages'
    WHATSAPP = '3', 'WhatsApp'

class MemberType(models.TextChoices):
    RESIDENT = '0', 'resident'
    INVITEE = '1', 'invitee'

class Relationship(models.TextChoices):
    RELATIVE = '0', 'Relative'
    FRIEND = '2', 'Friend'
    NEIGHBOUR = '3', 'Neighbour'
    FORMER_RESIDENT = '4', 'Former Resident'    
    WORK_COLLEAGUE = '5', 'Work colleague'
    OTHER = '6', 'Other'

class MessageType(models.TextChoices):
    UNDEFINED = '0', 'Undefined'
    OTHER = '1', 'Other'
    INTERNAL = '2', 'Internal'
    BORREQ = '3', 'Borrowing Request'
    REPLY_INBOX = '4', 'Reply Inbox/Item List'
    REPLY_EMAIL = '5', 'Reply Mail'
    INCOMING_SMS = '6', 'Incoming SMS'
    FREE_MESSAGE = '7', 'Free Message'
    REMINDER = '8', 'Reminder'

class ReminderType(models.TextChoices):
    STANDARD = '0', 'Standard'
    REMINDER_DAY = '1', 'Reminder 1 Day'
    REMINDER_HOURS = '2', 'Reminder 2 Hours'
    OVERDUE = '3', 'Overdue'
    OVERDUE_ESC = '4', 'Overdue escalate'

class Building(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False, unique=True, db_index=True)
    address_line1 = models.CharField(max_length=100, null=True, blank=True)
    address_line2 = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=100, null=True, blank=True)
    units = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_%(class)s_set')
    created = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_%(class)s_set')
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}"

class AppSettings(models.Model):
    building_id = models.ForeignKey(Building, on_delete=models.CASCADE)
    key = models.CharField(max_length=2, null=False, blank=False,
                             choices=ApplicationSettings.choices,
                             default=ApplicationSettings.DISTANCE)
    value = models.CharField(max_length=100, null=False, blank=False, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_%(class)s_set')
    created = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_%(class)s_set')
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}"
    
    class Meta:
        constraints = [
            UniqueConstraint(fields=['building_id', 'key'], name='unique_appSettings_building_id_key')
        ]


class AccessManager(models.Manager):
    # return authorization status of logged in user
    def get_member_authorized(self, user_id):
        with connection.cursor() as cursor:
            cursor.execute("""
                        select coalesce(authorized, 'False') as is_authorized
                                            from auth_user u
                                            left outer join neighborow_member m on m.user_id_id = u.id
                                            where u.id = %s 
                        """, [user_id])
            return cursor.fetchall()

class Access_Code(models.Model):
    building_id = models.ForeignKey(Building, on_delete=models.CASCADE) 
    flat_no = models.CharField(max_length=16, null=False, blank=False)
    code = models.CharField(max_length=16, null=False, blank=False)
    type = models.CharField(max_length=2, null=False, blank=False,
                             choices=MemberType.choices,
                             default=MemberType.RESIDENT)     
    is_used = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_%(class)s_set')
    created = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_%(class)s_set')
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['code'], name='unique_access_code_code')
        ]

    objects = models.Manager() 
    custom_objects = AccessManager() 

    def __str__(self):
        return f"{self.id}"

class Member(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE) 
    building_id = models.ForeignKey(Building, on_delete=models.CASCADE) 
    access_code_id = models.ForeignKey(Access_Code, on_delete=models.CASCADE) 
    nickname = models.CharField(max_length=32, null=False, blank=False)
    flat_no = models.CharField(max_length=16, null=False, blank=False)
    authorized = models.BooleanField(default=False)
    distance = models.IntegerField(null=False, blank=False, default=0)
    type = models.CharField(max_length=2, null=False, blank=False,
                             choices=MemberType.choices,
                             default=MemberType.RESIDENT)     
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_%(class)s_set')
    created = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_%(class)s_set')
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user_id'], name='unique_Member_user_id')
        ]
    
    objects = models.Manager() 
    #custom_objects = MemberManager() 

    def __str__(self):
        return f"{self.id}"

class Invitation(models.Model):
    building_id = models.ForeignKey(Building, on_delete=models.CASCADE)
    invitor_member_id = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="sent_invitation")
    invitee_member_id = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="received_invitation", null=True, blank=True)
    access_code_id = models.ForeignKey(Access_Code, on_delete=models.CASCADE) 
    distance = models.IntegerField(null=False, blank=False, default=1) 
    relationship = models.CharField(max_length=2, null=False, blank=False,
                             choices=Relationship.choices,
                             default=Relationship.RELATIVE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_%(class)s_set')
    created = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_%(class)s_set')
    modified = models.DateTimeField(auto_now=True)
                    
    def __str__(self):
        return f"{self.id}"

    objects = models.Manager()

    class Meta:
        indexes = [
            models.Index(fields=["invitee_member_id"]), 
            models.Index(fields=["access_code_id"]), 
            ]
        constraints = [
            UniqueConstraint(fields=['access_code_id'], name='unique_Invitation_access_code_id')
        ]


class Messages(models.Model):
    sender_member_id = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="message_sender")
    receiver_member_id = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="message_receiver")
    title = models.CharField(max_length=175, null=False, blank=False)
    body = models.CharField(max_length=2100, null=False, blank=False)
    message_code = models.CharField(max_length=16, null=False, blank=False)
    inbox = models.BooleanField(default=False)
    outbox = models.BooleanField(default=False)
    internal = models.BooleanField(default=False)
    is_sent_email = models.BooleanField(default=False)
    is_sent_sms = models.BooleanField(default=False)
    is_sent_whatsApp = models.BooleanField(default=True)
    message_type = models.CharField(max_length=2, null=False, blank=False,
                             choices=MessageType.choices,
                             default=MessageType.UNDEFINED)
    message_type_id = models.BigIntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_%(class)s_set')
    created = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_%(class)s_set')
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["sender_member_id"]),
            models.Index(fields=["receiver_member_id"]),
            models.Index(fields=["message_code"]),
            ]

    objects = models.Manager()

    def __str__(self):
        return f"{self.id}"
    


class Communication(models.Model):
    member_id = models.ForeignKey(Member, on_delete=models.CASCADE)
    channel = models.CharField(max_length=2, null=False, blank=False,
                             choices=Channels.choices,
                             default=Channels.BUILTIN)
    identification = models.CharField(max_length=120, null=False, blank=False)
    is_active = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_%(class)s_set')
    created = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_%(class)s_set')
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["member_id"]),
            models.Index(fields=["identification"])
            ]
#        constraints = [
#             UniqueConstraint(fields=['member_id', 'channel'], name='unique_communication_member_id_channel')
#        ]
    
    objects = models.Manager()

    def __str__(self):
        return f"{self.id}"
    

class Borrowing_Request(models.Model):
    member_id = models.ForeignKey(Member, on_delete=models.CASCADE)
    title = models.CharField(max_length=150, null=False, blank=False)
    body = models.CharField(max_length=2000, null=False, blank=False)
    required_from = models.DateTimeField(blank=True, null=True)
    required_until = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_%(class)s_set')
    created = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_%(class)s_set')
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["member_id"]),
            ]

    objects = models.Manager()  

    def __str__(self):
        return f"{self.id}"
    

class Borrowing_Request_Recipients(models.Model):
    member_id = models.ForeignKey(Member, on_delete=models.CASCADE)
    message_id = models.ForeignKey(Messages, on_delete=models.CASCADE, related_name="sent_message", null=True, blank=True)
    borrowing_request = models.ForeignKey(Borrowing_Request, on_delete=models.CASCADE, null=False, blank=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_%(class)s_set')
    created = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_%(class)s_set')
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["member_id"]),
            models.Index(fields=["borrowing_request"]),
            ]
        constraints = [
            UniqueConstraint(fields=['message_id'], name='unique_borrowing_request_recipients_message_id'),
            UniqueConstraint(fields=['member_id', 'borrowing_request'], name='unique_borrowing_request_recipients_member_id_borrowing_request_id')
        ]

    objects = models.Manager() 

    def __str__(self):
        return f"{self.id}"

class ItemsForLoanManager(models.Manager):
    # return details for each item
    def get_items_for_loan(self, member_id):
        with connection.cursor() as cursor:
            cursor.execute("""
                            SELECT  i.id,
                                    i.label,
                                    i.description,
                                    i.available_from,
                                    i.currently_borrowed,
                                    i.available,
                                    i.created,
                                    i.modified,
                                    i.created_by_id,
                                    i.member_id_id,
                                    i.modified_by_id,
                                    m.id as lender_member_id,
                                    m.nickname as lender_member_nickname,
                                    m.flat_no as lender_member_flat_no,
                                    u.id as user_member_id,
                                    u.nickname as user_member_nickname,
                                    u.flat_no as user_member_flat_no,
                                    g.id as image_id,
                                    g.image as image_url,
                                    g.caption as image_caption
                            FROM neighborow_items_for_loan as i
                            INNER JOIN neighborow_member as m ON m.id = i.member_id_id
                            INNER JOIN neighborow_member as u ON u.id = %s
                            LEFT OUTER JOIN neighborow_items_for_loan_image as g on g.items_for_loan_id_id = i.id
                                            and g.id = (Select min(id) from neighborow_items_for_loan_image g2 where g2.items_for_loan_id_id = g.items_for_loan_id_id)
                            WHERE m.building_id_id = u.building_id_id
                            AND i.available = true
                            and i.is_deleted = false
                            order by i.modified DESC
                            """, [member_id])
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results



    def get_filtered_items_for_loan(self, member_id, search_string):
        search_pattern = f"%{search_string}%"
        sql = """
                SELECT  i.id,
                        i.label,
                        i.description,
                        i.available_from,
                        i.currently_borrowed,
                        i.available,
                        i.created,
                        i.modified,
                        i.created_by_id,
                        i.member_id_id,
                        i.modified_by_id,
                        m.id as lender_member_id,
                        m.nickname as lender_member_nickname,
                        m.flat_no as lender_member_flat_no,
                        u.id as user_member_id,
                        u.nickname as user_member_nickname,
                        u.flat_no as user_member_flat_no,
                        g.id as image_id,
                        g.image as image_url,
                        g.caption as image_caption
                FROM neighborow_items_for_loan as i
                INNER JOIN neighborow_member as m ON m.id = i.member_id_id
                INNER JOIN neighborow_member as u ON u.id = %s
                LEFT OUTER JOIN neighborow_items_for_loan_image as g on g.items_for_loan_id_id = i.id
                                and g.id = (Select min(id) from neighborow_items_for_loan_image g2 where g2.items_for_loan_id_id = g.items_for_loan_id_id)
                WHERE m.building_id_id = u.building_id_id
                AND i.available = true
                and i.is_deleted = false
                AND (LOWER(i.label) LIKE LOWER(%s) OR LOWER(i.description) LIKE LOWER(%s))
                order by i.modified DESC
                """
        
        with connection.cursor() as cursor:
            cursor.execute(sql, [member_id, search_pattern, search_pattern])
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results


class Items_For_Loan(models.Model):
    member_id = models.ForeignKey(Member, on_delete=models.CASCADE)
    label = models.CharField(max_length=150, null=False, blank=False)
    description = models.CharField(max_length=2000, null=False, blank=False)
    available_from = models.DateTimeField(blank=True, null=True)
    currently_borrowed = models.BooleanField(default=False)      
    available = models.BooleanField(default=True)  
    is_deleted = models.BooleanField(default=False)  
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_%(class)s_set')
    created = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_%(class)s_set')
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["member_id"]),
            ]

    objects = models.Manager()
    custom_objects = ItemsForLoanManager() 

    def __str__(self):
        return f"{self.id}"

class Items_For_Loan_Image(models.Model):
    # Establish a one-to-many relationship: one Item can have more than one image
    items_for_loan_id = models.ForeignKey(Items_For_Loan, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='item_photos/')
    caption = models.CharField(max_length=255, blank=True)  

    def __str__(self):
        return f"{self.id}"

class Condition_Log(models.Model):
    label = models.CharField(max_length=150, null=False, blank=False) 
    description = models.CharField(max_length=2000, null=False, blank=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_%(class)s_set')
    created = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_%(class)s_set')
    modified = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    def __str__(self):
        return f"{self.id}"

class Condition_Image(models.Model):
    # Establish a one-to-many relationship: one Item can have more than one image
    condition_log_id = models.ForeignKey(Condition_Log, on_delete=models.CASCADE, related_name='condition_images')
    image = models.ImageField(upload_to='condition_photos/')
    caption = models.CharField(max_length=255, blank=True)  
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_%(class)s_set')
    created = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_%(class)s_set')
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}"



class TransactionManager(models.Manager):
    # return details borrowed items
    def get_borrowed_items(self, member_id):
        sql = """
                SELECT t.id as transaction_id,
                    i.id as items_for_loan_id,
                    i.label as items_for_loan_label,   
                    b.id as borrower_member_id,
                    b.nickname as borrower_member_nickname,
                    b.flat_no as borrower_member_flat_no,
                    l.id as lender_member_id,
                    l.nickname as lender_member_nickname,
                    l.flat_no as lender_member_flat_no,
                    t.borrowed_on,
                    t.borrowed_until,
                    t.return_date,
                    g.id as image_id,
                    g.image as image_url,
                    g.caption as image_caption,
                    clb.id as before_condition_id,
	                cla.id as after_condition_id 	   
                FROM neighborow_transaction as t
                INNER JOIN neighborow_Items_For_Loan as i on t.items_for_loan_id_id = i.id
                LEFT OUTER JOIN neighborow_items_for_loan_image as g on g.items_for_loan_id_id = i.id
                                                            and g.id = (Select min(id) 
                                                                        from neighborow_items_for_loan_image g2 
                                                                        where g2.items_for_loan_id_id = g.items_for_loan_id_id)
                INNER JOIN neighborow_member as b ON b.id = t.borrower_member_id_id
                INNER JOIN neighborow_member as l ON l.id = t.lender_member_id_id		
                LEFT OUTER JOIN neighborow_condition_Log as clb on clb.id = t.before_condition_id
                LEFT OUTER JOIN neighborow_condition_Log as cla on cla.id = t.after_condition_id								
                WHERE t.borrower_member_id_id = %s
                ORDER BY t.borrowed_until ASC
                """
        
        with connection.cursor() as cursor:
            cursor.execute(sql, [member_id])
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results

    # return details borrowed items
    def get_loaned_items(self, member_id):
        sql = """
                SELECT i.id,
                    i.label,   
                    b.id as borrower_member_id,
                    b.nickname as borrower_member_nickname,
                    b.flat_no as borrower_member_flat_no,
                    l.id as lender_member_id,
                    l.nickname as lender_member_nickname,
                    l.flat_no as lender_member_flat_no,
                    t.borrowed_on,
                    t.borrowed_until,
                    t.return_date,
                    g.id as image_id,
                    g.image as image_url,
                    g.caption as image_caption,
                    clb.id as before_condition_id,
	                cla.id as after_condition_id   
                FROM neighborow_transaction as t
                INNER JOIN neighborow_Items_For_Loan as i on t.items_for_loan_id_id = i.id
                LEFT OUTER JOIN neighborow_items_for_loan_image as g on g.items_for_loan_id_id = i.id
                                                            and g.id = (Select min(id) 
                                                                        from neighborow_items_for_loan_image g2 
                                                                        where g2.items_for_loan_id_id = g.items_for_loan_id_id)
                INNER JOIN neighborow_member as b ON b.id = t.borrower_member_id_id
                INNER JOIN neighborow_member as l ON l.id = t.lender_member_id_id		
                LEFT OUTER JOIN neighborow_condition_Log as clb on clb.id = t.before_condition_id
                LEFT OUTER JOIN neighborow_condition_Log as cla on cla.id = t.after_condition_id								
                WHERE t.lender_member_id_id = %s
                ORDER BY t.borrowed_until ASC
                """
        
        with connection.cursor() as cursor:
            cursor.execute(sql, [member_id])
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results


class Transaction(models.Model):
    items_for_loan_id = models.ForeignKey(Items_For_Loan, on_delete=models.CASCADE, related_name='borrowed_item')
    lender_member_id = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="lender")
    borrower_member_id = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="borrower")
    before_condition = models.ForeignKey(Condition_Log, on_delete=models.CASCADE, blank=True, null=True, related_name="condition_before")
    after_condition = models.ForeignKey(Condition_Log, on_delete=models.CASCADE, blank=True, null=True, related_name="condition_after")
    borrowed_on = models.DateTimeField(blank=True, null=True)
    borrowed_until = models.DateTimeField(blank=True, null=True)
    return_date = models.DateTimeField(blank=True, null=True)
    reminder = models.CharField(max_length=2, null=False, blank=False,
                             choices=ReminderType.choices,
                             default=ReminderType.STANDARD)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_%(class)s_set')
    created = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_%(class)s_set')
    modified = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    custom_objects = TransactionManager() 

    def __str__(self):
        return f"{self.id}"

