import requests
import json
import getpass
import sys

DIR_URL = 'http://directory.pythonanywhere.com/'
BASE_URL = ''
# BASE_URL = ''

airline_list = []
payment_list = []

def find_flight():
    print('\nFind a Flight\n')
    dep_date = input('Departure date (YYY-MM-DD): ')
    dep_airport = input('Departure airport: ')
    dest_airport = input('Destination airport: ')
    is_flex = input('Is the date flexible? (y/n): ')
    num_passengers = input('Number of passengers: ')

    if not num_passengers.isdigit():
        print('\nInvalid number of passengers')
        return

    if is_flex == 'y':
        is_flex = True
    else:
        is_flex = False

    find_params = {
        'dep_date': dep_date,
        'dep_airport': dep_airport,
        'dest_airport': dest_airport,
        'is_flex': is_flex,
        'num_passengers': int(num_passengers)
    }

    for airline in airline_list:
        print('\n' + airline['company_code'], airline['company_name'])
        r = requests.get(airline['url'] + '/api/findflight/', headers={'Content-Type': 'application/json'}, data=json.dumps(find_params))

        if r.status_code == 200:
            response = json.loads(r.text)

            print(len(response['flights']), 'FLIGHTS FOUND\n')

            for f in response['flights']:
                print('**************************************')
                print('Flight ID:', f['flight_id'])
                print('Flight Number:', f['flight_num'])
                print('Departure Airport:', f['dep_airport'])
                print('Destination Airport:', f['dest_airport'])
                print('Departure Date and Time:', f['dep_datetime'])
                print('Arrival Date and Time:', f['arr_datetime'])
                print('Duration:', f['duration'])
                print('Price: £', f['price'])

        elif r.status_code == 503:
            print(r.text, '\n')

        else:
            print("ERROR")

def pick_airline():
    global BASE_URL
    chosen_airline = input('Airline code: ')
    for airline in airline_list:
        if airline['company_code'] == chosen_airline:
            BASE_URL = airline['url']

def book_flight():
    print('\nBook a Flight\n')

    pick_airline()

    flight_id = input('Flight ID: ')
    num_passengers = input('Number of passengers: ')
    passengerList = []

    for i in range(int(num_passengers)):
        print('\nPassenger ' + str(i+1) + ':')
        passenger = {}
        passenger['first_name'] = input('First name: ')
        passenger['surname'] = input('Surname: ')
        passenger['email'] = input('Email Address: ')
        passenger['phone'] = input('Phone Number: ')

        passengerList.append(passenger)

    book_params = {}
    book_params['flight_id'] = flight_id
    book_params['passengers'] = passengerList

    r = requests.post(BASE_URL + '/api/bookflight/', data=json.dumps(book_params))

    if r.status_code == 201:
        response = json.loads(r.text)

        print('\nBooking Created\n')
        print('Booking Number: ', response['booking_num'])
        print('Booking Status: ', response['booking_status'])
        print('Total Price: £', response['tot_price'])
    elif r.status_code == 503:
        print('\n' + r.text)
    else:
        print('ERROR')

def payment_methods():
    pick_airline()

    r = requests.get(BASE_URL + '/api/paymentmethods/')

    if r.status_code == 200:
        response = json.loads(r.text)

        print('\nPayment Providers\n')

        for pp in response['pay_providers']:
            print('Provider ID:', pp['pay_provider_id'])
            print('Provider name:', pp['pay_provider_name'])
            print('**************************************')
    elif r.status_code == 503:
        print('\n' + r.text)
    else:
        print('ERROR')

def pay_for_booking():
    print('\nPay for Booking\n')

    pick_airline()

    pay_params = {}
    pay_params['pay_provider_id'] = input('Payment provider ID: ')
    pay_params['booking_num'] = input('Booking number: ')

    r = requests.post(BASE_URL + '/api/payforbooking/', data=json.dumps(pay_params))

    if r.status_code == 201:
        response = json.loads(r.text)

        print('\nPayment provider ID:', response['pay_provider_id'])
        print('Invoice reference:', response['invoice_id'])
        print('Booking number', response['booking_num'])
        print('Payment provider\'s website:', response['url'])

        print('\nPay Invoice\n')

        username = input('Username: ')
        password = getpass.getpass('Password: ')

        session = requests.session()

        login = session.post(response['url'] + '/api/login/', data={'username': username, 'password': password})

        if login.status_code == 200:
            pay_params = {}
            pay_params['payprovider_ref_num'] = input('\nInvoice reference: ')
            pay_params['client_ref_num'] = input('Booking number: ')
            pay_params['amount'] = input('Amount: ')

            r = session.post(response['url'] + '/api/payinvoice/',
                             headers={'Content-Type': 'application/json'},
                             data=json.dumps(pay_params))

            if r.status_code == 201:
                response = json.loads(r.text)

                print('\nElectronic stamp:', response['stamp_code'])
            elif r.status_code == 503:
                print(r.text)
            else:
                print('ERROR')
        elif login.status_code == 503:
            print(login.text)
        else:
            print('ERROR')
    elif r.status_code == 503:
        print(r.text)
    else:
        print('ERROR')

def finalize_booking():
    print('\nFinalize Booking\n')

    pick_airline()

    finalize_params = {}
    finalize_params['booking_num'] = input('Booking number: ')
    finalize_params['pay_provider_id'] = input('Payment provider ID: ')
    finalize_params['stamp'] = input('Electronic stamp: ')

    r = requests.post(BASE_URL + '/api/finalizebooking/', data=json.dumps(finalize_params))

    if r.status_code == 201:
        response = json.loads(r.text)

        print('\nBooking number:', response['booking_num'])
        print('Booking status:', response['booking_status'])
    elif r.status_code == 503:
        print(r.text)
    else:
        print('ERROR')

def booking_status():
    print('\nBooking Status\n')

    pick_airline()

    booking_params = {}
    booking_params['booking_num'] = input('Booking number: ')

    r = requests.get(BASE_URL + '/api/bookingstatus/', data=json.dumps(booking_params))

    if r.status_code == 200:
        response = json.loads(r.text)

        print('\nBooking number:', response['booking_num'])
        print('Booking status:', response['booking_status'])
        print('Flight number:', response['flight_num'])
        print('Deoarture Airport:', response['dep_airport'])
        print('Destination airport:', response['dest_airport'])
        print('Departure date and time:', response['dep_datetime'])
        print('Arrival date and time:', response['arr_datetime'])
        print('Flight duration:', response['duration'])
    elif r.status_code == 503:
        print(r.text)
    else:
        print('ERROR')

def cancel_booking():
    print('\nCancel Booking\n')

    pick_airline()

    booking_params = {}
    booking_params['booking_num'] = input('Booking number: ')

    r = requests.post(BASE_URL + '/api/cancelbooking/', data=json.dumps(booking_params))

    if r.status_code == 201:
        response = json.loads(r.text)

        print('\nBooking number:', response['booking_num'])
        print('Booking status:', response['booking_status'])
    elif r.status_code == 503:
        print(r.text)
    else:
        print(r.text)
        print('ERROR')

def list_payment_providers():
    directory = {'company_type': 'payment'}
    r = requests.get(DIR_URL + '/api/list/', headers={'Content-Type': 'application/json'}, data=json.dumps(directory))
    directory = json.loads(r.text)

    for company in directory['company_list']:
        print('\n')
        print(company['company_code'], company['company_name'])
        print(company['url'])

def pick_payment():
    global BASE_URL

    payment_code = input('\nPayment provider ID: ')

    for company in payment_list:
        if company['company_code'] == payment_code:
            BASE_URL = company['url']


def register():
    pick_payment()

    register_params = {
        'first_name': input('First name: '),
        'surname': input('Surname: '),
        'email': input('Email: '),
        'phone': input('Phone Number: '),
        'username': input('Username: '),
        'password': getpass.getpass('Password: '),
        'customer_type': input('Customer type: '),
    }

    headers = {
        'Content-Type': 'application/json'
    }

    r = requests.post(BASE_URL + '/api/register/', data=json.dumps(register_params), headers=headers)

    print(r.text)

ses = requests.Session()

def login():
    pick_payment()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    r = ses.post(BASE_URL + '/api/login/', data={'username': input('\nUsername: '), 'password': getpass.getpass('Password: ')}, headers=headers)

    print(r.text)

def create_account():
    pick_payment()

    r = ses.post(BASE_URL + '/api/newaccount/')

    print('\n' + r.text)

def balance():
    pick_payment()

    r = ses.get(BASE_URL + '/api/balance/')

    if r.status_code == 200:
        response = json.loads(r.text)
        for account in response['accounts']:
            print('\nAccount Number: ', account['account_num'])
            print('Balance: ', account['balance'])
    elif r.status_code == 503:
        print(r.text)
    else:
        print('ERROR')

def deposit():
    pick_payment()

    deposit_params = {
        'amount': input('\nAmount: '),
        'account_num': input('Account number: ')
    }

    headers = {
        'Content-Type': 'application/json'
    }

    r = ses.post(BASE_URL + '/api/deposit/', data=json.dumps(deposit_params), headers=headers)

    if r.status_code == 201:
        response = json.loads(r.text)
        print('\nAccount Number: ', response['account_num'])
        print('Balance: ', response['balance'])
    elif r.status_code == 503:
        print(r.text)
    else:
        print('ERROR')

def logout():
    r = ses.post(BASE_URL + '/api/logout/')

    print('\n' + r.text)

def populate_list(company_type):
    directory = {'company_type': company_type}
    r = requests.get(DIR_URL + 'api/list/', headers={'Content-Type': 'application/json'}, data=json.dumps(directory))
    directory = json.loads(r.text)

    if company_type == 'airline':
        for airline in directory['company_list']:
            airline_list.append(airline)
    elif company_type == 'payment':
        for payment in directory['company_list']:
            payment_list.append(payment)

def main():
    while True:
        airline_or_payment = input("[A]irline - [P]ayment - [Q]uit: ")

        if airline_or_payment == 'A' or airline_or_payment == 'a':
            populate_list('airline')
            while True:
                print('\n[1] Find a flight')
                print('[2] Book a flight')
                print('[3] Request payment methods')
                print('[4] Pay for booking')
                print('[5] Finalize booking')
                print('[6] Request booking status')
                print('[7] Cancel booking')
                print('[Other] Exit')
                choice = input('\nEnter an option: ')

                if choice == '1':
                    find_flight()
                elif choice == '2':
                    book_flight()
                elif choice == '3':
                    payment_methods()
                elif choice == '4':
                    pay_for_booking()
                elif choice == '5':
                    finalize_booking()
                elif choice == '6':
                    booking_status()
                elif choice == '7':
                    cancel_booking()
                elif choice == '8':
                    get_airlines()
                else:
                    break

        elif airline_or_payment == 'P' or airline_or_payment == 'p':
            populate_list('payment')
            while True:
                print('\n[1] List payment providers')
                print('[2] Register')
                print('[3] Login')
                print('[4] Create account')
                print('[5] Balance')
                print('[6] Deposit')
                print('[7] Logout')
                choice = input('\nEnter an option: ')

                if choice == '1':
                    list_payment_providers()
                elif choice == '2':
                    register()
                elif choice == '3':
                    login()
                elif choice == '4':
                    create_account()
                elif choice == '5':
                    balance()
                elif choice == '6':
                    deposit()
                elif choice == '7':
                    logout()
                    break
                else:
                    break
        else:
            print('Byeeee')
            break

if __name__ == '__main__':
    main()
