from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Aircraft)
admin.site.register(Airport)
admin.site.register(Flight)
admin.site.register(Passenger)
admin.site.register(Booking)
admin.site.register(PaymentProvider)
admin.site.register(Invoice)
