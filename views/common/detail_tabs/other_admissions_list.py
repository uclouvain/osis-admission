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
from django.views.generic import TemplateView

from admission.ddd.admission.commands import ListerToutesDemandesQuery
from admission.ddd.admission.enums.statut import STATUTS_TOUTE_PROPOSITION_SOUMISE_HORS_FRAIS_DOSSIER
from admission.views.common.mixins import AdmissionViewMixin
from infrastructure.messages_bus import message_bus_instance

__all__ = ['OtherAdmissionsListView']


class OtherAdmissionsListView(AdmissionViewMixin, TemplateView):
    permission_required = 'admission.view_enrolment_applications'
    template_name = 'admission/includes/lite_admission_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['autres_demandes'] = [
            demande
            for demande in message_bus_instance.invoke(
                ListerToutesDemandesQuery(
                    annee_academique=self.admission.determined_academic_year.year
                    if self.admission.determined_academic_year
                    else self.admission.training.academic_year.year,
                    matricule_candidat=self.admission.candidate.global_id,
                    etats=list(STATUTS_TOUTE_PROPOSITION_SOUMISE_HORS_FRAIS_DOSSIER),
                )
            )
            if demande.uuid != self.admission_uuid
        ]

        return context
