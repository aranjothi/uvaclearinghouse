from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('help/', views.help_support, name='help_support'),
    path('login/', views.login_page, name='login'),
    path('signup/', views.signup_page, name='signup'),
    path('signup/validate-exec-code/', views.validate_exec_code, name='validate_exec_code'),
    path('signup/store-exec-codes/', views.store_exec_codes, name='store_exec_codes'),
    path('profile/', views.profile_page, name='profile'),
    path('logout/', views.logout_page, name='logout'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('signup/google/', views.google_signup, name='google_signup'),
    path('create-profile/', views.create_profile_page, name='create_profile'),
    path('get-involved/', views.get_involved_page, name='get_involved'),

    path('clubs/<slug:slug>/', views.ClubDetailView.as_view(), name='club_detail'),
    path('clubs/<slug:slug>/save/', views.toggle_save_club, name='toggle_save_club'),
    path('clubs/<slug:slug>/join/', views.join_club, name='join_club'),
    path('clubs/<slug:slug>/verify/', views.verify_exec, name='verify_exec'),
    path('clubs/<slug:slug>/create-event/', views.create_event, name='create_event'),
    path('clubs/<slug:slug>/upload-image/', views.upload_club_image, name='upload_club_image'),
    path('clubs/<slug:slug>/edit-info/', views.edit_club_info, name='edit_club_info'),
    path('clubs/<slug:slug>/post-announcement/', views.post_announcement, name='post_announcement'),
    path('clubs/<slug:slug>/announcements/<int:ann_id>/vote/', views.vote_poll, name='vote_poll'),
    path('clubs/<slug:slug>/announcements/<int:ann_id>/delete/', views.delete_announcement, name='delete_announcement'),
    path('clubs/<slug:slug>/announcements/<int:ann_id>/unvote/', views.unvote_poll, name='unvote_poll'),
    path('clubs/<slug:slug>/highlights/add/', views.add_highlight, name='add_highlight'),
    path('clubs/<slug:slug>/highlights/<int:highlight_id>/delete/', views.delete_highlight, name='delete_highlight'),
    path('clubs/<slug:slug>/highlights/reorder/', views.reorder_highlights, name='reorder_highlights'),
    path('events/<int:event_id>/rsvp/', views.rsvp_event, name='rsvp_event'),
    path('events/<int:event_id>/subscribe/', views.toggle_event_subscription, name='subscribe_event'), # # Source: Generated with Claude AI, asked to create an email notification system, Apr. 28

    path('my-clubs/', views.my_clubs_page, name='my_clubs'),

    path('clubs/<slug:slug>/forum/', views.forum_list, name='forum_list'),
    path('clubs/<slug:slug>/forum/new/', views.forum_new_thread, name='forum_new_thread'),
    path('clubs/<slug:slug>/forum/<int:thread_id>/', views.forum_thread, name='forum_thread'),
    path('clubs/<slug:slug>/forum/<int:thread_id>/like/', views.like_thread, name='like_thread'),
    path('clubs/<slug:slug>/forum/reply/<int:reply_id>/like/', views.like_reply, name='like_reply'),
    path('clubs/<slug:slug>/forum/<int:thread_id>/pin/', views.pin_thread, name='pin_thread'),
    path('clubs/<slug:slug>/forum/<int:thread_id>/delete/', views.delete_thread, name='delete_thread'),

    #Indiviudal Events Page Setup
    path('events/', views.Events_page, name='events'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),

    path('user-admin/', views.user_admin, name='user_admin'),
    path('user-admin/change-role/', views.user_admin_change_role, name='user_admin_change_role'),

    # Messaging — Direct Messages
    path('messages/', views.dm_inbox, name='dm_inbox'),
    path('messages/<str:username>/', views.dm_conversation, name='dm_conversation'),

    # Messaging widget API
    path('widget/inbox/', views.widget_inbox, name='widget_inbox'),
    path('widget/conversation/<str:username>/', views.widget_conversation, name='widget_conversation'),
    path('widget/send/', views.widget_send, name='widget_send'),

    #Exec page stuff
    path('executives/', views.executive_page, name='executive_page'),
    path('executives/<slug:slug>/', views.executive_club_page, name='executive_club_page'),
    path('executives/<slug:slug>/events/', views.executive_club_events, name='executive_club_events'),
    path('executives/<slug:slug>/events/<int:event_id>/edit/', views.executive_edit_event, name='executive_edit_event'),
    path('executives/<slug:slug>/events/<int:event_id>/delete/', views.executive_delete_event, name='executive_delete_event'),
    path('executives/<slug:slug>/people/', views.executive_club_people, name='executive_club_people'),
    path('executives/<slug:slug>/people/<int:membership_id>/', views.executive_remove_member, name='executive_remove_member'),
    path('executives/<slug:slug>/manage/', views.executive_club_manage, name='executive_club_manage'),
    path('executives/<slug:slug>/manage/toggle-approval/', views.executive_toggle_approval,
         name='executive_toggle_approval'),
    path('executives/<slug:slug>/manage/request/<int:request_id>/<str:action>/', views.executive_handle_request,
         name='executive_handle_request'),
    path('executives/<slug:slug>/manage/ban/<int:membership_id>/', views.executive_ban_member,
         name='executive_ban_member'),
    path('executives/<slug:slug>/manage/unban/<int:ban_id>/', views.executive_unban_member,
         name='executive_unban_member'),
    path('executives/<slug:slug>/manage/remove/<int:membership_id>/', views.executive_remove_member,
         name='executive_remove_member'),
    path('users/suggest/', views.user_suggest, name='user_suggest'),
    path('users/<str:username>/', views.user_profile_page, name='user_profile'),

    path('search/', views.global_search, name='global_search'),
    path('search/suggest/', views.search_suggest, name='search_suggest'),
]