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

import ast

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.template.defaultfilters import yesno
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext as _, gettext_lazy
from django.views import View

from osis_async.models import AsyncTask
from osis_export.contrib.export_mixins import ExportMixin, ExcelFileExportMixin

__all__ = [
    'AdmissionListExcelExportView',
]

from osis_export.models import Export

from osis_export.models.enums.types import ExportTypes

from admission.ddd.admission.commands import ListerToutesDemandesQuery
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO
from admission.forms.admission.filter import AllAdmissionsFilterForm
from admission.templatetags.admission import admission_status
from infrastructure.messages_bus import message_bus_instance

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
    success_message = gettext_lazy('The export has been planned')
    failure_message = gettext_lazy('The export has failed')
    redirect_url_name = 'admission'
    command = None

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
            return HttpResponse(self.success_message if export else self.failure_message)

        return HttpResponseRedirect(reverse(self.redirect_url_name))


class AdmissionListExcelExportView(BaseAdmissionExcelExportView):
    command = ListerToutesDemandesQuery
    export_name = gettext_lazy('Admission applications export')
    export_description = gettext_lazy('Excel export of admission applications')
    permission_required = 'admission.view_dossiers'
    redirect_url_name = 'admission:all-list'
    urlpatterns = 'admission-list-excel-export'

    def get_header(self):
        return [
            _('Application numero'),
            _('Last name'),
            _('First name'),
            _('Noma'),
            _('Several applications?'),
            _('Training acronym'),
            _('Training title'),
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
            row.sigle_formation,
            row.intitule_formation,
            row.nationalite_candidat,
            yesno(row.vip),
            str(admission_status(row.etat_demande, row.type_formation)),
            row.derniere_modification_par,
            row.derniere_modification_le.strftime(FULL_DATE_FORMAT),
            row.date_confirmation.strftime(FULL_DATE_FORMAT) if row.date_confirmation else '',
        ]

    def get_filters(self):
        form = AllAdmissionsFilterForm(user=self.request.user, data=self.request.GET)
        if form.is_valid():
            filters = form.cleaned_data
            filters.pop('taille_page', None)
            filters.pop('page', None)
            filters['demandeur'] = str(self.request.user.person.uuid)
            return form.cleaned_data
        return {}
