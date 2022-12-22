# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid

import factory

from osis_profile.models import EducationalExperienceYear, ProfessionalExperience, EducationalExperience
from osis_profile.models.enums.curriculum import TranscriptType
from reference.tests.factories.language import LanguageFactory


class EducationalExperienceYearFactory(factory.DjangoModelFactory):
    class Meta:
        model = EducationalExperienceYear


class EducationalExperienceFactory(factory.DjangoModelFactory):
    class Meta:
        model = EducationalExperience

    country = factory.SubFactory('reference.tests.factories.country.CountryFactory')
    transcript_type = TranscriptType.ONE_FOR_ALL_YEARS.name
    transcript = factory.LazyFunction(lambda: [uuid.uuid4()])
    rank_in_diploma = '10'
    expected_graduation_date = factory.Faker('date')
    dissertation_title = 'Title'
    dissertation_score = '10'
    dissertation_summary = factory.LazyFunction(lambda: [uuid.uuid4()])
    graduate_degree = factory.LazyFunction(lambda: [uuid.uuid4()])
    linguistic_regime = factory.SubFactory(LanguageFactory)
    obtained_diploma = factory.Faker('boolean')


class ProfessionalExperienceFactory(factory.DjangoModelFactory):
    class Meta:
        model = ProfessionalExperience
