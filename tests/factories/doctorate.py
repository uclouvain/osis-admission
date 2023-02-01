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

from admission.contrib.models import DoctorateAdmission
from admission.ddd.parcours_doctoral.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutProposition,
    ChoixTypeFinancement,
)
from admission.tests.factories.utils import generate_proposition_reference
from admission.tests.factories.accounting import AccountingFactory
from admission.tests.factories.roles import CandidateFactory
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.student import StudentFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory


class DoctorateFactory(EducationGroupYearFactory):
    academic_year = factory.SubFactory(AcademicYearFactory, current=True)
    education_group_type = factory.SubFactory(EducationGroupTypeFactory, name=TrainingType.PHD.name)
    primary_language = None

    @factory.post_generation
    def create_related_group_version_factory(self, create, extracted, **kwargs):
        EducationGroupVersionFactory(offer=self, root_group__academic_year__year=self.academic_year.year)


def generate_token():
    from admission.tests.factories import WriteTokenFactory

    return WriteTokenFactory().token


class DoctorateAdmissionFactory(factory.DjangoModelFactory):
    class Meta:
        model = DoctorateAdmission

    candidate = factory.SubFactory(PersonFactory)
    training = factory.SubFactory(
        DoctorateFactory,
        enrollment_campus__name='Mons',
    )
    reference = factory.LazyAttribute(generate_proposition_reference)

    cotutelle = False
    financing_type = ChoixTypeFinancement.SELF_FUNDING.name
    planned_duration = 10
    dedicated_time = 10
    project_title = 'Test'
    project_abstract = 'Test'
    project_document = factory.LazyFunction(lambda: [uuid.uuid4()])
    program_proposition = factory.LazyFunction(lambda: [uuid.uuid4()])

    curriculum = factory.LazyFunction(lambda: [uuid.uuid4()])

    class Params:
        with_cotutelle = factory.Trait(
            cotutelle=True,
            cotutelle_motivation="Very motivated",
            cotutelle_institution_fwb=False,
            cotutelle_institution="Somewhere",
            cotutelle_opening_request=factory.LazyFunction(generate_token),  # This is to overcome circular import
            cotutelle_convention=factory.LazyFunction(generate_token),
        )
        admitted = factory.Trait(
            status=ChoixStatutProposition.ENROLLED.name,
            post_enrolment_status=ChoixStatutDoctorat.ADMITTED.name,
            submitted_profile={
                "coordinates": {
                    "city": "Louvain-La-Neuves",
                    "email": "user@uclouvain.be",
                    "place": "",
                    "street": "Place de l'Université",
                    "country": "BE",
                    "postal_box": "",
                    "postal_code": "1348",
                    "street_number": "2",
                },
                "identification": {
                    "gender": "M",
                    "last_name": "Doe",
                    "first_name": "John",
                    "country_of_citizenship": "BE",
                },
            },
        )
        with_thesis_institute = factory.Trait(
            thesis_institute=factory.SubFactory(EntityVersionFactory),
        )
        with_answers_to_specific_questions = factory.Trait(
            specific_question_answers={
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
                'fe254203-17c7-47d6-95e4-3c5c532da552': ['ae254203-17c7-47d6-95e4-3c5c532da550'],
            },
        )

    @factory.post_generation
    def create_candidate_role(self, create, extracted, **kwargs):
        CandidateFactory(person=self.candidate)

    @factory.post_generation
    def create_student_if_admitted(self, create, extracted, **kwargs):
        if self.post_enrolment_status != ChoixStatutDoctorat.ADMISSION_IN_PROGRESS.name:
            StudentFactory(person=self.candidate)

    @factory.post_generation
    def create_accounting(self, create, extracted, **kwargs):
        AccountingFactory(admission_id=self.pk)
