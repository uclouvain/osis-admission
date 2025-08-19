# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import json
import uuid
from typing import Dict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.template.defaultfilters import yesno
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.text import slugify
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy, pgettext
from django.views import View
from osis_async.models import AsyncTask
from osis_comment.models import CommentEntry
from osis_export.contrib.export_mixins import ExcelFileExportMixin, ExportMixin
from osis_export.models import Export
from osis_export.models.enums.types import ExportTypes

from admission.admission_utils.get_actor_option_text import get_actor_option_text
from admission.ddd.admission.doctorat.preparation.commands import (
    ListerDemandesQuery as ListerDemandesDoctoralesQuery,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    TOUS_CHOIX_COMMISSION_PROXIMITE,
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    OngletsChecklist as OngletsChecklistDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT as ORGANISATION_ONGLETS_CHECKLIST_DOCTORALE_PAR_STATUT,
)
from admission.ddd.admission.doctorat.preparation.dtos.liste import DemandeRechercheDTO
from admission.ddd.admission.doctorat.preparation.read_view.repository.i_tableau_bord import (
    ITableauBordRepositoryAdmissionMixin,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixGenre
from admission.ddd.admission.formation_continue.commands import (
    ListerDemandesQuery as ListerDemandesContinuesQuery,
)
from admission.ddd.admission.formation_continue.commands import (
    RecupererResumePropositionQuery as RecupererResumePropositionContinueQuery,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixEdition,
    ChoixInscriptionATitre,
    ChoixMoyensDecouverteFormation,
    ChoixStatutPropositionContinue,
    ChoixTypeAdresseFacturation,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    OngletsChecklist as OngletsChecklistContinue,
)
from admission.ddd.admission.formation_continue.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT as ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT_CONTINUE,
)
from admission.ddd.admission.formation_continue.dtos import PropositionDTO
from admission.ddd.admission.formation_continue.dtos.liste import (
    DemandeRechercheDTO as DemandeContinueRechercheDTO,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    OngletsChecklist as OngletsChecklistGenerale,
)
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT as ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT_GENERALE,
)
from admission.ddd.admission.shared_kernel.commands import ListerToutesDemandesQuery
from admission.ddd.admission.shared_kernel.dtos.liste import (
    DemandeRechercheDTO as TouteDemandeRechercheDTO,
)
from admission.ddd.admission.shared_kernel.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.shared_kernel.enums import TypeItemFormulaire
from admission.ddd.admission.shared_kernel.enums.checklist import ModeFiltrageChecklist
from admission.ddd.admission.shared_kernel.enums.liste import (
    TardiveModificationReorientationFiltre,
)
from admission.ddd.admission.shared_kernel.enums.statut import (
    CHOIX_STATUT_TOUTE_PROPOSITION_DICT,
)
from admission.ddd.admission.shared_kernel.enums.type_demande import TypeDemande
from admission.forms.admission.filter import (
    AllAdmissionsFilterForm,
    ContinuingAdmissionsFilterForm,
)
from admission.forms.doctorate.cdd.filter import DoctorateListFilterForm
from admission.models import AdmissionFormItem, SupervisionActor
from admission.templatetags.admission import admission_status
from admission.utils import add_messages_into_htmx_response
from admission.views import PaginatedList
from base.models.campus import Campus
from base.models.enums.civil_state import CivilState
from base.models.enums.education_group_types import TrainingType
from base.models.enums.got_diploma import GotDiploma
from base.models.person import Person
from base.utils.utils import format_academic_year
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import (
    ExperienceNonAcademiqueDTO,
)
from infrastructure.messages_bus import message_bus_instance
from osis_profile.models.enums.curriculum import ActivitySector, ActivityType
from reference.models.country import Country
from reference.models.enums.cycle import Cycle
from reference.models.scholarship import Scholarship

__all__ = [
    'AdmissionListExcelExportView',
    'ContinuingAdmissionListExcelExportView',
    'DoctorateAdmissionListExcelExportView',
]


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
        initial_specific_questions_answers: Dict,
    ):
        """
        Get the answers of the specific questions of the proposition based on a list of configurations.
        :param initial_specific_questions_answers: The answers to the specific questions.
        :return: The concatenation of the answers of the specific questions.
        """
        specific_questions_answers = []

        for specific_question_uuid, specific_question_answer in initial_specific_questions_answers.items():
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
                'bourse_recherche',
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

        deadline_for_complements = formatted_filters.get('delai_depasse_complements')
        if deadline_for_complements:
            mapping_filter_key_value['delai_depasse_complements'] = _('Deadline exceeded')

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
            self.get_row_data_specific_questions_answers(row.reponses_questions_specifiques),
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
    with_specific_questions = True

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
        for filter_name in ['inscription_requise', 'paye', 'injection_epc_en_erreur']:
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
            _('Last name'),
            _('First name'),
            _('Email address'),
            _('State'),
            _('Gender'),
            _('Civil status'),
            _('Nationality'),
            _('Date of birth'),
            _('Place of birth'),
            _('Country of birth'),
            _('Belgian National Register Number'),
            _('Identity card number'),
            _('Passport number'),
            _('Have you previously enrolled at UCLouvain?'),
            _('Most recent year of enrolment at UCL'),
            _('Previous NOMA'),
            _('Legal domicile'),
            _('Contact address'),
            _('Emergency contact'),
            _('Mobile phone (GSM)'),
            _('Secondary school diploma'),
            _('Secondary school graduation year'),
            _('Last degree level'),
            pgettext('admission', 'Institute'),
            _('Graduation year'),
            _('Other academic courses'),
            _('Current occupation'),
            _('Current employer'),
            _('Sector'),
            _('Past non-academic activities (prof. and not prof.)'),
            _('Motivations'),
            pgettext('admission', 'Course'),
            _('Faculty'),
            _('Course manager(s)'),
            _('How did you hear about this course?'),
            _('Registration type'),
            _('Head office name'),
            _('Unique business number'),
            _('VAT number'),
            _('Billing address'),
            _('Specific questions'),
            _('Training assistance'),
            _('Registration required'),
            _('In payement order'),
            _('Reduced rights'),
            _('Pay by training cheque'),
            _('CEP'),
            _('Payement spread'),
            _('Training spread'),
            _('Experience knowledge valorisation'),
            _('Assessment test presented'),
            _('Assessment test succeeded'),
            _('TFF label'),
            _('Certificate provided'),
            _('Comment'),
        ]

    @classmethod
    def _format_yes_no(cls, value):
        if value:
            return str(_('yes'))
        elif value is False:
            return str(_('no'))
        return ''

    def get_row_data(self, row: uuid.UUID):
        resume_proposition: ResumePropositionDTO = message_bus_instance.invoke(
            RecupererResumePropositionContinueQuery(uuid_proposition=str(row))
        )

        student_form_comment = CommentEntry.objects.filter(
            object_uuid=row,
            tags=[OngletsChecklistContinue.fiche_etudiant.name],
        ).first()

        proposition: PropositionDTO = resume_proposition.proposition
        identification = resume_proposition.identification
        coordinates = resume_proposition.coordonnees

        billing_address = {
            ChoixTypeAdresseFacturation.CONTACT.name: coordinates.adresse_correspondance_formatee(' - '),
            ChoixTypeAdresseFacturation.RESIDENTIEL.name: coordinates.adresse_domicile_legale_formatee(' - '),
            ChoixTypeAdresseFacturation.AUTRE.name: (
                proposition.adresse_facturation.adresse_formatee(' - ') if proposition.adresse_facturation else ''
            ),
        }.get(proposition.type_adresse_facturation, '')

        # Get the information about the last graduated academic experience
        last_experience_with_diploma = self._get_last_academic_experience(
            academic_experiences=resume_proposition.curriculum.experiences_academiques,
        )

        if last_experience_with_diploma:
            last_diploma_year = last_experience_with_diploma.derniere_annee + 1
            last_diploma_level = str(Cycle.get_value(last_experience_with_diploma.cycle_formation))
            last_diploma_institute = last_experience_with_diploma.nom_institut
        else:
            last_diploma_level = ''
            last_diploma_institute = ''
            last_diploma_year = ''

        # Get the information about the current working activity
        (
            current_activities,
            current_activities_employer,
            current_activities_sector,
            past_activities,
        ) = self._get_non_academic_activities_columns(resume_proposition.curriculum.experiences_non_academiques)

        return [
            identification.nom,
            identification.prenom,
            proposition.adresse_email_candidat,
            str(ChoixStatutPropositionContinue.get_value(proposition.statut)),
            str(ChoixGenre.get_value(identification.genre)),
            str(CivilState.get_value(identification.etat_civil)),
            identification.nom_pays_nationalite,
            (
                identification.date_naissance.isoformat()
                if identification.date_naissance
                else str(identification.annee_naissance or '')
            ),
            identification.lieu_naissance,
            identification.nom_pays_naissance,
            identification.numero_registre_national_belge,
            identification.numero_carte_identite,
            identification.numero_passeport,
            self._format_yes_no(identification.annee_derniere_inscription_ucl is not None),
            format_academic_year(identification.annee_derniere_inscription_ucl),
            identification.noma_derniere_inscription_ucl,
            coordinates.adresse_domicile_legale_formatee(' - '),
            coordinates.adresse_correspondance_formatee(' - '),
            coordinates.numero_contact_urgence,
            coordinates.numero_mobile,
            str(GotDiploma.get_value(resume_proposition.etudes_secondaires.diplome_etudes_secondaires)),
            (
                resume_proposition.etudes_secondaires.annee_diplome_etudes_secondaires + 1
                if resume_proposition.etudes_secondaires.annee_diplome_etudes_secondaires
                else ''
            ),
            last_diploma_level,
            last_diploma_institute,
            last_diploma_year,
            '\n'.join(
                f'{experience.titre_formate}, {experience.nom_institut}'
                for experience in resume_proposition.curriculum.experiences_academiques
                if experience != last_experience_with_diploma
            ),
            current_activities,
            current_activities_employer,
            current_activities_sector,
            past_activities,
            proposition.motivations,
            proposition.formation.sigle,
            proposition.formation.sigle_entite_gestion,
            '',  # TODO program manager
            '\n'.join(
                str(ChoixMoyensDecouverteFormation.get_value(moyen))
                for moyen in proposition.moyens_decouverte_formation + [proposition.autre_moyen_decouverte_formation]
            ),
            str(ChoixInscriptionATitre.get_value(proposition.inscription_a_titre)),
            proposition.nom_siege_social,
            proposition.numero_unique_entreprise,
            proposition.numero_tva_entreprise,
            billing_address,
            self.get_row_data_specific_questions_answers(proposition.reponses_questions_specifiques),
            self._format_yes_no(proposition.aide_a_la_formation),
            self._format_yes_no(proposition.inscription_au_role_obligatoire),
            self._format_yes_no(proposition.en_ordre_de_paiement),
            self._format_yes_no(proposition.droits_reduits),
            self._format_yes_no(proposition.paye_par_cheque_formation),
            self._format_yes_no(proposition.cep),
            self._format_yes_no(proposition.etalement_des_paiments),
            self._format_yes_no(proposition.etalement_de_la_formation),
            self._format_yes_no(proposition.valorisation_des_acquis_d_experience),
            self._format_yes_no(proposition.a_presente_l_epreuve_d_evaluation),
            self._format_yes_no(proposition.a_reussi_l_epreuve_d_evaluation),
            proposition.intitule_du_tff,
            self._format_yes_no(proposition.diplome_produit),
            student_form_comment.content if student_form_comment else '',
        ]

    @staticmethod
    def _get_non_academic_activities_columns(non_academic_experiences):
        """
        From a list of non academic experiences, retrieve the formatted columns.
        :param non_academic_experiences: A list of non academic experiences
        :return: the columns as a tuple : (current functions, current employers, current sectors, past activities)
        """
        today_date = datetime.date.today()

        current_activity_prefix = ''
        current_activities = ''
        current_activities_employer = ''
        current_activities_sector = ''
        default_activity_function_format = '{obj.libelle_type}'
        activity_function_format = {
            ActivityType.WORK.name: '{obj.fonction}',
            ActivityType.OTHER.name: '{obj.autre_activite}',
        }

        past_activity_prefix = ''
        past_activities = ''
        default_activity_description_format = '{obj.dates_formatees} : {obj.libelle_type}'
        activity_description_format = {
            ActivityType.WORK.name: str(_('{obj.dates_formatees} : {obj.fonction} at {obj.employeur}')),
            ActivityType.OTHER.name: '{obj.dates_formatees} : {obj.autre_activite}',
        }

        for activity in non_academic_experiences:
            if activity.date_debut <= today_date <= activity.date_fin:
                activity_function = activity_function_format.get(
                    activity.type,
                    default_activity_function_format,
                ).format(obj=activity)

                current_activities += f'{current_activity_prefix}{activity_function}'
                current_activities_employer += f'{current_activity_prefix}{activity.employeur}'
                current_activities_sector += f'{current_activity_prefix}{ActivitySector.get_value(activity.secteur)}'
                current_activity_prefix = '\n'

            else:
                activity_description = activity_description_format.get(
                    activity.type,
                    default_activity_description_format,
                ).format(obj=activity)

                past_activities += f'{past_activity_prefix}{activity_description}'
                past_activity_prefix = '\n'

        return current_activities, current_activities_employer, current_activities_sector, past_activities

    @staticmethod
    def _get_last_academic_experience(academic_experiences):
        """
        From a list of academic experiences, return the last one (based on the graduation year and on the program cycle)
        :param academic_experiences: A list of academic experiences
        :return: The last experience, or None if there is no graduating experience
        """
        last_experience = None
        last_experience_year = 0
        last_experience_cycle_value = 0

        cycle_value = {
            Cycle.FIRST_CYCLE.name: 1,
            Cycle.SECOND_CYCLE.name: 2,
            Cycle.THIRD_CYCLE.name: 3,
        }

        for experience in academic_experiences:
            current_year = experience.derniere_annee
            current_cycle_value = cycle_value.get(experience.cycle_formation, 0)

            if experience.a_obtenu_diplome and (
                current_year > last_experience_year
                or current_year == last_experience_year
                and current_cycle_value > last_experience_cycle_value
            ):
                last_experience = experience
                last_experience_year = current_year
                last_experience_cycle_value = current_cycle_value

        return last_experience

    def get_export_objects(self, **kwargs):
        paginated_list_of_objects: PaginatedList[DemandeContinueRechercheDTO] = super().get_export_objects(**kwargs)
        return paginated_list_of_objects.complete_ids_list

    def get_filters(self):
        form = ContinuingAdmissionsFilterForm(user=self.request.user, data=self.request.GET)
        if form.is_valid():
            filters = form.cleaned_data
            filters.pop('liste_travail', None)

            # We just want to retrieve the uuids of the propositions matching the input filters (via the
            # complete_ids_list property) and not the default data retrieved by the command : the desired data will
            # be loaded in get_row_data).
            filters['taille_page'] = 0
            filters['page'] = 0

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
        candidate_global_id = formatted_filters.get('matricule_candidat')
        if candidate_global_id:
            candidate = Person.objects.filter(global_id=candidate_global_id).first()
            if candidate:
                mapping_filter_key_value['matricule_candidat'] = candidate.full_name

        promoter_id = formatted_filters.get('id_promoteur')
        if promoter_id:
            promoter_as_dict = json.loads(promoter_id)
            promoter_option = get_actor_option_text(promoter_as_dict)
            mapping_filter_key_value['id_promoteur'] = promoter_option

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

        # Retrieve the name of the scholarship
        scholarship_uuid = formatted_filters.get('bourse_recherche')
        if scholarship_uuid:
            scholarship = Scholarship.objects.filter(uuid=scholarship_uuid).first()

            if scholarship:
                mapping_filter_key_value['bourse_recherche'] = scholarship.short_name

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

        dashboard_indicator = formatted_filters.get('indicateur_tableau_bord')
        if dashboard_indicator:
            mapping_filter_key_value['indicateur_tableau_bord'] = (
                ITableauBordRepositoryAdmissionMixin.libelles_indicateurs_admission.get(dashboard_indicator)
            )

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
            str(row.decision_fac),
            str(row.decision_sic),
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
