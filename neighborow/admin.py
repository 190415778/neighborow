from django.contrib import admin
from .models import (Building, Access_Code, Member, 
                     AppSettings, Invitation, Messages, 
                     Communication, Borrowing_Request_Recipients, 
                     Borrowing_Request, Items_For_Loan, Items_For_Loan_Image,
                     Condition_Log, Condition_Image, Transaction)

# Register your models here.
admin.site.register(Building)
admin.site.register(Access_Code)
admin.site.register(Member)
admin.site.register(AppSettings)
admin.site.register(Invitation)
admin.site.register(Messages)
admin.site.register(Communication)
admin.site.register(Borrowing_Request_Recipients)
admin.site.register(Borrowing_Request)
admin.site.register(Items_For_Loan)
admin.site.register(Items_For_Loan_Image)
admin.site.register(Condition_Log)
admin.site.register(Condition_Image)
admin.site.register(Transaction)


