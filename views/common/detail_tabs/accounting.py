# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime

from attr import asdict
from django.utils.functional import cached_property
from django.views.generic import TemplateView

from admission.api.serializers.accounting import get_last_french_community_high_education_institutes
from admission.ddd.admission.enums import FORMATTED_RELATIONSHIPS, CHOIX_AFFILIATION_SPORT_SELON_SITE
from admission.ddd.admission.formation_generale.commands import GetComptabiliteQuery
from admission.views.doctorate.mixins import LoadDossierViewMixin
from infrastructure.messages_bus import message_bus_instance

__all__ = ['AccountingDetailView']


class AccountingMixinView(LoadDossierViewMixin):
    @cached_property
    def accounting(self):
        accounting = message_bus_instance.invoke(GetComptabiliteQuery(uuid_proposition=self.admission_uuid))
        accounting_dict = asdict(accounting)
        accounting_dict['derniers_etablissements_superieurs_communaute_fr_frequentes'] = self.last_fr_institutes
        return accounting_dict

    @property
    def last_fr_institutes(self):
        return get_last_french_community_high_education_institutes(
            self.admission.candidate,
            date=self.admission.submitted_at or datetime.datetime.now(),
        )

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
