from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('upload/', views.upload_image, name='upload'),
    path('account/', views.account_page, name='account'),

    # urls for auth0
    path("", views.index, name="index"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("callback", views.callback, name="callback"),

    # urls for formation info pages
    path('formations/', views.formations, name="formations"),
    path('formations/pistol/', views.pistol, name="pistol"),
    path('formations/shotgun/', views.shotgun, name="shotgun"),
    path('formations/empty/', views.empty, name="empty"),
    path('formations/i/', views.i, name="i"),
    path('formations/singleback/', views.singleback, name="singleback"),

]
