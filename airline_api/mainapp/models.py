from django.db import models

class BookingInstance(models.Model):
    ID = models.AutoField(primary_key=True)
    booked_at_time = models.DateTimeField(auto_now_add=True) #the value of booked_at_time will be automatically set to the current date and time.
    lead_passenger_contact_email = models.CharField(max_length=100)
    lead_passenger_contact_number = models.CharField(max_length=15)
    total_booking_cost = models.FloatField()
    payment_confirmed = models.BooleanField(default=False)
    transaction_ID = models.IntegerField()
    #The on_delete=models.CASCADE parameter specifies that if a Flight object is deleted, all related Seat objects will also be deleted.
    

    def __str__(self):
        return self.id
    
class Plane(models.Model):
    ID = models.IntegerField(unique=True,primary_key=True)
    max_capacity = models.IntegerField()
    max_flight_distance = models.IntegerField()

    def __str__(self):
        return self.id
    
class Country(models.Model):
    ID = models.IntegerField(unique=True, primary_key=True)
    country_name = models.CharField(max_length=255)
    continent = models.CharField(max_length=255)
    longitude = models.FloatField(max_length=50)
    latitude = models.FloatField(max_length=50)

    def __str__(self):
        return self.id
    
class FlightInstance(models.Model):
    ID = models.IntegerField(unique=True,primary_key=True)
    plane = models.ForeignKey(Plane, on_delete=models.CASCADE)
    flight_ticket_cost = models.DecimalField(max_digits=8, decimal_places=2)
    departure_location = models.ForeignKey(Country, on_delete=models.CASCADE,related_name='departure_location')
    arrival_location =  models.ForeignKey(Country, on_delete=models.CASCADE,related_name='arrival_location')
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    num_available_seats = models.IntegerField()

    #need to implement this when having bookings table
    # def available_seats(self):
    #     reserved_seats = self.reservations.aggregate(reserved_seats=Sum('num_seats'))['reserved_seats'] or 0
    #     return self.total_number_of_seats - reserved_seats

    def __str__(self):
        return self.id
    
class SeatInstance(models.Model):
    ID = models.IntegerField(unique=True,primary_key=True)
    seat_name = models.CharField(max_length=10)
    available = models.BooleanField(default=True)
    flight = models.ForeignKey(FlightInstance, on_delete=models.CASCADE)
    #The on_delete=models.CASCADE parameter specifies that if a Flight object is deleted, all related Seat objects will also be deleted.
    

    def __str__(self):
        return self.id
    
class Passenger(models.Model):
    ID = models.IntegerField(unique=True,primary_key=True)
    booking =  models.ForeignKey(BookingInstance, on_delete=models.CASCADE) #foreign key
    first_name = models.CharField(max_length=105)
    last_name = models.CharField(max_length=105)
    date_of_birth = models.DateField()
    nationality_country = models.ForeignKey(Country,on_delete=models.CASCADE)
    passport_num = models.CharField(max_length=205)
    seat = models.ForeignKey(SeatInstance, on_delete=models.CASCADE)

    def __str__(self):
        return self.id