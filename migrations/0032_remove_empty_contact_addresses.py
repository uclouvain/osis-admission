# Generated by Django 2.2.24 on 2022-03-09 15:25

from django.db import migrations
from django.db.models import Q

from base.models.enums.person_address_type import PersonAddressType


def remove_empty_contact_addresses(apps, _):
    model = apps.get_model('base', 'PersonAddress')

    model.objects.filter(
        Q(location='') | Q(location__isnull=True),
        Q(postal_code='') | Q(postal_code__isnull=True),
        Q(city='') | Q(city__isnull=True),
        label=PersonAddressType.CONTACT.name,
        country__isnull=True,
        street='',
        street_number='',
        postal_box='',
        place='',
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0031_prefer_datetime_over_date'),
        ('base', '0622_person_curriculum'),
    ]

    operations = [
        migrations.RunPython(remove_empty_contact_addresses, migrations.RunPython.noop),
    ]
