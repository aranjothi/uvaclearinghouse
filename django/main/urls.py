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
]
