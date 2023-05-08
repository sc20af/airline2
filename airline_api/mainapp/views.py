from rest_framework import viewsets
from .models import FlightInstance,BookingInstance,Passenger,SeatInstance,Plane,Country,FlightInstance
from rest_framework import status
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.utils.timezone import get_default_timezone
from django.shortcuts import render
import json
from collections import defaultdict
from django.views.decorators.csrf import csrf_exempt
import requests
from datetime import datetime
#finds flights
def find_flights(request):
    if request.method != 'GET':
        response_data = {'error': 'Method not allowed', 'code': '405'}
        return JsonResponse(response_data, status=405)

    try:
        date = request.GET.get('departure_date')
        departure_c = request.GET.get('departure_country')
        arrival_c= request.GET.get('arrival_country')
        number_of_passengers = request.GET.get('number_passengers')
        max_price = request.GET.get('max_price')
        
        # Check if any  parameters are missing
        if not (date and departure_c and arrival_c and number_of_passengers):
            response_data = {"message": "Missing parameters in request"}
            return JsonResponse(response_data, status=400, safe=False)
        
        # Check if the 'date' parameter is a valid date of type string
        try:
            final_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            response_data = {"message": "Invalid date parameter. Required format: YYYY-MM-DD"}
            return JsonResponse(response_data, status=400, safe=False)
        
        # Check if the 'number_of_passengers' parameter is int
        try:
            number_of_passengers = int(number_of_passengers)
        except ValueError:
            response_data = {"message": "Invalid number_of_passengers parameter. Required integer value."}
            return JsonResponse(response_data, status=400, safe=False)
        
        departure_co = Country.objects.filter(country_name=departure_c).first() #departure country
        arrival_co = Country.objects.filter(country_name=arrival_c).first() #arrival country
        
        flights = FlightInstance.objects.filter(departure_time__date=final_date,
                                        departure_location_id=departure_co.ID,
                                        arrival_location_id=arrival_co.ID,
                                        num_available_seats__gte=number_of_passengers)

        # Filter with max price if it is given as a parameter
        if max_price is not None and max_price != '':
            try:
                max_price = float(max_price)
            except ValueError:
                response_data = {"message": "Invalid max_price parameter. Required float value."}
                return JsonResponse(response_data, status=400, safe=False)
            
            flights = flights.filter(flight_ticket_cost__lte=max_price)

        flights_list = []
        for flight in flights:
            flight_dict = {
                'cost': float(flight.flight_ticket_cost),
                'airline': "Angeliki Airline",
                'departure time': flight.departure_time,
                'arrival time': flight.arrival_time,
                'duration': str(flight.arrival_time - flight.departure_time),
                'ID': flight.ID,
            }   
            flights_list.append(flight_dict)

        # Create a response 
        response_data = {
            'flights': flights_list
        }

        # Return the response 
        return JsonResponse(response_data, status=200)
        
    except Exception as e:
        # Create a error response 
        response_data = {
            'message': str(e),
            'code': 500
        }

        # Return the response in JSON format
        return JsonResponse(response_data, status=500)
#finds the seats on a given flight
def find_seats(request):
    if request.method != 'GET':
        response_data = {'error': 'Method not allowed', 'code': '405'}
        return JsonResponse(response_data, status=405,safe=False)
    try:
        flight_number= request.GET.get('flight_id')
        seats = SeatInstance.objects.filter(flight_id=flight_number)
        if flight_number is None:
                response_data = {"message": "Missing parameters in request"}
                return JsonResponse(response_data, status=400, safe=False)
        seats_dict = defaultdict(str)
        seats_list = []
        for seat in seats:
            if seat.available == True:
                seats_dict = {
                    'seat name': seat.seat_name,
                    'available': "Available",
                }
            else:
                seats_dict = {
                    'seat name': seat.seat_name,
                    'available': "Not Available",
                }

            seats_list.append(seats_dict)

        # Check if the seats queryset is empty
        if not seats_list:
            seats_dict = {
                'seat name': 'No seats available',
                'status': False,
            }
            seats_list.append(seats_dict)

        response_data = {
            'seats': seats_list
        }

        return JsonResponse(response_data, status=200,safe=False)
    except ValueError:
            response_data = {"message": "Missing parameters/value error"}
            return JsonResponse(response_data, status=400, safe=False)
    except Exception as e:
        response_data = {
            'message': str(e),
            'code': 500
        }
        return JsonResponse(response_data, status=500,safe=False)
#update seats/ seats change
@csrf_exempt
def update_seats(request):
    if request.method != 'PUT':
        response_data = {'error': 'Method not allowed', 'code': '405'}
        return JsonResponse(response_data, status=405)

    try:

        data = request.body.decode('utf-8')
        load_data = json.loads(data)

        # Get the  parameters from  JSON 
        book_id = load_data.get('booking_id')
        passenger_first_name = load_data.get('passenger_first_name')
        passenger_last_name = load_data.get('passenger_last_name')
        new_seat_number = load_data.get('new_seat')
        # Check if all  parameters are giv4n
        if book_id is None or passenger_first_name is None or new_seat_number is None or passenger_last_name is None:
            response_data = {'message': 'Missing parameters', 'code': 400}
            return JsonResponse(response_data, status=400)
        
        booking = BookingInstance.objects.filter(ID=book_id).first()
        if booking is None:
            response_data = {'message': 'Booking not found', 'code': 401}
            return JsonResponse(response_data, status=401)
        passenger = Passenger.objects.filter(first_name=passenger_first_name, last_name = passenger_last_name,booking_id=book_id).first()
        if passenger is None:
            response_data = {'message': 'Passenger not found in the booking', 'code': 400}
            return JsonResponse(response_data, status=401)
        old_seat_id = passenger.seat_id
        old_seat = SeatInstance.objects.filter(ID=old_seat_id).first()
        name_current_seat = old_seat.seat_name
        old_seat.available = True
        new_seat = SeatInstance.objects.filter(seat_name=new_seat_number).first()
        if new_seat is None:
            response_data = {'message': 'Seat not found', 'code': 404}
            return JsonResponse(response_data, status=404)
        if not new_seat.available:
            response_data = {'message': 'Seat is not available', 'code': 401}
            return JsonResponse(response_data, status=401)
        new_seat.available = False
        passenger.seat_id = new_seat.ID
        passenger.save() #change in passenger
        old_seat.save() #change in old seat
        new_seat.save() #change in new seat
        response_data = {'message': 'Seat successfully changed'}
        return JsonResponse(response_data, status=200)
        
    except ValueError:
        response_data = {"message": "Missing parameters/value error", "code": 400}
        return JsonResponse(response_data, status=400, safe=False)
    except Exception as e:
        # Create a response dictionary with error code and message
        response_data = {
            'message': str(e),
            'code': 500
        }

        # Return the response as a JSON object with error code
        return JsonResponse(response_data, status=500, safe=False)
#get booking details from id and lead passenger email
def get_booking(request):
    if request.method != 'GET':
        response_data = {'error': 'Method not allowed', 'code': '405'}
        return JsonResponse(response_data, status=405)
    try:
        book_id = request.GET.get('booking_id')
        lead_passenger_e= request.GET.get('lead_passenger_contact_email')
        if book_id is None or lead_passenger_e is None:
                response_data = {"message": "Missing parameters in request"}
                return JsonResponse(response_data, status=400, safe=False)
        book = BookingInstance.objects.filter(ID=book_id,lead_passenger_contact_email=lead_passenger_e).first()
        if book is None:
            response_data = {'message': 'Booking not found or wrong email', 'code': 401}
            return JsonResponse(response_data, status=401)
        book_dict = {
                    'ID': book.ID,
                    'Booked time': book.booked_at_time,
                    'Lead passenger contact email': book.lead_passenger_contact_email,
                    'Lead passenger contact name': book.lead_passenger_contact_number,
                    'Total booking cost': book.total_booking_cost,
                    'Payment confirmed': book.payment_confirmed,
                    'Transaction ID': book.transaction_ID,
            }   
        
        response_data = {
            'booking': book_dict
            }

            # Return the response as a JSON object
        return JsonResponse(response_data, status=200)
    except ValueError:
            response_data = {"message": "Missing parameters/value error"}
            return JsonResponse(response_data, status=400, safe=False)
    except Exception as e:
            # Create a response dictionary with error code and message
            response_data = {
            'message': str(e),
            'code': 500
            }

                # Return the response as a JSON object with error code
            return JsonResponse(response_data, status=500, safe=False)

#delete booking and issue refund request
@csrf_exempt
def delete(request):
    if request.method != 'DELETE':
        response_data = {'error': 'Method not allowed', 'code': '405'}
        return JsonResponse(response_data, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        booking_id = data.get('booking_id')
        account_number = data.get('account_number')

        if booking_id is None or account_number is None:
            response_data = {'message': 'Missing parameters in request'}
            return JsonResponse(response_data, status=400)

        # Check if the booking exists
        booking = BookingInstance.objects.filter(ID=booking_id).first()

        if booking is None:
            response_data = {'message': 'Booking not found or wrong account number', 'code': 401}
            return JsonResponse(response_data, status=401)

        # Get the list of passengers for this booking based on booking id
        passengers = Passenger.objects.filter(booking_id=booking_id)

        # Update seat availability based on booking information
        seat_list = []
        for p in passengers:
            new_seat = SeatInstance.objects.get(ID=p.seat_id)
            new_seat.available = True
            new_seat.save()
            seat_list.append(new_seat)
        
        # Delete the booking
        booking.delete()
        data ={
            "account_number":account_number,
            "amount": booking.total_booking_cost,
            "booking_id": booking.ID,
        }
        #headers = {'Content-type': 'application/json'}
        #response = requests.post('/pay', data = json.dumps(data),headers=headers)
        #if response.status_code == 200:
        #    print("Refund successful!")
        #else:
        #    print("Error making refund:", response.text)
        response_data = {'message': 'Booking deleted successfully'}
        return JsonResponse(response_data, status=200)

    except json.JSONDecodeError:
        response_data = {'message': 'Invalid JSON in request body'}
        return JsonResponse(response_data, status=400)

    except Exception as e:
        response_data = {'message': str(e), 'code': 500}
        return JsonResponse(response_data, status=500)


#delete bookings that were made a week ago
def check_booking():
    week_ago = datetime.now() - timedelta(weeks=1) #find time a week ago from now
    old_bookings = BookingInstance.objects.filter(payment_confirmed=False, booked_at_time__lt=week_ago) #bookings that are peding and were made a week ago

    # Delete each of the old bookings
    for booking in old_bookings:
        passengers = Passenger.objects.filter(booking_id=booking.ID)

        # Update seat availability based on booking information
        seat_list = []
        for p in passengers:
            new_seat = SeatInstance.objects.get(ID=p.seat_id)
            new_seat.available = True
            new_seat.save()
            seat_list.append(new_seat)
        booking.delete()

#make a booking
@csrf_exempt
def book(request):
    if request.method != 'POST':
        response_data = {'error': 'Method not allowed', 'code': '405'}
        return JsonResponse(response_data, status=405)

    # Get request data from JSON payload
    try:
        check_booking()
        payload = json.loads(request.body)
        flight_id = payload['flight_id']
  #      airline_name = payload['airline_name']
        lead_passenger_contact_email = payload['lead_passenger_contact_email']
        lead_passenger_contact_number = payload['lead_passenger_contact_number']
        passengers = payload['passengers']
        cardholder_name = payload['cardholder_name']
        card_number = payload['card_number']
        cvc_hash = payload['cvc_hash']
        sortcode = payload['sortcode']
        expiry_date = payload['expiry_date']
        
    except KeyError:
        response_data = {"message": "Missing parameters in request"}
        return JsonResponse(response_data, status=400)
    
    # Make sure all required fields are present
    if all([flight_id, lead_passenger_contact_email, lead_passenger_contact_number, cardholder_name, 
            card_number, cvc_hash, sortcode, expiry_date, passengers]):
        # Do something if all parameters are present
        p = []
    else:
        response_data = {"message": "Missing parameters in request"}
        return JsonResponse(response_data, status=400)
    
    price = FlightInstance.objects.filter(ID=flight_id).values('flight_ticket_cost').first()['flight_ticket_cost']
    total_book_cost = len(passengers) * price
    # Check if the number of passengers is less than or equal to the number of available seats
    num_passengers = len(passengers)
    flight_instance = FlightInstance.objects.get(ID=flight_id)
    num_available_seats = flight_instance.num_available_seats
    if num_passengers > num_available_seats:
        response_data = {"message": "Not enough available seats to make the booking"}
        return JsonResponse(response_data, status=400)
    # Create a new booking
    try:
        booking = BookingInstance.objects.create(
        lead_passenger_contact_email=lead_passenger_contact_email,
        lead_passenger_contact_number=lead_passenger_contact_number,
        total_booking_cost=total_book_cost,
        payment_confirmed=False,
        transaction_ID=0 
        )
        #response = client.post('/payments',json=payload)
        #self.assertEqual(response.status_code, 200)
        #if response.status_code == 200:
        #    transaction_id = response.json['transaction_id']
        #    booking.payment_confirmed=True
        #    booking.transaction_ID=transaction_id


        for passenger_detail in passengers:
            seat_number = passenger_detail['seat_number']
            try:
            # Find the corresponding seat  for the specific flight and seat number
                seat_instance = SeatInstance.objects.get(flight_id=flight_id, seat_name=seat_number)

                # Check if seat is available
                if not seat_instance.available:
                    response_data = {"message": f"Seat {seat_number} is already reserved"}
                    return JsonResponse(response_data, status=400)

                c = Country.objects.get(country_name=passenger_detail['nationality_country'])
                nationality_c = c.ID

            # Create passenger instance
                passenger = Passenger.objects.create(
                booking_id=booking.ID,
                first_name=passenger_detail['first_name'],
                last_name=passenger_detail['last_name'],
                date_of_birth=passenger_detail['date_of_birth'],
                nationality_country_id=nationality_c,
                passport_num=passenger_detail['passport_number'],
                seat=seat_instance
                )

            # Update the seat as reserved
                seat_instance.available = False
                seat_instance.save()

            # Decrease the num_available_seats for the corresponding flight
                flight_instance.num_available_seats -= 1
                flight_instance.save()

            except SeatInstance.DoesNotExist:
                response_data = {"message": f"Seat instance does not exist for seat number {seat_number} and flight {flight_id}"}
                return JsonResponse(response_data, status=404)

            except FlightInstance.DoesNotExist:
                response_data = {"message": "Flight instance does not exist"}
                return JsonResponse(response_data, status=404)


    # Return booking ID as response
        response_data = {"booking_id": booking.ID}
        return JsonResponse(response_data, status=200)

    except Exception as e:
        response_data = {"message": str(e)}
        return JsonResponse(response_data, status=500)
