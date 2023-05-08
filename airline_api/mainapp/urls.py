from django.urls import path
from . import views

urlpatterns = [
    path('flights/', views.find_flights, name='search flights'),
    path('seats/', views.find_seats, name='search seats'),
    path('update_seats/', views.update_seats, name='update seats'),
    path('get_booking_details/', views.get_booking, name='get booking details'),
    path('delete_booking/',views.delete,name = 'delete booking'),
    path('book/',views.book,name = 'book'),
]