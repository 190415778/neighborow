import datetime, logging, pytz
import re
import calendar
from datetime import date, timedelta
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import (Building, AppSettings, Access_Code, Member, Invitation, 
                     Relationship, Borrowing_Request_Recipients, Borrowing_Request, 
                     MemberType, Communication, Messages, MessageType, Items_For_Loan, 
                     Items_For_Loan_Image, Transaction, Condition_Log, Condition_Image)
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from .forms import MyForm
from django.http import JsonResponse
from django.template.loader import render_to_string
from .utils import ajax_or_render, generate_unique_access_code, generate_unique_message_code
from django.db.models import Prefetch

logger = logging.getLogger(__name__)

# actual time
def now():
    return datetime.datetime.now()



@login_required
def index(request):

    # get the logged in user
    user_instance = request.user
    user_id = user_instance.id
    #user_id = User.objects.get(username=request.user).id
    #user_instance = User.objects.get(username=request.user)

    # process the access code at first login
    if request.method == 'POST':
        # which form has been posted
        form_type = request.POST.get('form_type')
        # Form: Access Code
        if form_type == 'modalAccessCode':
            access_code = request.POST.get('accessCodeInput')
            nickname = request.POST.get('nicknameInput')

            try:
                # check if access code is valid
                code_instance = Access_Code.objects.get(code=access_code)
                if code_instance.is_used == False:

                    try:
                        # update existing member
                        member = Member.objects.get(user_id=user_instance)
                        member.access_code_id = code_instance
                        member.building_id = code_instance.building_id
                        # member.nickname = nickname
                        member.flat_no = code_instance.flat_no
                        member.type = code_instance.type
                        member.authorized = True
                        member.modified_by = request.user
                        member.save()
                    except Member.DoesNotExist:
                        # add new member
                        # member is resident
                        if code_instance.type == '0':
                            member_distance = 0
                        # member is invitee
                        elif code_instance.type == '1':
                            try:
                                invitation_instance = Invitation.objects.get(access_code_id=code_instance)
                                member_distance = invitation_instance.distance + 1
                            except Invitation.DoesNotExist:
                                logger.exception("Error reading invitation data: %s", e)

                        # Database transaction for creation of new member and update of Invitation record
                        try:
                            with transaction.atomic():
                                # create new member instance (resident or invitee)                               
                                member = Member.objects.create(user_id=user_instance, 
                                                            building_id = code_instance.building_id,
                                                            access_code_id = code_instance,
                                                            nickname = nickname,
                                                            flat_no = code_instance.flat_no,
                                                            authorized = True,
                                                            distance = member_distance,
                                                            type = code_instance.type,
                                                            is_active = True,
                                                            created_by = user_instance 
                                                            )
                                # update invitation record for invitee user id
                                if code_instance.type == '1':
                                    invitation_instance.invitee_member_id = member
                                    invitation_instance.modified_by = request.user
                                    invitation_instance.save()

                        except Exception as e:        
                            # creation of transaction failed
                            logger.exception("Error creating new member: %s", e)
                            messages.error(request, "Error: Member cannot be created! <br>Please try later again.", extra_tags="popup")
                            return redirect('index')

                    # mark access_code as used
                    code_instance.is_used = True
                    code_instance.modified_by = request.user 
                    code_instance.save()
                else:
                    # access code is not valid
                    messages.error(request, "Code has already been used!", extra_tags="popup")
                    return redirect('index')                
            except Access_Code.DoesNotExist:
                # access code is not valid
                messages.error(request, "Code is not valid", extra_tags="popup")
                return redirect('index')
        # Form: Invitation
        elif form_type == 'modalInvitation':
            selectedRelationship = request.POST.get('relationship')
            # get member instance of invitor
            member = Member.objects.get(user_id=user_instance)

            # get AppSettings for invitation distance
            application_distance = AppSettings.objects.get(building_id=member.building_id, key='0')
            if member.distance >= int(application_distance.value):
                messages.error(request, "Error: Invitation distance is reached! <br>You cannot invite further members!", extra_tags="popup")
                return redirect('index')                

            # get new unique access code
            invitation_code = generate_unique_access_code()
            # Database transaction for access_code and invitation records
            try:
                with transaction.atomic():
                    # create an access_code record
                    access_code = Access_Code.objects.create(building_id = member.building_id,
                                                            flat_no = 'external',
                                                            code = invitation_code,
                                                            type = '1',
                                                            is_used = False,
                                                            created_by = user_instance
                    )
                    # create an invitation record
                    invitation = Invitation.objects.create(building_id = member.building_id,
                                                           invitor_member_id = member,
                                                           access_code_id = access_code,
                                                           distance = member.distance,
                                                           relationship = selectedRelationship,
                                                           created_by = user_instance
                    )
            except Exception as e:        
                # access code is not valid
                logger.exception("Error creating invitation: %s", e)
                messages.error(request, "Error: Invitation cannot be created! <br>Please try later again.", extra_tags="popup")
                return redirect('index')

            messages.error(request, f"Invitation code:  {invitation_code} <br>Invitation Code will be stored in your Inbox.", extra_tags="popup")
            return redirect('index')

        elif form_type == 'modalBuilding':
            # Get building fields from the POST data
            building_id = request.POST.get('building_id')
            name = request.POST.get('name')
            address_line1 = request.POST.get('address_line1')
            address_line2 = request.POST.get('address_line2')
            city = request.POST.get('city')
            postal_code = request.POST.get('postal_code')
            units = request.POST.get('units')
            try:
                units = int(units) if units else None
            except ValueError:
                units = None

            # If a building_id exists, update the existing Building
            # otherwise create new building
            if building_id:
                try:
                    building = Building.objects.get(pk=building_id)
                    building.name = name
                    building.address_line1 = address_line1
                    building.address_line2 = address_line2
                    building.city = city
                    building.postal_code = postal_code
                    building.units = units
                    building.modified_by = request.user  # track modification
                    building.save()
                    messages.success(request, "Building updated successfully!", extra_tags="popup")
                except Building.DoesNotExist:
                    messages.error(request, "Building not found!", extra_tags="popup")
            else:
                try:
                    with transaction.atomic():
                        Building.objects.create(
                            name=name,
                            address_line1=address_line1,
                            address_line2=address_line2,
                            city=city,
                            postal_code=postal_code,
                            units=units,
                            created_by=user_instance,  # created timestamp is auto-handled
                        )
                    messages.success(request, "New building created successfully!", extra_tags="popup")
                except Exception as e:
                    messages.error(request, "Error saving new building. Please try again later.", extra_tags="popup")
                    logger.exception("Error saving building: %s", e)
                    return redirect('index')
            return redirect('index')


    # check if user is authotized
    form1 = MyForm(prefix="form1")
    form2 = MyForm(prefix="form2")

    result = Access_Code.custom_objects.get_member_authorized(user_id=user_id)
    is_authorized = result[0][0]
    context = {
        'is_authorized': is_authorized,
        'form1': form1, 
        'form2': form2
    }    
    return render(request, 'neighborow/index.html', context)

@login_required
def app_settings(request):
    if request.method == 'POST':
        building_id = request.POST.get('building_id')
        if not building_id:
            messages.error(request, "Please select a building!", extra_tags="popup")
            return redirect('index')
        try:
            building = Building.objects.get(pk=building_id)
        except Building.DoesNotExist:
            messages.error(request, "Building not found!", extra_tags="popup")
            return redirect('index')
        
        # update existing settings
        index = 1
        while True:
            setting_id = request.POST.get(f"setting_id_{index}")
            key = request.POST.get(f"key_{index}")
            value = request.POST.get(f"value_{index}")
            if setting_id is None:
                break
            try:
                app_setting = AppSettings.objects.get(pk=setting_id)
                app_setting.key = key
                app_setting.value = value
                app_setting.modified_by = request.user
                app_setting.save()
            except AppSettings.DoesNotExist:
                pass
            index += 1
        
        # create new setting
        for i in range(1, 6):
            new_key = request.POST.get(f"new_key_{i}")
            new_value = request.POST.get(f"new_value_{i}")
            if new_key and new_value:
                AppSettings.objects.create(
                    building_id=building,
                    key=new_key,
                    value=new_value,
                    created_by=request.user
                )
        messages.success(request, "Application Settings saved successfully!", extra_tags="popup")
        return redirect('index')
    else:
        building_id = request.GET.get('building_id')
        buildings = Building.objects.all()
        if not building_id and buildings.exists():
            # If no building ID was provided, the first building is selected automatically.
            building = buildings.first()
            building_id = building.id
            app_settings_qs = AppSettings.objects.filter(building_id=building)
        elif building_id:
            try:
                building = Building.objects.get(pk=building_id)
                app_settings_qs = AppSettings.objects.filter(building_id=building)
            except Building.DoesNotExist:
                app_settings_qs = None
        else:
            app_settings_qs = None

        context = {
            'buildings': buildings,
            'app_settings': app_settings_qs,
            'application_settings_choices': AppSettings._meta.get_field('key').choices,
        }
        return render(request, 'neighborow/modals/app_settings.html', context)

@login_required
def get_app_settings(request):
    building_id = request.GET.get('building_id')
    if building_id:
        try:
            building = Building.objects.get(pk=building_id)
            settings_qs = AppSettings.objects.filter(building_id=building)
            settings_list = [{"id": s.id, "key": s.key, "value": s.value} for s in settings_qs]
            return JsonResponse({"settings": settings_list})
        except Building.DoesNotExist:
            return JsonResponse({"error": "Gebäude nicht gefunden"}, status=404)
    else:
        return JsonResponse({"error": "Keine Gebäude-ID angegeben"}, status=400)

@login_required
def form_invitation(request):
    context = {
        'relationship_choices': Relationship.choices
    }  
    return render(request, 'neighborow/modals/form_invitation.html', context)

@login_required
def form_building(request):
    # Check if a building_id is provided via GET (for updating an existing building)
    building_id = request.GET.get('building_id')
    building = None
    if building_id:
        try:
            building = Building.objects.get(pk=building_id)
        except Building.DoesNotExist:
            building = None  
    # Retrieve all buildings to populate the dropdown
    buildings = Building.objects.all()

    context = {
        'buildings': buildings,
        'building': building, 
    }
    return render(request, 'neighborow/modals/buildings.html', context)

@login_required
def get_building_details(request):
    # Get the building_id from the GET parameters
    building_id = request.GET.get('building_id')
    if building_id:
        try:
            building = Building.objects.get(pk=building_id)
            data = {
                'name': building.name,
                'address_line1': building.address_line1 or '',
                'address_line2': building.address_line2 or '',
                'city': building.city or '',
                'postal_code': building.postal_code or '',
                'units': building.units or '',
            }
            return JsonResponse(data)
        except Building.DoesNotExist:
            return JsonResponse({'error': 'Building not found'}, status=404)
    else:
        return JsonResponse({'error': 'No building id provided'}, status=400)

# view access codes
@login_required
def access_code(request):
    if request.method == 'POST':
        building_id = request.POST.get('building_id')
        if not building_id:
            messages.error(request, "Please select a building.", extra_tags="popup")
            return redirect('index')
        try:
            building = Building.objects.get(pk=building_id)
        except Building.DoesNotExist:
            messages.error(request, "Building not found.", extra_tags="popup")
            return redirect('index')
        
        # Update existing Access Codes
        index = 1
        while True:
            ac_id = request.POST.get(f"access_code_id_{index}")
            flat_no = request.POST.get(f"flat_no_{index}")
            code = request.POST.get(f"code_{index}")
            if ac_id is None:
                break
            try:
                ac_obj = Access_Code.objects.get(pk=ac_id)
                ac_obj.flat_no = flat_no
                ac_obj.code = code
                ac_obj.is_used = False
                ac_obj.modified_by = request.user
                ac_obj.save()
            except Access_Code.DoesNotExist:
                pass
            index += 1
        
        # Process new static rows (10 rows with names new_flat_no_X and new_code_X)
        for i in range(1, 11):
            new_flat = request.POST.get(f"new_flat_no_{i}")
            new_code = request.POST.get(f"new_code_{i}")
            # If any field is filled, treat the row as intended to be saved
            if new_flat or new_code:
                if not new_flat:
                    messages.error(request, "Flat Number is mandatory for new codes.", extra_tags="popup")
                    return redirect('index')
                if new_flat and new_code:
                    Access_Code.objects.create(
                        building_id=building,
                        flat_no=new_flat,
                        code=new_code,
                        type=MemberType.RESIDENT,  # Always default RESIDENT
                        is_used=False,
                        created_by=request.user
                    )
        
        # Process new generated rows (appended dynamically, with names as arrays)
        new_flats = request.POST.getlist("new_flat_no_generated[]")
        new_codes = request.POST.getlist("new_code_generated[]")
        for new_flat, new_code in zip(new_flats, new_codes):
            if new_flat or new_code:
                if not new_flat:
                    messages.error(request, "Flat Number is mandatory for new codes.", extra_tags="popup")
                    return redirect('index')
                if new_flat and new_code:
                    Access_Code.objects.create(
                        building_id=building,
                        flat_no=new_flat,
                        code=new_code,
                        type=MemberType.RESIDENT,  # Always default RESIDENT
                        created_by=request.user
                    )
        
        messages.success(request, "Access Codes saved successfully!", extra_tags="popup")
        return redirect('index')
    else:
        building_id = request.GET.get('building_id')
        buildings = Building.objects.all()
        if not building_id and buildings.exists():
            building = buildings.first()
            building_id = building.id
            access_codes_qs = Access_Code.objects.filter(
                            building_id=building, 
                            type=MemberType.RESIDENT
                            ).order_by('flat_no')
        elif building_id:
            try:
                building = Building.objects.get(pk=building_id)
                access_codes_qs = Access_Code.objects.filter(
                                building_id=building, 
                                type=MemberType.RESIDENT
                                ).order_by('flat_no')
            except Building.DoesNotExist:
                access_codes_qs = None
        else:
            access_codes_qs = None

        context = {
            'buildings': buildings,
            'access_codes': access_codes_qs,
        }
        return render(request, 'neighborow/modals/access_code.html', context)

# View for access codes
@login_required
def get_access_codes(request):
    building_id = request.GET.get('building_id')
    if building_id:
        try:
            building = Building.objects.get(pk=building_id)
            codes_qs = Access_Code.objects.filter(
                        building_id=building, 
                        type=MemberType.RESIDENT
                        ).order_by('flat_no')
            codes_list = [{"id": ac.id, "flat_no": ac.flat_no, "code": ac.code} for ac in codes_qs]
            return JsonResponse({"access_codes": codes_list})
        except Building.DoesNotExist:
            return JsonResponse({"error": "Building not found"}, status=404)
    else:
        return JsonResponse({"error": "No building id provided"}, status=400)

@login_required
def generate_code(request):
    # Return a JSON response with a single unique access code
    code = generate_unique_access_code()
    return JsonResponse({'code': code})

@login_required
def generate_codes(request):
    # Return a JSON response with a list of unique access codes
    try:
        count = int(request.GET.get('count', 1))
    except ValueError:
        count = 1
    # Ensure count is non-negative
    if count < 0:
        count = 0
    codes = [generate_unique_access_code() for _ in range(count)]
    return JsonResponse({'codes': codes})


@login_required
def widget_borrowing(request):

    if request.method == 'POST':
        # get users timezone
        #user_tz = request.POST.get('userTimeZone', 'UTC')
        #user_tz = pytz.timezone(user_tz)

        # read IDs from selected recipients and checkbox
        selected_recipients = request.POST.get('selectedRecipients')
        all_recipients = request.POST.get('allNeighbours', 'off')
        # when no recipient has been selected, send message
        if selected_recipients == '' and all_recipients == 'off':
            messages.error(request, "Please select a recipient!", extra_tags="popup")
            return ajax_or_render(request, 'neighborow/popup_modal.html', 'neighborow/index.html')

        # get required-timestamps and convert to timezone and set NULL if empty (DB default)
        required_from_str = request.POST.get('requiredFrom', '')
        if required_from_str:
            required_from = datetime.datetime.strptime(required_from_str, '%Y-%m-%dT%H:%M')
            #required_from = timezone.make_aware(required_from, user_tz)
            #required_from = required_from.astimezone(datetime.timezone.utc)  
        else:
            required_from = None

        required_until_str = request.POST.get('requiredUntil', '')
        if required_until_str:
            required_until = datetime.datetime.strptime(required_until_str, '%Y-%m-%dT%H:%M')
            #required_until = timezone.make_aware(required_until, user_tz)
            #required_until = required_until.astimezone(datetime.timezone.utc)
        else:
            required_until = None

        # get the logged in user instance
        user_instance = User.objects.get(username=request.user)
        # get the logged in member
        member = Member.objects.get(user_id=user_instance)

        # load recipients in comma seperated list (same as selected members)
        if all_recipients == 'on':
            # get all members of the same building
            member_list = Member.objects.filter(building_id=member.building_id)

        # create records in table Borrowing_Request_Recipients and Borrowing_Request
        # Database transaction for access_code and invitation records
        try:
            with transaction.atomic():
                borrowing_request = Borrowing_Request.objects.create(member_id=member,
                                                        title = request.POST.get('subject'),
                                                        body = request.POST.get('messageBody'),
                                                        required_from = required_from,
                                                        required_until = required_until,
                                                        created_by = user_instance  
                                                        )              

                if all_recipients == 'on':
                    for member in member_list:
                        recipient = Borrowing_Request_Recipients(
                            member_id=member,
                            borrowing_request=borrowing_request,
                            created_by=user_instance
                        )
                        recipient.save()
                else:
                    if selected_recipients:
                        for recipient_id in selected_recipients.split(','):
                            recipient = Borrowing_Request_Recipients(
                                member_id_id=int(recipient_id),
                                borrowing_request=borrowing_request,
                                created_by=user_instance
                            )
                            recipient.save()

                
        except Exception as e:        
            # DB transcation failed
            logger.exception("Error creating borrowing request: %s", e)
            messages.success(request, "Error: Borrowning request cannot be created! Please try later again.", extra_tags="popup")

        # Message if request was successfully stored in DB:
        messages.success(request, "The borrowing Request has been sent successfully!", extra_tags="popup")
        
        # For AJAX-requests return HTML-Code for popup
        return ajax_or_render(request, 'neighborow/popup_modal.html', 'neighborow/index.html')
        # if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        #     html = render_to_string('neighborow/popup_modal.html', request=request)
        #     return JsonResponse({'html': html})
        # else:
        #     return render(request, 'neighborow/index.html')
    else:
        return render(request, 'neighborow/widgets/borrowing_request.html')


@login_required
def select_recipients(request):
    # get the logged in user instance
    user_instance = User.objects.get(username=request.user)
    # get the logged in member
    member = Member.objects.get(user_id=user_instance)
    # get all members of the same building
    member_list = Member.objects.filter(building_id=member.building_id).values('id','flat_no', 'nickname')      
    context = {
        'member_list': member_list
    }
    return render(request, 'neighborow/modals/select_recipients.html', context)


@login_required
def widget_member_info(request):
    # Get the logged in user and associated member record
    user_instance = request.user
    try:
        member = Member.objects.get(user_id=user_instance)
    except Member.DoesNotExist:
        messages.error(request, "Member record not found.", extra_tags="popup")
        return ajax_or_render(request, 'neighborow/popup_modal.html', 'neighborow/index.html')
    
    if request.method == 'POST':
        new_nickname = request.POST.get('nickname')
        if new_nickname:
            try:
                with transaction.atomic():
                    member.nickname = new_nickname
                    member.modified_by = user_instance
                    member.save()
                messages.success(request, "Nickname updated successfully!", extra_tags="popup")
                return ajax_or_render(request, 'neighborow/popup_modal.html', 'neighborow/index.html')
            except Exception as e:
                messages.error(request, "Error updating nickname.", extra_tags="popup")
                return ajax_or_render(request, 'neighborow/popup_modal.html', 'neighborow/index.html')
        else:
            messages.error(request, "No nickname provided.", extra_tags="popup")
            return ajax_or_render(request, 'neighborow/popup_modal.html', 'neighborow/index.html')
    else:
        # GET: prepare context data for the widget
        building = member.building_id
        communications = Communication.objects.filter(member_id=member)
        borrowing_requests_count = Borrowing_Request.objects.filter(member_id=member).count()
        invitation = None
        # For invitee members, try to load invitation details to get invitor information
        if member.type == '1':
            try:
                invitation = Invitation.objects.get(invitee_member_id=member)
            except Invitation.DoesNotExist:
                invitation = None

        context = {
            'member': member,
            'building': building,
            'communications': communications,
            'borrowing_requests_count': borrowing_requests_count,
            'invitation': invitation,
        }
        return render(request, 'neighborow/widgets/member_info.html', context)


# Communication widget view
@login_required
def widget_member_communication(request):

    user_instance = request.user
    try:
        member = Member.objects.get(user_id=user_instance)
    except Member.DoesNotExist:
        messages.error(request, "Member record not found.", extra_tags="popup")
        return render(request, 'neighborow/popup_modal.html')
    
    if request.method == 'POST':
        try:
            total_rows = int(request.POST.get('row_counter', 0))
        except ValueError:
            total_rows = 0
        error_found = False
        errors = []
        
        for i in range(1, total_rows + 1):
            # Check if row is marked for deletion
            delete_val = request.POST.get(f'delete_{i}', '0')
            if delete_val == "1":
                comm_id = request.POST.get(f'comm_id_{i}', None)
                if comm_id:
                    try:
                        comm = Communication.objects.get(pk=comm_id, member_id=member)
                        comm.delete()
                    except Communication.DoesNotExist:
                        pass
                continue
            
            channel = request.POST.get(f'channel_{i}', '').strip()
            identification = request.POST.get(f'identification_{i}', '').strip()
            
            # If channel is built-in ("0"), skip processing to preserve the default record
            if channel == "0":
                continue
            
            if not channel or not identification:
                error_found = True
                errors.append(f"Row {i}: Channel and Identification are mandatory.")
                continue
            
            if channel == "1":  # Email validation
                email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
                if not re.match(email_regex, identification):
                    error_found = True
                    errors.append(f"Row {i}: Invalid email address.")
                    continue
            elif channel == "2":  # Phone number validation
                phone_regex = r'^\+?\d{7,15}$'
                if not re.match(phone_regex, identification):
                    error_found = True
                    errors.append(f"Row {i}: Invalid phone number.")
                    continue
            
            is_active = request.POST.get(f'is_active_{i}', 'off') == 'on'
            comm_id = request.POST.get(f'comm_id_{i}', None)
            if comm_id:
                try:
                    comm = Communication.objects.get(pk=comm_id, member_id=member)
                    comm.channel = channel
                    comm.identification = identification
                    comm.is_active = is_active
                    comm.modified_by = user_instance
                    comm.save()
                except Communication.DoesNotExist:
                    Communication.objects.create(
                        member_id=member,
                        channel=channel,
                        identification=identification,
                        is_active=is_active,
                        created_by=user_instance
                    )
            else:
                Communication.objects.create(
                    member_id=member,
                    channel=channel,
                    identification=identification,
                    is_active=is_active,
                    created_by=user_instance
                )
        
        if error_found:
            messages.error(request, "<br>".join(errors), extra_tags="popup")
        else:
            messages.success(request, "Communications saved successfully!", extra_tags="popup")
        
        html = render_to_string('neighborow/popup_modal.html', request=request)
        return JsonResponse({'html': html})
    
    else:
        communications = Communication.objects.filter(member_id=member)
        # Pass channel choices (including built-in) so that existing records can be rendered.
        channel_choices = Communication._meta.get_field('channel').choices
        context = {
            'communications': communications,
            'channel_choices': channel_choices,
        }
        return render(request, 'neighborow/widgets/member_communication.html', context)
    
@login_required
def widget_messages_inbox(request):
    user_instance = request.user
    try:
        member = Member.objects.get(user_id=user_instance)
    except Member.DoesNotExist:
        messages.error(request, "Member record not found.", extra_tags="popup")
        return render(request, 'neighborow/popup_modal.html')
    
    # Get the requested page number, default to 1
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    messages_per_page = 10
    
    # Filter messages where the receiver is the current member and inbox is True
    qs = Messages.objects.filter(
                                Q(receiver_member_id=member),
                                (Q(inbox=True) | Q(internal=True))
                                ).order_by('-created')
    paginator = Paginator(qs, messages_per_page)
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = []
    
    context = {
        'messages': page_obj,
        'page': page,
        'has_next': page_obj.has_next() if page_obj else False,
    }
    
    # If the request is AJAX, return only the new rows (for paging)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('neighborow/partials/message_list_rows.html', context, request=request)
        return JsonResponse({'html': html, 'has_next': context['has_next'], 'next_page': page + 1})
    else:
        # Render the full widget for the initial load
        return render(request, 'neighborow/widgets/messaging_inbox.html', context)
    

# send reply messages
@login_required
def send_reply(request):
    if request.method == 'POST':
        widget_origin = request.POST.get("widget_origin")
        try:
            original_sender_id = int(request.POST.get('replySenderId'))
            original_receiver_id = int(request.POST.get('replyReceiverId'))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid sender/receiver ID'}, status=400)
        title = request.POST.get('replyTitle')
        body = request.POST.get('replyText')
        message_code = request.POST.get('replyMessageCode')
        if not message_code:
            message_code = generate_unique_message_code()
        print("message_code", message_code) 
        # Swap sender and receiver
        #if widget_origin == "itemlist":
        sender_id = original_receiver_id
        receiver_id = original_sender_id

        try:
            sender_member = Member.objects.get(id=sender_id)
            receiver_member = Member.objects.get(id=receiver_id)
        except Member.DoesNotExist:
            return JsonResponse({'error': 'Member not found'}, status=404)

        # Create new message with the required settings
        new_message = Messages.objects.create(
            sender_member_id=sender_member,
            receiver_member_id=receiver_member,
            title=title,
            body=body,
            message_code=message_code,
            inbox=False,
            outbox=True,
            internal=False,
            is_sent_email=False,
            is_sent_sms=False,
            is_sent_whatsApp =False,
            message_type=MessageType.REPLY_INBOX.value,
            created_by=request.user
        )

        new_message = Messages.objects.create(
            sender_member_id=sender_member,
            receiver_member_id=receiver_member,
            title=title,
            body=body,
            message_code=message_code,
            inbox=True,
            outbox=False,
            internal=False,
            is_sent_email=True,
            is_sent_sms=True,
            is_sent_whatsApp =True,
            message_type=MessageType.REPLY_INBOX.value,
            created_by=request.user
        )

        return JsonResponse({'success': 'Reply sent successfully!'})
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def widget_messages_outbox(request):
    user_instance = request.user
    try:
        member = Member.objects.get(user_id=user_instance)
    except Member.DoesNotExist:
        messages.error(request, "Member record not found.", extra_tags="popup")
        return render(request, 'neighborow/popup_modal.html')
    
    # Get the requested page number, default to 1
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    messages_per_page = 10
    
    # Filter messages where the sender is the current member and outbox is True
    qs = Messages.objects.filter(
            Q(sender_member_id=member),
            Q(outbox=True)
          ).order_by('-created')
    paginator = Paginator(qs, messages_per_page)
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = []
    
    context = {
        'messages': page_obj,
        'page': page,
        'has_next': page_obj.has_next() if page_obj else False,
    }
    
    # For AJAX: return only the new rows (partial template), else render full widget
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('neighborow/partials/message_list_rows_outbox.html', context, request=request)
        return JsonResponse({'html': html, 'has_next': context['has_next'], 'next_page': page + 1})
    else:
        return render(request, 'neighborow/widgets/messaging_outbox.html', context)
    


@login_required
def widget_send_message(request):
    if request.method == 'POST':
        selected_recipients = request.POST.get('selectedRecipients', '')
        all_recipients = request.POST.get('allNeighbours', 'off')
        if selected_recipients == '' and all_recipients == 'off':
            messages.error(request, "Please select a recipient!", extra_tags="popup")
            html = render_to_string('neighborow/popup_modal.html', request=request)
            return JsonResponse({'html': html})
        
        subject = request.POST.get('subject')
        message_body = request.POST.get('messageBody')
        
        # Get logged in user and corresponding member
        user_instance = User.objects.get(username=request.user)
        member = Member.objects.get(user_id=user_instance)
        
        if all_recipients == 'on':
            recipient_list = Member.objects.filter(building_id=member.building_id)
        else:
            recipient_ids = [int(rid) for rid in selected_recipients.split(',') if rid.strip()]
            recipient_list = Member.objects.filter(id__in=recipient_ids)
        
        try:
            with transaction.atomic():
                for recipient in recipient_list:
                    message_code = generate_unique_message_code()
                    # Message for sender
                    Messages.objects.create(
                        sender_member_id=member,
                        receiver_member_id=recipient,
                        title=subject,
                        body=message_body,
                        message_code=message_code,
                        inbox=False,
                        outbox=True,
                        internal=False,
                        is_sent_email=False,
                        is_sent_sms=False,
                        is_sent_whatsApp=False,
                        message_type=MessageType.FREE_MESSAGE.value,
                        created_by=user_instance
                    )
                    # Message for receiver
                    Messages.objects.create(
                        sender_member_id=member,
                        receiver_member_id=recipient,
                        title=subject,
                        body=message_body,
                        message_code=message_code,
                        inbox=True,
                        outbox=False,
                        internal=False,
                        is_sent_email=True,
                        is_sent_sms=True,
                        is_sent_whatsApp=True,
                        message_type=MessageType.FREE_MESSAGE.value,
                        created_by=user_instance
                    )
        except Exception as e:
            logger.exception("Error sending message: %s", e)
            messages.error(request, "Error: Message cannot be sent! Please try again later.", extra_tags="popup")
            html = render_to_string('neighborow/popup_modal.html', request=request)
            return JsonResponse({'html': html})
        
        messages.success(request, "Message sent successfully!", extra_tags="popup")
        html = render_to_string('neighborow/popup_modal.html', request=request)
        return JsonResponse({'html': html})
    else:
        return render(request, 'neighborow/widgets/send_message.html')
    
# widgte items for loan
@login_required
def widget_item_list(request):
    query = request.GET.get('q', '').strip()
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        page = 1

    user_instance = request.user
    member = Member.objects.get(user_id=user_instance)
    
    if query:
        items_list = Items_For_Loan.custom_objects.get_filtered_items_for_loan(member.id, query)
    else:
        items_list = Items_For_Loan.custom_objects.get_items_for_loan(member.id)
    
    paginator = Paginator(items_list, 10)
    try:
        items_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        items_page = []

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'q' in request.GET or 'page' in request.GET:
        html = render_to_string('neighborow/partials/item_list_rows.html', {'items': items_page, 'member': member}, request=request)
        return JsonResponse({
            'html': html, 
            'has_next': items_page.has_next() if items_page else False,
            'next_page': page + 1
        })
    else:
        return render(request, 'neighborow/widgets/items_for_loan.html', {
            'items': items_page,
            'member': member,
            'has_next': items_page.has_next() if items_page else False,
            'next_page': page + 1
        })
    


    
# rply-modal html 
@login_required
def reply_modal(request):
    # the reply modal from its separate HTML file
    return render(request, 'neighborow/modals/reply_modal.html')

# widget ietm manager: add, update, delete
@login_required
def widget_item_manager(request):
    user_instance = request.user
    member = Member.objects.get(user_id=user_instance)
    items_qs = Items_For_Loan.objects.filter(member_id=member, is_deleted=False).order_by('-created')
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        page = 1
    paginator = Paginator(items_qs, 10)
    try:
        items_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        items_page = paginator.page(1)
    # If AJAX request or page parameter present, return only the table rows as a partial
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'page' in request.GET:
         html = render_to_string('neighborow/partials/item_manager_rows.html', {'items': items_page, 'member': member}, request=request)
         return JsonResponse({
             'html': html,
             'has_next': items_page.has_next(),
             'next_page': page + 1
         })
    else:
         context = {
             'items': items_page,
             'member': member,
             'has_next': items_page.has_next(),
             'next_page': page + 1
         }
         return render(request, 'neighborow/widgets/item_manager.html', context)

# get item images for item manger
@login_required
def get_item_images(request, item_id):
    try:
        # Retrieve the item
        item = Items_For_Loan.objects.get(id=item_id)
        # Retrieve all images for the item
        images_qs = Items_For_Loan_Image.objects.filter(items_for_loan_id=item_id)
        images_list = [{"id": image.id, "url": image.image.url, "caption": image.caption} for image in images_qs]
        return JsonResponse({
            "success": True,
            "label": item.label,
            "description": item.description,
            "images": images_list
        })
    except Items_For_Loan.DoesNotExist:
        messages.error(request, "Item not found", extra_tags="popup")
        html = render_to_string('neighborow/popup_modal.html', request=request)
        return JsonResponse({"success": False, "html": html, "images": []}, status=200)


# update item in item manger
@login_required
def update_item(request, item_id):

    if request.method == 'POST':
        user_instance = request.user
        member = Member.objects.get(user_id=user_instance)
        try:
            item = Items_For_Loan.objects.get(id=item_id, member_id=member, is_deleted=False)
        except Items_For_Loan.DoesNotExist:
            messages.error(request, "Item not found or not authorized", extra_tags="popup")
            html = render_to_string('neighborow/popup_modal.html', request=request)
            return JsonResponse({'success': False, 'html': html}, status=200)
        item.label = request.POST.get('label', item.label)
        item.description = request.POST.get('description', item.description)
        available_from_str = request.POST.get('available_from', '')
        if available_from_str:
            try:
                # Expecting format "YYYY-MM-DDTHH:MM"
                item.available_from = datetime.datetime.strptime(available_from_str, '%Y-%m-%dT%H:%M')
            except Exception as e:
                pass
        item.available = request.POST.get('available') == 'on'
        item.currently_borrowed = request.POST.get('currently_borrowed') == 'on'
        item.modified_by = user_instance
        item.save()
        messages.success(request, "Item updated successfully!", extra_tags="popup")
        html = render_to_string('neighborow/popup_modal.html', request=request)
        return JsonResponse({'success': True, 'html': html}, status=200)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


# delete item in widget item manger
@login_required
def delete_item(request, item_id):
    if request.method == 'POST':
        user_instance = request.user
        member = Member.objects.get(user_id=user_instance)
        try:
            item = Items_For_Loan.objects.get(id=item_id, member_id=member, is_deleted=False)
        except Items_For_Loan.DoesNotExist:
            messages.error(request, "Item not found or already deleted", extra_tags="popup")
            html = render_to_string('neighborow/popup_modal.html', request=request)
            return JsonResponse({'success': False, 'html': html}, status=200)
        item.is_deleted = True
        item.modified_by = user_instance
        item.save()
        messages.success(request, "Item deleted successfully!", extra_tags="popup")
        html = render_to_string('neighborow/popup_modal.html', request=request)
        return JsonResponse({'success': True, 'html': html}, status=200)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


# upload new image in item manegr
@login_required
def upload_item_image(request, item_id):

    if request.method == 'POST':
        user_instance = request.user
        member = Member.objects.get(user_id=user_instance)
        try:
            item = Items_For_Loan.objects.get(id=item_id, member_id=member, is_deleted=False)
        except Items_For_Loan.DoesNotExist:
            messages.error(request, "Item not found or not authorized", extra_tags="popup")
            html = render_to_string('neighborow/popup_modal.html', request=request)
            return JsonResponse({'success': False, 'html': html}, status=200)
        
        files = request.FILES.getlist('image')
        caption = request.POST.get('caption', '')
        uploaded_images = []
        if files:
            for image_file in files:
                new_image = Items_For_Loan_Image.objects.create(
                    items_for_loan_id=item,
                    image=image_file,
                    caption=caption
                )
                uploaded_images.append({
                    'image_id': new_image.id,
                    'image_url': new_image.image.url,
                    'caption': new_image.caption
                })
            messages.success(request, "Images uploaded successfully!", extra_tags="popup")
            html = render_to_string('neighborow/popup_modal.html', request=request)
            return JsonResponse({'success': True, 'html': html, 'images': uploaded_images}, status=200)
        else:
            messages.error(request, "No images provided", extra_tags="popup")
            html = render_to_string('neighborow/popup_modal.html', request=request)
            return JsonResponse({'success': False, 'html': html}, status=200)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


# delete item in item manager
@login_required
def delete_item_image(request, image_id):

    if request.method == 'POST':
        user_instance = request.user
        try:
            image_obj = Items_For_Loan_Image.objects.get(id=image_id)
            # Check that the image belongs to an item owned by the logged-in user.
            if image_obj.items_for_loan_id.member_id.user_id != request.user:
                messages.error(request, "Not authorized", extra_tags="popup")
                html = render_to_string('neighborow/popup_modal.html', request=request)
                return JsonResponse({'success': False, 'html': html}, status=200)
            image_obj.delete()
            messages.success(request, "Image deleted successfully!", extra_tags="popup")
            html = render_to_string('neighborow/popup_modal.html', request=request)
            return JsonResponse({'success': True, 'html': html}, status=200)
        except Items_For_Loan_Image.DoesNotExist:
            messages.error(request, "Image not found", extra_tags="popup")
            html = render_to_string('neighborow/popup_modal.html', request=request)
            return JsonResponse({'success': False, 'html': html}, status=200)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


# update image caption in itzem manager
@login_required
def update_item_image_caption(request, item_id):

    if request.method == 'POST':
        user_instance = request.user
        try:
            image_obj = Items_For_Loan_Image.objects.get(id=item_id)
            # Ensure the image belongs to an item owned by the logged-in user.
            if image_obj.items_for_loan_id.member_id.user_id != request.user:
                messages.error(request, "Not authorized", extra_tags="popup")
                html = render_to_string('neighborow/popup_modal.html', request=request)
                return JsonResponse({'success': False, 'html': html}, status=200)
            new_caption = request.POST.get('caption', '')
            image_obj.caption = new_caption
            image_obj.save()
            messages.success(request, "Caption updated successfully!", extra_tags="popup")
            html = render_to_string('neighborow/popup_modal.html', request=request)
            return JsonResponse({'success': True, 'html': html}, status=200)
        except Items_For_Loan_Image.DoesNotExist:
            messages.error(request, "Image not found", extra_tags="popup")
            html = render_to_string('neighborow/popup_modal.html', request=request)
            return JsonResponse({'success': False, 'html': html}, status=200)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


# create new item
@login_required
def create_item(request):
    if request.method == 'POST':
        user_instance = request.user
        member = Member.objects.get(user_id=user_instance)
        label = request.POST.get('label')
        description = request.POST.get('description')
        available_from_str = request.POST.get('available_from', '')
        available_from = None
        if available_from_str:
            try:
                available_from = datetime.datetime.strptime(available_from_str, '%Y-%m-%dT%H:%M')
            except Exception as e:
                pass
        available = request.POST.get('available') == 'on'
        currently_borrowed = request.POST.get('currently_borrowed') == 'on'
        # Create new item without processing images
        new_item = Items_For_Loan.objects.create(
            member_id=member,
            label=label,
            description=description,
            available_from=available_from,
            available=available,
            currently_borrowed=currently_borrowed,
            created_by=user_instance
        )
        
        messages.success(request, "Item created successfully!", extra_tags="popup")
        html = render_to_string('neighborow/popup_modal.html', request=request)
        # Return the new item id so that JS can later use it for image uploads
        return JsonResponse({'success': True, 'html': html, 'item_id': new_item.id})
    return JsonResponse({'error': 'Invalid request method'}, status=405)



# borrow item button
@login_required
def borrow_item(request):

    if request.method == 'POST':
        try:
            item_id = request.POST.get('item_id')
            borrowed_on_str = request.POST.get('borrowed_on')
            borrowed_until_str = request.POST.get('borrowed_until')
            if not (item_id and borrowed_on_str and borrowed_until_str):
                messages.error(request, "Alle Felder sind Pflicht.", extra_tags="popup")
                html = render_to_string('neighborow/popup_modal.html', request=request)
                return JsonResponse({'html': html}, status=200)
            
            # Parse and make aware the requested dates
            borrowed_on = datetime.datetime.strptime(borrowed_on_str, '%Y-%m-%dT%H:%M')
            borrowed_until = datetime.datetime.strptime(borrowed_until_str, '%Y-%m-%dT%H:%M')
            #borrowed_on = timezone.make_aware(borrowed_on)
            #borrowed_until = timezone.make_aware(borrowed_until)

            item = Items_For_Loan.objects.get(id=item_id)
            lender = item.member_id
            borrower = Member.objects.get(user_id=request.user)

            # Check for overlapping transactions:
            existing_transactions = Transaction.objects.filter(items_for_loan_id=item, return_date__isnull=True)
            for trans in existing_transactions:
                # Effective end: use return_date if set, otherwise borrowed_until
                effective_end = trans.return_date if trans.return_date is not None else trans.borrowed_until
                # Overlap if: requested.start < existing.effective_end and existing.start < requested.end
                if borrowed_on < effective_end and trans.borrowed_on < borrowed_until:
                    messages.error(request, "Item is already borrowed in the requested period. Please check the calendar for availibility", extra_tags="popup")
                    html = render_to_string('neighborow/popup_modal.html', request=request)
                    return JsonResponse({'success': False, 'html': html}, status=200)

            # # Create dummy Condition_Log entries
            # default_condition_before = Condition_Log.objects.create(
            #     label="Default", description="Default condition before"
            # )
            # default_condition_after = Condition_Log.objects.create(
            #     label="Default", description="Default condition after"
            # )

            with transaction.atomic():
                Transaction.objects.create(
                    items_for_loan_id=item,
                    lender_member_id=lender,
                    borrower_member_id=borrower,
                    # before_condition=default_condition_before,
                    # after_condition=default_condition_after,
                    borrowed_on=borrowed_on,
                    borrowed_until=borrowed_until,
                    created_by=request.user
                )
                item.available_from = borrowed_until
                now_time = timezone.now()
                if borrowed_on <= now_time + datetime.timedelta(hours=2):
                    item.currently_borrowed = True
                item.modified_by = request.user
                item.save()

            messages.success(request, "Item borrowed successfully!", extra_tags="popup")
            html = render_to_string('neighborow/popup_modal.html', request=request)
            return JsonResponse({'success': True, 'html': html})
        except Items_For_Loan.DoesNotExist:
            messages.error(request, "Item nicht gefunden.", extra_tags="popup")
            html = render_to_string('neighborow/popup_modal.html', request=request)
            return JsonResponse({'success': False, 'html': html}, status=200)
        except Exception as e:
            messages.error(request, f"Error: {str(e)}", extra_tags="popup")
            html = render_to_string('neighborow/popup_modal.html', request=request)
            return JsonResponse({'success': False, 'html': html}, status=200)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


# calendar widget
@login_required
def widget_calendar(request, year=None, month=None):
    # Use current month if no parameters are provided
    if year is None or month is None:
        today = date.today()
        year = today.year
        month = today.month
    else:
        year = int(year)
        month = int(month)

    # Create a calendar structure (week starting from Sunday)
    cal = calendar.Calendar(firstweekday=0)
    month_days = list(cal.itermonthdays(year, month))
    
    # Fetch all transactions for the selected month that do NOT have a return_date set
    entries = Transaction.objects.filter(
        borrowed_on__year=year,
        borrowed_until__month=month,
        return_date__isnull=True
    )
    
    # Group transactions by day and compute a time range for each day
    entries_by_day = {}
    for entry in entries:
        start_date = entry.borrowed_on.date()
        end_date = entry.borrowed_until.date()
        current_day = start_date
        while current_day <= end_date:
            day_num = current_day.day  # (Only the day number; adjust if needed for month/year)
            if start_date == end_date:
                time_range = f"{entry.borrowed_on.strftime('%H:%M')} - {entry.borrowed_until.strftime('%H:%M')}"
            else:
                if current_day == start_date:
                    time_range = f"{entry.borrowed_on.strftime('%H:%M')} - 24:00"
                elif current_day == end_date:
                    time_range = f"00:00 - {entry.borrowed_until.strftime('%H:%M')}"
                else:
                    time_range = "00:00 - 24:00"
            entries_by_day.setdefault(day_num, []).append({
                'entry': entry,
                'time_range': time_range
            })
            current_day += timedelta(days=1)
    
    # Build the calendar structure as a list of weeks
    month_calendar = []
    week = []
    for day in month_days:
        if day == 0:
            week.append({'day': '', 'entries': []})
        else:
            week.append({'day': day, 'entries': entries_by_day.get(day, [])})
        if len(week) == 7:
            month_calendar.append(week)
            week = []
    if week:
        while len(week) < 7:
            week.append({'day': '', 'entries': []})
        month_calendar.append(week)

    context = {
        'month_calendar': month_calendar,
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
    }
    return render(request, 'neighborow/widgets/calendar.html', context)


# widget borrowed item: list
@login_required
def widget_borrowed_items(request):
    user_instance = request.user
    member = Member.objects.get(user_id=user_instance)
    show_history = request.GET.get('show_history', 'off') == 'on'

    if show_history:
        # If "Show History" is enabled: All transactions,
        # sorted by return_date descending (NULL values last)
        qs = Transaction.objects.filter(borrower_member_id=member) \
             .select_related('items_for_loan_id', 'lender_member_id') \
             .prefetch_related('items_for_loan_id__images') \
             .order_by('-return_date', '-borrowed_on')
    else:
        # If "Show History" is disabled: Only open transactions (return_date is NULL),
        # sorted by borrowed_until ascending
        qs = Transaction.objects.filter(borrower_member_id=member, return_date__isnull=True) \
             .select_related('items_for_loan_id', 'lender_member_id') \
             .prefetch_related('items_for_loan_id__images') \
             .order_by('borrowed_until', 'borrowed_on')

    borrowed_items_all = []
    for t in qs:
        images = list(t.items_for_loan_id.images.all())
        if images:
            image_url = images[0].image.url  
            image_caption = images[0].caption
        else:
            image_url = ""
            image_caption = ""
        borrowed_items_all.append({
            'transaction_id': t.id,
            'id': t.id,
            'borrowed_on': t.borrowed_on,
            'borrowed_until': t.borrowed_until,
            'return_date': t.return_date,
            'image_url': image_url,
            'image_caption': image_caption,
            'label': t.items_for_loan_id.label,
            'lender_member_nickname': t.lender_member_id.nickname,
            'lender_member_flat_no': t.lender_member_id.flat_no,
        })

    paginator = Paginator(borrowed_items_all, 10)
    total_count = paginator.count

    try:
        page_number = int(request.GET.get('page', '1'))
    except ValueError:
        page_number = 1

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if page_number > paginator.num_pages:
            html = ""
            has_next = False
            next_page = None
        else:
            borrowed_items = paginator.page(page_number)
            html = render_to_string('neighborow/partials/borrowed_items_rows.html',
                                    {'borrowed_items': borrowed_items, 'member': member},
                                    request=request)
            has_next = borrowed_items.has_next()
            next_page = borrowed_items.next_page_number() if has_next else None
        return JsonResponse({
            'html': html,
            'has_next': has_next,
            'next_page': next_page,
            'total_count': total_count
        })
    else:
        try:
            borrowed_items = paginator.page(page_number)
        except (EmptyPage, PageNotAnInteger):
            borrowed_items = paginator.page(1)
        return render(request, 'neighborow/widgets/borrowed_items.html', {
            'borrowed_items': borrowed_items,
            'member': member,
            'total_count': total_count
        })


# return item button (widget borrowed items)
@login_required
def return_item(request, transaction_id):
    user_instance = request.user
    try:
        transaction_obj = Transaction.objects.get(id=transaction_id)
    except Transaction.DoesNotExist:
        return JsonResponse({"error": "Transaction not found."}, status=404)
    # only the borrower can di this
    if transaction_obj.borrower_member_id.user_id != user_instance:
        return JsonResponse({"error": "Not authorized."}, status=403)
    if request.method == 'POST':
        transaction_obj.return_date = timezone.now()
        transaction_obj.modified_by = user_instance
        transaction_obj.save()
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"error": "Invalid request method."}, status=405)

# condition log widget
@login_required
def condition_log(request, transaction_id):
    user_instance = request.user
    try:
        transaction_obj = Transaction.objects.get(id=transaction_id)
    except Transaction.DoesNotExist:
        return JsonResponse({"error": "Transaction not found."}, status=404)
    
    # Determine log type: "before" or "after"
    log_type = request.GET.get("log_type") if request.method == "GET" else request.POST.get("log_type")
    if log_type not in ["before", "after"]:
        log_type = "before"
    
    if request.method == "GET":
        condition_log_obj = transaction_obj.before_condition if log_type == "before" else transaction_obj.after_condition
        if condition_log_obj:
            images_qs = Condition_Image.objects.filter(condition_log_id=condition_log_obj.id)
            images_data = [{
                "id": img.id,
                "url": img.image.url,
                "caption": img.caption,
                "created": img.created.strftime("%Y-%m-%d %H:%M"),
                "modified": img.modified.strftime("%Y-%m-%d %H:%M"),
                "created_by": img.created_by.username if img.created_by else "",
                "modified_by": img.modified_by.username if img.modified_by else ""
            } for img in images_qs]
            data = {
                "label": condition_log_obj.label,
                "description": condition_log_obj.description,
                "images": images_data,
                "condition_log_id": condition_log_obj.id,
                "created": condition_log_obj.created.strftime("%Y-%m-%d %H:%M"),
                "modified": condition_log_obj.modified.strftime("%Y-%m-%d %H:%M"),
                "created_by": condition_log_obj.created_by.username if condition_log_obj.created_by else "",
                "modified_by": condition_log_obj.modified_by.username if condition_log_obj.modified_by else ""
            }
        else:
            data = {
                "label": "",
                "description": "",
                "images": [],
                "condition_log_id": None,
                "created": "",
                "modified": "",
                "created_by": "",
                "modified_by": ""
            }
        return JsonResponse({"success": True, "data": data})
    
    elif request.method == "POST":
        label = request.POST.get("label", "")[:150]
        description = request.POST.get("description", "")[:2000]
        condition_log_obj = transaction_obj.before_condition if log_type == "before" else transaction_obj.after_condition
        if condition_log_obj:
            condition_log_obj.label = label
            condition_log_obj.description = description
            condition_log_obj.modified_by = user_instance  # Set modified_by on update
            condition_log_obj.save()
        else:
            condition_log_obj = Condition_Log.objects.create(
                label=label,
                description=description,
                created_by=user_instance  # Set created_by on creation
            )
            if log_type == "before":
                transaction_obj.before_condition = condition_log_obj
            else:
                transaction_obj.after_condition = condition_log_obj
            transaction_obj.modified_by = user_instance
            transaction_obj.save()
        
        # Process uploaded images; set created_by for each image
        image_caption = request.POST.get("caption", "")
        images = request.FILES.getlist("images")
        for img in images:
            Condition_Image.objects.create(
                condition_log_id=condition_log_obj,
                image=img,
                caption=image_caption,
                created_by=user_instance  # Set creator for new images
            )
        return JsonResponse({"success": True, "condition_log_id": condition_log_obj.id})
    
    else:
        return JsonResponse({"error": "Invalid request method."}, status=405)

@login_required
def widget_loaned_items(request):
    user_instance = request.user
    member = Member.objects.get(user_id=user_instance)
    show_history = request.GET.get('show_history', 'off') == 'on'
    
    if show_history:
        qs = Transaction.objects.filter(lender_member_id=member) \
             .select_related('items_for_loan_id', 'borrower_member_id') \
             .prefetch_related('items_for_loan_id__images') \
             .order_by('-return_date', '-borrowed_on')
    else:
        qs = Transaction.objects.filter(lender_member_id=member, return_date__isnull=True) \
             .select_related('items_for_loan_id', 'borrower_member_id') \
             .prefetch_related('items_for_loan_id__images') \
             .order_by('borrowed_until', 'borrowed_on')

    loaned_items_all = []
    for t in qs:
        images = list(t.items_for_loan_id.images.all())
        if images:
            image_url = images[0].image.url
            image_caption = images[0].caption
        else:
            image_url = ""
            image_caption = ""
        loaned_items_all.append({
            'transaction_id': t.id,
            'id': t.id,
            'borrowed_on': t.borrowed_on,
            'borrowed_until': t.borrowed_until,
            'return_date': t.return_date,
            'image_url': image_url,
            'image_caption': image_caption,
            'label': t.items_for_loan_id.label,
            'borrower_member_nickname': t.borrower_member_id.nickname,
            'borrower_member_flat_no': t.borrower_member_id.flat_no,
        })

    paginator = Paginator(loaned_items_all, 10)
    total_count = paginator.count
    try:
        page_number = int(request.GET.get('page', '1'))
    except ValueError:
        page_number = 1

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if page_number > paginator.num_pages:
            html = ""
            has_next = False
            next_page = None
        else:
            loaned_items = paginator.page(page_number)
            html = render_to_string('neighborow/partials/loaned_items_rows.html',
                                    {'loaned_items': loaned_items, 'member': member},
                                    request=request)
            has_next = loaned_items.has_next()
            next_page = loaned_items.next_page_number() if has_next else None
        return JsonResponse({
            'html': html,
            'has_next': has_next,
            'next_page': next_page,
            'total_count': total_count
        })
    else:
        try:
            loaned_items = paginator.page(page_number)
        except (EmptyPage, PageNotAnInteger):
            loaned_items = paginator.page(1)
        return render(request, 'neighborow/widgets/loaned_items.html', {
            'loaned_items': loaned_items,
            'member': member,
            'total_count': total_count
        })

# return item button for lender
@login_required
def return_item_loaned(request, transaction_id):
    user_instance = request.user
    try:
        transaction_obj = Transaction.objects.get(id=transaction_id)
    except Transaction.DoesNotExist:
        return JsonResponse({"error": "Transaction not found."}, status=404)
    # Only allow if the logged-in user is the lender for this transaction.
    if transaction_obj.lender_member_id.user_id != user_instance:
        return JsonResponse({"error": "Not authorized."}, status=403)
    if request.method == 'POST':
        transaction_obj.return_date = timezone.now()
        transaction_obj.modified_by = user_instance
        transaction_obj.save()
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"error": "Invalid request method."}, status=405)

