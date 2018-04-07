from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt

from .models import *

import datetime
from datetime import timedelta
import json
import random
import string
import requests

def find_flight(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    dep_date = datetime.datetime.strptime(body['dep_date'], '%Y-%m-%d')
    try:
        dep_airport = Airport.objects.get(name__contains=body['dep_airport'])
        dest_airport = Airport.objects.get(name__contains=body['dest_airport'])
    except ObjectDoesNotExist:
        return HttpResponse('No flights found', status=503)

    num_passengers = body['num_passengers']
    is_flex = body['is_flex']

    if is_flex:
        flight_set = Flight.objects.filter(dep_airport=dep_airport,
                                           dest_airport=dest_airport,
                                           dep_datetime__range=[dep_date + datetime.timedelta(days=-2), dep_date + datetime.timedelta(days=2)])
    else:
        flight_set = Flight.objects.filter(dep_airport=dep_airport,
                                           dest_airport=dest_airport,
                                           dep_datetime__year=dep_date.year,
                                           dep_datetime__month=dep_date.month,
                                           dep_datetime__day=dep_date.day)

    flightList = []

    for result in flight_set:
        flight = {}
        flight['flight_id'] = result.pk
        flight['flight_num'] = result.flight_num
        flight['dep_airport'] = result.dep_airport.name
        flight['dest_airport'] = result.dest_airport.name
        flight['dep_datetime'] = result.dep_datetime.strftime("%Y-%m-%d %H:%M:%S")
        flight['arr_datetime'] = result.arr_datetime.strftime("%Y-%m-%d %H:%M:%S")
        flight['duration'] = str(result.duration)
        flight['price'] = result.price

        flightList.append(flight)

    response = {}
    response['flights'] = flightList

    if flight_set:
        return HttpResponse(json.dumps(response))
    else:
        return HttpResponse('No flights found', status=503)

@csrf_exempt
def book_flight(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    booking_number = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    try:
        flight = Flight.objects.get(id=body['flight_id'])
    except ObjectDoesNotExist:
        return HttpResponse('No flight with ID: ' + body['flight_id'], status=503)

    num_passengers = len(body['passengers'])
    expiration_date = datetime.datetime.now() + timedelta(days=7)

    bookings_this_flight = Booking.objects.filter(flight=flight)

    total_seats = flight.aircraft.number_of_seats
    seats_taken = 0
    for b in bookings_this_flight:
        seats_taken += b.number_of_seats

    if total_seats < (seats_taken + num_passengers):
        return HttpResponse('Not enough seats available, only ' + str(total_seats-seats_taken) + ' available', status=503)

    booking = Booking(number=booking_number,
                      flight=flight,
                      number_of_seats=num_passengers,
                      status='ONHOLD',
                      expiration_date=expiration_date)
    booking.save()

    for pas in body['passengers']:
        passenger = Passenger(first_name=pas['first_name'],
                              surname=pas['surname'],
                              email=pas['email'],
                              phone_number=pas['phone'])
        passenger.save()
        booking.passengers.add(passenger)

    response = {}
    response['booking_num'] = booking_number
    response['booking_status'] = 'ONHOLD'
    response['tot_price'] = num_passengers * flight.price

    return HttpResponse(json.dumps(response), status=201)

def payment_methods(request):
    payment_providers = PaymentProvider.objects.all()

    paymentList = []

    for pp in payment_providers:
        payment = {}
        payment['pay_provider_id'] = pp.pk
        payment['pay_provider_name'] = pp.name

        paymentList.append(payment)

    response = {}
    response['pay_providers'] = paymentList

    if payment_providers:
        return HttpResponse(json.dumps(response))
    else:
        return HttpResponse('No payment providers found', status=503)

@csrf_exempt
def pay_for_booking(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    try:
        pay_provider = PaymentProvider.objects.get(pk=body['pay_provider_id'])
    except ObjectDoesNotExist:
        return HttpResponse('No payment provider with ID: ' + body['pay_provider_id'], status=503)

    booking = Booking.objects.get(number=body['booking_num'])

    invoice_params = {}
    invoice_params['account_num'] = pay_provider.account_number
    invoice_params['client_ref_num'] = booking.number
    invoice_params['amount'] = str(booking.number_of_seats * booking.flight.price)

    session = requests.session()

    login_data = {}
    login_data['username'] = pay_provider.username
    login_data['password'] = pay_provider.password

    login = session.post(pay_provider.website + 'api/login/',
                         data={'username': pay_provider.username, 'password': pay_provider.password})

    r = session.post(pay_provider.website + 'api/createinvoice/',
                     headers={'Content-Type': 'application/json'},
                     data=json.dumps(invoice_params))
    print(login_data)
    print(r.status_code)
    print(r.text)
    if r.status_code == 201:
        response = json.loads(r.text)

        invoice = Invoice(payment_reference=response['payprovider_ref_num'],
                          booking=booking,
                          amount=booking.number_of_seats * booking.flight.price,
                          is_paid=False,
                          electronic_stamp=response['stamp_code'])
        invoice.save()

        client_response = {}
        client_response['pay_provider_id'] = body['pay_provider_id']
        client_response['invoice_id'] = invoice.payment_reference
        client_response['booking_num'] = booking.number
        client_response['url'] = pay_provider.website

        return HttpResponse(json.dumps(client_response), status=201)
    else:
        return HttpResponse("Could not establish connection to payment provider", status=503)

@csrf_exempt
def finalize_booking(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    booking = Booking.objects.get(number=body['booking_num'])

    if booking:
        invoice = Invoice.objects.get(booking=booking)
        if body['stamp'] == invoice.electronic_stamp:
            invoice.is_paid = True
            booking.status = 'CONFIRMED'

            invoice.save()
            booking.save()

            response = {}
            response['booking_num'] = booking.number
            response['booking_status'] = booking.status

            return HttpResponse(json.dumps(response), status=201)
        else:
            return HttpResponse('Electronic stamp does not match', status=503)
    else:
        return HttpResponse('Booking number not found', status=503)

def booking_status(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    booking = Booking.objects.get(number=body['booking_num'])

    if booking:
        response = {}
        response['booking_num'] = booking.number
        response['booking_status'] = booking.status
        response['flight_num'] = booking.flight.flight_num
        response['dep_airport'] = booking.flight.dep_airport.name
        response['dest_airport'] = booking.flight.dest_airport.name
        response['dep_datetime'] = booking.flight.dep_datetime.strftime("%Y-%m-%d %H:%M:%S")
        response['arr_datetime'] = booking.flight.arr_datetime.strftime("%Y-%m-%d %H:%M:%S")
        response['duration'] = str(booking.flight.duration)

        return HttpResponse(json.dumps(response))
    else:
        return HttpResponse('Booking number not found', status=503)

def cancel_booking(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    booking = Booking.objects.get(number=body['booking_num'])

    if booking:
        booking.status = 'CANCELLED'
        booking.save()

        response = {}
        response['booking_num'] = booking.number
        response['booking_status'] = booking.status

        return HttpResponse(json.dumps(response))
    else:
        return HttpResponse('Booking number not found', status=503)
