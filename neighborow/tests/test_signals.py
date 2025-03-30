import pytest
import datetime
from django.utils import timezone
from django.db import transaction

from django.contrib.auth.models import User
from neighborow import models
from neighborow.models import (
    Building, Member, Access_Code, Borrowing_Request, Borrowing_Request_Recipients,
    Messages, Communication, Items_For_Loan, Transaction, Invitation
)
from neighborow.signals import (
    create_messages, create_default_communication, create_invitation_message,
    update_available_from, update_item_availability
)
from neighborow.models import Channels, Relationship


# Helper function for testuser
def create_test_user(username):
    return User.objects.create(username=username)


#==================================================================================
# TEST SIGNALS create_messages (Borrowing_Request_Recipients)
#==================================================================================
@pytest.mark.django_db
@pytest.mark.enable_signals
@pytest.mark.django_db
# Test that when a new Borrowing_Request_Recipients is created corresponding Message records are created
def test_create_messages_signal_normal():
    # Create sender and receiver users
    sender_user = create_test_user("sender")
    receiver_user = create_test_user("receiver")
    
    # Create a building
    building = Building.objects.create(
        name="Test Building",
        address_line1="Test Street 123"
    )
    
    # Create Access_Code
    access_code = Access_Code.objects.create(
        building_id=building,
        flat_no="Flat 1A",
        code="CODE123456789000",
        type=models.MemberType.RESIDENT,
        is_used=False,
        created_by=sender_user
    )
    
    # Create sender and receiver Member instances
    sender_member = Member.objects.create(
        user_id=sender_user,
        building_id=building,
        access_code_id=access_code,
        nickname="Sender nickname",
        flat_no="Flat 1A",
        authorized=True
    )
    receiver_member = Member.objects.create(
        user_id=receiver_user,
        building_id=building,
        access_code_id=access_code,
        nickname="Receiver Nickname",
        flat_no="Flat 1B",
        authorized=True
    )
    
    # Create a Borrowing_Request
    req_from = timezone.now() + datetime.timedelta(days=1)
    req_until = req_from + datetime.timedelta(days=2)
    borrow_req = Borrowing_Request.objects.create(
        member_id=sender_member,
        title="Borrowing Request titel",
        body="Please lend me any item for free.",
        required_from=req_from,
        required_until=req_until,
        created_by=sender_user
    )
    
    # check if message is created
    initial_message_count = Messages.objects.count()
    
    # Create Borrowing_Request_Recipients instance  -- trigger signal
    recipient = Borrowing_Request_Recipients.objects.create(
        member_id=receiver_member,
        borrowing_request=borrow_req,
        created_by=sender_user
    )
    
    # check if message is created
    messages_created = Messages.objects.filter(message_type='3', message_type_id=recipient.pk)
    assert messages_created.count() == 2
    
    # Check that the body of the messages includes the borrowing period and created_by = sender_user 
    for msg in messages_created:
        assert "Required borrowing period from" in msg.body
        assert msg.created_by == sender_user




#==================================================================================
# TEST SIGNALS create_default_communication (Member)
#==================================================================================
@pytest.mark.django_db
@pytest.mark.enable_signals
@pytest.mark.django_db
# test that when a new Member is created a default Communication record is created
def test_create_default_communication_signal_normal():
    user = create_test_user("user")
    building = Building.objects.create(name="Sample Building")
    access_code = Access_Code.objects.create(
        building_id=building,
        flat_no="Flat 2A",
        code="CODE12345612345",
        type=models.MemberType.RESIDENT,
        is_used=False,
        created_by=user
    )
    # Create member; the signal should trigger on post_save.
    member = Member.objects.create(
        user_id=user,
        building_id=building,
        access_code_id=access_code,
        nickname="nickname user",
        flat_no="Flat 2A",
        authorized=True
    )
    
    comms = Communication.objects.filter(member_id=member)
    assert comms.count() == 1
    comm = comms.first()
    assert comm.channel == Channels.BUILTIN
    assert comm.identification == member.nickname
    assert comm.is_active is True
    # test created and modified by user
    assert comm.created_by == user
    assert comm.modified_by == user

#==================================================================================
# TEST SIGNALS create_invitation_message (Invitation)
#==================================================================================
@pytest.mark.django_db
@pytest.mark.enable_signals
@pytest.mark.django_db
# tst that when a new Invitation is created a corresponding Message record is created
def test_create_invitation_message_signal_normal():
    user2 = create_test_user("user 2")
    user3 = create_test_user("user 3")
    building = Building.objects.create(name="New Building")
    access_code = Access_Code.objects.create(
        building_id=building,
        flat_no="Flat 3A",
        code="CODE123123123123",
        type=models.MemberType.INVITEE,
        is_used=False,
        created_by=user2
    )
    # Create two members: one as invitor and one as invitee.
    invitor = Member.objects.create(
        user_id=user2,
        building_id=building,
        access_code_id=access_code,
        nickname="nickname invitor",
        flat_no="Flat 3A",
        authorized=True
    )
    invitee = Member.objects.create(
        user_id=user3,
        building_id=building,
        access_code_id=access_code,
        nickname="nickname invitee",
        flat_no="Flat 3B",
        authorized=True
    )
    # Create an Invitation with a specific relationship choice.
    invitation = Invitation.objects.create(
        building_id=building,
        invitor_member_id=invitor,
        invitee_member_id=invitee,
        access_code_id=access_code,
        distance=1,
        relationship=Relationship.FRIEND,  
        created_by=user2
    )
    
    # The signal should have created one Message record.
    msg = Messages.objects.filter(message_type='2', sender_member_id=invitor).first()
    assert msg is not None
    expected_title = "Access Code for invitee " + invitation.get_relationship_display()
    assert msg.title == expected_title
    # The body should contain the access code and a greeting.
    assert invitation.access_code_id.code in msg.body
    # check that is_sent_email is True and internal is True.
    assert msg.is_sent_email is True
    assert msg.internal is True


#==================================================================================
# TEST SIGNALS create_invitation_message (Invitation)
#==================================================================================
@pytest.mark.django_db
@pytest.mark.enable_signals
@pytest.mark.django_db
# test taht  when an Items_For_Loan instance is currently_borrowed is set correctly
def test_update_available_from_on_create():
    user4 = create_test_user("user4")
    building = Building.objects.create(name="Sample Building")
    access_code = Access_Code.objects.create(
        building_id=building,
        flat_no="Flat 4A",
        code="CODE123412341234",
        type=models.MemberType.RESIDENT,
        is_used=False,
        created_by=user4
    )
    member = Member.objects.create(
        user_id=user4,
        building_id=building,
        access_code_id=access_code,
        nickname="member 4 nicknae",
        flat_no="flat 4A",
        authorized=True
    )
    # Create with currently_borrowed False – available_from should be set.
    item1 = Items_For_Loan.objects.create(
        member_id=member,
        label="Item1",
        description="Test item",
        currently_borrowed=False,
        available=True
    )
    assert item1.available_from is not None
    # Create with currently_borrowed True – available_from should remain None.
    item2 = Items_For_Loan.objects.create(
        member_id=member,
        label="Item2",
        description="Test item 2",
        currently_borrowed=True,
        available=True
    )
    assert item2.available_from is None

@pytest.mark.django_db
@pytest.mark.enable_signals
@pytest.mark.django_db
# Test that xisting Items_For_Loan instance changes from currently_borrowed
def test_update_available_from_on_update():
    user5 = create_test_user("user5")
    building = Building.objects.create(name="new Test Building")
    access_code = Access_Code.objects.create(
        building_id=building,
        flat_no="Flat 5B",
        code="CODE000000000000",
        type=models.MemberType.RESIDENT,
        is_used=False,
        created_by=user5
    )
    member = Member.objects.create(
        user_id=user5,
        building_id=building,
        access_code_id=access_code,
        nickname="member nickname 5",
        flat_no="Flat 5B",
        authorized=True
    )
    # Create an item with currently_borrowed True (so available_from not set)
    item = Items_For_Loan.objects.create(
        member_id=member,
        label="new item",
        description="item description",
        currently_borrowed=True,
        available=True
    )
    assert item.available_from is None
    # Update the item: change currently_borrowed to False
    item.currently_borrowed = False
    item.save()
    # After update, available_from should be set to a recent timestamp
    assert item.available_from is not None
    delta = timezone.now() - item.available_from
    # Check that the delta is small (e.g. less than 5 seconds)
    assert delta.total_seconds() < 5


#==================================================================================
# TEST SIGNALS update_item_availability (Transaction)
#==================================================================================
@pytest.mark.django_db
@pytest.mark.enable_signals
@pytest.mark.django_db
# test that a Transaction with borrowed_on > now+5h is created 
def test_update_item_availability_with_open_transaction():
    user6 = create_test_user("user6")
    building = Building.objects.create(name="Smaple Building")
    access_code = Access_Code.objects.create(
        building_id=building,
        flat_no="Flat 6A",
        code="Code123456123456",
        type=models.MemberType.RESIDENT,
        is_used=False,
        created_by=user6
    )
    member = Member.objects.create(
        user_id=user6,
        building_id=building,
        access_code_id=access_code,
        nickname="nickname user 6",
        flat_no="Flat 6A",
        authorized=True
    )
    # Create an item
    item = Items_For_Loan.objects.create(
        member_id=member,
        label="new item",
        description="description of new item",
        currently_borrowed=False,
        available=True
    )
    
    now_time = timezone.now()
    # Set borrowed_on to now+6 hours 
    borrowed_on = now_time + datetime.timedelta(hours=6)
    borrowed_until = borrowed_on + datetime.timedelta(hours=2)
    
    # Create a Transaction (with return_date is None)
    trans = Transaction.objects.create(
        items_for_loan_id=item,
        lender_member_id=member,
        borrower_member_id=member,
        borrowed_on=borrowed_on,
        borrowed_until=borrowed_until,
        created_by=user6
    )
    # After saving the transaction, the post_save signal should update the item
    item.refresh_from_db()
    # The available_from should equal the borrowed_on (or be very close)
    delta = abs((item.available_from - borrowed_on).total_seconds())
    assert delta < 5
    # Since borrowed_on > now_time, currently_borrowed should be True
    assert item.currently_borrowed is True


@pytest.mark.django_db
@pytest.mark.enable_signals
@pytest.mark.django_db
# test if there are no open transactions then the item's available_from is set to now
def test_update_item_availability_no_open_transaction():
    user7 = create_test_user("user7")
    building = Building.objects.create(name="NoOpen Building")
    access_code = Access_Code.objects.create(
        building_id=building,
        flat_no="Flat 7B",
        code="CODE123456712346",
        type=models.MemberType.RESIDENT,
        is_used=False,
        created_by=user7
    )
    member = Member.objects.create(
        user_id=user7,
        building_id=building,
        access_code_id=access_code,
        nickname="nickname user 7",
        flat_no="Flat 7B",
        authorized=True
    )
    item = Items_For_Loan.objects.create(
        member_id=member,
        label="Label of item",
        description="description of item",
        currently_borrowed=False,
        available=True
    )
    # Create a transaction that is already closed (has a return_date)
    now_time = timezone.now()
    trans = Transaction.objects.create(
        items_for_loan_id=item,
        lender_member_id=member,
        borrower_member_id=member,
        borrowed_on=now_time + datetime.timedelta(hours=6),
        borrowed_until=now_time + datetime.timedelta(hours=8),
        return_date=now_time + datetime.timedelta(hours=9),
        created_by=user7
    )
    # trigger the post_save signal for Transaction
    update_item_availability(sender=Transaction, instance=trans)
    item.refresh_from_db()
    # no open transactions exist, therefore available_from should be close to now_time
    delta = abs((item.available_from - now_time).total_seconds())
    # Allow a delta of a few seconds
    assert delta < 5
    # And currently_borrowed should be False
    assert item.currently_borrowed is False
