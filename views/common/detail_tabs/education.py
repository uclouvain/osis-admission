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

from admission.ddd.admission.domain.model.formation import est_formation_medecine_ou_dentisterie
from admission.ddd.admission.enums import Onglets
from admission.infrastructure.admission.domain.service.profil_candidat import ProfilCandidatTranslator
from admission.views.common.mixins import LoadDossierViewMixin
from osis_profile import REGIMES_LINGUISTIQUES_SANS_TRADUCTION

__all__ = [
    'AdmissionEducationDetailView',
]


class AdmissionEducationDetailView(LoadDossierViewMixin, TemplateView):
    urlpatterns = 'education'
    template_name = 'admission/details/education.html'
    specific_questions_tab = Onglets.ETUDES_SECONDAIRES
    permission_required = 'admission.view_admission_secondary_studies'

    @cached_property
    def is_med_dent_training(self):
        return est_formation_medecine_ou_dentisterie(self.proposition.formation.code_domaine)

    @cached_property
    def etudes_secondaires(self):
        return ProfilCandidatTranslator.get_etudes_secondaires(self.proposition.matricule_candidat)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        etudes_secondaires = self.etudes_secondaires
        context_data['etudes_secondaires'] = etudes_secondaires

        if etudes_secondaires.diplome_etranger:
            context_data['need_translations'] = (
                etudes_secondaires.diplome_etranger.regime_linguistique not in REGIMES_LINGUISTIQUES_SANS_TRADUCTION
            )
            context_data['ue_or_assimilated'] = (
                etudes_secondaires.diplome_etranger.pays_membre_ue or self.is_med_dent_training
            )

        return context_data
