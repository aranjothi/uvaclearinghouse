from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_page, name='login'),
    path('signup/', views.signup_page, name='signup'),
    path('profile/', views.profile_page, name='profile'),
    path('logout/', views.logout_page, name='logout'),
    path('signup/google/', views.google_signup, name='google_signup'),
    path('create-profile/', views.create_profile_page, name='create_profile'),
    path('get-involved/', views.get_involved_page, name='get_involved'),
    path('my-clubs/', views.my_clubs_page, name='my_clubs'),
    path('events/', views.Events_page, name='events'),
        # Messaging — Threads
    path('clubs/<slug:slug>/threads/', views.thread_list, name='thread_list'),
    path('clubs/<slug:slug>/threads/new/', views.create_thread, name='create_thread'),
    path('clubs/<slug:slug>/threads/<int:thread_id>/', views.thread_detail, name='thread_detail'),
    path('clubs/<slug:slug>/threads/<int:thread_id>/pin/<int:message_id>/', views.pin_message, name='pin_message'),

    # Messaging — Direct Messages
    path('messages/', views.dm_inbox, name='dm_inbox'),
    path('messages/<str:username>/', views.dm_conversation, name='dm_conversation'),

]
