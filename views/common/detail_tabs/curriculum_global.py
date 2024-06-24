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

from admission.ddd.admission.commands import RechercherParcoursAnterieurQuery
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import CurriculumAdmissionDTO
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.enums.valorisation_experience import ExperiencesCVRecuperees
from admission.exports.admission_recap.constants import TRAINING_TYPES_WITH_EQUIVALENCE
from admission.views.common.mixins import LoadDossierViewMixin
from base.models.enums.education_group_types import TrainingType
from infrastructure.messages_bus import message_bus_instance


__namespace__ = ''

__all__ = [
    'CurriculumGlobalDetailsView',
]


class CurriculumGlobalCommonViewMixin(LoadDossierViewMixin):
    specific_questions_tab = Onglets.CURRICULUM

    @cached_property
    def curriculum(self) -> CurriculumAdmissionDTO:
        return message_bus_instance.invoke(
            RechercherParcoursAnterieurQuery(
                global_id=self.proposition.matricule_candidat,
                uuid_proposition=self.proposition.uuid,
                experiences_cv_recuperees=ExperiencesCVRecuperees.SEULEMENT_VALORISEES,
            )
        )

    @cached_property
    def display_curriculum(self):
        return (
            self.proposition.inscription_au_role_obligatoire is True
            if self.is_continuing
            else self.proposition.formation.type != TrainingType.BACHELOR.name
        )

    @cached_property
    def display_equivalence(self):
        return self.proposition.formation.type in TRAINING_TYPES_WITH_EQUIVALENCE and self.curriculum.a_diplome_etranger

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['curriculum'] = self.curriculum
        context['display_curriculum'] = self.display_curriculum
        context['display_equivalence'] = self.display_equivalence
        return context


class CurriculumGlobalDetailsView(CurriculumGlobalCommonViewMixin, TemplateView):
    urlpatterns = {'curriculum': 'curriculum'}
    template_name = 'admission/details/curriculum.html'
    permission_required = 'admission.view_admission_curriculum'
