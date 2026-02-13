"""
Django Signals for Operations App
Auto-update vehicle odometer and trigger maintenance alerts
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import FuelEntry, ServiceLog


@receiver(post_save, sender=FuelEntry)
def update_odometer_from_fuel_entry(sender, instance, created, **kwargs):
    """
    Automatically update vehicle's current_odometer when a new FuelEntry is saved
    Only updates if the new reading is greater than the current odometer
    """
    if created or instance.odometer_reading > instance.vehicle.current_odometer:
        if instance.odometer_reading > instance.vehicle.current_odometer:
            instance.vehicle.current_odometer = instance.odometer_reading
            instance.vehicle.save(update_fields=['current_odometer'])
            
            # TODO: Trigger maintenance alert check
            # check_upcoming_maintenance(instance.vehicle)


@receiver(post_save, sender=ServiceLog)
def update_odometer_from_service_log(sender, instance, created, **kwargs):
    """
    Automatically update vehicle's current_odometer when a new ServiceLog is saved
    Only updates if the new reading is greater than the current odometer
    """
    if created or instance.odometer_reading > instance.vehicle.current_odometer:
        if instance.odometer_reading > instance.vehicle.current_odometer:
            instance.vehicle.current_odometer = instance.odometer_reading
            instance.vehicle.save(update_fields=['current_odometer'])
            
            # TODO: Trigger maintenance alert check
            # check_upcoming_maintenance(instance.vehicle)


# Placeholder for future maintenance alert system
def check_upcoming_maintenance(vehicle):
    """
    Future implementation: Check if vehicle is due for maintenance
    based on current odometer reading and service history
    
    Logic:
    - Check last service date and mileage
    - Calculate next service due (e.g., every 10,000 km or 6 months)
    - Send alert if due within 14 days or 500 km
    """
    pass
