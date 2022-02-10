import datetime
import operator
import random
import uuid

import factory

from admission.tests.factories import WriteTokenFactory
from base import models as mdl
from base.models.person import Person
from base.tests.factories.person import PersonFactory
from reference.tests.factories.country import CountryFactory


class CompletePersonFactory(PersonFactory):
    birth_date = factory.Faker('past_date')
    birth_year = factory.Faker('pyint', min_value=1900, max_value=2005)
    sex = factory.Iterator(mdl.person.Person.SEX_CHOICES, getter=operator.itemgetter(0))
    country_of_citizenship = factory.SubFactory(CountryFactory)
    # id_photo = factory.LazyAttribute(lambda: list([WriteTokenFactory().token])),

    national_number = factory.Faker('pystr_format', string_format='##.##.##-###-##')
    id_card_number = factory.Faker('pystr_format', string_format='##-###-##')
    # id_card = factory.LazyAttribute([uuid.uuid4()]),

    passport_number = factory.Faker('pystr_format', string_format='??-######')
    passport_expiration_date = factory.Faker('future_date')
    # passport = factory.LazyAttribute([uuid.uuid4()]),
