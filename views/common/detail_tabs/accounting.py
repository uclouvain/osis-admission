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

from attr import asdict
from django.utils.functional import cached_property
from django.views.generic import TemplateView

from admission.ddd.admission.formation_generale.commands import GetComptabiliteQuery
from admission.ddd.admission.shared_kernel.commands import RechercherParcoursAnterieurQuery
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.shared_kernel.enums import CHOIX_AFFILIATION_SPORT_SELON_SITE, FORMATTED_RELATIONSHIPS
from admission.ddd.admission.shared_kernel.enums.valorisation_experience import ExperiencesCVRecuperees
from admission.views.common.mixins import AdmissionFormMixin, LoadDossierViewMixin
from infrastructure.messages_bus import message_bus_instance

__all__ = ['AccountingDetailView']


class AccountingMixinView(AdmissionFormMixin, LoadDossierViewMixin):
    @cached_property
    def accounting(self):
        accounting = message_bus_instance.invoke(GetComptabiliteQuery(uuid_proposition=self.admission_uuid))
        curriculum = message_bus_instance.invoke(
            RechercherParcoursAnterieurQuery(
                global_id=self.admission.candidate.global_id,
                uuid_proposition=self.admission_uuid,
                experiences_cv_recuperees=ExperiencesCVRecuperees.TOUTES
                if self.proposition.est_non_soumise
                else ExperiencesCVRecuperees.SEULEMENT_VALORISEES_PAR_ADMISSION,
            )
        )
        last_fr_institutes = (
            IProfilCandidatTranslator.recuperer_derniers_etablissements_superieurs_communaute_fr_frequentes(
                experiences_academiques=curriculum.experiences_academiques,
                annee_minimale=curriculum.annee_minimum_a_remplir,
            )
        )
        accounting_dict = asdict(accounting)
        accounting_dict['derniers_etablissements_superieurs_communaute_fr_frequentes'] = last_fr_institutes
        return accounting_dict

    @property
    def with_assimilation(self):
        return self.proposition.nationalite_ue_candidat is False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accounting'] = self.accounting
        context['formatted_relationship'] = FORMATTED_RELATIONSHIPS.get(self.accounting['relation_parente'])
        context['with_assimilation'] = self.with_assimilation
        context['sport_affiliation_choices_by_campus'] = CHOIX_AFFILIATION_SPORT_SELON_SITE
        context['is_general'] = self.is_general
        return context


class AccountingDetailView(AccountingMixinView, TemplateView):
    template_name = 'admission/details/accounting.html'
    permission_required = 'admission.view_admission_accounting'
    urlpatterns = 'accounting'
