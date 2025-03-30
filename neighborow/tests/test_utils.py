import pytest
import random, string
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from neighborow.utils import (
    generate_unique_access_code,
    generate_unique_message_code,
    ajax_or_render
)
from neighborow.models import Access_Code, Messages, Member, Building

#==================================================================================
# SIMPLE FIXTURES FOR ALL URL TESTS
#==================================================================================
@pytest.fixture
def existing_user(db):
    user = User.objects.create_user(username="user", password="neighborow")
    return user

@pytest.fixture
def existing_building(db):
    return Building.objects.create(name="Test Building", address_line1="Test Street 123")

@pytest.fixture
def existing_access_code(db, existing_user, existing_building):
    code = "CODE123456789123"  
    return Access_Code.objects.create(
        building_id=existing_building, 
        flat_no="Flat 1A",
        code=code,
        type="0",
        is_used=False,
        created_by=existing_user
    )
   


@pytest.fixture
def existing_member(db, existing_user, existing_building, existing_access_code):
    return Member.objects.create(
        user_id=existing_user,
        building_id=existing_building,
        access_code_id=existing_access_code,
        nickname="nickname test user",
        flat_no="Flat 1A",
        authorized=True
    )

@pytest.fixture
def existing_message_code(db, existing_user, existing_member):
    code = "CODE123456789012"  
    # Create a dummy Message object with that code.
    Messages.objects.create(
        sender_member_id=existing_member,
        receiver_member_id=existing_member,
        title="sample title",
        body="sample text in body",
        message_code=code,
        inbox=False,
        outbox=False,
        internal=False,
        is_sent_email=False,
        is_sent_sms=False,
        is_sent_whatsApp=False,
        message_type="0",
        created_by=existing_user
    )
    return code

#==================================================================================
# TEST function generate_unique_access_code
#==================================================================================
# Test that generate_unique_access_code returns a unique 16-character alphanumeric string
@pytest.mark.django_db
def test_generate_unique_access_code_normal(db):
    code = generate_unique_access_code()
    assert len(code) == 16
    allowed = set(string.ascii_letters + string.digits)
    assert set(code).issubset(allowed)

# Test that generate_unique_message_code returns a unique 16-character alphanumeric string
@pytest.mark.django_db
def test_generate_unique_message_code_normal(db):
    code = generate_unique_message_code()
    assert len(code) == 16
    allowed = set(string.ascii_letters + string.digits)
    assert set(code).issubset(allowed)

# Test that generate_unique_message_code avoids an already existing code using monkeypatch
@pytest.mark.django_db
def test_generate_unique_message_code_avoids_existing(db, existing_message_code, monkeypatch):
    existing = existing_message_code  
    new_code = "CODE123456123456"  
    # Ensure new_code is 16 characters
    new_code = new_code[:16] if len(new_code) > 16 else new_code.ljust(16, "X")
    
    call_count = {"count": 0}
    def fake_choices(seq, k):
        if call_count["count"] == 0:
            call_count["count"] += 1
            return list(existing)
        else:
            return list(new_code)
    
    monkeypatch.setattr(random, "choices", fake_choices)
    code = generate_unique_message_code()
    assert code == new_code
