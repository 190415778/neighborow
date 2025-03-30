import pytest
from django.db.models.signals import post_save
from neighborow.models import Borrowing_Request_Recipients
from neighborow.signals import create_messages


@pytest.fixture(autouse=True)
def disable_signals(request):
    if request.node.get_closest_marker("enable_signals"):
        print("Signals activated")
        yield
    else:
        print("Signals deactivated")
        post_save.disconnect(create_messages, sender=Borrowing_Request_Recipients)
        yield

        post_save.connect(create_messages, sender=Borrowing_Request_Recipients)

