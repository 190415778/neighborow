import pytest 
import datetime
import re 
from django.db import IntegrityError 
from django.core.exceptions import ValidationError 
from django.core.files.uploadedfile import SimpleUploadedFile 
from django.contrib.auth.models import User 
from neighborow.models import ( Building, AppSettings, Access_Code, Member, 
        Invitation, Messages, Communication, 
        Borrowing_Request, Borrowing_Request_Recipients, 
        Items_For_Loan, Items_For_Loan_Image, Condition_Log, 
        Condition_Image, Transaction, ApplicationSettings, 
        MemberType, Relationship, MessageType, Channels, ReminderType )

#==================================================================================
# SIMPLE FIXTURES FOR ALL MODELS
#==================================================================================

@pytest.fixture 
def user(db): 
    return User.objects.create_user(username="user1", password="neighborow1")

@pytest.fixture 
def user2(db): 
    return User.objects.create_user(username="user2", password="neighborow2")

@pytest.fixture 
def user3(db): 
    return User.objects.create_user(username="user3", password="neighborow3")

@pytest.fixture 
def building(user, db): 
    return Building.objects.create(name="Building 1", created_by=user, modified_by=user)

@pytest.fixture 
def access_code(building, user, db): 
    return Access_Code.objects.create(building_id=building, flat_no="1", code="CODE123456789000", created_by=user, modified_by=user)

@pytest.fixture 
def access_code2(building, user2, db): 
    return Access_Code.objects.create(building_id=building, flat_no="2", code="CODE123456789012", created_by=user2, modified_by=user2)

@pytest.fixture 
def access_code3(building, user3, db): 
    return Access_Code.objects.create(building_id=building, flat_no="3", code="CODE123456789123", created_by=user3, modified_by=user3)

@pytest.fixture 
def member(building, access_code, user, db): 
    return Member.objects.create(user_id=user, building_id=building, access_code_id=access_code, nickname="TestUser", flat_no="1", created_by=user, modified_by=user)

@pytest.fixture 
def member2(building, access_code, access_code2, user2, db): 
    return Member.objects.create(user_id=user2, building_id=building, access_code_id=access_code2, nickname="TestUser 2", flat_no="2", created_by=user2, modified_by=user2)

@pytest.fixture 
def invitation(building, member, access_code, user, user2, db): 
    invitee = Member.objects.create(user_id=user2, building_id=building, access_code_id=access_code, nickname="Invitee", flat_no="2", created_by=user, modified_by=user) 
    return Invitation.objects.create(building_id=building, invitor_member_id=member, invitee_member_id=invitee, access_code_id=access_code, distance=1, created_by=user, modified_by=user)

@pytest.fixture 
def message(member, user, user3, db): 
    receiver = Member.objects.create(user_id=user3, building_id=member.building_id, access_code_id=member.access_code_id, nickname="Mail receiver user", flat_no="3", created_by=user3, modified_by=user3) 
    return Messages.objects.create(sender_member_id=member, receiver_member_id=receiver, title="Message Title", body="This is a test message body", message_code="CODE123456789123", created_by=user, modified_by=user)

@pytest.fixture 
def communication(member, user, db): 
    return Communication.objects.create(member_id=member, identification="mailuser@eneighborow.com", created_by=user, modified_by=user)

@pytest.fixture 
def borrowing_request(member, user, db): 
    return Borrowing_Request.objects.create(member_id=member, title="New Borrow Request", body="sample request for sample item", created_by=user, modified_by=user, required_from=datetime.datetime.now(), required_until=datetime.datetime.now() + datetime.timedelta(days=7))

@pytest.fixture 
def borrowing_request_recipient(member, message, borrowing_request, user, db): 
    return Borrowing_Request_Recipients.objects.create(member_id=member, message_id=message, borrowing_request=borrowing_request, created_by=user, modified_by=user)

@pytest.fixture 
def items_for_loan(member, user, db): 
    return Items_For_Loan.objects.create(member_id=member, label="Item 1", description="Sample item description", created_by=user, modified_by=user, available=True, is_deleted=False)

@pytest.fixture 
def items_for_loan_image(items_for_loan, user, db): 
    image_file = SimpleUploadedFile("item.jpg", b"sample item image", content_type="image/jpeg") 
    return Items_For_Loan_Image.objects.create(items_for_loan_id=items_for_loan, image=image_file, caption="Test image")

@pytest.fixture 
def condition_log(user, db): 
    return Condition_Log.objects.create(label="Condition Log", description="Good condition of item", created_by=user, modified_by=user)

@pytest.fixture 
def condition_image(condition_log, user, db): 
    image_file = SimpleUploadedFile("conditionLog.jpg", b"sample image", content_type="image/jpeg") 
    return Condition_Image.objects.create(condition_log_id=condition_log, image=image_file, caption="Condition Log sample image", created_by=user, modified_by=user)

@pytest.fixture 
def transaction(items_for_loan, member, user, user2, condition_log, db): 
    # Create a separate borrower for the transaction 
    borrower = Member.objects.create(user_id=user2, building_id=member.building_id, access_code_id=member.access_code_id, nickname="Borrower", flat_no="4", created_by=user, modified_by=user) 
    return Transaction.objects.create( items_for_loan_id=items_for_loan, lender_member_id=member, borrower_member_id=borrower, before_condition=condition_log, after_condition=condition_log, borrowed_on=datetime.datetime.now(), borrowed_until=datetime.datetime.now() + datetime.timedelta(days=7), return_date=None, reminder=ReminderType.STANDARD, created_by=user, modified_by=user )

#==================================================================================
# TESTS MODEL BUILDING
#==================================================================================

class TestBuilding:
    # Test that a building instance can be created with valid data
    @pytest.mark.django_db 
    def test_building_creation_valid(self, user): 
        b = Building.objects.create(name="Building A", created_by=user, modified_by=user) 
        assert b.pk is not None

    # Test that a ValidationError is raised when a required field (name) is missing
    @pytest.mark.django_db
    def test_building_missing_name(self, user):
        b = Building(created_by=user, modified_by=user)
        with pytest.raises(ValidationError):
            b.full_clean()

    # Test that the __str__ method returns the building's id as a string
    @pytest.mark.django_db
    def test_building_str(self, building):
        assert str(building) == str(building.id)

    # Test that address fields are optional and default to None
    @pytest.mark.django_db
    def test_building_address_optional(self, user):
        b = Building.objects.create(name="Building B", created_by=user, modified_by=user)
        assert b.address_line1 is None
        assert b.address_line2 is None

    # Test that the 'units' field is correctly set upon creation
    @pytest.mark.django_db
    def test_building_units_field(self, user):
        b = Building.objects.create(name="Building C", units=10, created_by=user, modified_by=user)
        assert b.units == 10

    # Test that the auto-populated 'created' and 'modified' fields are set after creation
    @pytest.mark.django_db
    def test_building_created_modified_auto(self, building):
        assert building.created is not None
        assert building.modified is not None

    # Test that updating the building name results in an update to the 'modified' field
    @pytest.mark.django_db
    def test_building_update(self, building):
        old_modified = building.modified
        building.name = "New Building name"
        building.save()
        assert building.modified > old_modified

    # Test that the 'created_by' relationship returns the expected user
    @pytest.mark.django_db
    def test_building_relationship_created_by(self, building, user):
        assert building.created_by == user

    # Test that the 'modified_by' relationship returns the expected user
    @pytest.mark.django_db
    def test_building_relationship_modified_by(self, building, user):
        assert building.modified_by == user

    # Test that multiple building instances can be created with unique primary keys
    @pytest.mark.django_db
    def test_building_multiple_instances(self, user):
        b1 = Building.objects.create(name="Building 1", created_by=user, modified_by=user)
        b2 = Building.objects.create(name="Building 2", created_by=user, modified_by=user)
        assert b1.pk != b2.pk


#==================================================================================
# TESTS MODEL APPSETTINGS
#==================================================================================
class TestAppSettings:
    # Test that a valid AppSettings instance can be created
    @pytest.mark.django_db 
    def test_appsettings_creation_valid(self, building, user): 
        a = AppSettings.objects.create(building_id=building, key=ApplicationSettings.DISTANCE, value="Value1", created_by=user, modified_by=user) 
        assert a.pk is not None

    # Test that a ValidationError is raised when the 'value' field is missing
    @pytest.mark.django_db
    def test_appsettings_missing_value(self, building, user):
        a = AppSettings(building_id=building, key=ApplicationSettings.DISTANCE, created_by=user, modified_by=user)
        with pytest.raises(ValidationError):
            a.full_clean()

    # Test that the __str__ method returns the instance's id as a string
    @pytest.mark.django_db
    def test_appsettings_str(self, building, user):
        a = AppSettings.objects.create(building_id=building, key=ApplicationSettings.REPLY_MAIL_GMX, value="Value2", created_by=user, modified_by=user)
        assert str(a) == str(a.id)

    # Test that the unique constraint on the combination of building and key is enforced
    @pytest.mark.django_db
    def test_appsettings_unique_building_key(self, building, user):
        AppSettings.objects.create(building_id=building, key=ApplicationSettings.DISTANCE, value="UniqueValue", created_by=user, modified_by=user)
        with pytest.raises(IntegrityError):
            AppSettings.objects.create(building_id=building, key=ApplicationSettings.DISTANCE, value="AnotherValue", created_by=user, modified_by=user)

    # Test that the building relationship is correctly set
    @pytest.mark.django_db
    def test_appsettings_relationship_building(self, building, user):
        a = AppSettings.objects.create(building_id=building, key=ApplicationSettings.DISTANCE, value="Value3", created_by=user, modified_by=user)
        assert a.building_id == building

    # Test that the created_by relationship is correctly set
    @pytest.mark.django_db
    def test_appsettings_relationship_created_by(self, building, user):
        a = AppSettings.objects.create(building_id=building, key=ApplicationSettings.DISTANCE, value="Value4", created_by=user, modified_by=user)
        assert a.created_by == user

    # Test that updating the value field is persisted
    @pytest.mark.django_db
    def test_appsettings_update(self, building, user):
        a = AppSettings.objects.create(building_id=building, key=ApplicationSettings.DISTANCE, value="Value first", created_by=user, modified_by=user)
        a.value = "Value second"
        a.save()
        assert a.value == "Value second"

    # Test that the auto-populated 'created' and 'modified' fields are set
    @pytest.mark.django_db
    def test_appsettings_auto_fields(self, building, user):
        a = AppSettings.objects.create(building_id=building, key=ApplicationSettings.REPLY_MAIL_GMX, value="Value5", created_by=user, modified_by=user)
        assert a.created is not None and a.modified is not None

    # Test that the default key choice is correctly applied when not specified
    @pytest.mark.django_db
    def test_appsettings_default_choice(self, building, user):
        a = AppSettings.objects.create(building_id=building, value="Value6", created_by=user, modified_by=user)
        assert a.key == ApplicationSettings.DISTANCE

    # Test that multiple AppSettings instances have distinct primary keys
    @pytest.mark.django_db
    def test_appsettings_multiple_instances(self, building, user):
        a1 = AppSettings.objects.create(building_id=building, key=ApplicationSettings.DISTANCE, value="Val1", created_by=user, modified_by=user)
        a2 = AppSettings.objects.create(building_id=building, key=ApplicationSettings.REPLY_MAIL_GMX, value="Val2", created_by=user, modified_by=user)
        assert a1.pk != a2.pk

#==================================================================================
# TESTS MODEL Access_Code
#==================================================================================
class TestAccessCode:
    # Test that a valid Access_Code instance is created
    @pytest.mark.django_db 
    def test_accesscode_creation_valid(self, building, user): 
        ac = Access_Code.objects.create(building_id=building, flat_no="1", code="CODE123456789000", created_by=user, modified_by=user) 
        assert ac.pk is not None

    # Test that a ValidationError is raised when the flat_no field is missing
    @pytest.mark.django_db
    def test_accesscode_missing_flat_no(self, building, user):
        ac = Access_Code(building_id=building, code="CODE123456789000", created_by=user, modified_by=user)
        with pytest.raises(ValidationError):
            ac.full_clean()

    # Test that a ValidationError is raised when the code field is missing
    @pytest.mark.django_db
    def test_accesscode_missing_code(self, building, user):
        ac = Access_Code(building_id=building, flat_no="3", created_by=user, modified_by=user)
        with pytest.raises(ValidationError):
            ac.full_clean()

    # Test that the __str__ method returns the access code's id as a string
    @pytest.mark.django_db
    def test_accesscode_str(self, access_code):
        assert str(access_code) == str(access_code.id)

    # Test that the unique constraint on the 'code' field is enforced
    @pytest.mark.django_db
    def test_accesscode_unique_code(self, building, user):
        Access_Code.objects.create(building_id=building, flat_no="104", code="CODE123456789000", created_by=user, modified_by=user)
        with pytest.raises(IntegrityError):
            Access_Code.objects.create(building_id=building, flat_no="105", code="CODE123456789000", created_by=user, modified_by=user)

    # Test that the default type is set to MemberType.RESIDENT
    @pytest.mark.django_db
    def test_accesscode_default_type(self, building, user):
        ac = Access_Code.objects.create(building_id=building, flat_no="6", code="CODE123456789000", created_by=user, modified_by=user)
        assert ac.type == MemberType.RESIDENT

    # Test that the access code cannot be longer than 16 characters
    @pytest.mark.django_db
    def test_accesscode_max_length(self, building, user):
        long_code = "CODE1234567891234" 
        ac = Access_Code(building_id=building, flat_no="3", code=long_code, created_by=user, modified_by=user)
        with pytest.raises(ValidationError):
            ac.full_clean()

    # Test that the building relationship is correctly set
    @pytest.mark.django_db
    def test_accesscode_relationship_building(self, access_code, building):
        assert access_code.building_id == building

    # Test that the created_by relationship is correctly set
    @pytest.mark.django_db
    def test_accesscode_relationship_created_by(self, access_code, user):
        assert access_code.created_by == user

    # Test that updating the access code works and the modified field is updated
    @pytest.mark.django_db
    def test_accesscode_update(self, access_code):
        old_modified = access_code.modified
        access_code.code = "CODE123456789000"
        access_code.save()
        assert access_code.code == "CODE123456789000"
        assert access_code.modified > old_modified

    # Test that the custom manager method get_member_authorized returns a list
    @pytest.mark.django_db
    def test_accesscode_custom_manager_get_member_authorized(self, member, user):
        result = Access_Code.custom_objects.get_member_authorized(user.id)
        assert isinstance(result, list)

    # Test that a valid Access_Code instance defaults to MemberType.RESIDENT.
    @pytest.mark.django_db
    def test_accesscode_default_member_type(self, building, user):
        ac = Access_Code.objects.create(building_id=building, flat_no="2", code="CODE123456789012", created_by=user, modified_by=user)
        # Verify that the default member type is set to RESIDENT.
        assert ac.type == MemberType.RESIDENT

    # Test that a valid custom member type (e.g., INVITEE) is accepted.
    @pytest.mark.django_db
    def test_accesscode_custom_member_type_valid(self, building, user):
        ac = Access_Code.objects.create(building_id=building, flat_no="3", code="CODE123456789012", type=MemberType.INVITEE, created_by=user, modified_by=user)
        ac.full_clean()  # Ensure the instance is valid
        # Verify that the member type is correctly set to INVITEE.
        assert ac.type == MemberType.INVITEE

    # Test that setting an invalid member type value raises a ValidationError.
    @pytest.mark.django_db
    def test_accesscode_invalid_member_type(self, building, user):
        ac = Access_Code(building_id=building, flat_no="4", code="CODE123456789013", type="XX", created_by=user, modified_by=user)
        # Verify that an invalid member type triggers a ValidationError.
        with pytest.raises(ValidationError):
            ac.full_clean()

#==================================================================================
# TESTS MODEL Member 
#==================================================================================
class TestMember:
    # Test that a Member instance is created successfully with valid data.
    @pytest.mark.django_db 
    def test_member_creation_valid(self, building, access_code, user): 
        m = Member.objects.create(user_id=user, building_id=building, access_code_id=access_code, nickname="Member 1", flat_no="7", created_by=user, modified_by=user) 
        assert m.pk is not None

    # Test that a ValidationError is raised if the nickname is missing.
    @pytest.mark.django_db
    def test_member_missing_nickname(self, building, access_code, user):
        m = Member(building_id=building, user_id=user, access_code_id=access_code, flat_no="8", created_by=user, modified_by=user)
        with pytest.raises(ValidationError):
            m.full_clean()

    # Test that the __str__ method returns the member's id as a string.
    @pytest.mark.django_db
    def test_member_str(self, member):
        assert str(member) == str(member.id)

    # Test that the unique constraint on user_id is enforced.
    @pytest.mark.django_db
    def test_member_unique_user_id(self, building, access_code, user):
        Member.objects.create(user_id=user, building_id=building, access_code_id=access_code, nickname="Member Unique 1", flat_no="9", created_by=user, modified_by=user)
        with pytest.raises(IntegrityError):
            Member.objects.create(user_id=user, building_id=building, access_code_id=access_code, nickname="Member Unique2", flat_no="11", created_by=user, modified_by=user)

    # Test that the building relationship returns the correct Building instance.
    @pytest.mark.django_db
    def test_member_relationship_building(self, member, building):
        assert member.building_id == building

    # Test that the access_code relationship returns the correct Access_Code instance.
    @pytest.mark.django_db
    def test_member_relationship_access_code(self, member, access_code):
        assert member.access_code_id == access_code

    # Test that the default value for 'authorized' is False.
    @pytest.mark.django_db
    def test_member_default_authorized(self, member):
        assert member.authorized is False

    # Test that the default value for 'distance' is 0.
    @pytest.mark.django_db
    def test_member_default_distance(self, member):
        assert member.distance == 0

    # Test that updating the member's nickname is persisted.
    @pytest.mark.django_db
    def test_member_update(self, member):
        member.nickname = "Nickname update"
        member.save()
        assert member.nickname == "Nickname update"

    # Test that a member can be deactivated by setting is_active to False.
    @pytest.mark.django_db
    def test_member_deactivation(self, member):
        member.is_active = False
        member.save()
        assert member.is_active is False

    # Test that a nickname with exactly the maximum allowed length (32 characters) is valid.
    @pytest.mark.django_db
    def test_member_nickname_max_length_valid(self, building, access_code, user):
        nickname = "NicknameNicknameNicknameNickname"  # 32 characters
        m = Member.objects.create(user_id=user, building_id=building, access_code_id=access_code, nickname=nickname, flat_no="11", created_by=user, modified_by=user)
        m.full_clean()
        assert m.pk is not None


    # Test that a member with a nickname longer than 32 characters raises a ValidationError
    @pytest.mark.django_db
    def test_member_nickname_max_length_invalid(self, building, access_code, user):
        nickname = "NicknameNicknameNicknameNicknameNickname" 
        m = Member(user_id=user, building_id=building, access_code_id=access_code, nickname=nickname, flat_no="12", created_by=user, modified_by=user)
        with pytest.raises(ValidationError):
            m.full_clean()

    # Test that a member with a flat_no of exactly 16 characters is valid
    @pytest.mark.django_db
    def test_member_flat_no_max_length_valid(self, building, access_code, user):
        flat_no = "1234567890123456"
        m = Member.objects.create(user_id=user, building_id=building, access_code_id=access_code, nickname="TestFlatValid", flat_no=flat_no, created_by=user, modified_by=user)
        m.full_clean()
        assert m.pk is not None

    # Test that a member with a flat_no longer than 16 characters raises a ValidationError
    @pytest.mark.django_db
    def test_member_flat_no_max_length_invalid(self, building, access_code, user):
        flat_no = "12345678901234567" 
        m = Member(user_id=user, building_id=building, access_code_id=access_code, nickname="TestFlatInvalid", flat_no=flat_no, created_by=user, modified_by=user)
        with pytest.raises(ValidationError):
            m.full_clean()

#==================================================================================
# TESTS MODEL Invitation 
#==================================================================================

class TestInvitation:
    # Test that a valid Invitation instance is created.
    @pytest.mark.django_db 
    def test_invitation_creation_valid(self, building, member, access_code, user, user2): 
        invitee = Member.objects.create(
            user_id=user2,
            building_id=building,
            access_code_id=access_code,
            nickname="Test Invitee",
            flat_no="external",
            created_by=user,
            modified_by=user
        )
        inv = Invitation.objects.create(
            building_id=building,
            invitor_member_id=member,
            invitee_member_id=invitee,
            access_code_id=access_code,
            distance=2,
            created_by=user,
            modified_by=user
        )
        assert inv.pk is not None

    # Test that an Invitation can be created without an invitee (invitee_member_id is None).
    @pytest.mark.django_db
    def test_invitation_missing_invitee(self, building, member, access_code, user):
        inv = Invitation.objects.create(
            building_id=building,
            invitor_member_id=member,
            access_code_id=access_code,
            distance=3,
            created_by=user,
            modified_by=user
        )
        assert inv.invitee_member_id is None

    # Test that the __str__ method returns the Invitation's id as a string.
    @pytest.mark.django_db
    def test_invitation_str(self, invitation):
        assert str(invitation) == str(invitation.id)

    # Test that the unique constraint on the access_code field is enforced.
    @pytest.mark.django_db
    def test_invitation_unique_access_code(self, building, member, access_code, user):
        Invitation.objects.create(
            building_id=building,
            invitor_member_id=member,
            invitee_member_id=member,
            access_code_id=access_code,
            distance=1,
            created_by=user,
            modified_by=user
        )
        with pytest.raises(IntegrityError):
            Invitation.objects.create(
                building_id=building,
                invitor_member_id=member,
                invitee_member_id=member,
                access_code_id=access_code,
                distance=1,
                created_by=user,
                modified_by=user
            )

    # Test that the invitor relationship returns the correct Member.
    @pytest.mark.django_db
    def test_invitation_relationship_invitor(self, invitation, member):
        assert invitation.invitor_member_id == member

    # Test that the invitee relationship returns a valid Member.
    @pytest.mark.django_db
    def test_invitation_relationship_invitee(self, invitation):
        assert invitation.invitee_member_id is not None

    # Test that the building relationship returns the correct Building instance.
    @pytest.mark.django_db
    def test_invitation_relationship_building(self, invitation, building):
        assert invitation.building_id == building

    # Test that the created_by relationship returns the correct User.
    @pytest.mark.django_db
    def test_invitation_relationship_created_by(self, invitation, user):
        assert invitation.created_by == user

    # Test that modifying an Invitation updates the modified field.
    @pytest.mark.django_db
    def test_invitation_modified_field(self, invitation):
        old_modified = invitation.modified
        invitation.distance = 10
        invitation.save()
        assert invitation.modified > old_modified

     # Test that a distance of 0 is accepted.
    @pytest.mark.django_db
    def test_invitation_distance_zero(self, building, member, access_code, user, user2):
        invitee = Member.objects.create(
            user_id=user2,
            building_id=building,
            access_code_id=access_code,
            nickname="Test nickname",
            flat_no="12",
            created_by=user,
            modified_by=user
        )
        inv = Invitation.objects.create(
            building_id=building,
            invitor_member_id=member,
            invitee_member_id=invitee,
            access_code_id=access_code,
            distance=0,
            created_by=user,
            modified_by=user
        )
        inv.full_clean()
        assert inv.distance == 0

    # Test that an invalid relationship value (outside the defined choices) raises a ValidationError.
    @pytest.mark.django_db
    def test_invitation_invalid_relationship(self, building, member, access_code, user, user2):
        invitee = Member.objects.create(
            user_id=user2,
            building_id=building,
            access_code_id=access_code,
            nickname="Invitee nickname",
            flat_no="14",
            created_by=user,
            modified_by=user
        )
        inv = Invitation(
            building_id=building,
            invitor_member_id=member,
            invitee_member_id=invitee,
            access_code_id=access_code,
            distance=2,
            relationship="99",  
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            inv.full_clean()


#==================================================================================
# TESTS MODEL Messages 
#==================================================================================
class TestMessages:
    # Test that a valid Message instance is created with required fields.
    @pytest.mark.django_db 
    def test_messages_creation_valid(self, member, user, user2): 
        receiver = Member.objects.create(
            user_id=user2,
            building_id=member.building_id,
            access_code_id=member.access_code_id,
            nickname="nickname",
            flat_no="12",
            created_by=user,
            modified_by=user
        )
        m = Messages.objects.create(
            sender_member_id=member,
            receiver_member_id=receiver,
            title="Test Title",
            body="Test Body",
            message_code="CODE123456789000",
            created_by=user,
            modified_by=user
        ) 
        assert m.pk is not None

    # Test that a ValidationError is raised when the title field is missing.
    @pytest.mark.django_db
    def test_messages_missing_title(self, member, user, user2):
        receiver = Member.objects.create(
            user_id=user2,
            building_id=member.building_id,
            access_code_id=member.access_code_id,
            nickname="test nickname",
            flat_no="13",
            created_by=user,
            modified_by=user
        )
        m = Messages(
            sender_member_id=member,
            receiver_member_id=receiver,
            body="Test Body",
            message_code="CODE123456789000",
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            m.full_clean()

    # Test that the __str__ method returns the Message's id as a string.
    @pytest.mark.django_db
    def test_messages_str(self, message):
        assert str(message) == str(message.id)

    # Test that the sender relationship returns the correct Member.
    @pytest.mark.django_db
    def test_messages_relationship_sender(self, message, member):
        assert message.sender_member_id == member

    # Test that the receiver relationship returns a valid Member.
    @pytest.mark.django_db
    def test_messages_relationship_receiver(self, message):
        assert message.receiver_member_id is not None

    # Test that the inbox and outbox flags have their default values (False).
    @pytest.mark.django_db
    def test_messages_inbox_outbox_flags(self, message):
        assert message.inbox is False
        assert message.outbox is False

    # Test that the internal flag has its default value (False).
    @pytest.mark.django_db
    def test_messages_default_internal(self, message):
        assert message.internal is False

    # Test that the is_sent_email flag has its default value (False).
    @pytest.mark.django_db
    def test_messages_default_is_sent_email(self, message):
        assert message.is_sent_email is False

    # Test that the is_sent_sms flag has its default value (False).
    @pytest.mark.django_db
    def test_messages_default_is_sent_sms(self, message):
        assert message.is_sent_sms is False

    # Test that the is_sent_whatsApp flag has its default value (True).
    @pytest.mark.django_db
    def test_messages_default_is_sent_whatsApp(self, message):
        assert message.is_sent_whatsApp is True

    # Test that the default message_type is set to 'UNDEFINED'.
    @pytest.mark.django_db
    def test_messages_default_message_type(self, message):
        from neighborow.models import MessageType
        assert message.message_type == MessageType.UNDEFINED

    # Test that updating the message body is saved correctly.
    @pytest.mark.django_db
    def test_messages_update_body(self, message):
        message.body = "Updated body"
        message.save()
        assert message.body == "Updated body"


    # Test that the auto-populated 'created' and 'modified' fields are set.
    @pytest.mark.django_db
    def test_messages_auto_fields(self, message):
        assert message.created is not None and message.modified is not None

    # Test placeholder for verifying that database indexes exist.
    @pytest.mark.django_db
    def test_messages_indexes(self, message):
        # Placeholder test assuming database indexes exist.
        assert True

    # Test that a title with exactly 175 characters is valid.
    @pytest.mark.django_db
    def test_messages_title_max_length_valid(self, member, user, user2):
        title = "T" * 175  
        receiver = Member.objects.create(
            user_id=user2,
            building_id=member.building_id,
            access_code_id=member.access_code_id,
            nickname="Receiver",
            flat_no="14",
            created_by=user,
            modified_by=user
        )
        m = Messages.objects.create(
            sender_member_id=member,
            receiver_member_id=receiver,
            title=title,
            body="Test Body",
            message_code="CODE123456789000",
            created_by=user,
            modified_by=user
        )
        m.full_clean()  # Validate field lengths
        assert m.pk is not None

    # Test that a title with 176 characters raises a ValidationError.
    @pytest.mark.django_db
    def test_messages_title_max_length_invalid(self, member, user, user2):
        title = "T" * 176  # 176 characters, exceeding max length
        receiver = Member.objects.create(
            user_id=user2,
            building_id=member.building_id,
            access_code_id=member.access_code_id,
            nickname="test nickname",
            flat_no="15",
            created_by=user,
            modified_by=user
        )
        m = Messages(
            sender_member_id=member,
            receiver_member_id=receiver,
            title=title,
            body="Test Body",
            message_code="CODE123456789000",
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            m.full_clean()

    # Test that a message_code with exactly 16 characters is valid.
    @pytest.mark.django_db
    def test_messages_message_code_max_length_valid(self, member, user, user2):
        code = "M" * 16  # 16 characters, at max length
        receiver = Member.objects.create(
            user_id=user2,
            building_id=member.building_id,
            access_code_id=member.access_code_id,
            nickname="Test nickname",
            flat_no="116",
            created_by=user,
            modified_by=user
        )
        m = Messages.objects.create(
            sender_member_id=member,
            receiver_member_id=receiver,
            title="Test",
            body="Test Body",
            message_code=code,
            created_by=user,
            modified_by=user
        )
        m.full_clean()
        assert m.pk is not None

    # Test that a message_code with 17 characters raises a ValidationError.
    @pytest.mark.django_db
    def test_messages_message_code_max_length_invalid(self, member, user, user2):
        code = "M" * 17  # 17 characters, exceeding max length
        receiver = Member.objects.create(
            user_id=user2,
            building_id=member.building_id,
            access_code_id=member.access_code_id,
            nickname="test nickname",
            flat_no="17",
            created_by=user,
            modified_by=user
        )
        m = Messages(
            sender_member_id=member,
            receiver_member_id=receiver,
            title="Test",
            body="Test Body",
            message_code=code,
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            m.full_clean()

    # Test that a body with exactly 2100 characters is valid.
    @pytest.mark.django_db
    def test_messages_body_max_length_valid(self, member, user, user2):
        body = "B" * 2100  # 2100 characters, at max length
        receiver = Member.objects.create(
            user_id=user2,
            building_id=member.building_id,
            access_code_id=member.access_code_id,
            nickname="Test nickname",
            flat_no="18",
            created_by=user,
            modified_by=user
        )
        m = Messages.objects.create(
            sender_member_id=member,
            receiver_member_id=receiver,
            title="Test",
            body=body,
            message_code="CODE123456789000",
            created_by=user,
            modified_by=user
        )
        m.full_clean()
        assert m.pk is not None

    # Test that a body with 2101 characters raises a ValidationError.
    @pytest.mark.django_db
    def test_messages_body_max_length_invalid(self, member, user, user2):
        body = "B" * 2101  # 2101 characters, exceeding max length
        receiver = Member.objects.create(
            user_id=user2,
            building_id=member.building_id,
            access_code_id=member.access_code_id,
            nickname="tst",
            flat_no="19",
            created_by=user,
            modified_by=user
        )
        m = Messages(
            sender_member_id=member,
            receiver_member_id=receiver,
            title="Test",
            body=body,
            message_code="CODE123456789000",
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            m.full_clean()

#==================================================================================
# TESTS MODEL Communication
#==================================================================================
class TestCommunication:
    # Test that a valid Communication instance is created.
    @pytest.mark.django_db 
    def test_communication_creation_valid(self, member, user): 
        comm = Communication.objects.create(
            member_id=member, 
            identification="neighborow@gmx.net", 
            created_by=user, 
            modified_by=user
        ) 
        assert comm.pk is not None

    # Test that a ValidationError is raised when the identification field is missing.
    @pytest.mark.django_db
    def test_communication_missing_identification(self, member, user):
        comm = Communication(member_id=member, created_by=user, modified_by=user)
        with pytest.raises(ValidationError):
            comm.full_clean()

    # Test that the __str__ method returns the Communication's id as a string.
    @pytest.mark.django_db
    def test_communication_str(self, communication):
        assert str(communication) == str(communication.id)

    # Test that the default channel is set to Channels.BUILTIN.
    @pytest.mark.django_db
    def test_communication_default_channel(self, communication):
        assert communication.channel == Channels.BUILTIN

    # Test that the member relationship returns the correct Member instance.
    @pytest.mark.django_db
    def test_communication_relationship_member(self, communication, member):
        assert communication.member_id == member

    # Test that the default value for is_active is False.
    @pytest.mark.django_db
    def test_communication_is_active_default(self, communication):
        assert communication.is_active is False

    # Test that updating the is_active flag works correctly.
    @pytest.mark.django_db
    def test_communication_update_is_active(self, communication):
        communication.is_active = True
        communication.save()
        assert communication.is_active is True

    # Test that the auto-populated created and modified fields are set.
    @pytest.mark.django_db
    def test_communication_auto_fields(self, communication):
        assert communication.created is not None and communication.modified is not None

    # Test that multiple Communication instances have unique primary keys.
    @pytest.mark.django_db
    def test_communication_multiple_instances(self, member, user):
        comm1 = Communication.objects.create(
            member_id=member, 
            identification="neighborow@gmx.net", 
            created_by=user, 
            modified_by=user
        )
        comm2 = Communication.objects.create(
            member_id=member, 
            identification="neighborow@gmx.com", 
            created_by=user, 
            modified_by=user
        )
        assert comm1.pk != comm2.pk

    # Test that updating the identification field is saved correctly.
    @pytest.mark.django_db
    def test_communication_modify_identification(self, communication):
        communication.identification = "neighborow@gmx.com"
        communication.save()
        assert communication.identification == "neighborow@gmx.com"

    # Test that a Communication instance with an identification of exactly 120 characters is valid.
    @pytest.mark.django_db
    def test_communication_identification_max_length_valid(self, member, user):
        identification = "I" * 120  # 120 characters
        comm = Communication.objects.create(
            member_id=member, 
            identification=identification, 
            created_by=user, 
            modified_by=user
        )
        comm.full_clean()  
        assert comm.pk is not None

    # Test that a Communication instance with an identification longer than 120 characters raises a ValidationError.
    @pytest.mark.django_db
    def test_communication_identification_max_length_invalid(self, member, user):
        identification = "I" * 121  # 121 characters, exceeding limit
        comm = Communication(member_id=member, identification=identification, created_by=user, modified_by=user)
        with pytest.raises(ValidationError):
            comm.full_clean()

    # Test that setting a valid channel value (e.g., Channels.EMAIL) is accepted.
    @pytest.mark.django_db
    def test_communication_set_valid_channel(self, member, user):
        comm = Communication.objects.create(
            member_id=member, 
            identification="neighborow@gmx.net", 
            channel=Channels.EMAIL, 
            created_by=user, 
            modified_by=user
        )
        comm.full_clean()
        assert comm.channel == Channels.EMAIL

    # Test that setting an invalid channel value raises a ValidationError.
    @pytest.mark.django_db
    def test_communication_invalid_channel(self, member, user):
        comm = Communication(member_id=member, identification="neighborow@gmx.com", channel="XX", created_by=user, modified_by=user)
        with pytest.raises(ValidationError):
            comm.full_clean()



#==================================================================================
# TESTS MODEL BORROWING_REQUEST
#==================================================================================
class TestBorrowingRequest:
    # Test that a valid Borrowing_Request instance is created.
    @pytest.mark.django_db 
    def test_borrowing_request_creation_valid(self, member, user): 
        br = Borrowing_Request.objects.create(
            member_id=member,
            title="Request",
            body="Need tool",
            created_by=user,
            modified_by=user
        )
        assert br.pk is not None

    # Test that a ValidationError is raised when the title is missing.
    @pytest.mark.django_db
    def test_borrowing_request_missing_title(self, member, user):
        br = Borrowing_Request(
            member_id=member,
            body="Need tool",
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            br.full_clean()

    # Test that the __str__ method returns the Borrowing_Request's id as a string.
    @pytest.mark.django_db
    def test_borrowing_request_str(self, borrowing_request):
        assert str(borrowing_request) == str(borrowing_request.id)

    # Test that the member relationship returns the correct Member instance.
    @pytest.mark.django_db
    def test_borrowing_request_relationship_member(self, borrowing_request, member):
        assert borrowing_request.member_id == member

    # Test that the required_from and required_until fields are saved correctly.
    @pytest.mark.django_db
    def test_borrowing_request_required_from_until(self, member, user):
        now = datetime.datetime.now()
        later = now + datetime.timedelta(days=5)
        br = Borrowing_Request.objects.create(
            member_id=member,
            title="Time Request",
            body="Timing",
            required_from=now,
            required_until=later,
            created_by=user,
            modified_by=user
        )
        assert br.required_from == now
        assert br.required_until == later

    # Test that updating the title field is saved correctly.
    @pytest.mark.django_db
    def test_borrowing_request_update_title(self, borrowing_request):
        borrowing_request.title = "Updated Request"
        borrowing_request.save()
        assert borrowing_request.title == "Updated Request"

    # Test that the auto-populated created and modified fields are set.
    @pytest.mark.django_db
    def test_borrowing_request_auto_fields(self, borrowing_request):
        assert borrowing_request.created is not None and borrowing_request.modified is not None

    # Test that a ValidationError is raised when the body is missing.
    @pytest.mark.django_db
    def test_borrowing_request_missing_body(self, member, user):
        br = Borrowing_Request(
            member_id=member,
            title="No Body",
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            br.full_clean()

    # Test that the date fields are nullable.
    @pytest.mark.django_db
    def test_borrowing_request_date_fields_nullable(self, member, user):
        br = Borrowing_Request.objects.create(
            member_id=member,
            title="Nullable Dates",
            body="Dates",
            created_by=user,
            modified_by=user
        )
        assert br.required_from is None and br.required_until is None

    # Test that multiple Borrowing_Request instances have unique primary keys.
    @pytest.mark.django_db
    def test_borrowing_request_multiple_instances(self, member, user):
        br1 = Borrowing_Request.objects.create(
            member_id=member,
            title="Request 1",
            body="Body 1",
            created_by=user,
            modified_by=user
        )
        br2 = Borrowing_Request.objects.create(
            member_id=member,
            title="Request 2",
            body="Body 2",
            created_by=user,
            modified_by=user
        )
        assert br1.pk != br2.pk

    # Test that a title with exactly 150 characters is valid.
    @pytest.mark.django_db
    def test_borrowing_request_title_max_length_valid(self, member, user):
        title = "T" * 150  # 150 characters, at the max length limit
        br = Borrowing_Request.objects.create(
            member_id=member,
            title=title,
            body="Boundary test for title",
            created_by=user,
            modified_by=user
        )
        br.full_clean()
        assert br.pk is not None

    # Test that a title with 151 characters raises a ValidationError.
    @pytest.mark.django_db
    def test_borrowing_request_title_max_length_invalid(self, member, user):
        title = "T" * 151  # 151 characters, exceeding max length
        br = Borrowing_Request(
            member_id=member,
            title=title,
            body="Boundary test for title",
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            br.full_clean()

    # Test that a body with exactly 2000 characters is valid.
    @pytest.mark.django_db
    def test_borrowing_request_body_max_length_valid(self, member, user):
        body = "B" * 2000  # 2000 characters, at the max length limit
        br = Borrowing_Request.objects.create(
            member_id=member,
            title="Valid Body Length",
            body=body,
            created_by=user,
            modified_by=user
        )
        br.full_clean()
        assert br.pk is not None

    # Test that a body with 2001 characters raises a ValidationError.
    @pytest.mark.django_db
    def test_borrowing_request_body_max_length_invalid(self, member, user):
        body = "B" * 2001  # 2001 characters, exceeding max length
        br = Borrowing_Request(
            member_id=member,
            title="Invalid Body Length",
            body=body,
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            br.full_clean()

#==================================================================================
# TESTS MODEL BORROWING_REQUEST_RECEIPIENTS
#==================================================================================
class TestBorrowingRequestRecipients:
    # Test that a valid Borrowing_Request_Recipients instance is created
    @pytest.mark.django_db 
    def test_borrowing_request_recipients_creation_valid(self, member, message, borrowing_request, user): 
        brr = Borrowing_Request_Recipients.objects.create(
            member_id=member,
            message_id=message,
            borrowing_request=borrowing_request,
            created_by=user,
            modified_by=user
        ) 
        assert brr.pk is not None

    # Test that an instance can be created without a message (message_id is allowed to be None)
    @pytest.mark.django_db
    def test_borrowing_request_recipients_missing_message(self, member, borrowing_request, user):
        brr = Borrowing_Request_Recipients.objects.create(
            member_id=member,
            borrowing_request=borrowing_request,
            created_by=user,
            modified_by=user
        )
        assert brr.message_id is None

    # Test that the __str__ method returns the instance's id as a string
    @pytest.mark.django_db
    def test_borrowing_request_recipients_str(self, borrowing_request_recipient):
        assert str(borrowing_request_recipient) == str(borrowing_request_recipient.id)

    # Test that the unique constraint on the message_id field is enforced.
    @pytest.mark.django_db
    def test_borrowing_request_recipients_unique_message(self, member, message, borrowing_request, user):
        Borrowing_Request_Recipients.objects.create(
            member_id=member,
            message_id=message,
            borrowing_request=borrowing_request,
            created_by=user,
            modified_by=user
        )
        with pytest.raises(IntegrityError):
            Borrowing_Request_Recipients.objects.create(
                member_id=member,
                message_id=message,
                borrowing_request=borrowing_request,
                created_by=user,
                modified_by=user
            )

    # Test that the unique constraint on the (member, borrowing_request) combination is enforced
    @pytest.mark.django_db
    def test_borrowing_request_recipients_unique_member_borrowing_request(self, member, message, borrowing_request, user):
        Borrowing_Request_Recipients.objects.create(
            member_id=member,
            message_id=message,
            borrowing_request=borrowing_request,
            created_by=user,
            modified_by=user
        )
        with pytest.raises(IntegrityError):
            Borrowing_Request_Recipients.objects.create(
                member_id=member,
                borrowing_request=borrowing_request,
                created_by=user,
                modified_by=user
            )

    # Test that the member relationship returns the correct Member instance
    @pytest.mark.django_db
    def test_borrowing_request_recipients_relationship_member(self, borrowing_request_recipient, member):
        assert borrowing_request_recipient.member_id == member

    # Test that the borrowing_request relationship returns the correct Borrowing_Request instance
    @pytest.mark.django_db
    def test_borrowing_request_recipients_relationship_borrowing_request(self, borrowing_request_recipient, borrowing_request):
        assert borrowing_request_recipient.borrowing_request == borrowing_request

    # Test that updating a Borrowing_Request_Recipients instance updates the modified field
    @pytest.mark.django_db
    def test_borrowing_request_recipients_update(self, borrowing_request_recipient):
        old_modified = borrowing_request_recipient.modified
        borrowing_request_recipient.save()
        assert borrowing_request_recipient.modified >= old_modified

    # Test that the auto-populated created and modified fields are set
    @pytest.mark.django_db
    def test_borrowing_request_recipients_created_modified(self, borrowing_request_recipient):
        assert borrowing_request_recipient.created is not None and borrowing_request_recipient.modified is not None

    # Test that the created_by relationship returns the correct User
    @pytest.mark.django_db
    def test_borrowing_request_recipients_relationship_created_by(self, borrowing_request_recipient, user):
        assert borrowing_request_recipient.created_by == user

    # Test that multiple Borrowing_Request_Recipients instances have unique primary keys
    @pytest.mark.django_db
    def test_borrowing_request_recipients_multiple_instances(self, member, member2, message, borrowing_request, user):
        brr1 = Borrowing_Request_Recipients.objects.create(
            member_id=member,
            message_id=message,
            borrowing_request=borrowing_request,
            created_by=user,
            modified_by=user
        )
        brr2 = Borrowing_Request_Recipients.objects.create(
            member_id=member2,
            borrowing_request=borrowing_request,
            created_by=user,
            modified_by=user
        )
        assert brr1.pk != brr2.pk

    # Test that a ValidationError is raised when the required field borrowing_request is missing
    @pytest.mark.django_db
    def test_borrowing_request_recipients_missing_borrowing_request(self, member, user):
        brr = Borrowing_Request_Recipients(
            member_id=member,
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            brr.full_clean()

    # Test updating the message relationship to a new valid message
    @pytest.mark.django_db
    def test_borrowing_request_recipients_change_message(self, borrowing_request_recipient, member, borrowing_request, user):
        new_message = Messages.objects.create(
            sender_member_id=member,
            receiver_member_id=member,
            title="New Message",
            body="New message body",
            message_code="CODE123456789012",
            created_by=user,
            modified_by=user
        )
        borrowing_request_recipient.message_id = new_message
        borrowing_request_recipient.full_clean()
        borrowing_request_recipient.save()
        assert borrowing_request_recipient.message_id == new_message

#==================================================================================
# TESTS MODEL ITEMS_FOR_LOAN
#==================================================================================
class TestItemsForLoan:
    # Test that a valid Items_For_Loan instance is created
    @pytest.mark.django_db 
    def test_items_for_loan_creation_valid(self, member, user): 
        item = Items_For_Loan.objects.create(
            member_id=member, 
            label="New Item", 
            description="New item sample description", 
            created_by=user, 
            modified_by=user
        ) 
        assert item.pk is not None

    # Test that a ValidationError is raised when the label is missing
    @pytest.mark.django_db
    def test_items_for_loan_missing_label(self, member, user):
        item = Items_For_Loan(
            member_id=member, 
            description="Sample description", 
            created_by=user, 
            modified_by=user
        )
        with pytest.raises(ValidationError):
            item.full_clean()

    # Test that the __str__ method returns the item's id as a string
    @pytest.mark.django_db
    def test_items_for_loan_str(self, items_for_loan):
        assert str(items_for_loan) == str(items_for_loan.id)

    # Test that the member relationship returns the correct Member instance
    @pytest.mark.django_db
    def test_items_for_loan_relationship_member(self, items_for_loan, member):
        assert items_for_loan.member_id == member

    # Test that the default value for 'available' is True
    @pytest.mark.django_db
    def test_items_for_loan_default_available(self, items_for_loan):
        assert items_for_loan.available is True

    # Test that the default value for 'currently_borrowed is False
    @pytest.mark.django_db
    def test_items_for_loan_default_currently_borrowed(self, items_for_loan):
        assert items_for_loan.currently_borrowed is False

    # Test that updating the description field is saved correctly
    @pytest.mark.django_db
    def test_items_for_loan_update_description(self, items_for_loan):
        items_for_loan.description = "new sample description"
        items_for_loan.save()
        assert items_for_loan.description == "new sample description"

    # Test that the custom manager method get_items_for_loan returns a list
    @pytest.mark.django_db
    def test_items_for_loan_custom_manager_get_items_for_loan(self, member, user, items_for_loan):
        results = Items_For_Loan.custom_objects.get_items_for_loan(member.id)
        assert isinstance(results, list)

    # Test that the custom manager method get_filtered_items_for_loan returns a list
    @pytest.mark.django_db
    def test_items_for_loan_custom_manager_get_filtered_items_for_loan(self, member, user, items_for_loan):
        results = Items_For_Loan.custom_objects.get_filtered_items_for_loan(member.id, "Loan")
        assert isinstance(results, list)

    # Test that setting is_deleted to True marks the item as deleted
    @pytest.mark.django_db
    def test_items_for_loan_soft_delete(self, items_for_loan):
        items_for_loan.is_deleted = True
        items_for_loan.save()
        assert items_for_loan.is_deleted is True

    # Test that a label with exactly 150 characters is valid
    @pytest.mark.django_db
    def test_items_for_loan_label_max_length_valid(self, member, user):
        label = "A" * 150 
        item = Items_For_Loan.objects.create(
            member_id=member,
            label=label,
            description="sample description",
            created_by=user,
            modified_by=user
        )
        item.full_clean()
        assert item.pk is not None

    # Test that a label with 151 characters raises a ValidationError
    @pytest.mark.django_db
    def test_items_for_loan_label_max_length_invalid(self, member, user):
        label = "A" * 151  
        item = Items_For_Loan(
            member_id=member,
            label=label,
            description="sample description",
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            item.full_clean()

    # Test that a description with exactly 2000 characters is valid
    @pytest.mark.django_db
    def test_items_for_loan_description_max_length_valid(self, member, user):
        description = "A" * 2000 
        item = Items_For_Loan.objects.create(
            member_id=member,
            label="sample lable",
            description=description,
            created_by=user,
            modified_by=user
        )
        item.full_clean()
        assert item.pk is not None

    # Test that a description with 2001 characters raises a ValidationError
    @pytest.mark.django_db
    def test_items_for_loan_description_max_length_invalid(self, member, user):
        description = "A" * 2001  
        item = Items_For_Loan(
            member_id=member,
            label="sample lanle",
            description=description,
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            item.full_clean()

    # Test that an empty string for label raises a ValidationError
    @pytest.mark.django_db
    def test_items_for_loan_blank_label(self, member, user):
        item = Items_For_Loan(
            member_id=member,
            label="",
            description="sample description",
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            item.full_clean()

    # Test that an empty string for description raises a ValidationError
    @pytest.mark.django_db
    def test_items_for_loan_blank_description(self, member, user):
        item = Items_For_Loan(
            member_id=member,
            label="New item",
            description="",
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            item.full_clean()

    # Test that available_from accepts a valid datetime (within a delta of 1 second)
    @pytest.mark.django_db
    def test_items_for_loan_available_from_valid(self, member, user):
        now_datetime = datetime.datetime.now()
        item = Items_For_Loan.objects.create(
            member_id=member,
            label="new item",
            description="sample description",
            available_from=now_datetime,
            created_by=user,
            modified_by=user
        )
        item.full_clean()
        # Allow a deviation of up to 1 second.
        time_delta = abs((item.available_from - now_datetime).total_seconds())
        assert time_delta < 1

    # Test that available_from set to an invalid type raises a ValidationError
    @pytest.mark.django_db
    def test_items_for_loan_available_from_invalid(self, member, user):
        item = Items_For_Loan(
            member_id=member,
            label="new item",
            description="sampe description",
            available_from="not a datetime",
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            item.full_clean()

    # Test that updating the 'available' field to False works correctly
    @pytest.mark.django_db
    def test_items_for_loan_update_available(self, items_for_loan):
        items_for_loan.available = False
        items_for_loan.save()
        assert items_for_loan.available is False

    # Test that updating the 'currently_borrowed' field to True works correctly
    @pytest.mark.django_db
    def test_items_for_loan_update_currently_borrowed(self, items_for_loan):
        items_for_loan.currently_borrowed = True
        items_for_loan.save()
        assert items_for_loan.currently_borrowed is True

#==================================================================================
# TESTS MODEL ITEMS_FOR_LOAN_IMAGE
#==================================================================================
class TestItemsForLoanImage:
    # Test that a valid Items_For_Loan_Image instance is created
    @pytest.mark.django_db 
    def test_items_for_loan_image_creation_valid(self, items_for_loan, user):
        image_file = SimpleUploadedFile("image.jpg", b"content", content_type="image/jpeg")
        img = Items_For_Loan_Image.objects.create(
            items_for_loan_id=items_for_loan,
            image=image_file,
            caption="Image caption"
        )
        assert img.pk is not None

    # Test that if caption is not provided, it defaults to an empty string
    @pytest.mark.django_db
    def test_items_for_loan_image_missing_caption(self, items_for_loan, user):
        image_file = SimpleUploadedFile("image2.jpg", b"content", content_type="image/jpeg")
        img = Items_For_Loan_Image.objects.create(
            items_for_loan_id=items_for_loan,
            image=image_file
        )
        assert img.caption == ""

    # Test that the __str__ method returns the image instance's id as a string
    @pytest.mark.django_db
    def test_items_for_loan_image_str(self, items_for_loan_image):
        assert str(items_for_loan_image) == str(items_for_loan_image.id)

    # Test that the relationship to Items_For_Loan is correctly set
    @pytest.mark.django_db
    def test_items_for_loan_image_relationship_item(self, items_for_loan_image, items_for_loan):
        assert items_for_loan_image.items_for_loan_id == items_for_loan

    # Test that updating the caption field is saved correctly
    @pytest.mark.django_db
    def test_items_for_loan_image_update_caption(self, items_for_loan_image):
        items_for_loan_image.caption = "new caption"
        items_for_loan_image.save()
        assert items_for_loan_image.caption == "new caption"

    # Test that the image file field is properly populated
    @pytest.mark.django_db
    def test_items_for_loan_image_with_file(self, items_for_loan, user):
        image_file = SimpleUploadedFile("image3.jpg", b"content", content_type="image/jpeg")
        img = Items_For_Loan_Image.objects.create(
            items_for_loan_id=items_for_loan,
            image=image_file,
            caption="caption"
        )
        # Verify that the image field's file name is set
        assert img.image.name is not None

    # Test that multiple Items_For_Loan_Image instances have unique primary keys.
    @pytest.mark.django_db
    def test_items_for_loan_image_multiple_instances(self, items_for_loan, user):
        image_file1 = SimpleUploadedFile("img1.jpg", b"content", content_type="image/jpeg")
        image_file2 = SimpleUploadedFile("img2.jpg", b"content", content_type="image/jpeg")
        img1 = Items_For_Loan_Image.objects.create(
            items_for_loan_id=items_for_loan,
            image=image_file1,
            caption="caption image 1"
        )
        img2 = Items_For_Loan_Image.objects.create(
            items_for_loan_id=items_for_loan,
            image=image_file2,
            caption="caption image 1"
        )
        assert img1.pk != img2.pk

    # Test that an Items_For_Loan_Image instance can be deleted
    @pytest.mark.django_db
    def test_items_for_loan_image_delete(self, items_for_loan, user, items_for_loan_image):
        pk = items_for_loan_image.pk
        items_for_loan_image.delete()
        with pytest.raises(Items_For_Loan_Image.DoesNotExist):
            Items_For_Loan_Image.objects.get(pk=pk)

    # Test that auto-populated fields set
    @pytest.mark.django_db
    def test_items_for_loan_image_auto_fields(self, items_for_loan_image):
        assert items_for_loan_image.pk is not None

    # Test that the relationship to Items_For_Loan can be updated to a different item
    @pytest.mark.django_db
    def test_items_for_loan_image_change_item(self, items_for_loan_image, items_for_loan, user):
        new_item = Items_For_Loan.objects.create(
            member_id=items_for_loan.member_id,
            label="New Item",
            description="New description",
            created_by=user,
            modified_by=user
        )
        items_for_loan_image.items_for_loan_id = new_item
        items_for_loan_image.save()
        assert items_for_loan_image.items_for_loan_id == new_item


    # Test that a caption with exactly 255 characters is valid
    @pytest.mark.django_db
    def test_items_for_loan_image_caption_max_length_valid(self, items_for_loan, user):
        caption = "A" * 255  # 255 characters, at the max limit
        image_file = SimpleUploadedFile("image4.jpg", b"content", content_type="image/jpeg")
        img = Items_For_Loan_Image.objects.create(
            items_for_loan_id=items_for_loan,
            image=image_file,
            caption=caption
        )
        img.full_clean() 
        assert img.pk is not None

    # Test that a caption with 256 characters raises a ValidationError
    @pytest.mark.django_db
    def test_items_for_loan_image_caption_max_length_invalid(self, items_for_loan, user):
        caption = "A" * 256  
        image_file = SimpleUploadedFile("image5.jpg", b"content", content_type="image/jpeg")
        img = Items_For_Loan_Image(
            items_for_loan_id=items_for_loan,
            image=image_file,
            caption=caption
        )
        with pytest.raises(ValidationError):
            img.full_clean()

    # Test that missing the required image field raises a ValidationError
    @pytest.mark.django_db
    def test_items_for_loan_image_missing_image(self, items_for_loan, user):
        img = Items_For_Loan_Image(
            items_for_loan_id=items_for_loan,
            caption="image missing"
        )
        with pytest.raises(ValidationError):
            img.full_clean()

#==================================================================================
# TESTS MODEL CONDITION_LOG
#==================================================================================
class TestConditionLog:
    # Test that a valid Condition_Log instance is created
    @pytest.mark.django_db 
    def test_condition_log_creation_valid(self, user):
        cl = Condition_Log.objects.create(label="Label", description="description", created_by=user, modified_by=user)
        assert cl.pk is not None

    # Test that a ValidationError is raised when the label is missing
    @pytest.mark.django_db
    def test_condition_log_missing_label(self, user):
        cl = Condition_Log(description="description", created_by=user, modified_by=user)
        with pytest.raises(ValidationError):
            cl.full_clean()

    # Test that the __str__ method returns the instance's id as a string
    @pytest.mark.django_db
    def test_condition_log_str(self, condition_log):
        assert str(condition_log) == str(condition_log.id)

    # Test that updating the description field is persisted
    @pytest.mark.django_db
    def test_condition_log_update_description(self, condition_log):
        condition_log.description = "new condition"
        condition_log.save()
        assert condition_log.description == "new condition"

    # Test that the created_by relationship returns the correct User
    @pytest.mark.django_db
    def test_condition_log_relationship_created_by(self, condition_log, user):
        assert condition_log.created_by == user

    # Test that the auto-populated created and modified fields are set
    @pytest.mark.django_db
    def test_condition_log_auto_fields(self, condition_log):
        assert condition_log.created is not None and condition_log.modified is not None

    # Test that multiple Condition_Log instances have unique primary keys
    @pytest.mark.django_db
    def test_condition_log_multiple_instances(self, user):
        cl1 = Condition_Log.objects.create(label="label 2", description="description 1", created_by=user, modified_by=user)
        cl2 = Condition_Log.objects.create(label="label 3", description="description 2", created_by=user, modified_by=user)
        assert cl1.pk != cl2.pk

    # Test that updating the label field is persisted
    @pytest.mark.django_db
    def test_condition_log_change_label(self, condition_log):
        condition_log.label = "New Label"
        condition_log.save()
        assert condition_log.label == "New Label"

    # Test that deleting a Condition_Log instance works
    @pytest.mark.django_db
    def test_condition_log_delete(self, condition_log):
        pk = condition_log.pk
        condition_log.delete()
        with pytest.raises(Condition_Log.DoesNotExist):
            Condition_Log.objects.get(pk=pk)

    # Test that saving a clean Condition_Log instance works
    @pytest.mark.django_db
    def test_condition_log_save_clean(self, user):
        cl = Condition_Log(label="empty label", description="description", created_by=user, modified_by=user)
        cl.full_clean()
        cl.save()
        assert cl.pk is not None

    # Test that a label with exactly 150 characters is valid
    @pytest.mark.django_db
    def test_condition_log_label_max_length_valid(self, user):
        label = "A" *150
        cl = Condition_Log.objects.create(label=label, description="Desc", created_by=user, modified_by=user)
        cl.full_clean()
        assert cl.pk is not None

    # Test that a label with 151 characters raises a ValidationError
    @pytest.mark.django_db
    def test_condition_log_label_max_length_invalid(self, user):
        label = "A" * 151
        cl = Condition_Log(label=label, description="Desc", created_by=user, modified_by=user)
        with pytest.raises(ValidationError):
            cl.full_clean()

    # Test that a description with exactly 2000 characters is valid
    @pytest.mark.django_db
    def test_condition_log_description_max_length_valid(self, user):
        description = "A" * 2000
        cl = Condition_Log.objects.create(label="label text", description=description, created_by=user, modified_by=user)
        cl.full_clean()
        assert cl.pk is not None

    # Test that a description with 2001 characters raises a ValidationError
    @pytest.mark.django_db
    def test_condition_log_description_max_length_invalid(self, user):
        description = "A" * 2001
        cl = Condition_Log(label="sample label", description=description, created_by=user, modified_by=user)
        with pytest.raises(ValidationError):
            cl.full_clean()

    # Test that a missing description raises a ValidationError
    @pytest.mark.django_db
    def test_condition_log_missing_description(self, user):
        cl = Condition_Log(label="sample label", description="", created_by=user, modified_by=user)
        with pytest.raises(ValidationError):
            cl.full_clean()

    # Test that created_by can be None and still save
    @pytest.mark.django_db
    def test_condition_log_created_by_null(self, user):
        cl = Condition_Log.objects.create(label="sample label", description="description", created_by=None, modified_by=user)
        cl.full_clean()
        assert cl.pk is not None

    # Test that modified_by can be None (allowed since null=True) and still save
    @pytest.mark.django_db
    def test_condition_log_modified_by_null(self, user):
        cl = Condition_Log.objects.create(label="sample label", description="description", created_by=user, modified_by=None)
        cl.full_clean()
        assert cl.pk is not None


#==================================================================================
# TESTS MODEL CONDITION_LOG_IMAGE
#==================================================================================
class TestConditionImage:
    # Test that a valid Condition_Image instance is created
    @pytest.mark.django_db 
    def test_condition_image_creation_valid(self, condition_log, user):
        image_file = SimpleUploadedFile("image.jpg", b"content", content_type="image/jpeg")
        ci = Condition_Image.objects.create(
            condition_log_id=condition_log,
            image=image_file,
            caption="Caption",
            created_by=user,
            modified_by=user
        )
        assert ci.pk is not None

    # Test that if caption is not provided, it defaults to an empty string
    @pytest.mark.django_db
    def test_condition_image_missing_caption(self, condition_log, user):
        image_file = SimpleUploadedFile("image1.jpg", b"content", content_type="image/jpeg")
        ci = Condition_Image.objects.create(
            condition_log_id=condition_log,
            image=image_file,
            created_by=user,
            modified_by=user
        )
        assert ci.caption == ""

    # Test that the __str__ method returns the instance's id as a string
    @pytest.mark.django_db
    def test_condition_image_str(self, condition_image):
        assert str(condition_image) == str(condition_image.id)

    # Test that the relationship to Condition_Log is correctly set
    @pytest.mark.django_db
    def test_condition_image_relationship_condition_log(self, condition_image, condition_log):
        assert condition_image.condition_log_id == condition_log

    # Test that updating the caption field is persisted
    @pytest.mark.django_db
    def test_condition_image_update_caption(self, condition_image):
        condition_image.caption = "new caption"
        condition_image.save()
        assert condition_image.caption == "new caption"

    # Test that auto-populated fields (created and modified) are set
    @pytest.mark.django_db
    def test_condition_image_auto_fields(self, condition_image):
        assert condition_image.created is not None and condition_image.modified is not None

    # Test that multiple Condition_Image instances have unique primary keys
    @pytest.mark.django_db
    def test_condition_image_multiple_instances(self, condition_log, user):
        image_file1 = SimpleUploadedFile("image2.jpg", b"content", content_type="image/jpeg")
        image_file2 = SimpleUploadedFile("image3.jpg", b"content", content_type="image/jpeg")
        ci1 = Condition_Image.objects.create(
            condition_log_id=condition_log,
            image=image_file1,
            caption="caption image2",
            created_by=user,
            modified_by=user
        )
        ci2 = Condition_Image.objects.create(
            condition_log_id=condition_log,
            image=image_file2,
            caption="caption image3",
            created_by=user,
            modified_by=user
        )
        assert ci1.pk != ci2.pk


    # Test that the image file field is populated 
    @pytest.mark.django_db
    def test_condition_image_file_field(self, condition_log, user):
        image_file = SimpleUploadedFile("image4.jpg", b"content", content_type="image/jpeg")
        ci = Condition_Image.objects.create(
            condition_log_id=condition_log,
            image=image_file,
            caption="caption image4",
            created_by=user,
            modified_by=user
        )
        assert ci.image.name is not None

    # Boundary Test: Verify that a caption with exactly 255 characters is valid
    @pytest.mark.django_db
    def test_condition_image_caption_max_length_valid(self, condition_log, user):
        caption = "A" * 255 
        image_file = SimpleUploadedFile("cond4.jpg", b"content", content_type="image/jpeg")
        ci = Condition_Image.objects.create(
            condition_log_id=condition_log,
            image=image_file,
            caption=caption,
            created_by=user,
            modified_by=user
        )
        ci.full_clean()
        assert ci.pk is not None

    # Boundary Test: Verify that a caption with 256 characters raises a ValidationError
    @pytest.mark.django_db
    def test_condition_image_caption_max_length_invalid(self, condition_log, user):
        caption = "A" * 256  
        image_file = SimpleUploadedFile("cond5.jpg", b"content", content_type="image/jpeg")
        ci = Condition_Image(
            condition_log_id=condition_log,
            image=image_file,
            caption=caption,
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            ci.full_clean()

    # Test that missing the required image field raises a ValidationErro
    @pytest.mark.django_db
    def test_condition_image_missing_image(self, condition_log, user):
        ci = Condition_Image(
            condition_log_id=condition_log,
            caption="image missing",
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            ci.full_clean()

    # Test updating the image file field and verifying that the new file is used
    @pytest.mark.django_db
    def test_condition_image_update_file(self, condition_log, user, condition_image):
        new_image_file = SimpleUploadedFile("image45.jpg", b"new content", content_type="image/jpeg")
        condition_image.image = new_image_file
        condition_image.save()
        # Check that the image name contains "image45" and ends with ".jpg"
        assert re.search(r"image45.*\.jpg$", condition_image.image.name)


# #==================================================================================
# # TESTS MODEL TRANSACTION
# #==================================================================================
class TestTransaction:
    # Test that a valid Transaction instance is created
    @pytest.mark.django_db 
    def test_transaction_creation_valid(self, items_for_loan, member, user, user2, condition_log):
        borrower = Member.objects.create(
            user_id=user2,
            building_id=member.building_id,
            access_code_id=member.access_code_id,
            nickname="nickname user2",
            flat_no="15",
            created_by=user,
            modified_by=user
        )
        t = Transaction.objects.create(
            items_for_loan_id=items_for_loan,
            lender_member_id=member,
            borrower_member_id=borrower,
            before_condition=condition_log,
            after_condition=condition_log,
            borrowed_on=datetime.datetime.now(),
            borrowed_until=datetime.datetime.now() + datetime.timedelta(days=5),
            reminder=ReminderType.STANDARD,
            created_by=user,
            modified_by=user
        )
        assert t.pk is not None

    # Test that missing required fields causes an IntegrityError
    @pytest.mark.django_db
    def test_transaction_missing_required_fields(self, member, user, condition_log):
        t = Transaction(
            lender_member_id=member,
            borrower_member_id=member,
            reminder=ReminderType.STANDARD,
            created_by=user,
            modified_by=user
        )
        with pytest.raises(IntegrityError):
            t.save()

    # Test that the __str__ method returns the Transaction's id as a string
    @pytest.mark.django_db
    def test_transaction_str(self, transaction):
        assert str(transaction) == str(transaction.id)

    # Test that the items_for_loan relationship returns the correct Items_For_Loan instance
    @pytest.mark.django_db
    def test_transaction_relationship_items_for_loan(self, transaction, items_for_loan):
        assert transaction.items_for_loan_id == items_for_loan

    # Test that the lender_member relationship returns the correct Member instance
    @pytest.mark.django_db
    def test_transaction_relationship_lender_member(self, transaction, member):
        assert transaction.lender_member_id == member

    # Test that the borrower_member relationship returns a valid Member instance
    @pytest.mark.django_db
    def test_transaction_relationship_borrower_member(self, transaction):
        assert transaction.borrower_member_id is not None

    # Test that the condition relationships return the correct Condition_Log instance
    @pytest.mark.django_db
    def test_transaction_relationship_conditions(self, transaction, condition_log):
        assert transaction.before_condition == condition_log
        assert transaction.after_condition == condition_log

    # Test that updating the return_date field works correctly
    @pytest.mark.django_db
    def test_transaction_update_return_date(self, transaction):
        now = datetime.datetime.now()
        transaction.return_date = now
        transaction.save()
        assert transaction.return_date == now

    # Test that the custom manager method get_borrowed_items returns a list
    @pytest.mark.django_db
    def test_transaction_custom_manager_get_borrowed_items(self, member, user, transaction):
        results = Transaction.custom_objects.get_borrowed_items(member.id)
        assert isinstance(results, list)

    # Test that the custom manager method get_loaned_items returns a list
    @pytest.mark.django_db
    def test_transaction_custom_manager_get_loaned_items(self, member, user, transaction):
        results = Transaction.custom_objects.get_loaned_items(member.id)
        assert isinstance(results, list)

    # Test that each valid reminder choice is accepted
    @pytest.mark.django_db
    def test_transaction_valid_reminder_choices(self, items_for_loan, member, user, user2, condition_log):
        borrower = Member.objects.create(
            user_id=user2,
            building_id=member.building_id,
            access_code_id=member.access_code_id,
            nickname="nickname user 2",
            flat_no="16",
            created_by=user,
            modified_by=user
        )
        for valid_reminder in [ReminderType.STANDARD, ReminderType.REMINDER_DAY, ReminderType.REMINDER_HOURS, ReminderType.OVERDUE, ReminderType.OVERDUE_ESC]:
            t = Transaction.objects.create(
                items_for_loan_id=items_for_loan,
                lender_member_id=member,
                borrower_member_id=borrower,
                before_condition=condition_log,
                after_condition=condition_log,
                borrowed_on=datetime.datetime.now(),
                borrowed_until=datetime.datetime.now() + datetime.timedelta(days=5),
                reminder=valid_reminder,
                created_by=user,
                modified_by=user
            )
            t.full_clean()
            assert t.reminder == valid_reminder

    # Test that an invalid reminder value raises a ValidationError
    @pytest.mark.django_db
    def test_transaction_invalid_reminder(self, items_for_loan, member, user, user2, condition_log):
        borrower = Member.objects.create(
            user_id=user2,
            building_id=member.building_id,
            access_code_id=member.access_code_id,
            nickname="nickname",
            flat_no="17",
            created_by=user,
            modified_by=user
        )
        t = Transaction(
            items_for_loan_id=items_for_loan,
            lender_member_id=member,
            borrower_member_id=borrower,
            before_condition=condition_log,
            after_condition=condition_log,
            borrowed_on=datetime.datetime.now(),
            borrowed_until=datetime.datetime.now() + datetime.timedelta(days=5),
            reminder="XX", 
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            t.full_clean()

    # Test that a transaction with both borrowed_on and borrowed_until as None is valid
    @pytest.mark.django_db
    def test_transaction_nullable_datetime_fields(self, items_for_loan, member, user, user2, condition_log):
        borrower = Member.objects.create(
            user_id=user2,
            building_id=member.building_id,
            access_code_id=member.access_code_id,
            nickname="nickname user",
            flat_no="18",
            created_by=user,
            modified_by=user
        )
        t = Transaction.objects.create(
            items_for_loan_id=items_for_loan,
            lender_member_id=member,
            borrower_member_id=borrower,
            before_condition=condition_log,
            after_condition=condition_log,
            borrowed_on=None,
            borrowed_until=None,
            reminder=ReminderType.STANDARD,
            created_by=user,
            modified_by=user
        )
        t.full_clean()
        assert t.borrowed_on is None and t.borrowed_until is None

    # Test that invalid datetime values for borrowed_on raise a ValidationError
    @pytest.mark.django_db
    def test_transaction_invalid_borrowed_on(self, items_for_loan, member, user, user2, condition_log):
        borrower = Member.objects.create(
            user_id=user2,
            building_id=member.building_id,
            access_code_id=member.access_code_id,
            nickname="nickname user",
            flat_no="19",
            created_by=user,
            modified_by=user
        )
        t = Transaction(
            items_for_loan_id=items_for_loan,
            lender_member_id=member,
            borrower_member_id=borrower,
            before_condition=condition_log,
            after_condition=condition_log,
            borrowed_on="XX", 
            borrowed_until=datetime.datetime.now() + datetime.timedelta(days=5),
            reminder=ReminderType.STANDARD,
            created_by=user,
            modified_by=user
        )
        with pytest.raises(ValidationError):
            t.full_clean()
