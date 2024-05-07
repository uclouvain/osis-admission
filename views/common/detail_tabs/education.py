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

from django.utils.functional import cached_property
from django.views.generic import TemplateView

from admission.ddd.admission.commands import RecupererEtudesSecondairesQuery
from admission.ddd.admission.dtos import EtudesSecondairesAdmissionDTO
from admission.ddd.admission.enums import Onglets
from admission.utils import get_experience_urls
from admission.views.common.mixins import LoadDossierViewMixin
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    'AdmissionEducationDetailView',
]


class AdmissionEducationDetailView(LoadDossierViewMixin, TemplateView):
    urlpatterns = 'education'
    template_name = 'admission/details/education.html'
    specific_questions_tab = Onglets.ETUDES_SECONDAIRES
    permission_required = 'admission.view_admission_secondary_studies'

    @cached_property
    def etudes_secondaires(self) -> EtudesSecondairesAdmissionDTO:
        return message_bus_instance.invoke(
            RecupererEtudesSecondairesQuery(matricule_candidat=self.proposition.matricule_candidat)
        )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        etudes_secondaires = self.etudes_secondaires
        context_data['etudes_secondaires'] = etudes_secondaires

        experience_urls = get_experience_urls(
            user=self.request.user,
            admission=self.admission,
            experience=etudes_secondaires,
            candidate_noma=self.proposition.noma_candidat,
        )

        context_data['edit_url'] = experience_urls['edit_url']
        context_data['edit_new_link_tab'] = experience_urls['edit_new_link_tab']

        if etudes_secondaires.diplome_etranger:
            context_data['need_translations'] = etudes_secondaires.a_besoin_traductions
            context_data['ue_or_assimilated'] = (
                etudes_secondaires.diplome_etranger.pays_membre_ue
                or self.proposition.formation.est_formation_medecine_ou_dentisterie
            )

        return context_data
