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
import factory

from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from admission.contrib.models import ContinuingEducationAdmission
from admission.tests.factories.roles import CandidateFactory
from base.models.enums import education_group_categories
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.person import PersonFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory


class ContinuingEducationTrainingFactory(EducationGroupYearFactory):
    education_group_type = factory.SubFactory(
        'base.tests.factories.education_group_type.EducationGroupTypeFactory',
        category=education_group_categories.TRAINING,
        name=factory.fuzzy.FuzzyChoice(AnneeInscriptionFormationTranslator.CONTINUING_EDUCATION_TYPES),
    )

    @factory.post_generation
    def create_related_group_version_factory(self, create, extracted, **kwargs):
        EducationGroupVersionFactory(offer=self, root_group__academic_year__year=self.academic_year.year)


class ContinuingEducationAdmissionFactory(factory.DjangoModelFactory):
    class Meta:
        model = ContinuingEducationAdmission

    candidate = factory.SubFactory(PersonFactory)
    training = factory.SubFactory(ContinuingEducationTrainingFactory)

    @factory.post_generation
    def create_candidate_role(self, create, extracted, **kwargs):
        CandidateFactory(person=self.candidate)
