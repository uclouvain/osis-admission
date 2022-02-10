import operator

import factory

from base import models as mdl
from base.models.enums.person_address_type import PersonAddressType

from base.tests.factories.person import PersonFactory
from reference.tests.factories.country import CountryFactory


class PersonAddressFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'base.PersonAddress'

    street = factory.Faker('street_name')
    postal_code = factory.Faker('zipcode')
    city = factory.Faker('city')
    country = factory.SubFactory(CountryFactory)


class CompletePersonFactory(PersonFactory):
    birth_date = factory.Faker('past_date')
    birth_year = factory.Faker('pyint', min_value=1900, max_value=2005)
    sex = factory.Iterator(mdl.person.Person.SEX_CHOICES, getter=operator.itemgetter(0))
    country_of_citizenship = factory.SubFactory(CountryFactory)

    national_number = factory.Faker('pystr_format', string_format='##.##.##-###-##')
    id_card_number = factory.Faker('pystr_format', string_format='##-###-##')

    passport_number = factory.Faker('pystr_format', string_format='??-######')
    passport_expiration_date = factory.Faker('future_date')

    @factory.post_generation
    def create_related_adresses(self, create, extracted, **kwargs):
        PersonAddressFactory(person=self, label=PersonAddressType.RESIDENTIAL.name)
        PersonAddressFactory(person=self, label=PersonAddressType.CONTACT.name)
