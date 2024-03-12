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

import ast
from typing import Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.template.defaultfilters import yesno
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext as _, gettext_lazy, pgettext
from django.views import View

from admission.contrib.models import Scholarship
from admission.ddd.admission.commands import ListerToutesDemandesQuery
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO
from admission.ddd.admission.enums.statut import CHOIX_STATUT_TOUTE_PROPOSITION_DICT
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT,
)
from admission.ddd.admission.formation_generale.domain.model.enums import OngletsChecklist
from admission.forms.admission.filter import AllAdmissionsFilterForm
from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.templatetags.admission import admission_status
from admission.utils import add_messages_into_htmx_response
from base.models.campus import Campus
from base.models.enums.education_group_types import TrainingType
from base.models.person import Person
from infrastructure.messages_bus import message_bus_instance
from osis_async.models import AsyncTask
from osis_export.contrib.export_mixins import ExportMixin, ExcelFileExportMixin
from osis_export.models import Export
from osis_export.models.enums.types import ExportTypes

__all__ = [
    'AdmissionListExcelExportView',
]


FULL_DATE_FORMAT = '%Y/%m/%d, %H:%M:%S'


class BaseAdmissionExcelExportView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ExportMixin,
    ExcelFileExportMixin,
    View,
):
    export_name = gettext_lazy('Admission export')
    export_description = gettext_lazy('Excel export of admission')
    success_message = gettext_lazy(
        'Your export request has been planned, you will receive a notification as soon as it is available.'
    )
    failure_message = gettext_lazy('The export has failed')
    redirect_url_name = 'admission'
    command = None
    with_legend_worksheet = True
    with_parameters_worksheet = True
    description = gettext_lazy('Admissions')

    def get_filters(self):
        """Get filters as a dict of key/value pairs corresponding to the command params"""
        raise NotImplementedError

    def get_export_objects(self, **kwargs):
        # The filters are saved as dict string so we convert it here to a dict
        filters = ast.literal_eval(kwargs.get('filters'))
        return message_bus_instance.invoke(self.command(**filters))

    def get(self, request):
        # Get filters
        filters = self.get_filters()
        export = None

        if filters:
            # Create async task
            task = AsyncTask.objects.create(
                name=self.export_name,
                description=self.export_description,
                person=self.request.user.person,
            )

            # Create export
            export = Export.objects.create(
                called_from_class=f'{self.__module__}.{self.__class__.__name__}',
                filters=self.get_filters(),
                person=self.request.user.person,
                job_uuid=task.uuid,
                file_name=slugify(self.export_name),
                type=ExportTypes.EXCEL.name,
            )

        if export:
            messages.success(request, self.success_message)
        else:
            messages.error(request, self.failure_message)

        if self.request.htmx:
            response = HttpResponse(self.success_message if export else self.failure_message)
            add_messages_into_htmx_response(
                request=request,
                response=response,
            )
            return response

        return HttpResponseRedirect(reverse(self.redirect_url_name))


class AdmissionListExcelExportView(BaseAdmissionExcelExportView):
    command = ListerToutesDemandesQuery
    export_name = gettext_lazy('Admission applications export')
    export_description = gettext_lazy('Excel export of admission applications')
    permission_required = 'admission.view_enrolment_applications'
    redirect_url_name = 'admission:all-list'
    urlpatterns = 'admission-list-excel-export'

    def get_formatted_filters_parameters_worksheet(self, filters: str) -> Dict:
        formatted_filters = super().get_formatted_filters_parameters_worksheet(filters)

        formatted_filters.pop('demandeur', None)
        formatted_filters.pop('tri_inverse', None)
        formatted_filters.pop('champ_tri', None)

        # Formatting of the names of the filters
        base_fields = AllAdmissionsFilterForm.base_fields
        mapping_filter_key_name = {
            key: str(base_fields[key].label) if key in base_fields else key for key in formatted_filters
        }

        # Formatting of the values of the filters
        mapping_filter_key_value = {}

        # Retrieve candidate name
        candidate_global_id = formatted_filters.get('matricule_candidat')
        if candidate_global_id:
            person = Person.objects.filter(global_id=candidate_global_id).first()
            if person:
                mapping_filter_key_value['matricule_candidat'] = person.full_name

        # Retrieve enrolment site name
        campus = formatted_filters.get('site_inscription')
        if campus:
            campus = Campus.objects.filter(uuid=campus).first()
            if campus:
                mapping_filter_key_value['site_inscription'] = campus.name

        # Retrieve the names of the scholarships
        scholarship_values = {
            scholarship: formatted_filters.get(scholarship)
            for scholarship in [
                'bourse_internationale',
                'bourse_erasmus_mundus',
                'bourse_double_diplomation',
            ]
            if formatted_filters.get(scholarship)
        }

        if scholarship_values:
            scholarships_names_by_uuid = {
                str(s.uuid): s.short_name
                for s in Scholarship.objects.filter(uuid__in=scholarship_values.values()).only('uuid', 'short_name')
            }

            for scholarship in scholarship_values:
                mapping_filter_key_value[scholarship] = scholarships_names_by_uuid.get(
                    scholarship_values[scholarship],
                    scholarship_values[scholarship],
                )

        # Format the checklist filters mode
        checklist_mode = formatted_filters.get('mode_filtres_etats_checklist')
        if checklist_mode:
            mapping_filter_key_value['mode_filtres_etats_checklist'] = ModeFiltrageChecklist.get_value(checklist_mode)

        # Format the checklist filters
        mapping_filter_key_value['filtres_etats_checklist'] = {}
        for checklist_tab, checklist_statuses in formatted_filters.get('filtres_etats_checklist').items():
            if not checklist_statuses:
                continue

            mapping_filter_key_value['filtres_etats_checklist'][OngletsChecklist.get_value(checklist_tab)] = [
                ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT[checklist_tab][status].libelle
                for status in checklist_statuses
            ]

        # Format enums
        statuses = formatted_filters.get('etats')
        if statuses:
            mapping_filter_key_value['etats'] = [
                CHOIX_STATUT_TOUTE_PROPOSITION_DICT.get(status_key) for status_key in statuses
            ]

        admission_type = formatted_filters.get('type')
        if admission_type:
            mapping_filter_key_value['type'] = TypeDemande.get_value(admission_type)

        trainings_types = formatted_filters.get('types_formation')
        if trainings_types:
            mapping_filter_key_value['types_formation'] = [TrainingType.get_value(t) for t in trainings_types]

        return {
            mapping_filter_key_name[key]: mapping_filter_key_value.get(key, formatted_filters[key])
            for key, value in formatted_filters.items()
        }

    def get_header(self):
        return [
            _('Application numero'),
            _('Surname'),
            _('First name'),
            _('Noma'),
            _('Several applications?'),
            pgettext('admission', 'Training acronym'),
            pgettext('admission', 'Training title'),
            _('Nationality'),
            _('DD/scholarship/EM?'),
            _('Application status'),
            _('Last modification (author)'),
            _('Modification date'),
            _('Confirmation date'),
        ]

    def get_row_data(self, row: DemandeRechercheDTO):
        return [
            row.numero_demande,
            row.nom_candidat,
            row.prenom_candidat,
            row.noma_candidat,
            yesno(row.plusieurs_demandes),
            f'{row.sigle_formation}-1' if row.est_premiere_annee else row.sigle_formation,
            _('First year of') + ' ' + row.intitule_formation if row.est_premiere_annee else row.intitule_formation,
            row.nationalite_candidat,
            yesno(row.vip),
            str(admission_status(row.etat_demande, row.type_formation)),
            _('candidate') if row.derniere_modification_par_candidat else row.derniere_modification_par,
            row.derniere_modification_le.strftime(FULL_DATE_FORMAT),
            row.date_confirmation.strftime(FULL_DATE_FORMAT) if row.date_confirmation else '',
        ]

    def get_filters(self):
        form = AllAdmissionsFilterForm(user=self.request.user, data=self.request.GET)
        if form.is_valid():
            filters = form.cleaned_data
            filters.pop('taille_page', None)
            filters.pop('page', None)
            filters.pop('liste_travail', None)

            ordering_field = self.request.GET.get('o')
            if ordering_field:
                filters['tri_inverse'] = ordering_field[0] == '-'
                filters['champ_tri'] = ordering_field.lstrip('-')

            filters['demandeur'] = str(self.request.user.person.uuid)
            return form.cleaned_data
        return {}
