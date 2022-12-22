# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
import operator

import factory

from admission.ddd import BE_ISO_CODE
from admission.tests.factories import PdfUploadFactory
from admission.tests.factories.language import LanguageKnowledgeFactory
from admission.tests.factories.secondary_studies import (
    BelgianHighSchoolDiplomaFactory,
)
from base import models as mdl
from base.models.enums.civil_state import CivilState
from base.models.enums.got_diploma import GotDiploma
from base.models.enums.person_address_type import PersonAddressType
from base.tests.factories.academic_year import AcademicYearFactory, get_current_year
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_address import PersonAddressFactory
from osis_profile.tests.factories.curriculum import EducationalExperienceFactory, EducationalExperienceYearFactory
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.language import EnglishLanguageFactory, FrenchLanguageFactory


class CompletePersonFactory(PersonFactory):
    birth_date = factory.Faker('past_date')
    sex = factory.Iterator(mdl.person.Person.SEX_CHOICES, getter=operator.itemgetter(0))
    gender = factory.Iterator(mdl.person.Person.GENDER_CHOICES, getter=operator.itemgetter(0))
    country_of_citizenship = factory.SubFactory(CountryFactory)
    civil_state = CivilState.MARRIED.name
    id_photo = factory.LazyFunction(lambda: [PdfUploadFactory().uuid])
    id_card = factory.LazyFunction(lambda: [PdfUploadFactory().uuid])
    passport = factory.LazyFunction(lambda: [PdfUploadFactory().uuid])
    birth_country = factory.SubFactory(CountryFactory)
    birth_place = factory.Faker('address')
    national_number = factory.Faker('pystr_format', string_format='##.##.##-###-##')
    id_card_number = factory.Faker('pystr_format', string_format='##-###-##')

    passport_number = factory.Faker('pystr_format', string_format='??-######')

    last_registration_year = factory.LazyAttribute(lambda _: AcademicYearFactory(current=True))
    last_registration_id = '01234567'
    graduated_from_high_school = GotDiploma.YES.name
    graduated_from_high_school_year = factory.SubFactory(AcademicYearFactory)

    @factory.post_generation
    def create_related_objects(self, create, extracted, **kwargs):
        # Create addresses
        PersonAddressFactory(
            person=self,
            label=PersonAddressType.RESIDENTIAL.name,
            street='University street',
            street_number='1',
            postal_code='1348',
            city='Louvain-La-Neuve',
            country=CountryFactory(iso_code="BE"),
            postal_box='B1',
            place='P1',
        )
        PersonAddressFactory(
            person=self,
            label=PersonAddressType.CONTACT.name,
            street='University street',
            street_number='2',
            postal_code='1348',
            city='Louvain-La-Neuve',
            country=CountryFactory(iso_code="BE"),
            postal_box='B2',
            place='P2',
        )

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
        experience = EducationalExperienceFactory(
            person=self,
            obtained_diploma=False,
            country=CountryFactory(iso_code="BE"),
            transcript=['transcript.pdf'],
            transcript_translation=['transcript_translation.pdf'],
        )
        EducationalExperienceYearFactory(
            educational_experience=experience,
            academic_year=AcademicYearFactory(year=current_year),
        )
        EducationalExperienceYearFactory(
            educational_experience=experience,
            academic_year=AcademicYearFactory(year=current_year - 1),
        )

        # Create highschool belgian diploma
        BelgianHighSchoolDiplomaFactory(
            person=self,
            academic_graduation_year=AcademicYearFactory(year=current_year - 1),
        )


class CompletePersonForBachelorFactory(CompletePersonFactory):
    @factory.post_generation
    def create_related_objects(self, create, extracted, **kwargs):
        """Target is diplomation_secondaire_belge"""
        current_year = get_current_year()
        academic_year = AcademicYearFactory(year=current_year - 1)
        PersonAddressFactory(
            person=self,
            label=PersonAddressType.RESIDENTIAL.name,
            street='University street',
            street_number='1',
            postal_code='1348',
            city='Louvain-La-Neuve',
            country=CountryFactory(iso_code="BE"),
        )
        self.graduated_from_high_school_year = academic_year
        BelgianHighSchoolDiplomaFactory(
            person=self,
            academic_graduation_year=academic_year,
        )


class CompletePersonForIUFCFactory(CompletePersonFactory):
    @factory.post_generation
    def create_related_objects(self, create, extracted, **kwargs):
        """Target is diplomation_academique_belge"""
        PersonAddressFactory(
            person=self,
            label=PersonAddressType.RESIDENTIAL.name,
            street='University street',
            street_number='1',
            postal_code='1348',
            city='Louvain-La-Neuve',
            country=CountryFactory(iso_code="BE"),
        )
        current_year = get_current_year()
        experience = EducationalExperienceFactory(
            person=self,
            obtained_diploma=True,
            country=CountryFactory(iso_code="BE"),
        )
        EducationalExperienceYearFactory(
            educational_experience=experience,
            academic_year=AcademicYearFactory(year=current_year - 1),
        )


class IncompletePersonForBachelorFactory(CompletePersonFactory):
    @factory.post_generation
    def create_related_objects(self, create, extracted, **kwargs):
        PersonAddressFactory(
            person=self,
            label=PersonAddressType.RESIDENTIAL.name,
            street='University street',
            street_number='1',
            postal_code='1348',
            city='Louvain-La-Neuve',
            country=CountryFactory(iso_code="BE"),
        )


class IncompletePersonForIUFCFactory(CompletePersonFactory):
    @factory.post_generation
    def create_related_objects(self, create, extracted, **kwargs):
        PersonAddressFactory(
            person=self,
            label=PersonAddressType.RESIDENTIAL.name,
            street='University street',
            street_number='1',
            postal_code='1348',
            city='Louvain-La-Neuve',
            country=CountryFactory(iso_code="BE"),
        )
