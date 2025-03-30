import pytest
import json
import datetime
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from neighborow.models import (
    Member, Items_For_Loan, Transaction, AppSettings, Invitation, Access_Code, Building
)
from neighborow.models import Channels, Relationship

#==================================================================================
# SIMPLE FIXTURES FOR ALL URL TESTS
#==================================================================================

@pytest.fixture
def test_user(db):
    user = User.objects.create_user(username="user", password="neighborow")
    return user

@pytest.fixture
def building(db):
    return Building.objects.create(name="Test Building", address_line1="Test Street 123")

@pytest.fixture
def access_code(db, building, test_user):
    return Access_Code.objects.create(
        building_id=building,
        flat_no="Flat 1",
        code="CODE123456789000",
        type="0",  
        is_used=False,
        created_by=test_user
    )

@pytest.fixture
def member(db, test_user, building, access_code):
    return Member.objects.create(
        user_id=test_user,
        building_id=building,
        access_code_id=access_code,
        nickname="nickname test user",
        flat_no="Flat 1",
        authorized=True
    )

@pytest.fixture
def logged_in_client(client, test_user):
    client.login(username="user", password="neighborow")
    return client

#==================================================================================
# TESTS FOR URL ENDPOINTS
#==================================================================================
# Test that the index view returns 200 for an authenticated user
@pytest.mark.django_db
def test_index_view_authenticated(logged_in_client):
    url = reverse("index")
    response = logged_in_client.get(url)
    assert response.status_code == 200
    assert b"is_authorized" in response.content or b"index.html" in response.content

# Test that the index view redirects for an anonymous user
@pytest.mark.django_db
def test_index_view_anonymous(client):
    url = reverse("index")
    response = client.get(url)
    assert response.status_code in (301, 302)


# Test that form_invitation view returns 200 
@pytest.mark.django_db
def test_form_invitation_view(logged_in_client):
    url = reverse("form_invitation")
    response = logged_in_client.get(url)
    assert response.status_code == 200
    assert b"Relative" in response.content

# Test that form_building view returns 200 without a building_id 
@pytest.mark.django_db
def test_form_building_view_without_id(logged_in_client, building):
    url = reverse("form_building")
    response = logged_in_client.get(url)
    assert response.status_code == 200
    # Check that the modal identifier or a specific comment is present in the modal HTML.
    assert b"Modal Form for Creating/Updating Building" in response.content

# Test that form_building view returns 200 
@pytest.mark.django_db
def test_form_building_view_with_valid_id(logged_in_client, building):
    url = reverse("form_building") + f"?building_id={building.id}"
    response = logged_in_client.get(url)
    assert response.status_code == 200
    assert building.name.encode() in response.content

# Test that app_settings POST without building_id returns error 
@pytest.mark.django_db
def test_app_settings_post_without_building(logged_in_client):
    url = reverse("app_settings")
    response = logged_in_client.post(url, {})
    assert response.status_code in (302, 301)

# Test that app_settings GET returns 200 a
@pytest.mark.django_db
def test_app_settings_get(logged_in_client):
    url = reverse("app_settings")
    response = logged_in_client.get(url)
    assert response.status_code == 200
    assert b"Modal Form for Application Settings" in response.content


# Test that get_building_details returns an error when building_id is missing
@pytest.mark.django_db
def test_get_building_details_missing(logged_in_client):
    url = reverse("get_building_details")
    response = logged_in_client.get(url)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data

#Test that get_building_details returns 404 JSON for an invalid building id
@pytest.mark.django_db
def test_get_building_details_invalid(logged_in_client):
    url = reverse("get_building_details")
    response = logged_in_client.get(url, {"building_id": 99999})
    assert response.status_code == 404
    data = response.json()
    assert "error" in data


# Test that get_app_settings returns settings for a valid building."""
@pytest.mark.django_db
def test_get_app_settings_valid(logged_in_client, building, test_user):
    AppSettings.objects.create(
        building_id=building,
        key="0",
        value="TestValue",
        created_by=test_user
    )
   
    url = reverse("get_building_details")
    response = logged_in_client.get(url, {"building_id": building.id})
    assert response.status_code == 200
    data = response.json()
    assert "settings" in data

# Test that access_code GET returns 200 and renders a template with access codes
@pytest.mark.django_db
def test_access_code_get(logged_in_client, building):
    url = reverse("access_code")
    response = logged_in_client.get(url, {"building_id": building.id})
    assert response.status_code == 200
    assert b" Modal Form for Access Codes" in response.content

# Test that access_code POST without building_id returns error redirect
@pytest.mark.django_db
def test_access_code_post_without_building(logged_in_client):
    url = reverse("access_code")
    response = logged_in_client.post(url, {})
    assert response.status_code in (301, 302)

# Test that get_access_codes returns a valid list for a valid building
@pytest.mark.django_db
def test_get_access_codes_valid(logged_in_client, building, test_user):
    ac = Access_Code.objects.create(
        building_id=building,
        flat_no="Falt 1B",
        code="CODE123456789000",
        type="0",
        is_used=False,
        created_by=test_user
    )
    url = reverse("get_access_codes")
    response = logged_in_client.get(url, {"building_id": building.id})
    assert response.status_code == 200
    data = response.json()
    assert "access_codes" in data
    codes = [str(item["code"]) for item in data["access_codes"]]
    assert "CODE123456789000" in codes

# Test that get_access_codes returns 404  for an invalid building id
@pytest.mark.django_db
def test_get_access_codes_invalid(logged_in_client):
    url = reverse("get_access_codes")
    response = logged_in_client.get(url, {"building_id": 99999})
    assert response.status_code == 404
    data = response.json()
    assert "error" in data

# Test that generate_code returns a code string
@pytest.mark.django_db
def test_generate_code_view(logged_in_client):
    url = reverse("generate_code")
    response = logged_in_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert "code" in data
    assert isinstance(data["code"], str)
    assert len(data["code"]) > 0

# Test that generate_codes returns the requested number of unique codes
@pytest.mark.django_db
def test_generate_codes_valid(logged_in_client):
    url = reverse("generate_codes")
    response = logged_in_client.get(url, {"count": 3})
    assert response.status_code == 200
    data = response.json()
    assert "codes" in data
    assert isinstance(data["codes"], list)
    assert len(data["codes"]) == 3

# Test that generate_codes with negative count returns an empty list
@pytest.mark.django_db
def test_generate_codes_negative(logged_in_client):
    url = reverse("generate_codes")
    response = logged_in_client.get(url, {"count": -5})
    assert response.status_code == 200
    data = response.json()
    assert "codes" in data
    assert len(data["codes"]) == 0

# Test that widget_borrowing view returns 200 for a GET request 
@pytest.mark.django_db
def test_widget_borrowing_get(logged_in_client):
    url = reverse("widget_borrowing_request")
    response = logged_in_client.get(url)
    assert response.status_code == 200

# Test that widget_member_info GET returns 200 
@pytest.mark.django_db
def test_widget_member_info_get(logged_in_client, member):
    url = reverse("widget_member_info")
    response = logged_in_client.get(url)
    assert response.status_code == 200
    # Check for member nickname in the response content.
    assert member.nickname.encode() in response.content

# Test that messages_inbox view returns HTML for an AJAX request 
@pytest.mark.django_db
def test_messages_inbox_view_ajax_html(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
        user_id=test_user,
        defaults={
            "building_id": building,
            "access_code_id": access_code,
            "nickname": "test nickname",
            "flat_no": "Flat 1A",
            "authorized": True,
        }
    )
    url = reverse("widget_messages_inbox")
    response = logged_in_client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert response.status_code == 200
    # Check that the HTML contains expected markers (e.g. for pagination "has_next")
    assert b"has_next" in response.content



# Test that widget_item_list returns JSON with filtered items when a query is provided
@pytest.mark.django_db
def test_widget_item_list_with_query(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
        user_id=test_user,
        defaults={
            "building_id": building,
            "access_code_id": access_code,
            "nickname": "test nickname",
            "flat_no": "Flat 1A",
            "authorized": True,
        }
    )
    url = reverse("widget_item_list")
    response = logged_in_client.get(url, {"q": "nonexistent"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    data = response.json()
    assert "html" in data


# Test that widget_item_list returns full widget hen no query parameter is provided
@pytest.mark.django_db
def test_widget_item_list_without_query(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    url = reverse("widget_item_list")
    response = logged_in_client.get(url)
    assert response.status_code == 200
    assert b"widgetItemList" in response.content


# Test that item_manager view returns JSON when AJAX header is present
@pytest.mark.django_db
def test_item_manager_view_ajax(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    url = reverse("widget_item_manager")
    response = logged_in_client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    data = response.json()
    assert "html" in data


# Test that update_item returns 405 error when using GET instead of POST
@pytest.mark.django_db
def test_update_item_invalid_method(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    item = Items_For_Loan.objects.create(
         member_id=member,
         label="UpdateTest",
         description="Before update",
         available=True,
         currently_borrowed=False
    )
    url = reverse("update_item", kwargs={"item_id": item.id})
    response = logged_in_client.get(url)
    assert response.status_code == 405


# Test that update_item POST updates an item and returns JSON success
@pytest.mark.django_db
def test_update_item_post_valid(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    item = Items_For_Loan.objects.create(
         member_id=member,
         label="ItemToUpdate",
         description="Old description",
         available=True,
         currently_borrowed=False
    )
    url = reverse("update_item", kwargs={"item_id": item.id})
    new_desc = "New description"
    response = logged_in_client.post(url, {"label": "ItemToUpdate", "description": new_desc})
    data = response.json()
    assert data.get("success") is True
    item.refresh_from_db()
    assert item.description == new_desc


# Test that delete_item POST returns error JSON when trying to delete a non-existing item
@pytest.mark.django_db
def test_delete_item_invalid(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    url = reverse("delete_item", kwargs={"item_id": 99999})
    response = logged_in_client.post(url)
    data = response.json()
    assert data.get("success") is False


# Test that update_item_image_caption returns error JSON for an invalid image id
@pytest.mark.django_db
def test_update_item_image_caption_invalid(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    url = reverse("update_item_image_caption", kwargs={"item_id": 99999})
    response = logged_in_client.post(url, {"caption": "New Caption"})
    data = response.json()
    assert data.get("success") is False


# Test that upload_item_image POST returns error when no image file is provided
@pytest.mark.django_db
def test_upload_item_image_no_file(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    item = Items_For_Loan.objects.create(
         member_id=member,
         label="UploadTest",
         description="Test item",
         available=True
    )
    url = reverse("upload_item_image", kwargs={"item_id": item.id})
    response = logged_in_client.post(url, {"caption": "Test Caption"})
    data = response.json()
    assert data.get("success") is False
    assert "No images provided" in data.get("html", "")


# Test that delete_item_image POST returns error JSON when image_id is invalid
@pytest.mark.django_db
def test_delete_item_image_invalid(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    url = reverse("delete_item_image", kwargs={"image_id": 99999})
    response = logged_in_client.post(url)
    data = response.json()
    assert data.get("success") is False


# Test that create_item POST creates a new item and returns JSON with item_id
@pytest.mark.django_db
def test_create_item_post_valid(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    url = reverse("create_item")
    post_data = {
         "label": "New Item",
         "description": "New item description",
         "available_from": (timezone.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
         "available": "on",
         "currently_borrowed": ""
    }
    response = logged_in_client.post(url, post_data)
    data = response.json()
    assert data.get("success") is True
    assert "item_id" in data


# Test that borrow_item POST returns error when required fields are missing
@pytest.mark.django_db
def test_borrow_item_post_missing_fields(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    url = reverse("borrow_item")
    response = logged_in_client.post(url, {}) 
    data = response.json()
    assert "html" in data


# Test that calendar view returns 200 using default (current month) parameters
@pytest.mark.django_db
def test_calendar_default(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    url = reverse("widget_calendar")
    response = logged_in_client.get(url)
    assert response.status_code == 200
    current_month = datetime.date.today().strftime("%B").encode()
    assert current_month in response.content


# Test that calendar view returns 200 when valid year and month are provided
@pytest.mark.django_db
def test_calendar_with_year_month(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    url = reverse("calendar_widget", kwargs={"year": 2022, "month": 12})
    response = logged_in_client.get(url)
    assert response.status_code == 200
    assert b"December" in response.content


# Test that borrowed_items view returns JSON with paging info for an AJAX request
@pytest.mark.django_db
def test_borrowed_items_ajax(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    url = reverse("widget_borrowed_items")
    response = logged_in_client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    data = response.json()
    assert "html" in data
    assert "has_next" in data
    assert "total_count" in data


# Test that condition_log GET returns 404 JSON when given an invalid transaction_id
@pytest.mark.django_db
def test_condition_log_get_invalid_transaction(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    url = reverse("condition_log", kwargs={"transaction_id": 99999})
    response = logged_in_client.get(url)
    assert response.status_code == 404 or response.json().get("error")


# Test that condition_log POST updates or creates a condition log and returns JSON success
@pytest.mark.django_db
def test_condition_log_post_valid(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    item = Items_For_Loan.objects.create(
         member_id=member,
         label="Condition Test Item",
         description="Test",
         available=True
    )
    transaction_obj = Transaction.objects.create(
         items_for_loan_id=item,
         lender_member_id=member,
         borrower_member_id=member,
         borrowed_on=timezone.now() + datetime.timedelta(hours=1),
         borrowed_until=timezone.now() + datetime.timedelta(hours=2),
         created_by=member.user_id
    )
    url = reverse("condition_log", kwargs={"transaction_id": transaction_obj.id})
    post_data = {
         "log_type": "before",
         "label": "Test Condition",
         "description": "Test description",
         "caption": "Image Caption"
    }
    response = logged_in_client.post(url, post_data)
    data = response.json()
    assert data.get("success") is True
    assert "condition_log_id" in data


# Test that return_item POST returns 403 when the logged-in user is not the borrower
@pytest.mark.django_db
def test_return_item_unauthorized(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    other_user = User.objects.create_user(username="other", password="password")
    other_member = Member.objects.create(
         user_id=other_user,
         building_id=member.building_id,
         access_code_id=member.access_code_id,
         nickname="nickname user",
         flat_no="Flat 2B",
         authorized=True
    )
    item = Items_For_Loan.objects.create(
         member_id=member,
         label="Label Test Item",
         description="Test description",
         available=True
    )
    transaction_obj = Transaction.objects.create(
         items_for_loan_id=item,
         lender_member_id=member,
         borrower_member_id=other_member,
         borrowed_on=timezone.now() + datetime.timedelta(hours=1),
         borrowed_until=timezone.now() + datetime.timedelta(hours=2),
         created_by=member.user_id
    )
    url = reverse("return_item", kwargs={"transaction_id": transaction_obj.id})
    response = logged_in_client.post(url)
    assert response.status_code == 403


# Test that loaned_items view returns JSON with paging info for an AJAX request
@pytest.mark.django_db
def test_loaned_items_ajax(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    url = reverse("widget_loaned_items")
    response = logged_in_client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    data = response.json()
    assert "html" in data
    assert "has_next" in data


# Test that return_item_loaned POST returns 403 when the logged-in user is not the lender
@pytest.mark.django_db
def test_return_item_loaned_unauthorized(logged_in_client, test_user, building, access_code):
    member, created = Member.objects.get_or_create(
         user_id=test_user,
         defaults={
             "building_id": building,
             "access_code_id": access_code,
             "nickname": "test nickname",
             "flat_no": "Flat 1A",
             "authorized": True,
         }
    )
    other_user = User.objects.create_user(username="other_lender", password="password")
    other_member = Member.objects.create(
         user_id=other_user,
         building_id=member.building_id,
         access_code_id=member.access_code_id,
         nickname="lender nickname",
         flat_no="3C",
         authorized=True
    )
    item = Items_For_Loan.objects.create(
         member_id=other_member,
         label="Loaned Item Test",
         description="Test",
         available=True
    )
    transaction_obj = Transaction.objects.create(
         items_for_loan_id=item,
         lender_member_id=other_member,
         borrower_member_id=member,
         borrowed_on=timezone.now() + datetime.timedelta(hours=1),
         borrowed_until=timezone.now() + datetime.timedelta(hours=2),
         created_by=other_member.user_id
    )
    url = reverse("return_item_loaned", kwargs={"transaction_id": transaction_obj.id})
    response = logged_in_client.post(url)
    assert response.status_code == 403