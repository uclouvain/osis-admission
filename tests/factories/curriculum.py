# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime
import random
import uuid

import factory
from dateutil.relativedelta import relativedelta

from admission.models.base import (
    AdmissionEducationalValuatedExperiences,
    AdmissionProfessionalValuatedExperiences,
)
from base.tests.factories.academic_year import AcademicYearFactory
from osis_profile.models import EducationalExperienceYear, ProfessionalExperience, EducationalExperience
from osis_profile.models.enums.curriculum import TranscriptType, EvaluationSystem, Result, Grade, ActivityType
from reference.tests.factories.language import LanguageFactory


class EducationalExperienceYearFactory(factory.django.DjangoModelFactory):
    registered_credit_number = 10
    acquired_credit_number = 10
    result = Result.WAITING_RESULT.name
    transcript = factory.LazyFunction(lambda: [uuid.uuid4()])
    transcript_translation = factory.LazyFunction(lambda: [uuid.uuid4()])
    academic_year = factory.SubFactory(AcademicYearFactory, current=True)
    fwb_registered_credit_number = 20
    fwb_acquired_credit_number = 15

    class Meta:
        model = EducationalExperienceYear


# TODO: keep only one factory (this one or osis_profile.tests.factories.curriculum.EducationalExperienceFactory)
# Same for other factories in this file !!!
class EducationalExperienceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EducationalExperience

    country = factory.SubFactory('reference.tests.factories.country.CountryFactory')
    transcript_type = TranscriptType.ONE_FOR_ALL_YEARS.name
    transcript = factory.LazyFunction(lambda: [uuid.uuid4()])
    transcript_translation = factory.LazyFunction(lambda: [uuid.uuid4()])
    rank_in_diploma = '10'
    expected_graduation_date = factory.Faker('date')
    dissertation_title = 'Title'
    dissertation_score = '10'
    dissertation_summary = factory.LazyFunction(lambda: [uuid.uuid4()])
    graduate_degree = factory.LazyFunction(lambda: [uuid.uuid4()])
    graduate_degree_translation = factory.LazyFunction(lambda: [uuid.uuid4()])
    linguistic_regime = factory.SubFactory(LanguageFactory)
    obtained_diploma = factory.Faker('boolean')
    evaluation_type = EvaluationSystem.NO_CREDIT_SYSTEM.name
    obtained_grade = Grade.GREAT_DISTINCTION.name
    education_name = 'Computer science'
    institute_name = 'Institute'


class ProfessionalExperienceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProfessionalExperience

    start_date = factory.LazyAttribute(
        lambda experience: datetime.date(random.randint(2000, 2022), random.randint(1, 12), 1)
    )
    end_date = factory.LazyAttribute(
        lambda experience: experience.start_date + relativedelta(months=2) - relativedelta(days=1)
    )
    type = ActivityType.WORK.name


class AdmissionEducationalValuatedExperiencesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AdmissionEducationalValuatedExperiences


class AdmissionProfessionalValuatedExperiencesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AdmissionProfessionalValuatedExperiences
