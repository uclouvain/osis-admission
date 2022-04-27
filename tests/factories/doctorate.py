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

import factory
from django.db import connection

from admission.contrib.models import DoctorateAdmission
from admission.contrib.models.doctorate import REFERENCE_SEQ_NAME
from admission.ddd.projet_doctoral.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.projet_doctoral.preparation.domain.model.proposition import Proposition
from admission.tests.factories.roles import CandidateFactory
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class DoctorateFactory(EducationGroupYearFactory):
    academic_year = factory.SubFactory(AcademicYearFactory, current=True)
    education_group_type = factory.SubFactory(EducationGroupTypeFactory, name=TrainingType.PHD.name)


def _generate_reference(obj):
    cursor = connection.cursor()
    cursor.execute("SELECT NEXTVAL('%(sequence)s')" % {'sequence': REFERENCE_SEQ_NAME})
    next_id = cursor.fetchone()[0]
    return "{}-{}".format(
        obj.doctorate.academic_year.year % 100,
        Proposition.valeur_reference_base + next_id,
    )


def generate_token():
    from admission.tests.factories import WriteTokenFactory

    return WriteTokenFactory().token


class DoctorateAdmissionFactory(factory.DjangoModelFactory):
    class Meta:
        model = DoctorateAdmission

    candidate = factory.SubFactory(PersonFactory)
    doctorate = factory.SubFactory(DoctorateFactory)
    thesis_institute = factory.SubFactory(EntityVersionFactory)
    reference = factory.LazyAttribute(_generate_reference)

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
            post_enrolment_status=ChoixStatutDoctorat.ADMITTED.name,
        )

    @factory.post_generation
    def create_candidate_role(self, create, extracted, **kwargs):
        CandidateFactory(person=self.candidate)
