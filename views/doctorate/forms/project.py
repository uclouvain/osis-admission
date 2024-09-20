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
import attr
from django.shortcuts import resolve_url
from django.views.generic import FormView

from admission.ddd.admission.doctorat.preparation.commands import CompleterPropositionCommand
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeFinancement,
    ChoixDoctoratDejaRealise,
    ChoixTypeAdmission,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    JustificationRequiseException,
    ContratTravailInconsistantException,
    DoctoratNonTrouveException,
    InstitutionInconsistanteException,
    DomaineTheseInconsistantException,
)
from admission.forms.admission.doctorate.project import DoctorateAdmissionProjectForm
from admission.views.common.mixins import LoadDossierViewMixin

__all__ = [
    "DoctorateAdmissionProjectFormView",
]

from admission.views.mixins.business_exceptions_form_view_mixin import BusinessExceptionFormViewMixin
from infrastructure.messages_bus import message_bus_instance


class DoctorateAdmissionProjectFormView(
    LoadDossierViewMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    template_name = 'admission/doctorate/forms/project.html'
    permission_required = 'admission.change_admission_project'
    form_class = DoctorateAdmissionProjectForm
    error_mapping = {
        JustificationRequiseException: 'justification',
        ContratTravailInconsistantException: 'type_contrat_travail',
        DoctoratNonTrouveException: 'doctorate',
        InstitutionInconsistanteException: 'institution',
        DomaineTheseInconsistantException: 'domaine_these',
    }

    def get_success_url(self):
        return resolve_url('admission:doctorate:project', uuid=self.admission_uuid)

    def get_initial(self):
        return {
            **attr.asdict(self.proposition),
            'sector': self.proposition.code_secteur_formation,
            'doctorate': "{sigle}-{annee}".format(
                sigle=self.proposition.doctorat.sigle,
                annee=self.proposition.doctorat.annee,
            ),
            'bourse_recherche': self.proposition.bourse_recherche and self.proposition.bourse_recherche.uuid,
        }

    def prepare_data(self, data):
        # Process the form data to match the command
        if self.proposition.type_admission != ChoixTypeAdmission.PRE_ADMISSION.name:
            data['justification'] = ''

        if data['type_financement'] != ChoixTypeFinancement.WORK_CONTRACT.name:
            data['type_contrat_travail'] = ''
            data['eft'] = None

        if data['type_financement'] != ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name:
            data['bourse_recherche'] = ''
            data['autre_bourse_recherche'] = ''

        if not data['type_financement']:
            data['duree_prevue'] = None
            data['temps_consacre'] = None

        if data['doctorat_deja_realise'] not in [
            ChoixDoctoratDejaRealise.YES.name,
            ChoixDoctoratDejaRealise.PARTIAL.name,
        ]:
            data['institution'] = ''
            data['domaine_these'] = ''
            data['non_soutenue'] = None
            data['date_soutenance'] = None
            data['raison_non_soutenue'] = ''

        if data['non_soutenue']:
            data['date_soutenance'] = None
        else:
            data['raison_non_soutenue'] = ''

        del data['non_soutenue']

        data['commission_proximite'] = self.proposition.commission_proximite

        return data

    def call_command(self, form):
        # Save the confirmation paper
        message_bus_instance.invoke(
            CompleterPropositionCommand(
                uuid=self.admission_uuid,
                matricule_auteur=self.request.user.person.global_id,
                **self.prepare_data(form.cleaned_data),
            )
        )
