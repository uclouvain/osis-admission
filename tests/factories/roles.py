# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

import factory

from admission.auth.roles.ca_member import CommitteeMember
from admission.auth.roles.candidate import Candidate
from admission.auth.roles.central_manager import CentralManager
from admission.auth.roles.doctorate_committee_member import DoctorateCommitteeMember
from admission.auth.roles.program_manager import ProgramManager
from admission.auth.roles.promoter import Promoter
from admission.auth.roles.sic_management import SicManagement, AdmissionSicManagement
from admission.auth.scope import Scope
from osis_role.contrib.tests.factories import EducationGroupRoleModelFactory


class BaseFactory(factory.django.DjangoModelFactory):
    person = factory.SubFactory('base.tests.factories.person.PersonFactory')


class CandidateFactory(BaseFactory):
    class Meta:
        model = Candidate
        django_get_or_create = ('person',)


class PromoterRoleFactory(BaseFactory):
    class Meta:
        model = Promoter
        django_get_or_create = ('person',)


class CaMemberRoleFactory(BaseFactory):
    class Meta:
        model = CommitteeMember
        django_get_or_create = ('person',)


class DoctorateCommitteeMemberRoleFactory(EducationGroupRoleModelFactory):
    class Meta:
        model = DoctorateCommitteeMember
        django_get_or_create = ('person',)

    education_group = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if not kwargs:
            kwargs = {}

        if not kwargs.get('education_group'):
            from admission.tests.factories.doctorate import DoctorateFactory

            kwargs['education_group'] = DoctorateFactory().education_group

        return super()._create(model_class, *args, **kwargs)


class CentralManagerRoleFactory(BaseFactory):
    class Meta:
        model = CentralManager

    entity = factory.SubFactory(
        'base.tests.factories.entity.EntityWithVersionFactory',
        organization=None,
    )
    scopes = [Scope.GENERAL.name, Scope.DOCTORAT.name, Scope.IUFC.name]
    with_child = True


class SicManagementRoleFactory(BaseFactory):
    class Meta:
        model = AdmissionSicManagement

    entity = factory.SubFactory(
        'base.tests.factories.entity.EntityWithVersionFactory',
        organization=None,
    )
    with_child = True


class ProgramManagerRoleFactory(EducationGroupRoleModelFactory):
    class Meta:
        model = ProgramManager
