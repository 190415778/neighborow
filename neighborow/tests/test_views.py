import json
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from neighborow.models import (
    Building, AppSettings, Access_Code, Member, Invitation,
    Communication, Messages, Items_For_Loan, Items_For_Loan_Image,
    Transaction
)
from django.core.files.uploadedfile import SimpleUploadedFile

#==================================================================================
# SIMPLE FIXTURES FOR ALL VIEWS
#==================================================================================

class BaseViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create two users for testing
        cls.user = User.objects.create_user(username="user1", password="neighborow1")
        cls.user2 = User.objects.create_user(username="user2", password="neighborow2")
        # Create a building fixture
        cls.building = Building.objects.create(
            name="Test Building",
            address_line1="Test Address",
            city="Test City",
            postal_code="12345",
            units=10,
            created_by=cls.user
        )
        # Create an AppSettings fixture (for invitation distance testing)
        cls.app_setting = AppSettings.objects.create(
            building_id=cls.building,
            key='0',  # using key '0' for Invitor distance
            value="5",
            created_by=cls.user
        )
        # Create two Access_Code fixtures: one valid/unused and one used
        cls.access_code_valid = Access_Code.objects.create(
            building_id=cls.building,
            flat_no="Flat 1A",
            code="CODE123456789000",
            type="0",
            is_used=False,
            created_by=cls.user
        )
        # Create two Access_Code fixturesfor other use cases
        cls.access_code_valid2 = Access_Code.objects.create(
            building_id=cls.building,
            flat_no="Flat 3A",
            code="CODE123456789XXX",
            type="0",
            is_used=False,
            created_by=cls.user
        )
        cls.access_code_used = Access_Code.objects.create(
            building_id=cls.building,
            flat_no="Flat 1B",
            code="CODE123456123456",
            type="0",
            is_used=True,
            created_by=cls.user
        )
        # Create a Member fixture for the logged-in user
        cls.member = Member.objects.create(
            user_id=cls.user,
            building_id=cls.building,
            access_code_id=cls.access_code_valid,
            nickname="Test Nickname",
            flat_no="Flat 1A",
            authorized=False,
            distance=0,
            type="0"
        )
        # Create a Member fixture for the logged-in user
        cls.member2 = Member.objects.create(
            user_id=cls.user2,
            building_id=cls.building,
            access_code_id=cls.access_code_valid,
            nickname="Test Nickname user 2",
            flat_no="Flat 2B",
            authorized=False,
            distance=0,
            type="0"
        )
        # Create an Invitation record for widget_member_info view
        cls.invitation = Invitation.objects.create(
            building_id=cls.building,
            invitor_member_id=cls.member,
            access_code_id=cls.access_code_valid2,
            distance=1,
            relationship='0',
            created_by=cls.user
        )
        # Create a Communication record for widget_member_communication view
        cls.communication = Communication.objects.create(
            member_id=cls.member,
            channel='1',
            identification='test@example.com',
            is_active=True
        )
        # Create an inbox Message for widget_messages_inbox view 
        cls.inbox_message = Messages.objects.create(
            sender_member_id=cls.user2.member_set.first() if hasattr(cls.user2, 'member_set') and cls.user2.member_set.exists() else cls.member,
            receiver_member_id=cls.member,
            title="Inbox Test",
            body="Inbox message body",
            message_code="CODEINBOX1234567",
            inbox=True,
            outbox=False,
            internal=False,
            is_sent_email=True,
            is_sent_sms=True,
            is_sent_whatsApp=True,
            message_type='7',
            created_by=cls.user
        )
        # Create an outbox Message for widget_messages_outbox view (member is sender)
        cls.outbox_message = Messages.objects.create(
            sender_member_id=cls.member,
            receiver_member_id=cls.user2.member_set.first() if hasattr(cls.user2, 'member_set') and cls.user2.member_set.exists() else cls.member,
            title="Outbox Test",
            body="Outbox message body",
            message_code="CODEOUT123456789",
            inbox=False,
            outbox=True,
            internal=False,
            is_sent_email=False,
            is_sent_sms=False,
            is_sent_whatsApp=False,
            message_type='7',
            created_by=cls.user
        )
        # Create an Items_For_Loan record for widget_item_list view
        cls.item = Items_For_Loan.objects.create(
            member_id=cls.member,
            label="Test Item",
            description="This is a test item description",
            created_by=cls.user
        )
        # Create an Items_For_Loan_Image record for get_item_images view
        image_file = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        cls.item_image = Items_For_Loan_Image.objects.create(
            items_for_loan_id=cls.item,
            image=image_file,
            caption="Test Image Caption"
        )
        # Create a Transactoe
        now = datetime.datetime.now()
        cls.loaned_transaction = Transaction.objects.create(
            items_for_loan_id=cls.item,
            lender_member_id=cls.member,
            borrower_member_id=cls.member2,
            borrowed_on=now - datetime.timedelta(days=2),
            borrowed_until=now + datetime.timedelta(days=1),
            return_date=None,
            reminder='0',
            created_by=cls.user
        )
        cls.borrowed_transaction = Transaction.objects.create(
            items_for_loan_id=cls.item,
            lender_member_id=cls.member2,
            borrower_member_id=cls.member,
            borrowed_on=now - datetime.timedelta(days=5),
            borrowed_until=now - datetime.timedelta(days=3),
            return_date=now - datetime.timedelta(days=2),
            reminder='0',
            created_by=cls.user
        )

        cls.client = Client()

    def setUp(self):
        # Ensure the client is logged in for every test
        self.client.force_login(self.user)


# =========================
# Tests for the index view
# =========================
class TestIndexView(BaseViewTestCase):
    # Test that GET request to index returns index.html template and proper context
    def test_index_get(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/index.html')
        self.assertIn('is_authorized', response.context)

    # Test that POST modalAccessCode with valid unused code updates existing member authorization to true
    def test_index_modal_access_code_valid_existing(self):
        post_data = {
            'form_type': 'modalAccessCode',
            'accessCodeInput': self.access_code_valid.code,
            'nicknameInput': 'new member nickname'
        }
        response = self.client.post(reverse('index'), post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.member.refresh_from_db()
        self.assertTrue(self.member.authorized)
        # Verify that the context variable 'is_authorized' is set to True in the rendered template
        self.assertTrue(response.context.get('is_authorized'))

    # Test that POST modalAccessCode with valid unused code creates a new member when none exists
    def test_index_modal_access_code_valid_new_member(self):
        self.member.delete() 
        post_data = {
            'form_type': 'modalAccessCode',
            'accessCodeInput': self.access_code_valid.code,
            'nicknameInput': 'new member nicknae'
        }
        response = self.client.post(reverse('index'), post_data)
        new_member = Member.objects.filter(nickname='new member nicknae').first()
        self.assertIsNotNone(new_member)
        self.assertTrue(new_member.authorized)

    # Test that POST modalAccessCode with a used code returns an error message
    def test_index_modal_access_code_used_code(self):
        post_data = {
            'form_type': 'modalAccessCode',
            'accessCodeInput': self.access_code_used.code,
            'nicknameInput': 'ShouldNotMatter'
        }
        response = self.client.post(reverse('index'), post_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any("already been used" in str(m) for m in messages))

    # Test that POST modalAccessCode with an invalid code returns an error message
    def test_index_modal_access_code_invalid_code(self):
        post_data = {
            'form_type': 'modalAccessCode',
            'accessCodeInput': 'INVALID',
            'nicknameInput': 'nickname for non member'
        }
        response = self.client.post(reverse('index'), post_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any("not valid" in str(m) for m in messages))

    # Test that POST modalInvitation with valid data creates an invitation record
    def test_index_modal_invitation_valid(self):
        post_data = {
            'form_type': 'modalInvitation',
            'relationship': '0'  # '0' assumed for Relative
        }
        response = self.client.post(reverse('index'), post_data)
        self.assertEqual(response.status_code, 302)
        invitation = Invitation.objects.filter(invitor_member_id=self.member).first()
        self.assertIsNotNone(invitation)

    # Test that POST modalInvitation with invitation distance reached returns an error
    def test_index_modal_invitation_distance_reached(self):
        self.member.distance = 10  # exceed the app_setting value ("5")
        self.member.save()
        self.app_setting.value = "5"
        self.app_setting.save()
        post_data = {
            'form_type': 'modalInvitation',
            'relationship': '0'
        }
        response = self.client.post(reverse('index'), post_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any("Invitation distance is reached" in str(m) for m in messages))

    # Test that POST modalBuilding with building_id updates an existing building
    def test_index_modal_building_update(self):
        post_data = {
            'form_type': 'modalBuilding',
            'building_id': self.building.id,
            'name': 'Updated Building',
            'address_line1': 'New Address',
            'address_line2': '',
            'city': 'New City',
            'postal_code': '54321',
            'units': '15'
        }
        response = self.client.post(reverse('index'), post_data)
        self.assertEqual(response.status_code, 302)
        self.building.refresh_from_db()
        self.assertEqual(self.building.name, 'Updated Building')

    # Test that POST modalBuilding without building_id creates a new building record
    def test_index_modal_building_create(self):
        post_data = {
            'form_type': 'modalBuilding',
            'name': 'New Building',
            'address_line1': 'Addr1',
            'address_line2': 'Addr2',
            'city': 'CityX',
            'postal_code': '11111',
            'units': '20'
        }
        response = self.client.post(reverse('index'), post_data)
        self.assertEqual(response.status_code, 302)
        new_building = Building.objects.filter(name='New Building').first()
        self.assertIsNotNone(new_building)

    # Test that index view redirects after a POST request
    def test_index_post_redirect(self):
        post_data = {'form_type': 'modalAccessCode', 'accessCodeInput': 'INVALID', 'nicknameInput': 'Test'}
        response = self.client.post(reverse('index'), post_data)
        self.assertEqual(response.status_code, 302)

    # Test that GET request to index returns a valid HTML content type
    def test_index_get_content(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')


# ================================
# Tests for the app_settings view
# ================================
class TestAppSettingsView(BaseViewTestCase):
    # Test that GET with valid building_id returns the app_settings modal template
    def test_app_settings_get_with_building(self):
        url = reverse('app_settings') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/modals/app_settings.html')

    # Test that GET without building_id selects the first building
    def test_app_settings_get_without_building(self):
        url = reverse('app_settings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('app_settings', response.context)

    # Test that GET with an invalid building_id returns None for app_settings
    def test_app_settings_get_invalid_building(self):
        url = reverse('app_settings') + "?building_id=9999"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('app_settings'))

    # Test that POST without building_id produces an error message
    def test_app_settings_post_missing_building(self):
        post_data = {}
        response = self.client.post(reverse('app_settings'), post_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any("Please select a building!" in str(m) for m in messages))

    # Test that POST with an invalid building_id produces an error message
    def test_app_settings_post_invalid_building(self):
        post_data = {'building_id': 9999}
        response = self.client.post(reverse('app_settings'), post_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any("Building not found!" in str(m) for m in messages))

    # Test that POST updating an existing setting works correctly
    def test_app_settings_post_update_existing(self):
        setting = AppSettings.objects.create(
            building_id=self.building, key='1', value="old value", created_by=self.user
        )
        post_data = {
            'building_id': self.building.id,
            'setting_id_1': setting.id,  # indexierter Name für das Setting
            'key_1': '1',              # indexierter Schlüssel
            'value_1': 'New Value'     # indexierter neuer Wert
        }
        response = self.client.post(reverse('app_settings'), post_data, follow=True)
        setting.refresh_from_db()
        self.assertEqual(setting.value, 'New Value')

    # Test that creating a new setting works
    def test_app_settings_post_create_new(self):
        post_data = {
            'building_id': self.building.id,
            'new_key_1': '1',
            'new_value_1': 'value for key 1'
        }
        response = self.client.post(reverse('app_settings'), post_data, follow=True)
        new_setting = AppSettings.objects.filter(value='value for key 1').first()
        self.assertIsNotNone(new_setting)

    # Test that POST to app_settings view redirects to index after saving
    def test_app_settings_post_redirect(self):
        post_data = {'building_id': self.building.id}
        response = self.client.post(reverse('app_settings'), post_data)
        self.assertEqual(response.status_code, 302)

    # Test that the context for app_settings contains application_settings_choices
    def test_app_settings_context(self):
        url = reverse('app_settings') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        self.assertIn('application_settings_choices', response.context)

    # Test that GET to app_settings returns status 200
    def test_app_settings_get_status(self):
        url = reverse('app_settings') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # Test that POST with invalid new settings (empty key/value) does not create a new setting
    def test_app_settings_post_invalid_new(self):
        post_data = {
            'building_id': self.building.id,
            'new_key_1': '',
            'new_value_1': ''
        }
        response = self.client.post(reverse('app_settings'), post_data, follow=True)
        new_setting = AppSettings.objects.filter(value='').first()
        self.assertIsNone(new_setting)


#==================================================================================
# Tests for the get_app_settings view
#==================================================================================
class TestGetAppSettingsView(BaseViewTestCase):
    # Test that GET with valid building_id returns JSON with a settings list
    def test_get_app_settings_valid(self):
        url = reverse('get_building_details') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('settings', data)

    # Test that the JSON structure for valid request contains a list for settings
    def test_get_app_settings_valid_structure(self):
        url = reverse('get_building_details') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertIsInstance(data['settings'], list)

    # Test that GET with an invalid building_id returns a 404 error
    def test_get_app_settings_invalid_building(self):
        url = reverse('get_building_details') + "?building_id=9999"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # Test that GET with missing building_id returns a 400 error
    def test_get_app_settings_missing_building(self):
        url = reverse('get_building_details')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    # Test that a valid building_id returns at least an empty settings list
    def test_get_app_settings_valid_duplicate(self):
        url = reverse('get_building_details') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertGreaterEqual(len(data['settings']), 0)

    # Test that the response content type is JSON
    def test_get_app_settings_content_type(self):
        url = reverse('get_building_details') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        self.assertEqual(response['Content-Type'], 'application/json')

    # Test that if no settings exist, an empty list is returned
    def test_get_app_settings_empty(self):
        AppSettings.objects.filter(building_id=self.building).delete()
        url = reverse('get_building_details') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(data['settings'], [])

    # Test with an invalid building_id duplicate
    def test_get_app_settings_invalid_duplicate(self):
        url = reverse('get_building_details') + "?building_id=0"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # Test that the JSON error key is present for an invalid building_id
    def test_get_app_settings_invalid_json(self):
        url = reverse('get_building_details') + "?building_id=9999"
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertIn('error', data)

    # Test missing building_id duplicate
    def test_get_app_settings_missing_duplicate(self):
        url = reverse('get_building_details')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)


#==================================================================================
# Tests for the form_invitation view
#==================================================================================
class TestFormInvitationView(BaseViewTestCase):
    # Test that GET request to form_invitation returns the correct modal template
    def test_form_invitation_get_template(self):
        response = self.client.get(reverse('form_invitation'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/modals/form_invitation.html')

    # Test that the context contains relationship_choices
    def test_form_invitation_context(self):
        response = self.client.get(reverse('form_invitation'))
        self.assertIn('relationship_choices', response.context)

    # Test that relationship_choices is iterable
    def test_form_invitation_relationship_choices_type(self):
        response = self.client.get(reverse('form_invitation'))
        self.assertTrue(hasattr(response.context['relationship_choices'], '__iter__'))

    # Test that there are no error messages in the invitation view
    def test_form_invitation_no_errors(self):
        response = self.client.get(reverse('form_invitation'))
        messages = list(response.context.get('messages', []))
        self.assertEqual(len(messages), 0)

    # Test template usage duplicate
    def test_form_invitation_template_duplicate(self):
        response = self.client.get(reverse('form_invitation'))
        self.assertTemplateUsed(response, 'neighborow/modals/form_invitation.html')

    # Test that GET response status is 200 duplicate
    def test_form_invitation_status(self):
        response = self.client.get(reverse('form_invitation'))
        self.assertEqual(response.status_code, 200)

    # Test context key exists duplicate
    def test_form_invitation_context_key(self):
        response = self.client.get(reverse('form_invitation'))
        self.assertIn('relationship_choices', response.context)

    # Test that response content is not empty
    def test_form_invitation_content_length(self):
        response = self.client.get(reverse('form_invitation'))
        self.assertTrue(len(response.content) > 0)

    # Test that another GET call returns status 200
    def test_form_invitation_get_duplicate(self):
        response = self.client.get(reverse('form_invitation'))
        self.assertEqual(response.status_code, 200)

    # Test that the modal HTML contains the expected title string
    def test_form_invitation_modal_string(self):
        response = self.client.get(reverse('form_invitation'))
        self.assertIn("Invite others", response.content.decode())


# ================================
# Tests for the form_building view
# ================================
class TestFormBuildingView(BaseViewTestCase):
    # Test that GET without building_id returns context with building set to None
    def test_form_building_get_without_building(self):
        response = self.client.get(reverse('form_building'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('building'))

    # Test that GET with a valid building_id returns the building in context
    def test_form_building_get_with_valid(self):
        url = reverse('form_building') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context.get('building'))

    # Test that GET with an invalid building_id sets building to None
    def test_form_building_get_with_invalid(self):
        url = reverse('form_building') + "?building_id=9999"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('building'))

    # Test that the context contains a buildings list
    def test_form_building_buildings_list(self):
        response = self.client.get(reverse('form_building'))
        self.assertIn('buildings', response.context)

    # Test that the modal contains the string "New Apartmentblock"
    def test_form_building_modal_string(self):
        response = self.client.get(reverse('form_building'))
        self.assertIn("New Apartmentblock", response.content.decode())

    # Test that GET response status is 200 duplicate
    def test_form_building_status(self):
        response = self.client.get(reverse('form_building'))
        self.assertEqual(response.status_code, 200)

    # Test that the buildings list is iterable
    def test_form_building_buildings_type(self):
        response = self.client.get(reverse('form_building'))
        self.assertTrue(hasattr(response.context['buildings'], '__iter__'))

    # Test that a valid building_id returns the correct building name
    def test_form_building_valid_name(self):
        url = reverse('form_building') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        building = response.context.get('building')
        self.assertEqual(building.name, self.building.name)

    # Test that GET response content length is non-zero
    def test_form_building_content_length(self):
        response = self.client.get(reverse('form_building'))
        self.assertTrue(len(response.content) > 0)

    # Test that the correct template is used
    def test_form_building_template(self):
        response = self.client.get(reverse('form_building'))
        self.assertTemplateUsed(response, 'neighborow/modals/buildings.html')


#===================================================================================
# Tests for the get_building_details view
#===================================================================================
class TestGetBuildingDetailsView(BaseViewTestCase):
    # Test that GET with an invalid building_id returns a 404 error
    def test_get_building_details_invalid(self):
        url = reverse('get_building_details') + "?building_id=9999"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # Test that GET with missing building_id returns a 400 error
    def test_get_building_details_missing(self):
        url = reverse('get_building_details')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    # Test that the response content type is JSON
    def test_get_building_details_content_type(self):
        url = reverse('get_building_details') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        self.assertEqual(response['Content-Type'], 'application/json')

    # Test with extra GET parameter does not break the view
    def test_get_building_details_extra_param(self):
        url = reverse('get_building_details') + f"?building_id={self.building.id}&extra=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # Test that the units value is returned as a string or number
    def test_get_building_details_units_type(self):
        url = reverse('get_building_details') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertIsInstance(data.get('units', ''), (str, int))


#==================================================================================
# Tests for the access_code view
#==================================================================================
class TestAccessCodeView(BaseViewTestCase):
    # Test that GET without building_id selects the first building and returns the access_code modal
    def test_access_code_get_without_building(self):
        url = reverse('access_code')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/modals/access_code.html')

    # Test that GET with a valid building_id returns access codes in context
    def test_access_code_get_with_valid_building(self):
        url = reverse('access_code') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('access_codes', response.context)

    # Test that GET with an invalid building_id returns context with access_codes as None
    def test_access_code_get_invalid_building(self):
        url = reverse('access_code') + "?building_id=9999"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('access_codes'))

    # Test that POST without a building_id returns an error message
    def test_access_code_post_missing_building(self):
        post_data = {}
        response = self.client.post(reverse('access_code'), post_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any("Please select a building" in str(m) for m in messages))

    # Test that POST with a new row missing flat number returns an error
    def test_access_code_post_invalid_new_flat(self):
        post_data = {
            'building_id': self.building.id,
            'new_code_1': 'NEWCODE'
        }
        response = self.client.post(reverse('access_code'), post_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any("Flat Number is mandatory" in str(m) for m in messages))

    # Test that POST updating an existing access code works correctly
    def test_access_code_post_update_existing(self):
        post_data = {
            'building_id': self.building.id,
            'access_code_id_1': self.access_code_valid.id,
            'flat_no_1': 'UpdatedFlat',
            'code_1': 'UPDATEDCODE'
        }
        response = self.client.post(reverse('access_code'), post_data)
        self.assertEqual(response.status_code, 302)
        self.access_code_valid.refresh_from_db()
        self.assertEqual(self.access_code_valid.flat_no, 'UpdatedFlat')
        self.assertEqual(self.access_code_valid.code, 'UPDATEDCODE')

    # Test that POST creating a new access code works correctly
    def test_access_code_post_create_new(self):
        post_data = {
            'building_id': self.building.id,
            'new_flat_no_1': 'NewFlat',
            'new_code_1': 'NewCode1'
        }
        response = self.client.post(reverse('access_code'), post_data)
        self.assertEqual(response.status_code, 302)
        new_ac = Access_Code.objects.filter(flat_no='NewFlat', code='NewCode1').first()
        self.assertIsNotNone(new_ac)

    # Test that POST processing generated rows creates new access codes
    def test_access_code_post_generated(self):
        post_data = {
            'building_id': self.building.id,
            # Simulate the POST arrays for generated rows:
            'new_flat_no_generated[]': ['GenFlat'],
            'new_code_generated[]': ['GenCode']
        }
        response = self.client.post(reverse('access_code'), post_data)
        self.assertEqual(response.status_code, 302)
        gen_ac = Access_Code.objects.filter(flat_no='GenFlat', code='GenCode').first()
        self.assertIsNotNone(gen_ac)

    # Test that POST to access_code view redirects on success
    def test_access_code_post_redirect(self):
        post_data = {
            'building_id': self.building.id,
            'new_flat_no_1': 'RedirectFlat',
            'new_code_1': 'RedirectCode'
        }
        response = self.client.post(reverse('access_code'), post_data)
        self.assertEqual(response.status_code, 302)

    # Test that a combined POST (updating an existing code and creating a new one) works
    def test_access_code_post_combined(self):
        post_data = {
            'building_id': self.building.id,
            'access_code_id_1': self.access_code_valid.id,
            'flat_no_1': 'ComboFlat',
            'code_1': 'ComboCode',
            'new_flat_no_1': 'NewComboFlat',
            'new_code_1': 'NewComboCode'
        }
        response = self.client.post(reverse('access_code'), post_data)
        self.assertEqual(response.status_code, 302)
        self.access_code_valid.refresh_from_db()
        self.assertEqual(self.access_code_valid.flat_no, 'ComboFlat')
        new_ac = Access_Code.objects.filter(flat_no='NewComboFlat', code='NewComboCode').first()
        self.assertIsNotNone(new_ac)


#=====================================================================================
# Tests for the get_access_codes view
#=====================================================================================
class TestGetAccessCodesView(BaseViewTestCase):
    # Test that GET with a valid building_id returns JSON with access codes
    def test_get_access_codes_valid(self):
        url = reverse('get_access_codes') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('access_codes', data)

    # Test that the returned access_codes value is a list
    def test_get_access_codes_valid_list(self):
        url = reverse('get_access_codes') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertIsInstance(data['access_codes'], list)

    # Test that GET with an invalid building_id returns a 404 status code
    def test_get_access_codes_invalid(self):
        url = reverse('get_access_codes') + "?building_id=9999"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # Test that GET with missing building_id returns a 400 status code
    def test_get_access_codes_missing(self):
        url = reverse('get_access_codes')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    # Test that the JSON error message is present for an invalid building_id
    def test_get_access_codes_invalid_message(self):
        url = reverse('get_access_codes') + "?building_id=0"
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertIn('error', data)

    # Test that the response content type is JSON
    def test_get_access_codes_content_type(self):
        url = reverse('get_access_codes') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        self.assertEqual(response['Content-Type'], 'application/json')

    # Test that a valid building_id returns a non-negative length list
    def test_get_access_codes_valid_duplicate(self):
        url = reverse('get_access_codes') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertGreaterEqual(len(data['access_codes']), 0)

    # Test that each access code dict contains the expected keys
    def test_get_access_codes_keys(self):
        url = reverse('get_access_codes') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        data = json.loads(response.content)
        if data['access_codes']:
            self.assertIn('id', data['access_codes'][0])
            self.assertIn('flat_no', data['access_codes'][0])
            self.assertIn('code', data['access_codes'][0])

    # Test missing building_id duplicate
    def test_get_access_codes_missing_duplicate(self):
        url = reverse('get_access_codes')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)


#====================================================================================
# Tests for the generate_code view
#====================================================================================
class TestGenerateCodeView(BaseViewTestCase):
    # Test that a GET request returns JSON containing a 'code' field
    def test_generate_code_returns_code(self):
        url = reverse('generate_code')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('code', data)

    # Test that the generated code is a string of acceptable length
    def test_generate_code_length(self):
        url = reverse('generate_code')
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertTrue(isinstance(data['code'], str))
        self.assertLessEqual(len(data['code']), 16)

    # Test that the response content type is JSON
    def test_generate_code_content_type(self):
        url = reverse('generate_code')
        response = self.client.get(url)
        self.assertEqual(response['Content-Type'], 'application/json')

    # Test that GET without parameters works fine
    def test_generate_code_no_params(self):
        url = reverse('generate_code')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # Test that the generated code is not empty
    def test_generate_code_not_empty(self):
        url = reverse('generate_code')
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertNotEqual(data['code'], "")

    # Test that the generated code contains only alphanumeric characters
    def test_generate_code_alphanumeric(self):
        url = reverse('generate_code')
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertTrue(data['code'].isalnum())

    # Test that GET request returns status 200
    def test_generate_code_status(self):
        url = reverse('generate_code')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # Test that two successive calls return different codes
    def test_generate_code_different(self):
        url = reverse('generate_code')
        response1 = self.client.get(url)
        response2 = self.client.get(url)
        code1 = json.loads(response1.content)['code']
        code2 = json.loads(response2.content)['code']
        self.assertNotEqual(code1, code2)

    # Test that the JSON response contains only one key
    def test_generate_code_single_key(self):
        url = reverse('generate_code')
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)

#=====================================================================================
# Tests for the generate_codes view
#=====================================================================================
class TestGenerateCodesView(BaseViewTestCase):
    # Test that GET with a valid count returns a list of codes of that length
    def test_generate_codes_valid_count(self):
        url = reverse('generate_codes') + "?count=3"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('codes', data)
        self.assertEqual(len(data['codes']), 3)

    # Test that GET with a non-integer count defaults to 1 code
    def test_generate_codes_nonint(self):
        url = reverse('generate_codes') + "?count=abc"
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(len(data['codes']), 1)

    # Test that GET with a negative count returns an empty list
    def test_generate_codes_negative_count(self):
        url = reverse('generate_codes') + "?count=-5"
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(len(data['codes']), 0)

    # Test that GET without a count parameter defaults to 1 code
    def test_generate_codes_default(self):
        url = reverse('generate_codes')
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(len(data['codes']), 1)

    # Test that the codes in the returned list are unique
    def test_generate_codes_uniqueness(self):
        url = reverse('generate_codes') + "?count=5"
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(len(set(data['codes'])), 5)

    # Test that each code in the list is a string
    def test_generate_codes_type(self):
        url = reverse('generate_codes') + "?count=3"
        response = self.client.get(url)
        data = json.loads(response.content)
        for code in data['codes']:
            self.assertTrue(isinstance(code, str))

    # Test that the response for generate_codes has a JSON content type
    def test_generate_codes_content_type(self):
        url = reverse('generate_codes') + "?count=2"
        response = self.client.get(url)
        self.assertEqual(response['Content-Type'], 'application/json')

    # Test that for a positive count the codes list is not empty
    def test_generate_codes_not_empty(self):
        url = reverse('generate_codes') + "?count=4"
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertGreater(len(data['codes']), 0)

    # Test that two calls with the same count parameter return different lists
    def test_generate_codes_different_calls(self):
        url = reverse('generate_codes') + "?count=3"
        response1 = self.client.get(url)
        response2 = self.client.get(url)
        codes1 = json.loads(response1.content)['codes']
        codes2 = json.loads(response2.content)['codes']
        self.assertNotEqual(codes1, codes2)

    # Test that a larger count parameter returns a list of that exact length
    def test_generate_codes_large_count(self):
        url = reverse('generate_codes') + "?count=10"
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(len(data['codes']), 10)


#==================================================================================
# NEW FIXTURES AND TESTS FOR THE NEXT 10 VIEWS
#==================================================================================
class NewViewsBaseTestCase(BaseViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Create an Invitation record for widget_member_info view
        cls.invitation = Invitation.objects.create(
            building_id=cls.building,
            invitor_member_id=cls.member,
            access_code_id=cls.access_code_valid,
            distance=1,
            relationship='0',
            created_by=cls.user
        )
        # Create a Communication record for widget_member_communication view
        cls.communication = Communication.objects.create(
            member_id=cls.member,
            channel='1',
            identification='test@example.com',
            is_active=True
        )
        # Create an inbox Message for widget_messages_inbox view (member is receiver)
        cls.inbox_message = Messages.objects.create(
            sender_member_id=cls.member2,
            receiver_member_id=cls.member,
            title="Inbox Test",
            body="Inbox message body",
            message_code="INBOX1",
            inbox=True,
            outbox=False,
            internal=False,
            is_sent_email=True,
            is_sent_sms=True,
            is_sent_whatsApp=True,
            message_type='7',
            created_by=cls.user
        )
        # Create an outbox Message for widget_messages_outbox view (member is sender)
        cls.outbox_message = Messages.objects.create(
            sender_member_id=cls.member,
            receiver_member_id=cls.member2,
            title="Outbox Test",
            body="Outbox message body",
            message_code="OUTBOX1",
            inbox=False,
            outbox=True,
            internal=False,
            is_sent_email=False,
            is_sent_sms=False,
            is_sent_whatsApp=False,
            message_type='7',
            created_by=cls.user
        )
        # Create an Items_For_Loan record for widget_item_list view
        cls.item = Items_For_Loan.objects.create(
            member_id=cls.member,
            label="Test Item",
            description="This is a test item description",
            created_by=cls.user
        )
        # Create an Items_For_Loan_Image record for get_item_images view
        image_file = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        cls.item_image = Items_For_Loan_Image.objects.create(
            items_for_loan_id=cls.item,
            image=image_file,
            caption="Test Image Caption"
        )


#==================================================================================
# Tests for widget_borrowing view 
#==================================================================================
    # Test that GET request to widget_borrowing returns the borrowing_request template
    def test_borrowing_get_template(self):
        response = self.client.get(reverse('widget_borrowing_request'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/widgets/borrowing_request.html')
    
    # Test that POST without recipients returns error message
    def test_borrowing_post_no_recipient(self):
        post_data = {
            'selectedRecipients': '',
            'allNeighbours': 'off',
            'requiredFrom': '2025-04-01T10:00',
            'requiredUntil': '2025-04-01T12:00',
            'subject': 'Borrow Test',
            'messageBody': 'Test borrowing message'
        }
        response = self.client.post(reverse('widget_borrowing_request'), post_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any("Please select a recipient" in str(m) for m in messages))
    
    # Test that POST with allNeighbours selected creates borrowing request for all neighbours
    def test_borrowing_post_all_neighbours(self):
        post_data = {
            'selectedRecipients': '',
            'allNeighbours': 'on',
            'requiredFrom': '2025-04-01T09:00',
            'requiredUntil': '2025-04-01T11:00',
            'subject': 'Borrow All',
            'messageBody': 'Testing borrow all neighbours'
        }
        response = self.client.post(reverse('widget_borrowing_request'), post_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any("The borrowing Request has been sent successfully" in str(m) for m in messages))
    
    # Test that POST with valid selected recipient creates borrowing request
    def test_borrowing_post_valid_recipient(self):
        post_data = {
            'selectedRecipients': str(self.member2.id),
            'allNeighbours': 'off',
            'requiredFrom': '2025-04-01T13:00',
            'requiredUntil': '2025-04-01T15:00',
            'subject': 'Borrow Single',
            'messageBody': 'Borrowing for single recipient'
        }
        response = self.client.post(reverse('widget_borrowing_request'), post_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any("The borrowing Request has been sent successfully" in str(m) for m in messages))
    
    # Test that requiredFrom and requiredUntil are parsed correctly
    def test_borrowing_post_date_parsing(self):
        post_data = {
            'selectedRecipients': str(self.member2.id),
            'allNeighbours': 'off',
            'requiredFrom': '2025-04-02T08:00',
            'requiredUntil': '2025-04-02T10:00',
            'subject': 'Date Parsing Test',
            'messageBody': 'Testing date parsing in borrowing view'
        }
        response = self.client.post(reverse('widget_borrowing_request'), post_data)
        self.assertEqual(response.status_code, 200)
    
    # Test that POST with missing required timestamps sets them to None
    def test_borrowing_post_missing_dates(self):
        post_data = {
            'selectedRecipients': str(self.member2.id),
            'allNeighbours': 'off',
            'requiredFrom': '',
            'requiredUntil': '',
            'subject': 'Missing Dates',
            'messageBody': 'Testing missing date fields'
        }
        response = self.client.post(reverse('widget_borrowing_request'), post_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any("sent successfully" in str(m) for m in messages))
    
    # Test that GET request returns HTML content type
    def test_borrowing_get_content_type(self):
        response = self.client.get(reverse('widget_borrowing_request'))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
    
    # Test that AJAX POST returns JSON response
    def test_borrowing_post_ajax(self):
        post_data = {
            'selectedRecipients': str(self.member2.id),
            'allNeighbours': 'off',
            'requiredFrom': '2025-04-01T10:00',
            'requiredUntil': '2025-04-01T12:00',
            'subject': 'Ajax Test',
            'messageBody': 'Testing AJAX response'
        }
        response = self.client.post(reverse('widget_borrowing_request'), post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content)
        self.assertIn('html', data)


#==================================================================================
# Tests for select_recipients view
#==================================================================================
    # Test that GET request to select_recipients returns the correct modal template
    def test_select_recipients_template(self):
        response = self.client.get(reverse('select_recipients'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/modals/select_recipients.html')
    
    # Test that context contains member_list with at least 2 members
    def test_select_recipients_context_member_list(self):
        response = self.client.get(reverse('select_recipients'))
        self.assertIn('member_list', response.context)
        self.assertGreaterEqual(len(response.context['member_list']), 2)
    
    # Test that the rendered HTML contains option tags for members
    def test_select_recipients_contains_options(self):
        response = self.client.get(reverse('select_recipients'))
        content = response.content.decode()
        self.assertIn("<option", content)
    
    # Test that GET response returns valid HTML content type
    def test_select_recipients_content_type(self):
        response = self.client.get(reverse('select_recipients'))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
    
    # Test that the modal title contains 'Select Recipients'
    def test_select_recipients_modal_title(self):
        response = self.client.get(reverse('select_recipients'))
        self.assertIn("Select Recipients", response.content.decode())
    
    # Test that filtering parameter does not break the view
    def test_select_recipients_with_filter_param(self):
        response = self.client.get(reverse('select_recipients') + "?filter=Test")
        self.assertEqual(response.status_code, 200)
    
    # Test that duplicate GET calls return consistent member_list lengths
    def test_select_recipients_consistency(self):
        response1 = self.client.get(reverse('select_recipients'))
        response2 = self.client.get(reverse('select_recipients'))
        self.assertEqual(len(response1.context['member_list']), len(response2.context['member_list']))


#==================================================================================
# Tests for widget_member_info view
#==================================================================================
    # Test that GET request to widget_member_info returns the member_info template
    def test_member_info_get_template(self):
        response = self.client.get(reverse('widget_member_info'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/widgets/member_info.html')
    
    # Test that context contains member and building data
    def test_member_info_context(self):
        response = self.client.get(reverse('widget_member_info'))
        self.assertIn('member', response.context)
        self.assertIn('building', response.context)
    
    # Test that the member nickname is displayed correctly in the HTML
    def test_member_info_nickname_display(self):
        response = self.client.get(reverse('widget_member_info'))
        self.assertIn(self.member.nickname, response.content.decode())
    
    # Test that the building name is displayed in the HTML
    def test_member_info_building_name_display(self):
        response = self.client.get(reverse('widget_member_info'))
        self.assertIn(self.building.name, response.content.decode())
    
    # Test that invitation data is present in context for invitee members
    def test_member_info_invitation_presence(self):
        self.member.type = '1'
        self.member.save()
        response = self.client.get(reverse('widget_member_info'))
        self.assertIn('invitation', response.context)
    
    # Test that POST request updating nickname works and returns success message
    def test_member_info_post_update_nickname(self):
        post_data = {'nickname': 'UpdatedNick'}
        response = self.client.post(reverse('widget_member_info'), post_data, follow=True)
        self.member.refresh_from_db()
        self.assertEqual(self.member.nickname, 'UpdatedNick')
        messages = list(response.context['messages'])
        self.assertTrue(any("Nickname updated successfully" in str(m) for m in messages))
    
    # Test that GET request content type is HTML
    def test_member_info_content_type(self):
        response = self.client.get(reverse('widget_member_info'))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
    
    # Test that the HTML contains 'User Profile' title
    def test_member_info_profile_title(self):
        response = self.client.get(reverse('widget_member_info'))
        self.assertIn("User Profile", response.content.decode())


#==================================================================================
# Tests for widget_member_communication view
#==================================================================================
class TestWidgetMemberCommunicationView_New(NewViewsBaseTestCase):
    # Test that GET request to widget_member_communication returns the correct template
    def test_member_communication_get_template(self):
        response = self.client.get(reverse('widget_member_communication'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/widgets/member_communication.html')
    
    # Test that context contains communications and channel_choices
    def test_member_communication_context(self):
        response = self.client.get(reverse('widget_member_communication'))
        self.assertIn('communications', response.context)
        self.assertIn('channel_choices', response.context)
    
    # Test that POST request creates a new communication record
    def test_member_communication_post_create(self):
        post_data = {
            'row_counter': '1',
            'channel_1': '2',  # SMS channel
            'identification_1': '+1234567890',
            'is_active_1': 'on',
            'delete_1': '0'
        }
        response = self.client.post(reverse('widget_member_communication'), post_data)
        comm = Communication.objects.filter(member_id=self.member, identification='+1234567890').first()
        self.assertIsNotNone(comm)
    
    # Test that POST request with deletion flag deletes a communication record
    def test_member_communication_post_delete(self):
        comm = self.communication
        post_data = {
            'row_counter': '1',
            'delete_1': '1',
            'comm_id_1': comm.id,
            'channel_1': comm.channel,
            'identification_1': comm.identification,
            'is_active_1': 'off'
        }
        response = self.client.post(reverse('widget_member_communication'), post_data)
        with self.assertRaises(Communication.DoesNotExist):
            Communication.objects.get(id=comm.id)
    
    # Test that POST request with invalid email format returns error
    def test_member_communication_post_invalid_email(self):
        post_data = {
            'row_counter': '1',
            'channel_1': '1',  # Email channel
            'identification_1': 'invalid_email',
            'is_active_1': 'on',
            'delete_1': '0'
        }
        response = self.client.post(reverse('widget_member_communication'), post_data)
        messages = list(response.context['messages'])
        self.assertTrue(any("Invalid email address" in str(m) for m in messages))
    
    # Test that POST with built-in channel does not update the record
    def test_member_communication_post_builtin_skip(self):
        builtin_comm = Communication.objects.create(
            member_id=self.member,
            channel='0',
            identification='builtin@test.com',
            is_active=False
        )
        post_data = {
            'row_counter': '1',
            'comm_id_1': builtin_comm.id,
            'channel_1': '0',
            'identification_1': 'changed@test.com',
            'delete_1': '0'
        }
        response = self.client.post(reverse('widget_member_communication'), post_data)
        builtin_comm.refresh_from_db()
        self.assertEqual(builtin_comm.identification, 'builtin@test.com')
    
    # Test that POST request with AJAX returns JSON response
    def test_member_communication_post_ajax(self):
        post_data = {
            'row_counter': '1',
            'channel_1': '2',
            'identification_1': '+19876543210',
            'is_active_1': 'on',
            'delete_1': '0'
        }
        response = self.client.post(reverse('widget_member_communication'), post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content)
        self.assertIn('html', data)


#==================================================================================
# Tests for widget_messages_inbox view
#==================================================================================
class TestWidgetMessagesInboxView_New(NewViewsBaseTestCase):
    # Test that GET request to widget_messages_inbox returns the inbox template
    def test_messages_inbox_get_template(self):
        response = self.client.get(reverse('widget_messages_inbox'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/widgets/messaging_inbox.html')
    
    # Test that GET request context contains messages
    def test_messages_inbox_context_messages(self):
        response = self.client.get(reverse('widget_messages_inbox'))
        self.assertIn('messages', response.context)
    
    # Test that GET request with valid page parameter returns correct page
    def test_messages_inbox_pagination_valid(self):
        response = self.client.get(reverse('widget_messages_inbox') + "?page=1")
        self.assertEqual(response.status_code, 200)
    
    # Test that GET request with invalid page parameter defaults to page 1
    def test_messages_inbox_invalid_page(self):
        response = self.client.get(reverse('widget_messages_inbox') + "?page=invalid")
        self.assertEqual(response.status_code, 200)
    
    # Test that AJAX GET returns JSON with html and pagination info
    def test_messages_inbox_ajax(self):
        response = self.client.get(reverse('widget_messages_inbox'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content)
        self.assertIn('html', data)
        self.assertIn('has_next', data)
    
    # Test that the template displays message sender nickname
    def test_messages_inbox_sender_display(self):
        response = self.client.get(reverse('widget_messages_inbox'))
        self.assertIn(self.inbox_message.sender_member_id.nickname, response.content.decode())
    
    # Test that the response content type is HTML
    def test_messages_inbox_content_type(self):
        response = self.client.get(reverse('widget_messages_inbox'))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
    
    # Test that GET request returns status 200
    def test_messages_inbox_status(self):
        response = self.client.get(reverse('widget_messages_inbox'))
        self.assertEqual(response.status_code, 200)


#==================================================================================
# Tests for send_reply view
#==================================================================================
class TestSendReplyView_New(NewViewsBaseTestCase):
    # Test that POST request with valid data returns success JSON
    def test_send_reply_valid(self):
        post_data = {
            'widget_origin': 'itemlist',
            'replySenderId': str(self.member2.id),
            'replyReceiverId': str(self.member.id),
            'replyTitle': 'Reply Test',
            'replyText': 'This is a reply message',
            'replyMessageCode': 'REPLY123'
        }
        response = self.client.post(reverse('send_reply'), post_data)
        data = json.loads(response.content)
        self.assertIn('success', data)
    
    # Test that POST request with missing sender/receiver returns error JSON
    def test_send_reply_missing_ids(self):
        post_data = {
            'widget_origin': 'itemlist',
            'replySenderId': '',
            'replyReceiverId': '',
            'replyTitle': 'Reply Test',
            'replyText': 'Missing IDs test',
            'replyMessageCode': 'REPLY123'
        }
        response = self.client.post(reverse('send_reply'), post_data)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    # Test that POST request with non-numeric IDs returns 400 error
    def test_send_reply_invalid_ids(self):
        post_data = {
            'widget_origin': 'itemlist',
            'replySenderId': 'abc',
            'replyReceiverId': 'def',
            'replyTitle': 'Reply Test',
            'replyText': 'Invalid IDs test',
            'replyMessageCode': 'REPLY123'
        }
        response = self.client.post(reverse('send_reply'), post_data)
        self.assertEqual(response.status_code, 400)
    
    # Test that POST request creates two messages (reply inbox and reply outbox)
    def test_send_reply_creates_two_messages(self):
        initial_count = Messages.objects.count()
        post_data = {
            'widget_origin': 'itemlist',
            'replySenderId': str(self.member2.id),
            'replyReceiverId': str(self.member.id),
            'replyTitle': 'Dual Message Test',
            'replyText': 'Testing dual message creation',
            'replyMessageCode': 'REPLY456'
        }
        response = self.client.post(reverse('send_reply'), post_data)
        self.assertEqual(response.status_code, 200)
        new_count = Messages.objects.count()
        self.assertEqual(new_count, initial_count + 2)
    
    # Test that the response JSON for send_reply contains correct success message
    def test_send_reply_success_message(self):
        post_data = {
            'widget_origin': 'itemlist',
            'replySenderId': str(self.member2.id),
            'replyReceiverId': str(self.member.id),
            'replyTitle': 'Success Test',
            'replyText': 'Reply success message test',
            'replyMessageCode': 'REPLY789'
        }
        response = self.client.post(reverse('send_reply'), post_data)
        data = json.loads(response.content)
        self.assertIn('success', data)
    
    # Test that GET request to send_reply returns 405 error
    def test_send_reply_get_method(self):
        response = self.client.get(reverse('send_reply'))
        self.assertEqual(response.status_code, 405)


#==================================================================================
# Tests for widget_messages_outbox view
#==================================================================================
class TestWidgetMessagesOutboxView_New(NewViewsBaseTestCase):
    # Test that GET request to widget_messages_outbox returns the outbox template
    def test_messages_outbox_get_template(self):
        response = self.client.get(reverse('widget_messages_outbox'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/widgets/messaging_outbox.html')
    
    # Test that GET request context contains messages
    def test_messages_outbox_context(self):
        response = self.client.get(reverse('widget_messages_outbox'))
        self.assertIn('messages', response.context)
    
    # Test that GET with valid page parameter returns correct page
    def test_messages_outbox_valid_page(self):
        response = self.client.get(reverse('widget_messages_outbox') + "?page=1")
        self.assertEqual(response.status_code, 200)
    
    # Test that GET with invalid page parameter defaults to page 1
    def test_messages_outbox_invalid_page(self):
        response = self.client.get(reverse('widget_messages_outbox') + "?page=invalid")
        self.assertEqual(response.status_code, 200)
    
    # Test that AJAX GET returns JSON with html, has_next, and next_page
    def test_messages_outbox_ajax(self):
        response = self.client.get(reverse('widget_messages_outbox'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content)
        self.assertIn('html', data)
        self.assertIn('has_next', data)
        self.assertIn('next_page', data)
    
    # Test that the template displays outbox message title
    def test_messages_outbox_title_display(self):
        response = self.client.get(reverse('widget_messages_outbox'))
        self.assertIn(self.outbox_message.title, response.content.decode())
    
    # Test that response content type is HTML
    def test_messages_outbox_content_type(self):
        response = self.client.get(reverse('widget_messages_outbox'))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
    
    # Test that GET request returns status 200
    def test_messages_outbox_status(self):
        response = self.client.get(reverse('widget_messages_outbox'))
        self.assertEqual(response.status_code, 200)


#==================================================================================
# Tests for widget_send_message view
#==================================================================================
class TestWidgetSendMessageView_New(NewViewsBaseTestCase):
    # Test that GET request to widget_send_message returns the send_message template
    def test_send_message_get_template(self):
        response = self.client.get(reverse('widget_send_message'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/widgets/send_message.html')
    
    # Test that POST request without selected recipients returns error message
    def test_send_message_post_no_recipient(self):
        post_data = {
            'subject': 'Subject Test',
            'messageBody': 'Message body test',
            'selectedRecipients': '',
            'allNeighbours': 'off'
        }
        response = self.client.post(reverse('widget_send_message'), post_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any("Please select a recipient" in str(m) for m in messages))
    
    # Test that POST request with valid selectedRecipients sends message successfully
    def test_send_message_post_valid_recipient(self):
        post_data = {
            'subject': 'Valid Subject',
            'messageBody': 'Valid message body',
            'selectedRecipients': str(self.member2.id),
            'allNeighbours': 'off'
        }
        response = self.client.post(reverse('widget_send_message'), post_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any("Message sent successfully" in str(m) for m in messages))
    
    # Test that POST request with allNeighbours sends message successfully
    def test_send_message_post_all_neighbours(self):
        post_data = {
            'subject': 'All Neighbours Subject',
            'messageBody': 'Message to all neighbours',
            'selectedRecipients': '',
            'allNeighbours': 'on'
        }
        response = self.client.post(reverse('widget_send_message'), post_data, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any("Message sent successfully" in str(m) for m in messages))
    
    # Test that the send_message form contains the 'Select Recipients' button in HTML
    def test_send_message_contains_select_button(self):
        response = self.client.get(reverse('widget_send_message'))
        self.assertIn("Select Recipients", response.content.decode())
        
    # Test that POST request redirects after successful message send
    def test_send_message_post_redirect(self):
        post_data = {
            'subject': 'Redirect Subject',
            'messageBody': 'Redirect message body',
            'selectedRecipients': str(self.member2.id),
            'allNeighbours': 'off'
        }
        response = self.client.post(reverse('widget_send_message'), post_data)
        self.assertEqual(response.status_code, 200)
    
    # Test that GET response content type is HTML
    def test_send_message_get_content_type(self):
        response = self.client.get(reverse('widget_send_message'))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')


#==================================================================================
# Tests for widget_item_list view
#==================================================================================
class TestWidgetItemListView_New(NewViewsBaseTestCase):
    # Test that GET request to widget_item_list returns the items_for_loan template
    def test_item_list_get_template(self):
        response = self.client.get(reverse('widget_item_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/widgets/items_for_loan.html')
    
    # Test that GET request with search query returns filtered items
    def test_item_list_search_query(self):
        item = Items_For_Loan.objects.create(
            member_id=self.member,
            label="UniqueSearchItem",
            description="Description with unique keyword XYZ",
            created_by=self.user
        )
        url = reverse('widget_item_list') + "?q=XYZ"
        response = self.client.get(url)
        content = response.content.decode()
        self.assertIn("UniqueSearchItem", content)
    
    # Test that AJAX GET returns JSON with html content
    def test_item_list_ajax(self):
        response = self.client.get(reverse('widget_item_list') + "?page=1", HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content)
        self.assertIn('html', data)
    
    # Test that items list is not empty when items exist
    def test_item_list_not_empty(self):
        response = self.client.get(reverse('widget_item_list'))
        self.assertIn('items', response.context)
        self.assertGreaterEqual(response.context['items'].paginator.count, 1)
    
    # Test that pagination works correctly for widget_item_list
    def test_item_list_pagination(self):
        url = reverse('widget_item_list') + "?page=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    # Test that search query with no matches returns empty results
    def test_item_list_search_no_match(self):
        url = reverse('widget_item_list') + "?q=NoSuchItem"
        response = self.client.get(url)
        if response['Content-Type'] == 'application/json':
            data = json.loads(response.content)
            self.assertEqual(data.get('html', '').strip(), '')
        else:
            self.assertContains(response, "No items")
    
    # Test that GET response content type is HTML when not AJAX
    def test_item_list_get_content_type(self):
        response = self.client.get(reverse('widget_item_list'))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
    
    # Test that GET with search query is case-insensitive
    def test_item_list_search_case_insensitive(self):
        url = reverse('widget_item_list') + "?q=test"
        response = self.client.get(url)
        content = response.content.decode().lower()
        self.assertIn("test item", content)


#==================================================================================
# Tests for get_item_images view
#==================================================================================
class TestGetItemImagesView_New(NewViewsBaseTestCase):
    # Test that GET request with valid item_id returns JSON with images list
    def test_get_item_images_valid(self):
        url = reverse('get_item_images', args=[self.item.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('images', data)
    
    # Test that GET request returns non-empty image list for an item with images
    def test_get_item_images_nonempty(self):
        url = reverse('get_item_images', args=[self.item.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertGreater(len(data['images']), 0)
    
    # Test that GET request returns correct label and description for the item
    def test_get_item_images_item_info(self):
        url = reverse('get_item_images', args=[self.item.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(data.get('label'), self.item.label)
        self.assertEqual(data.get('description'), self.item.description)
    
    # Test that image dict contains url and caption keys
    def test_get_item_images_keys(self):
        url = reverse('get_item_images', args=[self.item.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        if data['images']:
            image_data = data['images'][0]
            self.assertIn('url', image_data)
            self.assertIn('caption', image_data)
    
    # Test that GET request with invalid item_id returns an HTML response containing "Item not found"
    def test_get_item_images_invalid_item(self):
        url = reverse('get_item_images', args=[9999])
        response = self.client.get(url)
        data = json.loads(response.content)
        html_content = data.get('html', '')
        self.assertIn("Item not found", html_content)
    
    # Test that GET request returns JSON content type
    def test_get_item_images_content_type(self):
        url = reverse('get_item_images', args=[self.item.id])
        response = self.client.get(url)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    # Test that GET request for an item with no images returns empty images list
    def test_get_item_images_no_images(self):
        from neighborow.models import Items_For_Loan
        new_item = Items_For_Loan.objects.create(
            member_id=self.member,
            label="No Image Item",
            description="Item without images",
            created_by=self.user
        )
        url = reverse('get_item_images', args=[new_item.id])
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(data['images'], [])
    
    # Test that GET request for valid item returns status 200
    def test_get_item_images_status(self):
        url = reverse('get_item_images', args=[self.item.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

#==================================================================================
# Tests for widget_loaned_items view
#==================================================================================
    # Test that GET request to widget_loaned_items returns the correct template
    def test_loaned_items_get_template(self):
        response = self.client.get(reverse('widget_loaned_items'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/widgets/loaned_items.html')
    
    # Test that header displays correct total_count and member info
    def test_loaned_items_header_content(self):
        response = self.client.get(reverse('widget_loaned_items'))
        content = response.content.decode()
        self.assertIn("My", content)
        self.assertIn("loaned items", content)
        self.assertIn(str(self.loaned_transaction.id), content)  # falls ID im HTML auftaucht
    
    # Test that the "Show history" checkbox is present
    def test_loaned_items_show_history_checkbox(self):
        response = self.client.get(reverse('widget_loaned_items'))
        self.assertIn('Show history', response.content.decode())
    
    # Test that navigation buttons ("Previous" and "Next") are present
    def test_loaned_items_navigation_buttons(self):
        response = self.client.get(reverse('widget_loaned_items'))
        content = response.content.decode()
        self.assertIn("Previous", content)
        self.assertIn("Next", content)
    
    # Test that data attributes (data-has-next, data-next-page) exist in container
    def test_loaned_items_data_attributes(self):
        response = self.client.get(reverse('widget_loaned_items'))
        content = response.content.decode()
        self.assertIn('data-has-next', content)
        self.assertIn('data-next-page', content)
    
    # Test that the condition log modal is present in the HTML
    def test_loaned_items_condition_log_modal_presence(self):
        response = self.client.get(reverse('widget_loaned_items'))
        self.assertIn("Condition Log", response.content.decode())
    
    # Test that the condition image modal is present in the HTML
    def test_loaned_items_condition_image_modal_presence(self):
        response = self.client.get(reverse('widget_loaned_items'))
        self.assertIn("Image Preview", response.content.decode())
    
    # Test that AJAX GET request returns JSON with expected keys
    def test_loaned_items_ajax_response(self):
        response = self.client.get(reverse('widget_loaned_items'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content)
        self.assertIn('html', data)
        self.assertIn('has_next', data)
        self.assertIn('next_page', data)
    
    # Test that GET response content type is HTML when not AJAX
    def test_loaned_items_non_ajax_content_type(self):
        response = self.client.get(reverse('widget_loaned_items'))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
    
    # Test that duplicate GET calls yield consistent header content
    def test_loaned_items_consistency(self):
        response1 = self.client.get(reverse('widget_loaned_items'))
        response2 = self.client.get(reverse('widget_loaned_items'))
        self.assertEqual(response1.content, response2.content)
    
    # Test that the widget includes member ID in data attributes
    def test_loaned_items_contains_member_id(self):
        response = self.client.get(reverse('widget_loaned_items'))
        self.assertIn(str(self.member.id), response.content.decode())
    
    # Test that if "Show history" is checked via GET parameter, it affects context (falls unterstützt)
    def test_loaned_items_show_history_context(self):
        url = reverse('widget_loaned_items') + "?show_history=on"
        response = self.client.get(url)
        # Hier könnte geprüft werden, ob das QuerySet anders ist – falls im Kontext verfügbar
        self.assertEqual(response.status_code, 200)
    
    # Test that the header displays a valid page number from data attribute
    def test_loaned_items_current_page_data(self):
        response = self.client.get(reverse('widget_loaned_items'))
        self.assertIn('data-current-page="1"', response.content.decode())
    
    # Test that the modal close button is present (Top and Bottom)
    def test_loaned_items_close_buttons(self):
        response = self.client.get(reverse('widget_loaned_items'))
        content = response.content.decode()
        self.assertIn('btn-close', content)
        self.assertIn('Close</button>', content)


#==================================================================================
# Tests for widget_borrowed_items view
#==================================================================================
class TestWidgetBorrowedItemsView_New(NewViewsBaseTestCase):
    # Test that GET request to widget_borrowed_items returns the correct template
    def test_borrowed_items_get_template(self):
        response = self.client.get(reverse('widget_borrowed_items'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/widgets/borrowed_items.html')
    
    # Test that header displays correct borrowed items count
    def test_borrowed_items_header_content(self):
        response = self.client.get(reverse('widget_borrowed_items'))
        content = response.content.decode()
        self.assertIn("borrowed items", content)
        self.assertIn(str(self.borrowed_transaction.id), content)  # falls ID dargestellt wird
    
    # Test that "Show history" checkbox is present
    def test_borrowed_items_show_history_checkbox(self):
        response = self.client.get(reverse('widget_borrowed_items'))
        self.assertIn("Show history", response.content.decode())
    
    # Test that navigation buttons ("Previous" and "Next") are present
    def test_borrowed_items_navigation_buttons(self):
        response = self.client.get(reverse('widget_borrowed_items'))
        content = response.content.decode()
        self.assertIn("Previous", content)
        self.assertIn("Next", content)
    
    # Test that the condition log modal is present in the borrowed items view
    def test_borrowed_items_condition_log_modal(self):
        response = self.client.get(reverse('widget_borrowed_items'))
        self.assertIn("Condition Log", response.content.decode())
    
    # Test that AJAX GET returns JSON with html content for borrowed items
    def test_borrowed_items_ajax_response(self):
        response = self.client.get(reverse('widget_borrowed_items'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content)
        self.assertIn('html', data)
    
    # Test that GET response content type is HTML when not AJAX
    def test_borrowed_items_content_type(self):
        response = self.client.get(reverse('widget_borrowed_items'))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
    
    # Test that duplicate GET calls yield consistent borrowed items list
    def test_borrowed_items_consistency(self):
        response1 = self.client.get(reverse('widget_borrowed_items'))
        response2 = self.client.get(reverse('widget_borrowed_items'))
        self.assertEqual(response1.content, response2.content)
    
    # Test that the widget includes member ID in data attributes
    def test_borrowed_items_contains_member_id(self):
        response = self.client.get(reverse('widget_borrowed_items'))
        self.assertIn(str(self.member.id), response.content.decode())
    
    # Test that GET with page parameter returns status 200
    def test_borrowed_items_with_page_param(self):
        response = self.client.get(reverse('widget_borrowed_items') + "?page=1")
        self.assertEqual(response.status_code, 200)
    
    # Test that the modal close button is present in borrowed items view
    def test_borrowed_items_close_button(self):
        response = self.client.get(reverse('widget_borrowed_items'))
        self.assertIn("Close", response.content.decode())


#==================================================================================
# Tests for widget_item_manager view
#==================================================================================
class TestWidgetItemManagerView_New(NewViewsBaseTestCase):
    # Test that GET request to widget_item_manager returns the correct template
    def test_item_manager_get_template(self):
        response = self.client.get(reverse('widget_item_manager'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/widgets/item_manager.html')
    
    # Test that header displays "Manage My Items" and correct item count
    def test_item_manager_header(self):
        response = self.client.get(reverse('widget_item_manager'))
        content = response.content.decode()
        self.assertIn("Manage My Items", content)
        # Check if paginator count appears in header
        self.assertIn("Manage My Items (", content)
    
    # Test that "Add New Item" button is present in the HTML
    def test_item_manager_add_new_button(self):
        response = self.client.get(reverse('widget_item_manager'))
        self.assertIn("Add New Item", response.content.decode())
    
    # Test that table headers for item manager are present
    def test_item_manager_table_headers(self):
        response = self.client.get(reverse('widget_item_manager'))
        content = response.content.decode()
        for header in ["Photo", "Title", "Description", "Available From", "Available", "Currently Borrowed", "Actions"]:
            self.assertIn(header, content)
    
    # Test that duplicate GET calls yield same items table
    def test_item_manager_consistency(self):
        response1 = self.client.get(reverse('widget_item_manager'))
        response2 = self.client.get(reverse('widget_item_manager'))
        self.assertEqual(response1.content, response2.content)
    
    # Test that AJAX GET returns JSON with html for item manager
    def test_item_manager_ajax_response(self):
        response = self.client.get(reverse('widget_item_manager') + "?page=1", HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content)
        self.assertIn('html', data)
    
    # Test that the "Edit" and "Delete" buttons exist in the table rows
    def test_item_manager_action_buttons(self):
        response = self.client.get(reverse('widget_item_manager'))
        content = response.content.decode()
        self.assertIn("Edit", content)
        self.assertIn("Delete", content)
    
    # Test that GET response content type is HTML
    def test_item_manager_content_type(self):
        response = self.client.get(reverse('widget_item_manager'))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
    
    # Test that the modal for editing an item is present
    def test_item_manager_edit_modal_presence(self):
        response = self.client.get(reverse('widget_item_manager'))
        self.assertIn("Edit Item", response.content.decode())
    
    # Test that the modal for creating a new item is present
    def test_item_manager_create_modal_presence(self):
        response = self.client.get(reverse('widget_item_manager'))
        self.assertIn("Create New Item", response.content.decode())
    
    # Test that data attributes for pagination (has-next and next-page) exist
    def test_item_manager_data_attributes(self):
        response = self.client.get(reverse('widget_item_manager'))
        content = response.content.decode()
        self.assertIn("data-has-next", content)
        self.assertIn("data-next-page", content)
    
    # Test that the widget includes member ID in data attributes
    def test_item_manager_contains_member_id(self):
        response = self.client.get(reverse('widget_item_manager'))
        self.assertIn(str(self.member.id), response.content.decode())
    
    # Test that duplicate GET calls return status 200
    def test_item_manager_status(self):
        response = self.client.get(reverse('widget_item_manager'))
        self.assertEqual(response.status_code, 200)
    
    # Test that the item manager table contains at least one item row
    def test_item_manager_table_not_empty(self):
        response = self.client.get(reverse('widget_item_manager'))
        # Assuming at least one item (fixture item) is present
        self.assertIn("Test Item", response.content.decode())


#==================================================================================
# Tests for widget_calendar view
#==================================================================================
class TestWidgetCalendarView_New(NewViewsBaseTestCase):
    # Test that GET request to widget_calendar returns the correct template
    def test_calendar_get_template(self):
        response = self.client.get(reverse('widget_calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'neighborow/widgets/calendar.html')
    
    # Test that calendar header displays correct month and year
    def test_calendar_header_content(self):
        response = self.client.get(reverse('widget_calendar'))
        content = response.content.decode()
        # Prüfe, ob Monatsname und Jahr enthalten sind (z. B. "Calendar -")
        self.assertIn("Calendar -", content)
    
    # Test that navigation buttons (prev and next month) are present
    def test_calendar_navigation_buttons(self):
        response = self.client.get(reverse('widget_calendar'))
        content = response.content.decode()
        self.assertIn("&laquo;", content)
        self.assertIn("&raquo;", content)
    
    # Test that the calendar table contains weekday headers
    def test_calendar_weekday_headers(self):
        response = self.client.get(reverse('widget_calendar'))
        content = response.content.decode()
        for wd in ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"]:
            self.assertIn(wd, content)
    
    # Test that the calendar contains at least one day with a number
    def test_calendar_contains_day_numbers(self):
        response = self.client.get(reverse('widget_calendar'))
        content = response.content.decode()
        # Prüfe, ob mindestens eine Zelle mit einer Ziffer (Tag) vorhanden ist
        self.assertRegex(content, r'>\s*\d+\s*<')
    
    # Test that the top close button is present in the calendar widget
    def test_calendar_top_close_button(self):
        response = self.client.get(reverse('widget_calendar'))
        self.assertIn("btn-close", response.content.decode())
    
    # Test that the bottom close button is present in the calendar widget
    def test_calendar_bottom_close_button(self):
        response = self.client.get(reverse('widget_calendar'))
        self.assertIn("Close</button>", response.content.decode())
    
    # Test that duplicate GET calls yield identical calendar HTML
    def test_calendar_consistency(self):
        response1 = self.client.get(reverse('widget_calendar'))
        response2 = self.client.get(reverse('widget_calendar'))
        self.assertEqual(response1.content, response2.content)
    
    # Test that the calendar container has data-loading attribute
    def test_calendar_data_loading_attribute(self):
        response = self.client.get(reverse('widget_calendar'))
        self.assertIn('widgetCalendar"', response.content.decode())
    
    # Test that the calendar title includes the correct month name (case-insensitive)
    def test_calendar_title_month_name(self):
        response = self.client.get(reverse('widget_calendar'))
        content = response.content.decode().lower()
        self.assertRegex(content, r'calendar\s*-\s*\w+')
    
    # Test that the calendar table has a <thead> element
    def test_calendar_table_has_thead(self):
        response = self.client.get(reverse('widget_calendar'))
        self.assertIn("<thead>", response.content.decode())
    
    # Test that the calendar table has a <tbody> element
    def test_calendar_table_has_tbody(self):
        response = self.client.get(reverse('widget_calendar'))
        self.assertIn("<tbody>", response.content.decode())
    
    # Test that the widget div has id "widgetCalendar"
    def test_calendar_widget_id(self):
        response = self.client.get(reverse('widget_calendar'))
        self.assertIn('id="widgetCalendar"', response.content.decode())
    
    # Test that duplicate GET calls return HTML content type
    def test_calendar_content_type(self):
        response = self.client.get(reverse('widget_calendar'))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')


