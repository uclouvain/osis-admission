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
import datetime
import uuid
from typing import Dict, Union

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.template.defaultfilters import yesno
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.text import slugify
from django.utils.translation import gettext as _, gettext_lazy, pgettext, get_language
from django.views import View
from osis_async.models import AsyncTask
from osis_export.contrib.export_mixins import ExportMixin, ExcelFileExportMixin
from osis_export.models import Export
from osis_export.models.enums.types import ExportTypes

from admission.ddd.admission.enums.liste import TardiveModificationReorientationFiltre
from admission.models import Scholarship, AdmissionFormItem
from admission.ddd.admission.commands import ListerToutesDemandesQuery
from admission.ddd.admission.doctorat.preparation.commands import ListerDemandesQuery as ListerDemandesDoctoralesQuery
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
    TOUS_CHOIX_COMMISSION_PROXIMITE,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.preparation.dtos.liste import DemandeRechercheDTO
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO as TouteDemandeRechercheDTO
from admission.ddd.admission.enums import TypeItemFormulaire
from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.ddd.admission.enums.statut import CHOIX_STATUT_TOUTE_PROPOSITION_DICT
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_continue.commands import ListerDemandesQuery as ListerDemandesContinuesQuery
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue, ChoixEdition
from admission.ddd.admission.formation_continue.dtos.liste import DemandeRechercheDTO as DemandeContinueRechercheDTO
from admission.ddd.admission.formation_generale.domain.model.enums import OngletsChecklist
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT as ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT_GENERALE,
)
from admission.ddd.admission.formation_continue.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT as ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT_CONTINUE,
)
from admission.ddd.admission.formation_continue.domain.model.enums import OngletsChecklist as OngletsChecklistContinue
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT as ORGANISATION_ONGLETS_CHECKLIST_DOCTORALE_PAR_STATUT,
)
from admission.ddd.admission.formation_generale.domain.model.enums import OngletsChecklist as OngletsChecklistGenerale
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    OngletsChecklist as OngletsChecklistDoctorale,
)
from admission.forms.admission.filter import AllAdmissionsFilterForm, ContinuingAdmissionsFilterForm
from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.forms.doctorate.cdd.filter import DoctorateListFilterForm
from admission.templatetags.admission import admission_status
from admission.utils import add_messages_into_htmx_response
from base.models.campus import Campus
from base.models.enums.education_group_types import TrainingType
from base.models.person import Person
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    'AdmissionListExcelExportView',
    'ContinuingAdmissionListExcelExportView',
    'DoctorateAdmissionListExcelExportView',
]

from reference.models.country import Country

FULL_DATE_FORMAT = '%Y/%m/%d, %H:%M:%S'
SHORT_DATE_FORMAT = '%Y/%m/%d'
SPECIFIC_QUESTION_SEPARATOR = '|'
SPECIFIC_QUESTION_SEPARATOR_REPLACEMENT = '#'


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
    with_specific_questions = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.specific_questions: Dict[str, AdmissionFormItem] = {}
        self.language = settings.LANGUAGE_CODE

    def generate_file(self, person, filters, **kwargs):
        # Get the person language
        if person.language:
            self.language = person.language

        # Load the specific questions if needed
        if self.with_specific_questions:
            self.initialize_specific_questions()

        return super().generate_file(person, filters, **kwargs)

    def initialize_specific_questions(self):
        """Initialize the specific questions."""
        self.specific_questions = {
            str(form_item.uuid): form_item
            for form_item in AdmissionFormItem.objects.filter(
                type__in=[TypeItemFormulaire.SELECTION.name, TypeItemFormulaire.TEXTE.name],
                active=True,
            )
        }

    def get_filters(self):
        """Get filters as a dict of key/value pairs corresponding to the command params"""
        raise NotImplementedError

    def process_filters_before_command(self, filters):
        """Process filters before sending them to the command"""
        return filters

    def get_export_objects(self, **kwargs):
        # The filters are saved as dict string so we convert it here to a dict
        filters = ast.literal_eval(kwargs.get('filters'))
        self.process_filters_before_command(filters)
        return message_bus_instance.invoke(self.command(**filters))

    def get_row_data_specific_questions_answers(
        self,
        proposition_dto: Union[
            TouteDemandeRechercheDTO,
        ],
    ):
        """
        Get the answers of the specific questions of the proposition based on a list of configurations.
        :param proposition_dto: The DTO of the proposition.
        :return: The concatenation of the answers of the specific questions.
        """
        specific_questions_answers = []

        for specific_question_uuid, specific_question_answer in proposition_dto.reponses_questions_specifiques.items():
            form_item = self.specific_questions.get(specific_question_uuid)

            if form_item:
                if not specific_question_answer:
                    answer = ''

                elif form_item.type == TypeItemFormulaire.SELECTION.name:
                    # Create a dict mapping the keys of the options to the corresponding labels in the user's language
                    if not hasattr(form_item, '_current_values'):
                        setattr(
                            form_item,
                            '_current_values',
                            {
                                option.get('key'): option.get(self.language, '').replace(
                                    SPECIFIC_QUESTION_SEPARATOR,
                                    SPECIFIC_QUESTION_SEPARATOR_REPLACEMENT,
                                )
                                for option in form_item.values
                            },
                        )
                    current_values = getattr(form_item, '_current_values')

                    # Concatenate the labels of the selected options
                    answer = (
                        ','.join([current_values[key] for key in specific_question_answer if key in current_values])
                        if isinstance(specific_question_answer, list)
                        else current_values.get(specific_question_answer, '')
                    )

                else:
                    answer = specific_question_answer

                    # Replace the separator in case the answer already contains it
                    if isinstance(answer, str):
                        answer = answer.replace(SPECIFIC_QUESTION_SEPARATOR, SPECIFIC_QUESTION_SEPARATOR_REPLACEMENT)

                specific_questions_answers.append(f'{form_item.internal_label} : {answer}')

        return SPECIFIC_QUESTION_SEPARATOR.join(specific_questions_answers)

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
                extra_data={'description': str(self.export_description)},
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

    def get_task_done_async_manager_extra_kwargs(self, file_name: str, file_url: str, export_extra_data: Dict) -> Dict:
        download_message = format_html(
            "{}: <a href='{}' target='_blank'>{}</a>",
            _("Your document is available here"),
            file_url,
            file_name,
        )
        description = export_extra_data.get('description')
        return {'description': f"{description}<br>{download_message}"}

    def get_read_token_extra_kwargs(self) -> Dict:
        return {'custom_ttl': settings.EXPORT_FILE_DEFAULT_TTL}


class AdmissionListExcelExportView(BaseAdmissionExcelExportView):
    command = ListerToutesDemandesQuery
    export_name = gettext_lazy('Admission applications export')
    export_description = gettext_lazy('Excel export of admission applications')
    permission_required = 'admission.view_enrolment_applications'
    redirect_url_name = 'admission:all-list'
    urlpatterns = 'all-admissions-list'
    with_specific_questions = True

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

            mapping_filter_key_value['filtres_etats_checklist'][OngletsChecklistGenerale.get_value(checklist_tab)] = [
                ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT_GENERALE[checklist_tab][status].libelle
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

        late_modification_reorientation = formatted_filters.get('tardif_modif_reorientation')
        if late_modification_reorientation:
            mapping_filter_key_value['tardif_modif_reorientation'] = TardiveModificationReorientationFiltre.get_value(
                late_modification_reorientation
            )

        trainings_types = formatted_filters.get('types_formation')
        if trainings_types:
            mapping_filter_key_value['types_formation'] = [TrainingType.get_value(t) for t in trainings_types]

        # Format boolean values
        mapping_filter_key_value['quarantaine'] = yesno(formatted_filters.get('quarantaine'), _('Yes,No,All'))

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
            _('Private email address'),
            _('Dynamic questions'),
        ]

    def get_row_data(self, row: TouteDemandeRechercheDTO):
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
            row.adresse_email_candidat,
            self.get_row_data_specific_questions_answers(row),
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


class ContinuingAdmissionListExcelExportView(BaseAdmissionExcelExportView):
    command = ListerDemandesContinuesQuery
    export_name = gettext_lazy('Admission applications export')
    export_description = gettext_lazy('Excel export of admission applications')
    permission_required = 'admission.view_continuing_enrolment_applications'
    redirect_url_name = 'admission:continuing-education:list'
    urlpatterns = 'continuing-admissions-list'

    def get_formatted_filters_parameters_worksheet(self, filters: str) -> Dict:
        formatted_filters = super().get_formatted_filters_parameters_worksheet(filters)

        # Remove the filters not used in the excel export
        formatted_filters.pop('demandeur', None)
        formatted_filters.pop('tri_inverse', None)
        formatted_filters.pop('champ_tri', None)

        # Formatting of the names of the filters
        base_fields = ContinuingAdmissionsFilterForm.base_fields
        mapping_filter_key_name = {
            key: str(base_fields[key].label) if key in base_fields else key for key in formatted_filters
        }

        mapping_filter_key_name['facultes'] = _('Faculty')
        mapping_filter_key_name['matricule_candidat'] = _('Last name / First name / Email / NOMA')

        # Formatting of the values of the filters
        mapping_filter_key_value = {}

        # Retrieve candidate name
        candidate_global_id = formatted_filters.get('matricule_candidat')
        if candidate_global_id:
            person = Person.objects.filter(global_id=candidate_global_id).first()
            if person:
                mapping_filter_key_value['matricule_candidat'] = person.full_name

        # Format enums
        statuses = formatted_filters.get('etats')
        if statuses:
            mapping_filter_key_value['etats'] = [
                ChoixStatutPropositionContinue.get_value(status_key) for status_key in statuses
            ]

        edition = formatted_filters.get('edition')
        if edition:
            mapping_filter_key_value['edition'] = [ChoixEdition.get_value(status_key) for status_key in edition]

        # Format boolean values
        # > "Yes" / "No" / ""
        for filter_name in ['inscription_requise', 'paye']:
            formatted_filters[filter_name] = yesno(formatted_filters[filter_name], _('yes,no,'))

        # > "Yes" / ""
        for filter_name in ['marque_d_interet']:
            formatted_filters[filter_name] = _('yes') if formatted_filters[filter_name] else ''

        trainings_types = formatted_filters.get('types_formation')
        if trainings_types:
            mapping_filter_key_value['types_formation'] = [TrainingType.get_value(t) for t in trainings_types]

        # Format the checklist filters mode
        checklist_mode = formatted_filters.get('mode_filtres_etats_checklist')
        if checklist_mode:
            mapping_filter_key_value['mode_filtres_etats_checklist'] = ModeFiltrageChecklist.get_value(checklist_mode)

        # Format the checklist filters
        mapping_filter_key_value['filtres_etats_checklist'] = {}
        for checklist_tab, checklist_statuses in formatted_filters.get('filtres_etats_checklist').items():
            if not checklist_statuses:
                continue

            mapping_filter_key_value['filtres_etats_checklist'][OngletsChecklistContinue.get_value(checklist_tab)] = [
                ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT_CONTINUE[checklist_tab][status].libelle
                for status in checklist_statuses
            ]

        return {
            mapping_filter_key_name[key]: mapping_filter_key_value.get(key, formatted_filters[key])
            for key, value in formatted_filters.items()
        }

    def get_header(self):
        return [
            _('Application no.'),
            _('Last name'),
            _('First name'),
            _('NOMA'),
            _('Email address'),
            pgettext('admission', 'Course'),
            _('Edition'),
            _('Faculty'),
            _('Paid'),
            _('Reduced rights'),
            _('Pay by training cheque'),
            _('CEP'),
            _('Payement spread'),
            _('Training spread'),
            _('Experience knowledge valorisation'),
            _('Assessment test presented'),
            _('Assessment test succeeded'),
            _('Certificate provided'),
            _('Status'),
            _('EPC status'),
            _('Confirmation date'),
            _('Last modif.'),
            _('Modification author'),
        ]

    def get_row_data(self, row: DemandeContinueRechercheDTO):
        return [
            row.numero_demande,
            row.nom_candidat,
            row.prenom_candidat,
            row.noma_candidat,
            row.courriel_candidat,
            row.formation,
            str(ChoixEdition.get_value(row.edition)) if row.edition else '',
            row.sigle_faculte,
            yesno(row.paye, _('yes,no')),
            yesno(row.droits_reduits, _('yes,no')),
            yesno(row.paye_par_cheque_formation, _('yes,no')),
            yesno(row.cep, _('yes,no')),
            yesno(row.etalement_des_paiements, _('yes,no')),
            yesno(row.etalement_de_la_formation, _('yes,no')),
            yesno(row.valorisation_des_acquis_d_experience, _('yes,no')),
            yesno(row.a_presente_l_epreuve_d_evaluation, _('yes,no')),
            yesno(row.a_reussi_l_epreuve_d_evaluation, _('yes,no')),
            yesno(row.diplome_produit, _('yes,no')),
            str(ChoixStatutPropositionContinue.get_value(row.etat_demande)),
            '',  # TODO Add EPC status
            row.date_confirmation.strftime(FULL_DATE_FORMAT) if row.date_confirmation else '',
            row.derniere_modification_le.strftime(FULL_DATE_FORMAT),
            row.derniere_modification_par,
        ]

    def get_filters(self):
        form = ContinuingAdmissionsFilterForm(user=self.request.user, data=self.request.GET)
        if form.is_valid():
            filters = form.cleaned_data
            filters.pop('taille_page', None)
            filters.pop('page', None)

            ordering_field = self.request.GET.get('o')
            if ordering_field:
                filters['tri_inverse'] = ordering_field[0] == '-'
                filters['champ_tri'] = ordering_field.lstrip('-')

            filters['demandeur'] = str(self.request.user.person.uuid)
            return form.cleaned_data
        return {}


class DoctorateAdmissionListExcelExportView(BaseAdmissionExcelExportView):
    command = ListerDemandesDoctoralesQuery
    export_name = gettext_lazy('Admission applications export')
    export_description = gettext_lazy('Excel export of admission applications')
    permission_required = 'admission.view_doctorate_enrolment_applications'
    redirect_url_name = 'admission:doctorate:cdd:list'
    urlpatterns = 'doctorate-admissions-list'
    DATE_FIELDS = [
        'date_soumission_debut',
        'date_soumission_fin',
    ]

    @cached_property
    def current_language(self):
        return get_language()

    def get_formatted_filters_parameters_worksheet(self, filters: str) -> Dict:
        current_language = self.current_language

        formatted_filters = super().get_formatted_filters_parameters_worksheet(filters)

        # Remove the filters not used in the excel export
        formatted_filters.pop('demandeur', None)
        formatted_filters.pop('tri_inverse', None)
        formatted_filters.pop('champ_tri', None)

        # Formatting of the names of the filters
        base_fields = DoctorateListFilterForm.base_fields
        mapping_filter_key_name = {
            key: str(base_fields[key].label) if key in base_fields else key for key in formatted_filters
        }

        mapping_filter_key_name['matricule_candidat'] = _('Last name / First name / Email / NOMA')
        mapping_filter_key_name['date_soumission_debut'] = _('Submitted from')
        mapping_filter_key_name['date_soumission_fin'] = _('Submitted until')

        # Formatting of the values of the filters
        mapping_filter_key_value = {}

        # Retrieve the names of the persons
        field_name_by_global_id = {
            formatted_filters[field_name]: field_name
            for field_name in [
                'matricule_candidat',
                'matricule_promoteur',
            ]
            if formatted_filters.get(field_name)
        }

        if field_name_by_global_id:
            persons = Person.objects.filter(global_id__in=list(field_name_by_global_id.keys()))
            for person in persons:
                mapping_filter_key_value[field_name_by_global_id[person.global_id]] = person.full_name

        # Retrieve the nationality
        country_of_citizenship_iso_code = formatted_filters.get('nationalite')
        if country_of_citizenship_iso_code:
            country_field = {
                settings.LANGUAGE_CODE_FR: 'name',
                settings.LANGUAGE_CODE_EN: 'name_en',
            }.get(current_language, 'name')

            country = Country.objects.filter(iso_code=country_of_citizenship_iso_code).first()

            if country:
                mapping_filter_key_value['nationalite'] = getattr(country, country_field)

        # Retrieve the names of the scholarships
        field_name_by_global_id = {
            uuid.UUID(formatted_filters[field_name]): field_name
            for field_name in [
                'bourse_recherche',
            ]
            if formatted_filters.get(field_name)
        }

        if field_name_by_global_id:
            scholarships = Scholarship.objects.filter(uuid__in=list(field_name_by_global_id.keys()))
            for scholarship in scholarships:
                mapping_filter_key_value[field_name_by_global_id[scholarship.uuid]] = scholarship.short_name

        # Format the checklist filters
        mapping_filter_key_value['filtres_etats_checklist'] = {}
        for checklist_tab, checklist_statuses in formatted_filters.get('filtres_etats_checklist').items():
            if not checklist_statuses:
                continue

            mapping_filter_key_value['filtres_etats_checklist'][OngletsChecklistDoctorale.get_value(checklist_tab)] = [
                ORGANISATION_ONGLETS_CHECKLIST_DOCTORALE_PAR_STATUT[checklist_tab][status].libelle
                for status in checklist_statuses
            ]

        # Format enums
        checklist_mode = formatted_filters.get('mode_filtres_etats_checklist')
        if checklist_mode:
            mapping_filter_key_value['mode_filtres_etats_checklist'] = ModeFiltrageChecklist.get_value(checklist_mode)

        statuses = formatted_filters.get('etats')
        if statuses:
            mapping_filter_key_value['etats'] = [
                ChoixStatutPropositionDoctorale.get_value(status_key) for status_key in statuses
            ]

        admission_type = formatted_filters.get('type')
        if admission_type:
            mapping_filter_key_value['type'] = ChoixTypeAdmission.get_value(admission_type)

        proximity_commission = formatted_filters.get('commission_proximite')
        if proximity_commission:
            mapping_filter_key_value['commission_proximite'] = TOUS_CHOIX_COMMISSION_PROXIMITE.get(proximity_commission)

        financing_type = formatted_filters.get('type_financement')
        if financing_type:
            mapping_filter_key_value['type_financement'] = ChoixTypeFinancement.get_value(financing_type)

        checklist_mode = formatted_filters.get('mode_filtres_etats_checklist')
        if checklist_mode:
            mapping_filter_key_value['mode_filtres_etats_checklist'] = ModeFiltrageChecklist.get_value(checklist_mode)

        # Format boolean values
        # > "Yes" / "No" / ""
        for filter_name in ['cotutelle']:
            mapping_filter_key_value[filter_name] = yesno(formatted_filters[filter_name], _('yes,no,'))

        # > "Yes" / ""
        for filter_name in ['fnrs_fria_fresh']:
            formatted_filters[filter_name] = _('yes') if formatted_filters[filter_name] else ''

        return {
            mapping_filter_key_name[key]: mapping_filter_key_value.get(key, formatted_filters[key])
            for key, value in formatted_filters.items()
        }

    def get_header(self):
        return [
            _('Application no.'),
            _('Last name / First name'),
            _('Nationality'),
            _('Scholarship'),
            pgettext('admission', 'Course'),
            _('Dossier status'),
            _('CDD decision'),
            _('SIC decision'),
            _('Submission date'),
            _('Last modification'),
            _('Modification author'),
            _('Pre-admission'),
            _('Cotutelle'),
        ]

    def get_row_data(self, row: DemandeRechercheDTO):
        return [
            row.numero_demande,
            row.candidat,
            row.nom_pays_nationalite_candidat,
            row.code_bourse,
            row.formation,
            str(ChoixStatutPropositionDoctorale.get_value(row.etat_demande)),
            row.decision_fac,
            row.decision_sic,
            row.date_confirmation.strftime(SHORT_DATE_FORMAT) if row.date_confirmation else '',
            row.derniere_modification_le.strftime(SHORT_DATE_FORMAT),
            row.derniere_modification_par,
            yesno(row.type_admission == ChoixTypeAdmission.PRE_ADMISSION.name),
            yesno(row.cotutelle, _('yes,no,')),
        ]

    def get_filters(self):
        form = DoctorateListFilterForm(user=self.request.user, data=self.request.GET)

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

            # Convert the dates to strings
            for date_field in self.DATE_FIELDS:
                filters[date_field] = filters[date_field].toisoformat() if filters.get(date_field) else ''

            return form.cleaned_data
        return {}

    def process_filters_before_command(self, filters):
        # Convert the dates from strings to dates
        for date_field in self.DATE_FIELDS:
            filters[date_field] = datetime.date.fromisoformat(filters[date_field]) if filters.get(date_field) else None

        return filters
