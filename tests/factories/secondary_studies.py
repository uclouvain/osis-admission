# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

import factory

from admission.tests.factories import PdfUploadFactory
from base.tests.factories.academic_year import AcademicYearFactory
from osis_profile.models import BelgianHighSchoolDiploma, ForeignHighSchoolDiploma, HighSchoolDiplomaAlternative
from osis_profile.models.enums.education import BelgianCommunitiesOfEducation, EducationalType
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.language import LanguageFactory


class HighSchoolDiplomaFactory(factory.django.DjangoModelFactory):
    person = factory.SubFactory('base.tests.factories.person.PersonFactory')
    academic_graduation_year = factory.SubFactory(AcademicYearFactory, current=True)


class BelgianHighSchoolDiplomaFactory(HighSchoolDiplomaFactory):
    high_school_diploma = factory.LazyAttribute(lambda _: [PdfUploadFactory().uuid])
    community = BelgianCommunitiesOfEducation.GERMAN_SPEAKING.name
    educational_type = EducationalType.PROFESSIONAL_EDUCATION.name
    other_institute_name = 'HS UCL'
    other_institute_address = 'Louvain-la-Neuve'

    class Meta:
        model = BelgianHighSchoolDiploma


class ForeignHighSchoolDiplomaFactory(HighSchoolDiplomaFactory):
    country = factory.SubFactory(CountryFactory)
    linguistic_regime = factory.SubFactory(LanguageFactory)

    class Meta:
        model = ForeignHighSchoolDiploma


class HighSchoolDiplomaAlternativeFactory(factory.django.DjangoModelFactory):
    person = factory.SubFactory('base.tests.factories.person.PersonFactory')

    class Meta:
        model = HighSchoolDiplomaAlternative
