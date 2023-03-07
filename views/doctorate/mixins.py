##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin

from admission.contrib.models import DoctorateAdmission
from admission.ddd.parcours_doctoral.commands import RecupererDoctoratQuery
from admission.ddd.parcours_doctoral.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.parcours_doctoral.dtos import DoctoratDTO
from admission.ddd.parcours_doctoral.epreuve_confirmation.commands import (
    RecupererDerniereEpreuveConfirmationQuery,
)
from admission.ddd.parcours_doctoral.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from admission.ddd.parcours_doctoral.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationNonTrouveeException,
)
from admission.ddd.admission.doctorat.preparation.commands import GetPropositionCommand
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.doctorat.preparation.dtos import PropositionDTO
from admission.ddd.admission.doctorat.validation.commands import RecupererDemandeQuery
from admission.ddd.admission.doctorat.validation.domain.validator.exceptions import DemandeNonTrouveeException
from admission.ddd.admission.doctorat.validation.dtos import DemandeDTO
from admission.templatetags.admission import CONTEXT_CONTINUING, CONTEXT_DOCTORATE, CONTEXT_GENERAL
from admission.utils import (
    get_cached_admission_perm_obj,
    get_cached_continuing_education_admission_perm_obj,
    get_cached_general_education_admission_perm_obj,
)
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import PermissionRequiredMixin


class LoadDossierViewMixin(LoginRequiredMixin, PermissionRequiredMixin, ContextMixin):
    @property
    def admission_uuid(self):
        return self.kwargs.get('uuid')

    @property
    def current_context(self):
        return self.request.resolver_match.namespaces[1]

    @property
    def admission(self) -> DoctorateAdmission:
        return {
            CONTEXT_DOCTORATE: get_cached_admission_perm_obj,
            CONTEXT_GENERAL: get_cached_general_education_admission_perm_obj,
            CONTEXT_CONTINUING: get_cached_continuing_education_admission_perm_obj,
        }[self.current_context](self.admission_uuid)

    @cached_property
    def proposition(self) -> 'PropositionDTO':
        return message_bus_instance.invoke(GetPropositionCommand(uuid_proposition=self.admission_uuid))

    @cached_property
    def dossier(self) -> 'DemandeDTO':
        return message_bus_instance.invoke(RecupererDemandeQuery(uuid=self.admission_uuid))

    @cached_property
    def doctorate(self) -> 'DoctoratDTO':
        return message_bus_instance.invoke(RecupererDoctoratQuery(doctorat_uuid=self.admission_uuid))

    @cached_property
    def last_confirmation_paper(self) -> EpreuveConfirmationDTO:
        try:
            last_confirmation_paper = message_bus_instance.invoke(
                RecupererDerniereEpreuveConfirmationQuery(self.admission_uuid)
            )
            if not last_confirmation_paper:
                raise Http404(_('Confirmation paper not found.'))
            return last_confirmation_paper
        except (DoctoratNonTrouveException, EpreuveConfirmationNonTrouveeException) as e:
            raise Http404(e.message)

    def get_permission_object(self):
        return self.admission

    @cached_property
    def base_namespace(self):
        return ':'.join(self.request.resolver_match.namespaces[:2])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admission_status = self.admission.status
        context['base_namespace'] = self.base_namespace

        if self.current_context == CONTEXT_DOCTORATE:
            try:
                if admission_status == ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name:
                    context['dossier'] = self.dossier
                    context['doctorate'] = self.doctorate
                else:
                    if admission_status == ChoixStatutPropositionDoctorale.CONFIRMEE.name:
                        context['dossier'] = self.dossier

                    context['admission'] = self.proposition

            except (PropositionNonTrouveeException, DemandeNonTrouveeException, DoctoratNonTrouveException) as e:
                raise Http404(e.message)
        else:
            context['admission'] = self.admission
        return context


class DoctorateAdmissionLastConfirmationMixin(LoadDossierViewMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}
        context['confirmation_paper'] = self.last_confirmation_paper
        return context
