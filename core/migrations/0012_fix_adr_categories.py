# Generated manually to fix ADR categories
from django.db import migrations


def update_adr_categories(apps, schema_editor):
    """Update ADR categories to correct Π1-Π8 definitions"""
    AdrCategory = apps.get_model('core', 'AdrCategory')
    
    # Delete existing incorrect categories
    AdrCategory.objects.all().delete()
    
    # Create correct ADR categories (Π1-Π8)
    categories = [
        {'code': 'Π1', 'label_el': 'Βασική', 'label_en': 'Basic', 'display_order': 1},
        {'code': 'Π2', 'label_el': 'Βασική + Κλάση 1', 'label_en': 'Basic + Class 1', 'display_order': 2},
        {'code': 'Π3', 'label_el': 'Βασική + Κλάση 7', 'label_en': 'Basic + Class 7', 'display_order': 3},
        {'code': 'Π4', 'label_el': 'Βασική + Κλάση 1 + Κλάση 7', 'label_en': 'Basic + Class 1 + Class 7', 'display_order': 4},
        {'code': 'Π5', 'label_el': 'Βασική + Βυτία', 'label_en': 'Basic + Tanks', 'display_order': 5},
        {'code': 'Π6', 'label_el': 'Βασική + Βυτία + Κλάση 1', 'label_en': 'Basic + Tanks + Class 1', 'display_order': 6},
        {'code': 'Π7', 'label_el': 'Βασική + Βυτία + Κλάση 7', 'label_en': 'Basic + Tanks + Class 7', 'display_order': 7},
        {'code': 'Π8', 'label_el': 'Βασική + Βυτία + Κλάση 1 + Κλάση 7', 'label_en': 'Basic + Tanks + Class 1 + Class 7', 'display_order': 8},
    ]
    
    for cat in categories:
        AdrCategory.objects.create(**cat)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_adrcategory_drivinglicensecategory_drivercompliance'),
    ]

    operations = [
        migrations.RunPython(update_adr_categories, reverse_code=migrations.RunPython.noop),
    ]
