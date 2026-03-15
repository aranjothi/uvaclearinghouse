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
    #creates the urls for each club's page
   path('clubs/<slug:slug>/', views.ClubDetailView.as_view(), name='club_detail'),
   path('clubs/<slug:slug>/join/', views.join_club, name='join_club'),
   path('clubs/<slug:slug>/verify/', views.verify_exec, name='verify_exec'),
   path("clubs/<slug:slug>/create-event/", views.create_event, name="create_event"),
   path('executives/', views.executive_page, name='executive_page'),
   path('clubs/<slug:slug>/create-event/', views.create_event, name='create_event'),
]