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
from rest_framework.decorators import api_view
#finds flights

def home(request):
    context = {
        'title': 'Home'
    }
    return JsonResponse(context)
#find flights on specific days
@api_view(['GET'])
def find_flights(request):
    if request.method != 'GET':
        response_data = {'error': 'Method not allowed', 'code': '405'}
        return JsonResponse(response_data, status=405)

    try:
        date = request.GET.get('departure_date')
        departure_c = request.GET.get('departure_country')
        arrival_c= request.GET.get('arrival_country')
        number_of_passengers = request.GET.get('num_passengers')
        max_price = request.GET.get('max_price')
        
        # Check if any  parameters are missing
        if not (date and departure_c and arrival_c and number_of_passengers):
            response_data = {"message": "Missing parameters in request"}
            return JsonResponse(response_data, status=400, safe=False)
        
        # Check if the 'date' parameter is a valid date with valid format
        try:
            final_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            response_data = {"message": "Invalid date parameter. Required format: YYYY-MM-DD"}
            return JsonResponse(response_data, status=400, safe=False)
        
        # Check if the 'num_passengers' is int
        try:
            number_of_passengers = int(number_of_passengers)
        except ValueError:
            response_data = {"message": "Invalid number_of_passengers parameter. Required integer value."}
            return JsonResponse(response_data, status=400, safe=False)
        #find departure and arrival countries
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
                'flight_ticket_cost': float(flight.flight_ticket_cost),
                'airline_name': "Angeliki's Airline",
                'departure_time': flight.departure_time,
                'arrival_time': flight.arrival_time,
                'duration': str(flight.arrival_time - flight.departure_time),
                'id': flight.ID,
                'num_available_seats': flight.num_available_seats
            }   
            flights_list.append(flight_dict)

        # Create a response 
        response_data = flights_list
        

        # Return 200
        return JsonResponse(response_data, status=200,safe=False)
        
    except Exception as e:
        # Create a error response 
        response_data = {
            'message': str(e),
            'code': 500
        }

        # Return the response in JSON format
        return JsonResponse(response_data, status=500)
#finds the seats on a given flight
@api_view(['GET'])
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
                    'seat_name': seat.seat_name,
                    'available': seat.available,
                }
            else:
                seats_dict = {
                    'seat_name': seat.seat_name,
                    'available': seat.available,
                }

            seats_list.append(seats_dict)

        # Check if the seats is empty
        if not seats_list:
            seats_dict = {
                'seat_name': seat.seat_name,
                'status': seat.available,
            }
            seats_list.append(seats_dict)

        response_data = seats_list

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
@api_view(['PUT'])
@csrf_exempt
def update_seats(request):
    if request.method != 'PUT':
        response_data = {'error': 'Method not allowed', 'code': '405'}
        return JsonResponse(response_data, status=405)

    try:
        data = request.body.decode('utf-8')
        # Replace single quotes with double quotes -> problem with aggregator
        data = data.replace("'", "\"")
        # Parse JSON 
        data_dict = json.loads(data)

        # Get parameters from JSON data
        book_id = data_dict['booking_id']
        passenger_first_name = data_dict['first_name']
        passenger_last_name = data_dict['last_name']
        new_seat_number = data_dict['seat_name']
        # Check if all parameters are present
        if book_id is None or passenger_first_name is None or passenger_last_name is None or new_seat_number is None:
            return JsonResponse({'message': 'Missing parameters1/value error', 'code': 400}, status=400)
        
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
@api_view(['GET'])
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
        passengers = Passenger.objects.filter(booking_id=book_id)
        p1 = Passenger.objects.filter(booking_id=book_id).first()
        seat = SeatInstance.objects.filter(ID=p1.seat_id).first()
        flight_id = seat.flight_id
        # change in datatime format to fix aggregator problem
        if isinstance(book.booked_at_time, datetime):
            formatted_dt = book.booked_at_time.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            dt = datetime.strptime(book.booked_at_time, "%Y-%m-%d %H:%M:%S")
            formatted_dt = dt.strftime("%Y-%m-%dT%H:%M:%S")
        book_dict = {
                    'id': book.ID,
                    'flight_id': flight_id,
                    'num_passengers': len(passengers),
                    'booked_at_time': formatted_dt,
                    'lead_passenger_contact_email': book.lead_passenger_contact_email,
                    'lead_passenger_contact_number': book.lead_passenger_contact_number,
                    'total_booking_cost': book.total_booking_cost,
                    'payment_confirmed': book.payment_confirmed,
                    'transaction_id': book.transaction_ID,
            }   
        
        response_data = book_dict

            # Return the response as a JSON object
        return JsonResponse(response_data, status=200)
    except ValueError:
            response_data = {"message": "Missing parameters/value error"}
            return JsonResponse(response_data, status=400, safe=False)
    except Exception as e:
            # Create a response dictionary
            response_data = {
            'message': str(e),
            'code': 500
            }

                # Return the response as a JSON object with error 500
            return JsonResponse(response_data, status=500, safe=False)
#delete booking and issue refund request
@api_view(['DELETE'])
@csrf_exempt
def delete(request):
    if request.method != 'DELETE':
        response_data = {'error': 'Method not allowed', 'code': '405'}
        return JsonResponse(response_data, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        booking_id = data.get('booking_id')
        account_number = data.get('account_number')
        lead_passenger_contact_email = data.get('lead_passenger_contact_email')
        p_sortcode = data.get('sortcode')

        if booking_id is None or account_number is None:
            response_data = {'message': 'Missing parameters in request'}
            return JsonResponse(response_data, status=400)

        # Check if the booking exists
        booking = BookingInstance.objects.filter(ID=booking_id).first()

        if booking is None:
            response_data = {'message': 'Booking not found or wrong account number', 'code': 401}
            return JsonResponse(response_data, status=401)

        # Delete the booking
        data ={
            "transaction_id": booking.transaction_ID
        }
        if p_sortcode == "373891":
            response = requests.post("https://sc20jzl.pythonanywhere.com/get_transaction_details/", json=data)
        elif p_sortcode == "232323":
            response = requests.post("https://lanre.pythonanywhere.com/get_transaction_details/", json=data)
        
        if response.status_code == 200:
            response_data = json.loads(response.text)

        else:
            response_data = {'message': 'Transaction ID not found', 'code': 404}
            return JsonResponse(response_data)
        if p_sortcode== "373891":
            post_data = {
                        "sender_cardholder_name":"Angeliki Fragkeskou",
                         "sender_card_number_hash":"bd9b1d4f9207e60821103d3cf7be503ded1a7a93b2f9430cc6a6c68072675c7e2176518fed365e25b9974f90265ec741",
                         "sender_cvc_hash":"07f211044fd60906cd609486d0949bf697cfbc48310c8f71bdfc3dc15724066a4506142275aa73ef512f875229a2e66f",
                        "sender_sortcode":p_sortcode, #need that
                        "sender_expiry_date":"2023-09-15", #need that
                        "recipient_cardholder_name":response_data['sender_name'],
                        "recipient_sortcode":p_sortcode,
                        "recipient_account_number":account_number,
                        "payment_amount":booking.total_booking_cost
                        }
            response1 = requests.post('https://sc20jzl.pythonanywhere.com/pay/', json=post_data)
        elif p_sortcode == "232323":
            post_data = {
                        "sender_cardholder_name":"Angeliki Fragkeskou",
                         "sender_card_number_hash":"8bb0e5d235ab8d642775375ea1f19ce688d28af57719d4916c57dc9a6a50bb49ec60c00e935983242692c80e2b264141",
                         "sender_cvc_hash":"49093ddfa6f1e83caa8b56a7b13aeaebdbbe2e491ee31931c5a5c1118d08835da7cbf9e050ecf0043351bf92f340312d",
                        "sender_sortcode":p_sortcode, #need that
                        "sender_expiry_date":"09/23", #need that
                        "recipient_cardholder_name":response_data['sender_name'],
                        "recipient_sortcode":p_sortcode,
                        "recipient_account_number":account_number,
                        "payment_amount":booking.total_booking_cost
                        }
            response1 = requests.post('https://lanre.pythonanywhere.com/pay/', json=post_data)
        if response1.status_code == 200:
            print("Refund successful!")

            passengers = Passenger.objects.filter(booking_id=booking_id)

            # Update available seats
            seat_list = []
            for p in passengers:
                new_seat = SeatInstance.objects.get(ID=p.seat_id)
                new_seat.available = True
                flightID = new_seat.flight_id
                flight_instance = FlightInstance.objects.get(ID=flightID)
                flight_instance.num_available_seats += 1
                flight_instance.save()
            #   increase flight num

                new_seat.save()
                seat_list.append(new_seat)
        else:
            print("Error making refund:", response.text)
        
        response_data = {'message': 'Booking deleted successfully', 'transaction_id': booking.transaction_ID,"payment_amount": booking.total_booking_cost }
        booking.delete()
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
#make a booking function
@api_view(['POST'])
@csrf_exempt
def book(request):

    if request.method != 'POST':
        response_data = {'error': 'Method not allowed', 'code': '405'}
        return JsonResponse(response_data, status=405)
    # Get request data from JSON 
    try:
        data = request.body.decode('utf-8')
        # Replace single with double quotes
        data = data.replace("'", "\"")
        # Parse JSON data
        data_dict = json.loads(data)

        check_booking() #call check booking to delete old pending bookings
        data = json.loads(request.body)
        flight_id = data_dict['flight_id']
        lead_passenger_contact_email = data_dict['lead_passenger_contact_email']
        lead_passenger_contact_number = data_dict['lead_passenger_contact_number']
        passengers = data_dict['passengers']
        payment_details = data_dict['payment_details']
        cardholder_name = payment_details['cardholder_name']
        card_number = payment_details['card_number']
        cvc_hash = payment_details['cvc']
        sortcode = payment_details['sortcode']
        expiry_date = payment_details['expiry_date']

        data = {
            "flight_id":flight_id,
            "lead_passenger_contact_email":lead_passenger_contact_email,
            "lead_passenger_contact_number":lead_passenger_contact_number,
            "passengers":passengers,
            "cardholder_name":cardholder_name,
            "card_number":card_number,
            "cvc_hash":cvc_hash,
            "sortcode":sortcode,
            "expiry_date":expiry_date,
        }
        #return JsonResponse(data, status=200)
    except KeyError:
        response_data = {"message": "Missing parameters 1 in request"}
        return JsonResponse(response_data, status=400)
    
    # Make sure all required fields are present
    if all([flight_id, lead_passenger_contact_email, lead_passenger_contact_number, payment_details, 
             passengers]):
        # Do something if all parameters are present
        p = []
    else:
        response_data = {"message": "Missing parameters 2 in request"}
        return JsonResponse(response_data, status=400)
    
    price = FlightInstance.objects.filter(ID=flight_id).values('flight_ticket_cost').first()['flight_ticket_cost']
    total_book_cost = len(passengers) * price
    # Check if there are available seats on the flight
    num_passengers = len(passengers)
    flight_instance = FlightInstance.objects.get(ID=flight_id)
    num_available_seats = flight_instance.num_available_seats
    if num_passengers > num_available_seats:
        response_data = {"message": "Not enough available seats to make the booking"}
        return JsonResponse(response_data, status=400)
    # Create a new booking
    booking = BookingInstance.objects.create(
    lead_passenger_contact_email=lead_passenger_contact_email,
    lead_passenger_contact_number=lead_passenger_contact_number,
    total_booking_cost=total_book_cost,
    payment_confirmed=False,
    transaction_ID=0 
    )
    post_data = {"sender_cardholder_name"       :cardholder_name,
                "sender_card_number_hash"       :card_number,
                "sender_cvc_hash"               :cvc_hash,
                "sender_sortcode"               :sortcode,
                "sender_expiry_date"            :expiry_date,
                "recipient_cardholder_name"     :"Angeliki Fragkeskou",
                "recipient_sortcode"            :sortcode,
                "recipient_account_number"      :"26102002",
                "payment_amount"                :int(total_book_cost)
                }
    if sortcode == "373891":
        response = requests.post("https://sc20jzl.pythonanywhere.com/pay/", json=post_data)
    elif sortcode == "232323":
        response = requests.post("https://lanre.pythonanywhere.com/pay/", json=post_data)
    if response.status_code == 200:
        response_body = json.loads(response.text)  # parse response JSON
        transaction_ID2 = response_body["transaction_id"] #get transaction ID
        booking.transaction_ID = transaction_ID2
        booking.payment_confirmed= True
        booking.save()
        
    else:
        response_data = {"message": response.text}
        return JsonResponse(response_data, status=401)


    for passenger_detail in passengers:
        seat_number = passenger_detail['seat_name']
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

        # Decrease the num_available_seats for the  flight
            flight_instance.num_available_seats -= 1
            flight_instance.save()

        except SeatInstance.DoesNotExist:
            response_data = {"message": f"Seat instance does not exist for seat number {seat_number} and flight {flight_id}"}
            return JsonResponse(response_data, status=404)

        except FlightInstance.DoesNotExist:
            response_data = {"message": "Flight instance does not exist"}
            return JsonResponse(response_data, status=404)

        response_data = {"id": booking.ID}
        return JsonResponse(response_data, status=200)
