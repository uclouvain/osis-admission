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
from typing import List, Dict

from dal_select2.views import Select2ListView, Select2QuerySetView
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, F, Value, Case, When
from django.db.models.functions import Coalesce, Concat
from django.utils.functional import cached_property
from django.utils.translation import get_language

from admission.ddd.admission.dtos.formation import BaseFormationDTO
from admission.ddd.admission.shared_kernel.role.commands import RechercherFormationsGereesQuery
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.models.education_group_year import EducationGroupYear
from education_group.contrib.models import EducationGroupRoleModel
from infrastructure.messages_bus import message_bus_instance

__namespace__ = False


__all__ = [
    'ManagedEducationTrainingsAutocomplete',
    'ContinuingManagedEducationTrainingsAutocomplete',
]

from osis_role.contrib.models import EntityRoleModel

from osis_role.contrib.permissions import _get_relevant_roles


class ManagedEducationTrainingsAutocomplete(LoginRequiredMixin, Select2ListView):
    urlpatterns = 'managed-education-trainings'

    def get_list(self) -> List[BaseFormationDTO]:
        return message_bus_instance.invoke(
            RechercherFormationsGereesQuery(
                terme_recherche=self.q,
                annee=self.forwarded.get('annee_academique'),
                matricule_gestionnaire=self.request.user.person.global_id,
            )
        )

    def autocomplete_results(self, results):
        # Do nothing as we already filter in get_list
        return results

    def results(self, results: List[BaseFormationDTO]) -> List[Dict]:
        excluded_training = self.forwarded.get('excluded_training')

        formatted_results = []

        for result in results:
            result_uuid = str(result.uuid)

            if excluded_training and result_uuid == excluded_training:
                continue

            formatted_results.append(
                {
                    'id': result_uuid,
                    'text': f'{result.sigle} - {result.intitule} ({result.lieu_enseignement})',
                }
            )

        return formatted_results


class ContinuingManagedEducationTrainingsAutocomplete(LoginRequiredMixin, Select2QuerySetView):
    urlpatterns = 'continuing-managed-education-trainings'
    model_field_name = 'formatted_title'

    @classmethod
    def get_base_queryset(cls, user, acronyms=None):
        # Filter on the type of training (continuing education)
        qs = EducationGroupYear.objects.filter(
            education_group_type__name__in=AnneeInscriptionFormationTranslator.CONTINUING_EDUCATION_TYPES,
        )

        if acronyms:
            qs = qs.filter(acronym__in=acronyms)

        # Filter on the permissions of the user
        relevant_roles = _get_relevant_roles(user, 'admission.view_continuing_enrolment_applications')
        role_conditions = Q()
        for role in relevant_roles:
            if issubclass(role, EntityRoleModel):
                role_conditions |= Q(
                    management_entity_id__in=role.objects.filter(person=user.person).get_entities_ids()
                )
            elif issubclass(role, EducationGroupRoleModel):
                role_conditions |= Q(
                    education_group_id__in=role.objects.filter(person=user.person).get_education_groups_affected()
                )
        qs = (
            qs.filter(role_conditions)
            .distinct('acronym')
            .annotate(
                formatted_title=Concat(
                    F('acronym'),
                    Value(' - '),
                    F('title')
                    if get_language() == settings.LANGUAGE_CODE_FR
                    else Case(When(title_english='', then=F('title')), default=F('title_english')),
                ),
            )
            .only('acronym')
            .order_by('acronym')
        )
        return qs

    @cached_property
    def queryset(self):
        return self.get_base_queryset(user=self.request.user)

    def get_result_label(self, result):
        return result.formatted_title

    def get_result_value(self, result):
        return result.acronym
