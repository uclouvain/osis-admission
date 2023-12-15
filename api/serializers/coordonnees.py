# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from rest_framework import serializers

from base.api.serializers.person_address import PersonAddressSerializer
from base.models.enums.person_address_type import PersonAddressType
from base.models.person_address import PersonAddress


class CoordonneesSerializer(serializers.Serializer):
    contact = PersonAddressSerializer(allow_null=True)
    residential = PersonAddressSerializer(allow_null=True)
    private_email = serializers.EmailField(allow_blank=True)
    phone_mobile = serializers.CharField(allow_blank=True, max_length=30)
    emergency_contact_phone = serializers.CharField(allow_blank=True, max_length=30)

    def load_addresses(self, instance):
        instance.contact = PersonAddress.objects.filter(
            person=instance,
            label=PersonAddressType.CONTACT.name,
        ).first()
        instance.residential = PersonAddress.objects.filter(
            person=instance,
            label=PersonAddressType.RESIDENTIAL.name,
        ).first()

    def to_representation(self, instance):
        self.load_addresses(instance)
        return super().to_representation(instance)

    def update(self, instance, validated_data):
        person = instance
        # Always create / update the residential address
        PersonAddress.objects.update_or_create(
            person=person,
            label=PersonAddressType.RESIDENTIAL.name,
            defaults=validated_data["residential"],
        )
        if validated_data.get("contact"):
            # If some data is specified for the contact address, create / update it
            PersonAddress.objects.update_or_create(
                person=person,
                label=PersonAddressType.CONTACT.name,
                defaults=validated_data["contact"],
            )
        else:
            # If no data is specified for the contact address, delete the previous one (if it exists)
            PersonAddress.objects.filter(
                person=instance,
                label=PersonAddressType.CONTACT.name,
            ).delete()

        person_fields = ["phone_mobile", "private_email", "emergency_contact_phone"]
        for field in person_fields:
            setattr(person, field, validated_data[field])
        person.save(update_fields=person_fields)
        self.load_addresses(person)
        return person
