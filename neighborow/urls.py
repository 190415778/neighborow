from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
#    path('test-function/', function_view_test),
    #path('index/', ClassViewIndex.as_view(), name='index'),
    path('', views.index, name='index'),
    path('form_invitation/', views.form_invitation, name='form_invitation'),
    path('form_building/', views.form_building, name='form_building'),
    path('get_building_details/', views.get_building_details, name='get_building_details'),
    path('app_settings/', views.app_settings, name='app_settings'),
    path('get_app_settings/', views.get_app_settings, name='get_building_details'),
    path('access_code/', views.access_code, name='access_code'),
    path('get_access_codes/', views.get_access_codes, name='get_access_codes'),

    path('generate_code/', views.generate_code, name='generate_code'),
    path('generate_codes/', views.generate_codes, name='generate_codes'),

    path('borrowing_request/', views.widget_borrowing, name='widget_borrowing_request'),
    path('select_recipients/', views.select_recipients, name='select_recipients'),

    path('member_info/', views.widget_member_info, name='widget_member_info'),

    path('member_communication/', views.widget_member_communication, name='widget_member_communication'),

    path('messages_inbox/', views.widget_messages_inbox, name='widget_messages_inbox'),
    path('send_reply/', views.send_reply, name='send_reply'),
    path('reply_modal/', views.reply_modal, name='reply_modal'),


    path('messages_outbox/', views.widget_messages_outbox, name='widget_messages_outbox'),

    path('send_message/', views.widget_send_message, name='widget_send_message'),

    path('item_list/', views.widget_item_list, name='widget_item_list'),
    path('item_list_search/', views.widget_item_list, name='item_list_search'),   
    path('item_images/<int:item_id>/', views.get_item_images, name='get_item_images'),

    path('item_manager/', views.widget_item_manager, name='widget_item_manager'),
    path('update_item/<int:item_id>/', views.update_item, name='update_item'),
    path('delete_item/<int:item_id>/', views.delete_item, name='delete_item'),
    path('get_item_images/<int:item_id>/', views.get_item_images, name='get_item_images'),
    path('update_item_image_caption/<int:item_id>/', views.update_item_image_caption, name='update_item_image_caption'),
    path('upload_item_image/<int:item_id>/', views.upload_item_image, name='upload_item_image'),
    path('delete_item_image/<int:image_id>/', views.delete_item_image, name='delete_item_image'), 
    path('create_item/', views.create_item, name='create_item'),

    path('borrow_item/', views.borrow_item, name='borrow_item'),  

    path('calendar/', views.widget_calendar, name='widget_calendar'),
    path('calendar/<int:year>/<int:month>/', views.widget_calendar, name='calendar_widget'),

    path('borrowed_items/', views.widget_borrowed_items, name='widget_borrowed_items'),
    path('condition_log/<int:transaction_id>/', views.condition_log, name='condition_log'),
    path('return_item/<int:transaction_id>/', views.return_item, name='return_item'),

    path('loaned_items/', views.widget_loaned_items, name='widget_loaned_items'),
    path('return_item_loaned/<int:transaction_id>/', views.return_item_loaned, name='return_item_loaned'),



    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
