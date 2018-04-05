from django.db import models

class Aircraft(models.Model):
    aircraft_type = models.CharField(max_length=20, default="unknown")
    registration_number = models.CharField(max_length=10, unique=True, default="unknown")
    number_of_seats = models.PositiveIntegerField()

    def __str__(self):
        return self.registration_number

class Airport(models.Model):
    name = models.CharField(max_length=20, unique=True, default="unknown")
    country = models.CharField(max_length=20, default="unknown")
    time_zone = models.CharField(max_length=20, default="unknown")

    def __str__(self):
        return self.name

class Flight(models.Model):
    flight_num = models.CharField(max_length=20, default="unknown")
    dep_airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='departure')
    dest_airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='destination')
    dep_datetime = models.DateTimeField()
    arr_datetime = models.DateTimeField()
    duration = models.DurationField()
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE)
    price = models.FloatField()

    def __str__(self):
        return self.flight_num

class Passenger(models.Model):
    first_name = models.CharField(max_length=20, default="unknown")
    surname = models.CharField(max_length=20, default="unknown")
    email = models.EmailField()
    phone_number = models.CharField(max_length=15, default="unknown")

    def __str__(self):
        return self.email

class Booking(models.Model):
    number = models.CharField(max_length=20, unique=True, default="unknown")
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE)
    number_of_seats = models.PositiveIntegerField()
    passengers = models.ManyToManyField(Passenger)
    STATUS_CHOICES = (('ONHOLD', 'On hold'), ('CONFIRMED', 'Confirmed'), ('CANCELLED', 'Cancelled'), ('TRAVELLED', 'Travelled'))
    status = models.CharField(max_length=15, choices=STATUS_CHOICES)
    expiration_date = models.DateTimeField()

    def __str__(self):
        return self.number

class PaymentProvider(models.Model):
    name = models.CharField(max_length=20, default="unknown")
    website = models.URLField()
    account_number = models.CharField(max_length=30, default="unknown")
    username = models.CharField(max_length=20, default="unknown")
    password = models.CharField(max_length=20, default="unknown")

    def __str__(self):
        return self.name

class Invoice(models.Model):
    payment_reference = models.CharField(max_length=20, unique=True, default="unknown")
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    amount = models.FloatField()
    is_paid = models.BooleanField()
    electronic_stamp = models.CharField(max_length=20, default="unknown")

    def __str__(self):
        return self.payment_reference
