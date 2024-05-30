# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.views.generic import TemplateView
from admission.ddd.admission.commands import RechercherParcoursAnterieurQuery
from admission.templatetags.admission import format_matricule
from base.models.person import Person
from base.utils.htmx import HtmxPermissionRequiredMixin
from osis_common.utils.htmx import HtmxMixin

__all__ = [
    "SearchPreviousExperienceView",
]


class SearchPreviousExperienceView(HtmxMixin, HtmxPermissionRequiredMixin, TemplateView):
    name = "search_previous_experience"

    template_name = "admission/previous_experience.html"
    htmx_template_name = "admission/previous_experience.html"
    urlpatterns = {'previous-experience': 'previous-experience/<uuid:admission_uuid>'}
    permission_required = "admission.merge_candidate_with_known_person"

    @property
    def candidate(self):
        return Person.objects.values(
            'first_name', 'middle_name', 'last_name', 'email', 'gender', 'birth_date', 'civil_state',
            'birth_place', 'country_of_citizenship__name', 'national_number', 'id_card_number',
            'passport_number', 'last_registration_id', 'global_id',
        ).get(baseadmissions__uuid=self.kwargs['admission_uuid'])

    @property
    def provided_experience(self):
        from infrastructure.messages_bus import message_bus_instance
        return message_bus_instance.invoke(
            RechercherParcoursAnterieurQuery(
                global_id=self.candidate['global_id'],
                uuid_proposition=self.request.GET.get('admission_uuid')
            )
        )

    @property
    def known_experience(self):
        from infrastructure.messages_bus import message_bus_instance
        return message_bus_instance.invoke(
            RechercherParcoursAnterieurQuery(
                global_id=format_matricule(self.request.GET.get('matricule')),
                uuid_proposition=self.kwargs['admission_uuid'],
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['professional_experience'] = sorted(
            self.provided_experience.experiences_non_academiques, key=lambda exp: (exp.date_debut, exp.date_fin), reverse=True
        )
        context['educational_experience'] = sorted(
            self.provided_experience.experiences_academiques, key=lambda exp: exp.titre_formate, reverse=True
        )
        context['provided_high_school_graduation_year'] = self.provided_experience.annee_diplome_etudes_secondaires
        if self.known_experience:
            context['professional_experience'] = self._merge_professional_experiences()
            context['educational_experience'] = self._merge_academic_experiences()
            context['mergeable_experiences_uuids'] = self._get_mergeable_experiences_uuids()
            context['known_high_school_graduation_year'] = self.known_experience.annee_diplome_etudes_secondaires
        return context

    def _merge_professional_experiences(self):
        return sorted(
            self.provided_experience.experiences_non_academiques + self.known_experience.experiences_non_academiques,
            key=lambda exp: (exp.date_debut, exp.date_fin), reverse=True
        )

    def _merge_academic_experiences(self):
        return sorted(
            self.provided_experience.experiences_academiques + self.known_experience.experiences_academiques,
            key=lambda exp: exp.titre_formate, reverse=True
        )

    def _get_mergeable_experiences_uuids(self):
        return [
            exp.uuid for exp in
            (self.known_experience.experiences_non_academiques + self.known_experience.experiences_academiques)
        ]
