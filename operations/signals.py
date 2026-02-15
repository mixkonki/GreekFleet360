"""
Django Signals for Operations App
Auto-update vehicle odometer, trigger maintenance alerts, and auto-create CostCenter
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import FuelEntry, ServiceLog, Vehicle


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


@receiver(post_save, sender=Vehicle)
def create_cost_center_for_vehicle(sender, instance, created, **kwargs):
    """
    Automatically create a CostCenter in the finance app when a new Vehicle is created
    
    Logic:
    - Name: {license_plate} - {make}
    - Company: Same as vehicle
    - This allows tracking vehicle-specific costs
    """
    if created:
        from finance.models import CostCenter
        
        # Create CostCenter with vehicle details
        cost_center_name = f"{instance.license_plate} - {instance.make}"
        
        # Check if CostCenter already exists (safety check)
        if not CostCenter.objects.filter(company=instance.company, name=cost_center_name).exists():
            CostCenter.objects.create(
                company=instance.company,
                name=cost_center_name,
                description=f"Αυτόματο Κέντρο Κόστους για όχημα {instance.license_plate} ({instance.make} {instance.model})",
                is_active=True
            )


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
