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
from osis_common.utils.htmx import HtmxMixin

__all__ = [
    "SearchPreviousExperienceView",
]


class SearchPreviousExperienceView(HtmxMixin, TemplateView):
    name = "search_previous_experience"

    template_name = "admission/previous_experience.html"
    htmx_template_name = "admission/previous_experience.html"
    urlpatterns = {'previous-experience': 'previous-experience/<uuid:admission_uuid>'}

    @property
    def experience(self):
        from infrastructure.messages_bus import message_bus_instance
        return message_bus_instance.invoke(
            RechercherParcoursAnterieurQuery(
                global_id=self.request.GET.get('matricule'),
                uuid_proposition=self.request.GET.get('admission_uuid')
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['professional_experience'] = self.experience.experiences_academiques
        context['educational_experience'] = self.experience.experiences_non_academiques
        context['high_school_graduation_year'] = self.experience.annee_diplome_etudes_secondaires
        return context
