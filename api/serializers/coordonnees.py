from rest_framework import serializers

from base.api.serializers.person_address import PersonAddressSerializer
from base.models.enums.person_address_type import PersonAddressType
from base.models.person_address import PersonAddress


class CoordonneesSerializer(serializers.Serializer):
    contact = PersonAddressSerializer(allow_null=True)
    residential = PersonAddressSerializer(allow_null=True)
    email = serializers.CharField(read_only=True)
    phone_mobile = serializers.CharField(allow_blank=True)

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
        PersonAddress.objects.update_or_create(
            person=person,
            label=PersonAddressType.RESIDENTIAL.name,
            defaults=validated_data["residential"],
        )
        PersonAddress.objects.update_or_create(
            person=person,
            label=PersonAddressType.CONTACT.name,
            defaults=validated_data["contact"],
        )
        person.phone_mobile = validated_data["phone_mobile"]
        person.save()
        self.load_addresses(person)
        return person
