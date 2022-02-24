import operator

import factory

from admission.tests.factories.language import LanguageKnowledgeFactory
from admission.tests.factories.secondary_studies import BelgianHighSchoolDiplomaFactory
from base.tests.factories.academic_year import get_current_year, AcademicYearFactory
from base import models as mdl
from base.models.enums.person_address_type import PersonAddressType

from base.tests.factories.person import PersonFactory
from osis_profile.tests.factories.curriculum import CurriculumYearFactory
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.language import FrenchLanguageFactory, EnglishLanguageFactory


class PersonAddressFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'base.PersonAddress'

    street = factory.Faker('street_name')
    postal_code = factory.Faker('zipcode')
    city = factory.Faker('city')
    country = factory.SubFactory(CountryFactory)


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

    last_registration_year = factory.LazyAttribute(lambda _: AcademicYearFactory(current=True))

    @factory.post_generation
    def create_related_objects(self, create, extracted, **kwargs):
        # Create addresses
        PersonAddressFactory(person=self, label=PersonAddressType.RESIDENTIAL.name)
        PersonAddressFactory(person=self, label=PersonAddressType.CONTACT.name)

        # Create language knowledges
        LanguageKnowledgeFactory(
            person=self,
            language=FrenchLanguageFactory(),
            listening_comprehension='C2',
            speaking_ability='C2',
            writing_ability='C2',
        )
        LanguageKnowledgeFactory(
            person=self,
            language=EnglishLanguageFactory(),
            listening_comprehension='C2',
            speaking_ability='B2',
            writing_ability='C1',
        )

        # Create curriculum years
        current_year = get_current_year()
        CurriculumYearFactory(person=self, academic_year=AcademicYearFactory(year=current_year))
        CurriculumYearFactory(person=self, academic_year=AcademicYearFactory(year=current_year-1))

        # Create highschool belgian diploma
        BelgianHighSchoolDiplomaFactory(person=self, academic_graduation_year=AcademicYearFactory(year=current_year-1))
