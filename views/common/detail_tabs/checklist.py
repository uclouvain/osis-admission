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
import datetime
from typing import Dict, Set, Optional, List

from django.conf import settings
from django.db.models import QuerySet
from django.forms import Form
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import resolve_url, redirect, render
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils import translation
from django.utils.formats import date_format
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _, gettext, get_language
from django.views.generic import TemplateView, FormView
from django.views.generic.base import RedirectView
from osis_comment.models import CommentEntry
from osis_history.models import HistoryEntry
from osis_history.utilities import add_history_entry
from osis_mail_template.exceptions import EmptyMailTemplateContent
from osis_mail_template.models import MailTemplate
from rest_framework import serializers, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from admission.contrib.models.online_payment import PaymentStatus, PaymentMethod
from admission.ddd import MOIS_DEBUT_ANNEE_ACADEMIQUE, MAIL_VERIFICATEUR_CURSUS
from admission.ddd import MONTANT_FRAIS_DOSSIER
from admission.ddd.admission.commands import ListerToutesDemandesQuery
from admission.ddd.admission.domain.validator.exceptions import ExperienceNonTrouveeException
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.dtos.resume import (
    ResumeCandidatDTO,
    ResumePropositionDTO,
)
from admission.ddd.admission.dtos.resume import ResumeEtEmplacementsDocumentsPropositionDTO
from admission.ddd.admission.dtos.titre_acces_selectionnable import TitreAccesSelectionnableDTO
from admission.ddd.admission.enums import Onglets, TypeItemFormulaire
from admission.ddd.admission.enums.emplacement_document import (
    DocumentsAssimilation,
    StatutEmplacementDocument,
    EMPLACEMENTS_DOCUMENTS_RECLAMABLES,
)
from admission.ddd.admission.enums.emplacement_document import (
    OngletsDemande,
    DocumentsEtudesSecondaires,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.commands import (
    RecupererResumeEtEmplacementsDocumentsNonLibresPropositionQuery,
    ModifierChecklistChoixFormationCommand,
    SpecifierPaiementNecessaireCommand,
    EnvoyerRappelPaiementCommand,
    SpecifierPaiementPlusNecessaireCommand,
    RecupererQuestionsSpecifiquesQuery,
    EnvoyerPropositionAFacLorsDeLaDecisionFacultaireCommand,
    SpecifierMotifsRefusPropositionParFaculteCommand,
    SpecifierInformationsAcceptationPropositionParFaculteCommand,
    ApprouverPropositionParFaculteCommand,
    RefuserPropositionParFaculteCommand,
    RecupererListePaiementsPropositionQuery,
    ModifierStatutChecklistParcoursAnterieurCommand,
    SpecifierConditionAccesPropositionCommand,
    SpecifierEquivalenceTitreAccesEtrangerPropositionCommand,
    SpecifierExperienceEnTantQueTitreAccesCommand,
    SpecifierFinancabiliteRegleCommand,
    ModifierStatutChecklistExperienceParcoursAnterieurCommand,
    ModifierAuthentificationExperienceParcoursAnterieurCommand,
    EnvoyerPropositionAuSicLorsDeLaDecisionFacultaireCommand,
    SpecifierBesoinDeDerogationSicCommand,
    SpecifierInformationsAcceptationPropositionParSicCommand,
    SpecifierMotifsRefusPropositionParSicCommand,
    RecupererDocumentsPropositionQuery,
    RefuserAdmissionParSicCommand,
    ApprouverAdmissionParSicCommand,
    RecupererPdfTemporaireDecisionSicQuery,
    RefuserInscriptionParSicCommand,
    ApprouverInscriptionParSicCommand,
    RecupererTitresAccesSelectionnablesPropositionQuery,
    RecupererResumePropositionQuery,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC,
    ChoixStatutPropositionGenerale,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_ETENDUS,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC_ETENDUS,
    PoursuiteDeCycle,
    STATUTS_PROPOSITION_GENERALE_ENVOYABLE_EN_FAC_POUR_DECISION,
)
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.ddd.admission.formation_generale.dtos.proposition import PropositionGestionnaireDTO
from admission.exports.admission_recap.section import get_dynamic_questions_by_tab
from admission.forms import disable_unavailable_forms
from admission.forms.admission.checklist import ChoixFormationForm, SicDecisionDerogationForm, FinancabiliteApprovalForm
from admission.forms.admission.checklist import (
    CommentForm,
    AssimilationForm,
    FacDecisionRefusalForm,
    FacDecisionApprovalForm,
    SicDecisionRefusalForm,
    SicDecisionApprovalForm,
    SicDecisionFinalRefusalForm,
    SicDecisionFinalApprovalForm,
)
from admission.forms.admission.checklist import (
    ExperienceStatusForm,
    can_edit_experience_authentication,
)
from admission.forms.admission.checklist import (
    StatusForm,
    PastExperiencesAdmissionRequirementForm,
    PastExperiencesAdmissionAccessTitleForm,
    SinglePastExperienceAuthenticationForm,
)
from admission.mail_templates import ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL
from admission.mail_templates.checklist import (
    ADMISSION_EMAIL_SIC_REFUSAL,
    ADMISSION_EMAIL_SIC_APPROVAL,
    ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CHECKERS,
    ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CANDIDATE,
)
from admission.templatetags.admission import authentication_css_class, bg_class_by_checklist_experience
from admission.utils import (
    get_portal_admission_list_url,
    get_backoffice_admission_url,
    get_portal_admission_url,
    get_access_titles_names,
)
from admission.views.common.detail_tabs.comments import COMMENT_TAG_SIC, COMMENT_TAG_FAC
from admission.views.doctorate.mixins import LoadDossierViewMixin, AdmissionFormMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.person import Person
from base.utils.htmx import HtmxPermissionRequiredMixin
from epc.models.email_fonction_programme import EmailFonctionProgramme
from epc.models.enums.condition_acces import ConditionAcces
from epc.models.enums.type_email_fonction_programme import TypeEmailFonctionProgramme
from infrastructure.messages_bus import message_bus_instance
from osis_common.ddd.interface import BusinessException
from osis_document.api.utils import get_remote_metadata, get_remote_token
from osis_document.utils import get_file_url
from osis_profile.models import EducationalExperience
from osis_role.templatetags.osis_role import has_perm

__all__ = [
    'ChecklistView',
    'ChangeStatusView',
    'ChangeExtraView',
    'SaveCommentView',
    'ApplicationFeesView',
    'ChoixFormationFormView',
    'ChoixFormationDetailView',
    'FacultyDecisionView',
    'FacultyDecisionSendToFacultyView',
    'FacultyRefusalDecisionView',
    'FacultyApprovalDecisionView',
    'FacultyDecisionSendToSicView',
    'PastExperiencesStatusView',
    'PastExperiencesAdmissionRequirementView',
    'PastExperiencesAccessTitleEquivalencyView',
    'PastExperiencesAccessTitleView',
    'FinancabiliteChangeStatusView',
    'FinancabiliteApprovalView',
    'FinancabiliteComputeRuleView',
    'SinglePastExperienceChangeStatusView',
    'SinglePastExperienceChangeAuthenticationView',
    'SicApprovalDecisionView',
    'SicApprovalFinalDecisionView',
    'SicRefusalDecisionView',
    'SicRefusalFinalDecisionView',
    'SicDecisionDispensationView',
    'SicDecisionChangeStatusView',
    'SicDecisionPdfPreviewView',
]


__namespace__ = False


TABS_WITH_SIC_AND_FAC_COMMENTS = {'decision_facultaire'}


class CheckListDefaultContextMixin(LoadDossierViewMixin):
    extra_context = {
        'checklist_tabs': {
            'assimilation': _("Belgian student status"),
            'financabilite': _("Financeability"),
            'frais_dossier': _("Application fee"),
            'choix_formation': _("Course choice"),
            'parcours_anterieur': _("Previous experience"),
            'donnees_personnelles': _("Personal data"),
            'specificites_formation': _("Training specificities"),
            'decision_facultaire': _("Decision of the faculty"),
            'decision_sic': _("Decision of SIC"),
        },
        'hide_files': True,
        'condition_acces_enum': ConditionAcces,
        'checker_email_address': MAIL_VERIFICATEUR_CURSUS,
    }

    @cached_property
    def can_update_checklist_tab(self):
        return has_perm('admission.change_checklist', user=self.request.user, obj=self.admission)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        checklist_additional_icons = {}

        # A SIC user has an additional icon for the decision of the faculty if a fac manager wrote a comment
        if self.is_sic:
            has_comment = (
                CommentEntry.objects.filter(
                    object_uuid=self.admission_uuid,
                    tags__contains=['decision_facultaire', COMMENT_TAG_FAC],
                )
                .exclude(content='')
                .exists()
            )
            if has_comment:
                checklist_additional_icons['decision_facultaire'] = 'fa-regular fa-comment'

        context['checklist_additional_icons'] = checklist_additional_icons
        context['can_update_checklist_tab'] = self.can_update_checklist_tab
        context['can_change_payment'] = self.request.user.has_perm('admission.change_payment', self.admission)
        context['can_change_faculty_decision'] = self.request.user.has_perm(
            'admission.checklist_change_faculty_decision',
            self.admission,
        )
        context['bg_classes'] = {}
        return context


def get_email(template_identifier, language, proposition_dto: PropositionGestionnaireDTO):
    mail_template = MailTemplate.objects.get(
        identifier=template_identifier,
        language=language,
    )

    # Needed to get the complete reference
    with translation.override(language):
        tokens = {
            'admission_reference': proposition_dto.reference,
            'candidate_first_name': proposition_dto.prenom_candidat,
            'candidate_last_name': proposition_dto.nom_candidat,
            'candidate_nationality_country': {
                settings.LANGUAGE_CODE_FR: proposition_dto.nationalite_candidat_fr,
                settings.LANGUAGE_CODE_EN: proposition_dto.nationalite_candidat_en,
            }[language],
            'training_acronym': proposition_dto.formation.sigle,
            'training_title': {
                settings.LANGUAGE_CODE_FR: proposition_dto.formation.intitule_fr,
                settings.LANGUAGE_CODE_EN: proposition_dto.formation.intitule_en,
            }[language],
            'admissions_link_front': get_portal_admission_list_url(),
            'admission_link_front': get_portal_admission_url('general-education', str(proposition_dto.uuid)),
            'admission_link_back': get_backoffice_admission_url('general-education', str(proposition_dto.uuid)),
            'training_campus': proposition_dto.formation.campus.nom,
        }

        return (
            mail_template.render_subject(tokens),
            mail_template.body_as_html(tokens),
        )


class RequestApplicationFeesContextDataMixin(CheckListDefaultContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        payments = message_bus_instance.invoke(
            RecupererListePaiementsPropositionQuery(uuid_proposition=self.admission_uuid)
        )

        context['payments'] = payments
        context['payment_status_translations'] = PaymentStatus.translated_names()
        context['payment_method_translations'] = PaymentMethod.translated_names()

        context['last_request'] = (
            HistoryEntry.objects.filter(
                object_uuid=self.admission_uuid,
                tags__contains=['proposition', 'application-fees-payment', 'request'],
            )
            .order_by('-created')
            .first()
        )

        context['application_fees_amount'] = MONTANT_FRAIS_DOSSIER

        # Checklist specificities
        context['fees_already_payed'] = bool(
            self.admission.checklist.get('current')
            and self.admission.checklist['current']['frais_dossier']['statut']
            == ChoixStatutChecklist.SYST_REUSSITE.name
        )

        email_content = get_email(
            template_identifier=ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL,
            language=self.proposition.langue_contact_candidat,
            proposition_dto=self.proposition,
        )

        context['request_message_subject'] = email_content[0]
        context['request_message_body'] = email_content[1]

        return context


class PastExperiencesMixin:
    @cached_property
    def past_experiences_admission_requirement_form(self):
        return PastExperiencesAdmissionRequirementForm(instance=self.admission, data=self.request.POST or None)

    @cached_property
    def past_experiences_admission_access_title_equivalency_form(self):
        return PastExperiencesAdmissionAccessTitleForm(instance=self.admission, data=self.request.POST or None)

    @property
    def access_title_url(self):
        return resolve_url(
            f'{self.base_namespace}:past-experiences-access-title',
            uuid=self.kwargs['uuid'],
        )


# Fac decision
class FacultyDecisionMixin(CheckListDefaultContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['in_sic_statuses'] = self.admission.status in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_ETENDUS
        context['in_fac_statuses'] = self.admission.status in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC_ETENDUS
        context['sic_statuses_for_transfer'] = ChoixStatutPropositionGenerale.get_specific_values(
            STATUTS_PROPOSITION_GENERALE_ENVOYABLE_EN_FAC_POUR_DECISION
        )
        context['fac_statuses_for_transfer'] = ChoixStatutPropositionGenerale.get_specific_values(
            STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC
        )
        context['is_fac'] = self.is_fac
        context['is_sic'] = self.is_sic
        context['fac_decision_send_to_fac_history_entry'] = (
            HistoryEntry.objects.filter(
                object_uuid=self.admission_uuid,
                tags__contains=['proposition', 'fac-decision', 'send-to-fac'],
            )
            .order_by('-created')
            .first()
        )
        context['fac_decision_refusal_form'] = self.fac_decision_refusal_form
        context['fac_decision_approval_form'] = self.fac_decision_approval_form
        context['program_faculty_email'] = self.program_faculty_email.email if self.program_faculty_email else None

        return context

    @cached_property
    def program_faculty_email(self):
        return EmailFonctionProgramme.objects.filter(
            type=TypeEmailFonctionProgramme.DESTINATAIRE_ADMISSION.name,
            programme=self.admission.training.education_group,
            premiere_annee=bool(
                self.proposition.poursuite_de_cycle_a_specifier
                and self.proposition.poursuite_de_cycle != PoursuiteDeCycle.YES.name,
            ),
        ).first()

    @cached_property
    def fac_decision_refusal_form(self):
        form_kwargs = {
            'prefix': 'fac-decision-refusal',
        }
        if self.request.method == 'POST':
            form_kwargs['data'] = self.request.POST
        else:
            form_kwargs['initial'] = {
                'reasons': [reason.uuid for reason in self.admission.refusal_reasons.all()]
                + self.admission.other_refusal_reasons,
            }

        return FacDecisionRefusalForm(**form_kwargs)

    @property
    def additional_approval_conditions_for_diploma(self):
        experiences: QuerySet[EducationalExperience] = EducationalExperience.objects.select_related('program').filter(
            person=self.admission.candidate
        )
        with translation.override(self.admission.candidate.language):
            return [
                gettext('Graduation of {program_name}').format(
                    program_name=experience.program.title if experience.program else experience.education_name
                )
                for experience in experiences
            ]

    @cached_property
    def fac_decision_approval_form(self):
        return FacDecisionApprovalForm(
            academic_year=self.admission.determined_academic_year.year,
            instance=self.admission if self.request.method != 'POST' else None,
            data=self.request.POST if self.request.method == 'POST' else None,
            prefix='fac-decision-approval',
            additional_approval_conditions_for_diploma=self.additional_approval_conditions_for_diploma,
            current_training_uuid=str(self.admission.training.uuid),
        )


class FacultyDecisionView(
    AdmissionFormMixin,
    FacultyDecisionMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'fac-decision-status'
    urlpatterns = {'fac-decision-change-status': 'fac-decision/status-change/<str:status>'}
    permission_required = 'admission.checklist_change_faculty_decision'
    template_name = 'admission/general_education/includes/checklist/fac_decision.html'
    htmx_template_name = 'admission/general_education/includes/checklist/fac_decision.html'
    form_class = Form

    def form_valid(self, form):
        admission = self.get_permission_object()

        extra = {}
        if 'decision' in self.request.GET:
            extra['decision'] = self.request.GET['decision']

        change_admission_status(
            tab='decision_facultaire',
            admission_status=self.kwargs['status'],
            extra=extra,
            admission=admission,
            replace_extra=True,
            author=self.request.user.person,
        )

        return super().form_valid(form)


class FacultyDecisionSendToFacultyView(
    AdmissionFormMixin,
    FacultyDecisionMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'faculty-decision-send-to-faculty'
    urlpatterns = {'fac-decision-send-to-faculty': 'fac-decision/send-to-faculty'}
    permission_required = 'admission.checklist_faculty_decision_transfer_to_fac'
    template_name = 'admission/general_education/includes/checklist/fac_decision.html'
    htmx_template_name = 'admission/general_education/includes/checklist/fac_decision.html'
    form_class = Form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                EnvoyerPropositionAFacLorsDeLaDecisionFacultaireCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)
        self.htmx_refresh = True
        return super().form_valid(form)


class FacultyDecisionSendToSicView(
    AdmissionFormMixin,
    FacultyDecisionMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'faculty-decision-send-to-sic'
    urlpatterns = {'fac-decision-send-to-sic': 'fac-decision/send-to-sic'}
    template_name = 'admission/general_education/includes/checklist/fac_decision.html'
    htmx_template_name = 'admission/general_education/includes/checklist/fac_decision.html'
    form_class = Form

    def get_permission_required(self):
        return (
            ('admission.checklist_faculty_decision_transfer_to_sic_with_decision',)
            if (self.request.GET.get('approval') or self.request.GET.get('refusal')) and self.is_fac
            else ('admission.checklist_faculty_decision_transfer_to_sic_without_decision',)
        )

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                ApprouverPropositionParFaculteCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
                if self.request.GET.get('approval') and self.is_fac
                else RefuserPropositionParFaculteCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
                if self.request.GET.get('refusal') and self.is_fac
                else EnvoyerPropositionAuSicLorsDeLaDecisionFacultaireCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    envoi_par_fac=self.is_fac,
                )
            )

        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        self.htmx_refresh = True

        return super().form_valid(form)


class FacultyRefusalDecisionView(
    FacultyDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'fac-decision-refusal'
    urlpatterns = {'fac-decision-refusal': 'fac-decision/fac-decision-refusal'}
    template_name = 'admission/general_education/includes/checklist/fac_decision_refusal_form.html'
    htmx_template_name = 'admission/general_education/includes/checklist/fac_decision_refusal_form.html'

    def get_permission_required(self):
        return (
            (
                'admission.checklist_faculty_decision_transfer_to_sic_with_decision'
                if 'save_transfer' in self.request.POST
                else 'admission.checklist_change_faculty_decision'
            ),
        )

    def get_form(self, form_class=None):
        return self.fac_decision_refusal_form

    def form_valid(self, form):
        base_params = {
            'uuid_proposition': self.admission_uuid,
            'uuids_motifs': form.cleaned_data['reasons'],
            'autres_motifs': form.cleaned_data['other_reasons'],
            'gestionnaire': self.request.user.person.global_id,
        }

        try:
            message_bus_instance.invoke(SpecifierMotifsRefusPropositionParFaculteCommand(**base_params))
            if 'save-transfer' in self.request.POST:
                message_bus_instance.invoke(
                    RefuserPropositionParFaculteCommand(
                        uuid_proposition=self.admission_uuid,
                        gestionnaire=self.request.user.person.global_id,
                    )
                )
                self.htmx_refresh = True
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        return super().form_valid(form)


class FacultyApprovalDecisionView(
    FacultyDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'fac-decision-approval'
    urlpatterns = {'fac-decision-approval': 'fac-decision/fac-decision-approval'}
    template_name = 'admission/general_education/includes/checklist/fac_decision_approval_form.html'
    htmx_template_name = 'admission/general_education/includes/checklist/fac_decision_approval_form.html'

    def get_permission_required(self):
        return (
            (
                'admission.checklist_faculty_decision_transfer_to_sic_with_decision'
                if 'save_transfer' in self.request.POST
                else 'admission.checklist_change_faculty_decision'
            ),
        )

    def get_form(self, form_class=None):
        return self.fac_decision_approval_form

    def form_valid(self, form):
        base_params = {
            'uuid_proposition': self.admission_uuid,
            'sigle_autre_formation': form.cleaned_data['other_training_accepted_by_fac'].acronym
            if form.cleaned_data['other_training_accepted_by_fac']
            else '',
            'avec_conditions_complementaires': form.cleaned_data['with_additional_approval_conditions'],
            'uuids_conditions_complementaires_existantes': form.cleaned_data['additional_approval_conditions'],
            'conditions_complementaires_libres': form.cleaned_data['free_additional_approval_conditions'],
            'avec_complements_formation': form.cleaned_data['with_prerequisite_courses'],
            'uuids_complements_formation': form.cleaned_data['prerequisite_courses'],
            'commentaire_complements_formation': form.cleaned_data['prerequisite_courses_fac_comment'],
            'nombre_annees_prevoir_programme': form.cleaned_data['program_planned_years_number'],
            'nom_personne_contact_programme_annuel': form.cleaned_data['annual_program_contact_person_name'],
            'email_personne_contact_programme_annuel': form.cleaned_data['annual_program_contact_person_email'],
            'commentaire_programme_conjoint': form.cleaned_data['join_program_fac_comment'],
            'gestionnaire': self.request.user.person.global_id,
        }
        try:
            message_bus_instance.invoke(SpecifierInformationsAcceptationPropositionParFaculteCommand(**base_params))
            if 'save-transfer' in self.request.POST:
                message_bus_instance.invoke(
                    ApprouverPropositionParFaculteCommand(
                        uuid_proposition=self.admission_uuid,
                        gestionnaire=self.request.user.person.global_id,
                    )
                )
                self.htmx_refresh = True
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        return super().form_valid(form)


class SicDecisionMixin(CheckListDefaultContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sic_decision_refusal_form'] = self.sic_decision_refusal_form
        context['sic_decision_approval_form'] = self.sic_decision_approval_form
        context['sic_decision_refusal_final_form'] = self.sic_decision_refusal_final_form
        context['sic_decision_approval_final_form'] = self.sic_decision_approval_final_form

        # Get information about mail sent if any
        token = None
        if self.proposition.certificat_refus_sic:
            token = get_remote_token(self.proposition.certificat_refus_sic[0])
        elif self.proposition.certificat_approbation_sic:
            token = get_remote_token(self.proposition.certificat_approbation_sic[0])
        if token is not None:
            metadata = get_remote_metadata(token)
            context['sic_decision_sent_at'] = metadata['uploaded_at']
            try:
                context['sic_decision_sent_by'] = Person.objects.get(global_id=metadata['author'])
            except Person.DoesNotExist:
                context['sic_decision_sent_by'] = metadata['author']

        context['sic_decision_dispensation_form'] = SicDecisionDerogationForm(
            initial={
                'dispensation_needed': self.admission.dispensation_needed,
            },
        )
        context['requested_documents'] = {
            document.identifiant: {
                'reason': self.proposition.documents_demandes.get(document.identifiant, {}).get('reason', ''),
                'label': document.libelle_langue_candidat,
                'tab_label': document.nom_onglet,
                'candidate_language_tab_label': document.nom_onglet_langue_candidat,
                'tab': document.onglet,
            }
            for document in self.sic_decision_approval_form_requestable_documents
        }

        if self.request.htmx:
            comment = CommentEntry.objects.filter(object_uuid=self.admission_uuid, tags=['decision_sic']).first()
            comment_derogation = CommentEntry.objects.filter(
                object_uuid=self.admission_uuid, tags=['decision_sic', 'derogation']
            ).first()
            context['comment_forms'] = {
                'decision_sic': CommentForm(
                    comment=comment,
                    form_url=resolve_url(
                        f'{self.base_namespace}:save-comment', uuid=self.admission_uuid, tab='decision_sic'
                    ),
                    prefix='decision_sic__derogation',
                ),
                'decision_sic__derogation': CommentForm(
                    comment=comment_derogation,
                    form_url=resolve_url(
                        f'{self.base_namespace}:save-comment', uuid=self.admission_uuid, tab='decision_sic__derogation'
                    ),
                    prefix='decision_sic__derogation',
                    label=_('Comment about dispensation'),
                ),
            }
        return context

    @cached_property
    def sic_decision_refusal_form(self):
        form_kwargs = {
            'prefix': 'sic-decision-refusal',
        }
        if self.request.method == 'POST' and 'sic-decision-refusal-refusal_type' in self.request.POST:
            form_kwargs['data'] = self.request.POST
        else:
            form_kwargs['initial'] = {
                'reasons': [reason.uuid for reason in self.admission.refusal_reasons.all()]
                + self.admission.other_refusal_reasons,
            }

        return SicDecisionRefusalForm(**form_kwargs)

    @property
    def additional_approval_conditions_for_diploma(self):
        experiences: QuerySet[EducationalExperience] = EducationalExperience.objects.select_related('program').filter(
            person=self.admission.candidate
        )
        with translation.override(self.admission.candidate.language):
            return [
                gettext('Graduation of {program_name}').format(
                    program_name=experience.program.title if experience.program else experience.education_name
                )
                for experience in experiences
            ]

    @cached_property
    def sic_decision_approval_form_requestable_documents(self):
        documents = message_bus_instance.invoke(
            RecupererDocumentsPropositionQuery(
                uuid_proposition=self.admission_uuid,
            )
        )
        return [
            document
            for document in documents
            if document.statut == StatutEmplacementDocument.A_RECLAMER.name
            and document.type in EMPLACEMENTS_DOCUMENTS_RECLAMABLES
        ]

    @cached_property
    def sic_decision_approval_form(self):
        return SicDecisionApprovalForm(
            academic_year=self.admission.determined_academic_year.year,
            instance=self.admission,
            data=self.request.POST
            if self.request.method == 'POST'
            and 'sic-decision-approval-with_additional_approval_conditions' in self.request.POST
            else None,
            prefix='sic-decision-approval',
            additional_approval_conditions_for_diploma=self.additional_approval_conditions_for_diploma,
            documents=self.sic_decision_approval_form_requestable_documents,
            candidate_nationality_is_no_ue_5=self.proposition.candidat_a_nationalite_hors_ue_5,
        )

    @cached_property
    def sic_decision_refusal_final_form(self):
        tokens = {
            "admission_reference": self.proposition.reference,
            "candidate": (
                f"{self.proposition.profil_soumis_candidat.prenom} " f"{self.proposition.profil_soumis_candidat.nom}"
            )
            if self.proposition.profil_soumis_candidat
            else "",
            "academic_year": f"{self.proposition.formation.annee}-{self.proposition.formation.annee + 1}",
            "admission_training": f"{self.proposition.formation.sigle} / {self.proposition.formation.intitule}",
        }

        try:
            mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
                ADMISSION_EMAIL_SIC_REFUSAL,
                settings.LANGUAGE_CODE_FR,
            )

            subject = mail_template.render_subject(tokens=tokens)
            body = mail_template.body_as_html(tokens=tokens)
        except EmptyMailTemplateContent:
            subject = ''
            body = ''

        return SicDecisionFinalRefusalForm(
            data=self.request.POST
            if self.request.method == 'POST' and 'sic-decision-refusal-final-subject' in self.request.POST
            else None,
            prefix='sic-decision-refusal-final',
            initial={
                'subject': subject,
                'body': body,
            },
        )

    @cached_property
    def sic_decision_approval_final_form(self):
        tokens = {
            "admission_reference": self.proposition.reference,
            "candidate": (
                f"{self.proposition.profil_soumis_candidat.prenom} " f"{self.proposition.profil_soumis_candidat.nom}"
            )
            if self.proposition.profil_soumis_candidat
            else "",
            "academic_year": f"{self.proposition.formation.annee}-{self.proposition.formation.annee + 1}",
            "academic_year_start_date": date_format(self.proposition.formation.date_debut),
            "admission_email": self.proposition.formation.campus_inscription.email,
            "admission_training": f"{self.proposition.formation.sigle} / {self.proposition.formation.intitule}",
        }
        if get_language() == settings.LANGUAGE_CODE_FR:
            if self.proposition.genre_candidat == "H":
                tokens['greetings'] = "Cher"
            elif self.proposition.genre_candidat == "F":
                tokens['greetings'] = "Chère"
            else:
                tokens['greetings'] = "Cher·ère"

        try:
            mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
                ADMISSION_EMAIL_SIC_APPROVAL,
                settings.LANGUAGE_CODE_FR,
            )

            subject = mail_template.render_subject(tokens=tokens)
            body = mail_template.body_as_html(tokens=tokens)
        except EmptyMailTemplateContent:
            subject = ''
            body = ''

        is_inscription = self.admission.type_demande == TypeDemande.INSCRIPTION.name
        return SicDecisionFinalApprovalForm(
            data=self.request.POST
            if self.request.method == 'POST'
            and is_inscription
            or ('sic-decision-approval-final-subject' in self.request.POST)
            else None,
            prefix='sic-decision-approval-final',
            initial={
                'subject': subject,
                'body': body,
            },
            is_inscription=is_inscription,
        )


class SicApprovalDecisionView(
    SicDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'sic-decision-approval'
    urlpatterns = {'sic-decision-approval': 'sic-decision/sic-decision-approval'}
    template_name = 'admission/general_education/includes/checklist/sic_decision_approval_form.html'
    htmx_template_name = 'admission/general_education/includes/checklist/sic_decision_approval_form.html'
    permission_required = 'admission.checklist_change_sic_decision'

    def get_form(self, form_class=None):
        return self.sic_decision_approval_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                SpecifierInformationsAcceptationPropositionParSicCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    avec_conditions_complementaires=form.cleaned_data['with_additional_approval_conditions'],
                    uuids_conditions_complementaires_existantes=form.cleaned_data['additional_approval_conditions'],
                    conditions_complementaires_libres=form.cleaned_data['free_additional_approval_conditions'],
                    avec_complements_formation=form.cleaned_data['with_prerequisite_courses'],
                    uuids_complements_formation=form.cleaned_data['prerequisite_courses'],
                    commentaire_complements_formation=form.cleaned_data['prerequisite_courses_fac_comment'],
                    nombre_annees_prevoir_programme=form.cleaned_data['program_planned_years_number'],
                    nom_personne_contact_programme_annuel=form.cleaned_data['annual_program_contact_person_name'],
                    email_personne_contact_programme_annuel=form.cleaned_data['annual_program_contact_person_email'],
                    droits_inscription_montant=form.cleaned_data['tuition_fees_amount'],
                    droits_inscription_montant_autre=form.cleaned_data.get('tuition_fees_amount_other', None),
                    dispense_ou_droits_majores=form.cleaned_data['tuition_fees_dispensation'],
                    tarif_particulier=form.cleaned_data.get('particular_cost', ''),
                    refacturation_ou_tiers_payant=form.cleaned_data.get('rebilling_or_third_party_payer', ''),
                    annee_de_premiere_inscription_et_statut=form.cleaned_data.get(
                        'first_year_inscription_and_status', ''
                    ),
                    est_mobilite=form.cleaned_data.get('is_mobility', ''),
                    nombre_de_mois_de_mobilite=form.cleaned_data.get('mobility_months_amount', ''),
                    doit_se_presenter_en_sic=form.cleaned_data.get('must_report_to_sic', False),
                    communication_au_candidat=form.cleaned_data['communication_to_the_candidate'],
                    doit_fournir_visa_etudes=form.cleaned_data.get('must_provide_student_visa_d', False),
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        return super().form_valid(form)


class SicRefusalDecisionView(
    SicDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'sic-decision-refusal'
    urlpatterns = {'sic-decision-refusal': 'sic-decision/sic-decision-refusal'}
    template_name = 'admission/general_education/includes/checklist/sic_decision_refusal_form.html'
    htmx_template_name = 'admission/general_education/includes/checklist/sic_decision_refusal_form.html'
    permission_required = 'admission.checklist_change_sic_decision'

    def get_form(self, form_class=None):
        return self.sic_decision_refusal_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                SpecifierMotifsRefusPropositionParSicCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    type_de_refus=form.cleaned_data['refusal_type'],
                    uuids_motifs=form.cleaned_data['reasons'],
                    autres_motifs=form.cleaned_data['other_reasons'],
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        return super().form_valid(form)


class SicRefusalFinalDecisionView(
    SicDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'sic-decision-refusal-final'
    urlpatterns = {'sic-decision-refusal-final': 'sic-decision/sic-decision-refusal-final'}
    template_name = 'admission/general_education/includes/checklist/sic_decision_refusal_final_form.html'
    htmx_template_name = 'admission/general_education/includes/checklist/sic_decision_refusal_final_form.html'
    permission_required = 'admission.checklist_change_sic_decision'

    def get_form(self, form_class=None):
        return self.sic_decision_refusal_final_form

    def form_valid(self, form):
        try:
            if self.proposition.type == TypeDemande.ADMISSION.name:
                message_bus_instance.invoke(
                    RefuserAdmissionParSicCommand(
                        uuid_proposition=self.admission_uuid,
                        objet_message=form.cleaned_data['subject'],
                        corps_message=form.cleaned_data['body'],
                        auteur=self.request.user.person.global_id,
                    )
                )
            else:
                message_bus_instance.invoke(
                    RefuserInscriptionParSicCommand(
                        uuid_proposition=self.admission_uuid,
                        objet_message=form.cleaned_data['subject'],
                        corps_message=form.cleaned_data['body'],
                        auteur=self.request.user.person.global_id,
                    )
                )
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        # Invalidate cached_property for status update
        del self.proposition
        return super().form_valid(form)


class SicApprovalFinalDecisionView(
    SicDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'sic-decision-approval-final'
    urlpatterns = {'sic-decision-approval-final': 'sic-decision/sic-decision-approval-final'}
    template_name = 'admission/general_education/includes/checklist/sic_decision_approval_final_form.html'
    htmx_template_name = 'admission/general_education/includes/checklist/sic_decision_approval_final_form.html'
    permission_required = 'admission.checklist_change_sic_decision'

    def get_form(self, form_class=None):
        return self.sic_decision_approval_final_form

    def form_valid(self, form):
        try:
            if self.proposition.type == TypeDemande.ADMISSION.name:
                message_bus_instance.invoke(
                    ApprouverAdmissionParSicCommand(
                        uuid_proposition=self.admission_uuid,
                        objet_message=form.cleaned_data['subject'],
                        corps_message=form.cleaned_data['body'],
                        auteur=self.request.user.person.global_id,
                    )
                )
            else:
                message_bus_instance.invoke(
                    ApprouverInscriptionParSicCommand(
                        uuid_proposition=self.admission_uuid,
                        auteur=self.request.user.person.global_id,
                    )
                )
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        # Invalidate cached_property for status update
        del self.proposition
        return super().form_valid(form)


class SicDecisionDispensationView(AdmissionFormMixin, HtmxPermissionRequiredMixin, FormView):
    name = 'sic-decision-dispensation'
    urlpatterns = {'sic-decision-dispensation': 'sic-decision/dispensation'}
    permission_required = 'admission.checklist_change_sic_decision'
    form_class = SicDecisionDerogationForm

    def render_to_response(self, context, **response_kwargs):
        return HttpResponse()

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                SpecifierBesoinDeDerogationSicCommand(
                    uuid_proposition=self.admission_uuid,
                    besoin_de_derogation=form.cleaned_data['dispensation_needed'],
                    gestionnaire=self.request.user.person.global_id,
                )
            )
        except BusinessException as exception:
            self.message_on_failure = exception.message
            return super().form_invalid(form)

        return super().form_valid(form)


class SicDecisionChangeStatusView(HtmxPermissionRequiredMixin, SicDecisionMixin, TemplateView):
    urlpatterns = {'sic-decision-change-status': 'sic-decision-change-checklist-status/<str:status>'}
    template_name = 'admission/general_education/includes/checklist/sic_decision.html'
    permission_required = 'admission.checklist_change_sic_decision'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        admission = self.get_permission_object()

        try:
            status, extra = self.kwargs['status'].split('-')
            if status == 'GEST_BLOCAGE':
                extra = {'blocage': extra}
            elif status == 'GEST_EN_COURS':
                extra = {'en_cours': extra}
        except ValueError:
            status = self.kwargs['status']
            extra = {}

        if status == 'GEST_BLOCAGE' and extra == {'blocage': 'closed'}:
            global_status = ChoixStatutPropositionGenerale.CLOTUREE.name
        else:
            global_status = ChoixStatutPropositionGenerale.CONFIRMEE.name

        admission_status_has_changed = admission.status != global_status

        change_admission_status(
            tab='decision_sic',
            admission_status=status,
            extra=extra,
            admission=admission,
            global_status=global_status,
            author=self.request.user.person,
        )

        if admission_status_has_changed:
            add_history_entry(
                admission.uuid,
                'Le statut de la proposition a évolué au cours du processus de décision SIC.',
                'The status of the proposal has changed during the SIC decision process.',
                '{first_name} {last_name}'.format(
                    first_name=self.request.user.person.first_name,
                    last_name=self.request.user.person.last_name,
                ),
                tags=['proposition', 'sic-decision', 'status-changed'],
            )

        return self.render_to_response(self.get_context_data())


class SicDecisionPdfPreviewView(LoadDossierViewMixin, RedirectView):
    urlpatterns = {'sic-decision-pdf-preview': 'sic-decision-pdf-preview/<str:pdf>'}
    permission_required = 'admission.checklist_change_sic_decision'

    def get(self, request, *args, **kwargs):
        try:
            token = message_bus_instance.invoke(
                RecupererPdfTemporaireDecisionSicQuery(
                    uuid_proposition=self.admission_uuid,
                    pdf=self.kwargs['pdf'],
                    auteur=request.user.person.global_id,
                )
            )
        except BusinessException as exception:
            return HttpResponseBadRequest(exception.message)

        self.url = get_file_url(token)
        return super().get(request, *args, **kwargs)


class ChecklistView(
    PastExperiencesMixin,
    FacultyDecisionMixin,
    SicDecisionMixin,
    RequestApplicationFeesContextDataMixin,
    TemplateView,
):
    urlpatterns = 'checklist'
    template_name = "admission/general_education/checklist.html"
    permission_required = 'admission.view_checklist'

    @classmethod
    def checklist_documents_by_tab(cls, specific_questions: List[QuestionSpecifiqueDTO]) -> Dict[str, Set[str]]:
        assimilation_documents = {
            'CARTE_IDENTITE',
            'PASSEPORT',
        }

        for document in DocumentsAssimilation:
            assimilation_documents.add(document)

        documents_by_tab = {
            'assimilation': assimilation_documents,
            'financabilite': {
                'DIPLOME_EQUIVALENCE',
                'DIPLOME_BELGE_CERTIFICAT_INSCRIPTION',
                'DIPLOME_ETRANGER_CERTIFICAT_INSCRIPTION',
                'DIPLOME_ETRANGER_TRADUCTION_CERTIFICAT_INSCRIPTION',
                'CURRICULUM',
            },
            'frais_dossier': assimilation_documents,
            'choix_formation': {
                'ATTESTATION_INSCRIPTION_REGULIERE',
                'FORMULAIRE_MODIFICATION_INSCRIPTION',
            },
            'parcours_anterieur': {
                'ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT',
                'DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_UE',
                'DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_HORS_UE',
                'DIPLOME_ETRANGER_PREUVE_DECISION_EQUIVALENCE',
                'DIPLOME_EQUIVALENCE',
                'CURRICULUM',
            },
            'donnees_personnelles': assimilation_documents,
            'specificites_formation': {
                'ADDITIONAL_DOCUMENTS',
            },
            'decision_facultaire': {
                'ATTESTATION_ACCORD_FACULTAIRE',
                'ATTESTATION_REFUS_FACULTAIRE',
            },
            f'parcours_anterieur__{OngletsDemande.ETUDES_SECONDAIRES.name}': set(DocumentsEtudesSecondaires.keys()),
            'decision_sic': {
                'ATTESTATION_ACCORD_SIC',
                'ATTESTATION_ACCORD_ANNEXE_SIC',
                'ATTESTATION_REFUS_SIC',
            },
        }

        # Add documents from the specific questions
        checklist_target_tab_by_specific_question_tab = {
            Onglets.CURRICULUM.name: 'parcours_anterieur',
            Onglets.ETUDES_SECONDAIRES.name: f'parcours_anterieur__{OngletsDemande.ETUDES_SECONDAIRES.name}',
            Onglets.INFORMATIONS_ADDITIONNELLES.name: 'specificites_formation',
        }

        for specific_question in specific_questions:
            if (
                specific_question.type == TypeItemFormulaire.DOCUMENT.name
                and specific_question.onglet in checklist_target_tab_by_specific_question_tab
            ):
                documents_by_tab[checklist_target_tab_by_specific_question_tab[specific_question.onglet]].add(
                    specific_question.uuid
                )

        return documents_by_tab

    def get_template_names(self):
        if self.request.htmx:
            return ["admission/general_education/checklist_menu.html"]
        return ["admission/general_education/checklist.html"]

    def get_context_data(self, **kwargs):
        from infrastructure.messages_bus import message_bus_instance

        context = super().get_context_data(**kwargs)
        if not self.request.htmx:
            # Retrieve data related to the proposition
            command_result: ResumeEtEmplacementsDocumentsPropositionDTO = message_bus_instance.invoke(
                RecupererResumeEtEmplacementsDocumentsNonLibresPropositionQuery(uuid_proposition=self.admission_uuid),
            )

            context['resume_proposition'] = command_result.resume

            specific_questions: List[QuestionSpecifiqueDTO] = message_bus_instance.invoke(
                RecupererQuestionsSpecifiquesQuery(
                    uuid_proposition=self.admission_uuid,
                    onglets=[
                        Onglets.INFORMATIONS_ADDITIONNELLES.name,
                        Onglets.ETUDES_SECONDAIRES.name,
                        Onglets.CURRICULUM.name,
                    ],
                )
            )

            context['specific_questions_by_tab'] = get_dynamic_questions_by_tab(specific_questions)

            etats = [
                status
                for status in ChoixStatutPropositionGenerale.get_names()
                if status
                not in {
                    ChoixStatutPropositionGenerale.EN_BROUILLON,
                    ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE,
                    ChoixStatutPropositionGenerale.ANNULEE,
                }
            ]
            context['autres_demandes'] = [
                demande
                for demande in message_bus_instance.invoke(
                    ListerToutesDemandesQuery(
                        annee_academique=self.admission.determined_academic_year.year,
                        matricule_candidat=self.admission.candidate.global_id,
                        etats=etats,
                    )
                )
                if demande.uuid != self.admission_uuid
            ]

            # Initialize forms
            tab_names = list(self.extra_context['checklist_tabs'].keys())

            comments = {
                ('__'.join(c.tags)): c
                for c in CommentEntry.objects.filter(object_uuid=self.admission_uuid, tags__overlap=tab_names)
            }

            for tab in TABS_WITH_SIC_AND_FAC_COMMENTS:
                tab_names.remove(tab)
                tab_names += [f'{tab}__{COMMENT_TAG_SIC}', f'{tab}__{COMMENT_TAG_FAC}']
            tab_names.append('decision_sic__derogation')

            comments_labels = {
                'decision_sic__derogation': _('Comment about dispensation'),
            }

            context['comment_forms'] = {
                tab_name: CommentForm(
                    comment=comments.get(tab_name, None),
                    form_url=resolve_url(f'{self.base_namespace}:save-comment', uuid=self.admission_uuid, tab=tab_name),
                    prefix=tab_name,
                    label=comments_labels.get(tab_name, None),
                )
                for tab_name in tab_names
            }
            context['assimilation_form'] = AssimilationForm(
                initial=self.admission.checklist.get('current', {}).get('assimilation', {}).get('extra'),
                form_url=resolve_url(
                    f'{self.base_namespace}:change-checklist-extra',
                    uuid=self.admission_uuid,
                    tab='assimilation',
                ),
            )

            context['financabilite_approval_form'] = FinancabiliteApprovalForm(
                instance=self.admission,
                prefix='financabilite',
            )

            # Documents
            admission_documents = command_result.emplacements_documents

            documents_by_tab = self.checklist_documents_by_tab(specific_questions=specific_questions)

            context['documents'] = {
                tab_name: sorted(
                    [
                        admission_document
                        for admission_document in admission_documents
                        if admission_document.identifiant.split('.')[-1] in tab_documents
                    ],
                    key=lambda doc: doc.libelle,
                )
                for tab_name, tab_documents in documents_by_tab.items()
            }

            # Experiences
            experiences = self._get_experiences(command_result.resume)
            experiences_by_uuid = self._get_experiences_by_uuid(command_result.resume)
            context['experiences'] = experiences
            context['experiences_by_uuid'] = experiences_by_uuid

            # Access titles
            context['access_title_url'] = self.access_title_url
            context['access_titles'] = self.selectable_access_titles
            context['selected_access_titles_names'] = get_access_titles_names(
                access_titles=self.selectable_access_titles,
                curriculum_dto=command_result.resume.curriculum,
                etudes_secondaires_dto=command_result.resume.etudes_secondaires,
            )

            context['past_experiences_admission_requirement_form'] = self.past_experiences_admission_requirement_form
            context[
                'past_experiences_admission_access_title_equivalency_form'
            ] = self.past_experiences_admission_access_title_equivalency_form

            # Financabilité
            context['financabilite'] = self._get_financabilite()

            # Authentication forms (one by experience)
            context['authentication_forms'] = {}

            children = (
                context['original_admission']
                .checklist.get('current', {})
                .get('parcours_anterieur', {})
                .get('enfants', [])
            )

            context['check_authentication_mail_to_checkers'] = get_email(
                template_identifier=ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CHECKERS,
                language=settings.LANGUAGE_CODE_FR,
                proposition_dto=self.proposition,
            )
            context['check_authentication_mail_to_candidate'] = get_email(
                template_identifier=ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CANDIDATE,
                language=self.proposition.langue_contact_candidat,
                proposition_dto=self.proposition,
            )

            all_experience_authentication_history_entries = HistoryEntry.objects.filter(
                object_uuid=self.admission_uuid,
                tags__contains=['proposition', 'experience-authentication', 'message'],
            ).order_by('-created')

            context['all_experience_authentication_history_entries'] = {}
            for entry in all_experience_authentication_history_entries:
                experience_id = entry.extra_data.get('experience_id')
                if experience_id:
                    context['all_experience_authentication_history_entries'].setdefault(experience_id, entry)

            children_by_identifier = {
                child['extra']['identifiant']: child for child in children if child.get('extra', {}).get('identifiant')
            }

            for experience_uuid, current_experience in experiences_by_uuid.items():
                tab_identifier = f'parcours_anterieur__{experience_uuid}'

                if experience_uuid in children_by_identifier:
                    experience_checklist_info = children_by_identifier.get(experience_uuid, {})
                else:
                    experience_checklist_info = Checklist.initialiser_checklist_experience(experience_uuid).to_dict()
                    children.append(experience_checklist_info)

                context['checklist_additional_icons'][tab_identifier] = authentication_css_class(
                    authentication_status=experience_checklist_info['extra'].get('etat_authentification'),
                )
                context['authentication_forms'][experience_uuid] = SinglePastExperienceAuthenticationForm(
                    experience_checklist_info,
                )
                context['bg_classes'][tab_identifier] = bg_class_by_checklist_experience(current_experience)
                context['checklist_tabs'][tab_identifier] = truncatechars(current_experience.titre_formate, 50)
                context['comment_forms'][tab_identifier] = CommentForm(
                    comment=comments.get(tab_identifier, None),
                    form_url=resolve_url(
                        f'{self.base_namespace}:save-comment',
                        uuid=self.admission_uuid,
                        tab=tab_identifier,
                    ),
                    prefix=tab_identifier,
                )
                authentication_comment_identifier = f'{tab_identifier}__authentication'
                context['comment_forms'][authentication_comment_identifier] = CommentForm(
                    comment=comments.get(authentication_comment_identifier, None),
                    form_url=resolve_url(
                        f'{self.base_namespace}:save-comment',
                        uuid=self.admission_uuid,
                        tab=authentication_comment_identifier,
                    ),
                    prefix=authentication_comment_identifier,
                    disabled=not can_edit_experience_authentication(experience_checklist_info),
                    label=_('Comment about the authentication'),
                )

            # Remove the experiences that we had in the checklist that have been removed
            children[:] = [child for child in children if child['extra']['identifiant'] in experiences_by_uuid]

            # Add the documents related to cv experiences
            for admission_document in admission_documents:
                document_tab_identifier = admission_document.onglet.split('.')

                if document_tab_identifier[0] == OngletsDemande.CURRICULUM.name and len(document_tab_identifier) > 1:
                    tab_identifier = f'parcours_anterieur__{document_tab_identifier[1]}'

                    if tab_identifier not in context['documents']:
                        context['documents'][tab_identifier] = [admission_document]
                    else:
                        context['documents'][tab_identifier].append(admission_document)

            if children:
                # Order the experiences in chronological order
                ordered_experiences = {}
                order = 0

                for annee, experience_list in experiences.items():
                    for experience in experience_list:
                        experience_uuid = str(experience.uuid)
                        if experience_uuid not in ordered_experiences:
                            ordered_experiences[experience_uuid] = order
                            order += 1

                children.sort(key=lambda x: ordered_experiences.get(x['extra']['identifiant'], 0))

                # Some tabs also contain the documents of each experience
                past_experiences_documents = []
                for experience_uuid in ordered_experiences:
                    current_uuid = f'parcours_anterieur__{experience_uuid}'
                    if context['documents'].get(current_uuid):
                        past_experiences_documents.append(
                            [
                                context['checklist_tabs'][current_uuid],  # Name of the experience
                                context['documents'][current_uuid],  # List of documents of the experience
                            ]
                        )

                context['documents']['parcours_anterieur'].extend(past_experiences_documents)
                context['documents']['financabilite'].extend(past_experiences_documents)

            original_admission = self.admission

            can_change_checklist = self.request.user.has_perm('admission.change_checklist', original_admission)
            can_change_faculty_decision = self.request.user.has_perm(
                'admission.checklist_change_faculty_decision',
                original_admission,
            )
            can_change_past_experiences = self.request.user.has_perm(
                'admission.checklist_change_past_experiences',
                original_admission,
            )
            can_change_access_title = self.request.user.has_perm(
                'admission.checklist_select_access_title',
                original_admission,
            )
            comment_permissions = {
                'admission.checklist_change_comment': self.request.user.has_perm(
                    'admission.checklist_change_comment',
                    original_admission,
                ),
                'admission.checklist_change_fac_comment': self.request.user.has_perm(
                    'admission.checklist_change_fac_comment',
                    original_admission,
                ),
                'admission.checklist_change_sic_comment': self.request.user.has_perm(
                    'admission.checklist_change_sic_comment',
                    original_admission,
                ),
            }

            disable_unavailable_forms(
                {
                    context['assimilation_form']: can_change_checklist,
                    context['fac_decision_refusal_form']: can_change_faculty_decision,
                    context['fac_decision_approval_form']: can_change_faculty_decision,
                    context['financabilite_approval_form']: can_change_checklist,
                    context['past_experiences_admission_requirement_form']: can_change_past_experiences,
                    context['past_experiences_admission_access_title_equivalency_form']: can_change_access_title,
                    context['financabilite_approval_form']: can_change_checklist,
                    **{
                        authentication_form: can_change_checklist
                        for authentication_form in context['authentication_forms'].values()
                    },
                    **{
                        comment_form: comment_permissions[comment_form.permission]
                        for comment_form in context['comment_forms'].values()
                    },
                }
            )
            context['can_choose_access_title'] = can_change_access_title

        return context

    def _get_experiences(self, resume: ResumePropositionDTO):
        experiences = {}

        for experience_academique in resume.curriculum.experiences_academiques:
            for annee_academique in experience_academique.annees:
                experiences.setdefault(annee_academique.annee, [])
                if experience_academique.a_obtenu_diplome:
                    experiences[annee_academique.annee].insert(0, experience_academique)
                else:
                    experiences[annee_academique.annee].append(experience_academique)

        experiences_non_academiques = {}
        for experience_non_academique in resume.curriculum.experiences_non_academiques:
            date_courante = experience_non_academique.date_debut
            while True:
                annee = (
                    date_courante.year if date_courante.month >= MOIS_DEBUT_ANNEE_ACADEMIQUE else date_courante.year - 1
                )
                if experience_non_academique not in experiences_non_academiques.get(annee, []):
                    experiences_non_academiques.setdefault(annee, []).append(experience_non_academique)
                if date_courante == experience_non_academique.date_fin:
                    break
                date_courante = min(
                    date_courante.replace(year=date_courante.year + 1), experience_non_academique.date_fin
                )
        for annee, experiences_annee in experiences_non_academiques.items():
            experiences_annee.sort(key=lambda x: x.date_fin, reverse=True)
            experiences.setdefault(annee, []).extend(experiences_annee)

        etudes_secondaires = resume.etudes_secondaires
        if etudes_secondaires:
            if etudes_secondaires.annee_diplome_etudes_secondaires:
                experiences.setdefault(etudes_secondaires.annee_diplome_etudes_secondaires, []).append(
                    etudes_secondaires
                )
            elif etudes_secondaires.alternative_secondaires:
                experiences.setdefault(0, []).append(etudes_secondaires)

        experiences = {annee: experiences[annee] for annee in sorted(experiences.keys(), reverse=True)}

        return experiences

    def _get_financabilite(self):
        # TODO
        return {
            'inscription_precedentes': 2,
            'inscription_supplementaire': 1,
        }

    def _get_experiences_by_uuid(self, resume: ResumeCandidatDTO):
        experiences = {}
        for experience_academique in resume.curriculum.experiences_academiques:
            experiences[str(experience_academique.uuid)] = experience_academique
        for experience_non_academique in resume.curriculum.experiences_non_academiques:
            experiences[str(experience_non_academique.uuid)] = experience_non_academique
        experiences[OngletsDemande.ETUDES_SECONDAIRES.name] = resume.etudes_secondaires
        return experiences


class ApplicationFeesView(
    AdmissionFormMixin,
    RequestApplicationFeesContextDataMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'application-fees'
    urlpatterns = {'application-fees': 'application-fees/<str:status>'}
    permission_required = 'admission.change_payment'
    template_name = 'admission/general_education/includes/checklist/application_fees_request.html'
    htmx_template_name = 'admission/general_education/includes/checklist/application_fees_request.html'
    form_class = Form

    def form_valid(self, form):
        current_status = self.kwargs.get('status')
        remind = self.request.GET.get('remind')

        if current_status == ChoixStatutChecklist.GEST_BLOCAGE.name:
            if remind:
                cmd = EnvoyerRappelPaiementCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
            else:
                cmd = SpecifierPaiementNecessaireCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
                self.htmx_refresh = True
        else:
            cmd = SpecifierPaiementPlusNecessaireCommand(
                uuid_proposition=self.admission_uuid,
                gestionnaire=self.request.user.person.global_id,
                statut_checklist_frais_dossier=self.kwargs['status'],
            )
            self.htmx_refresh = 'confirm' in self.request.GET

        try:
            message_bus_instance.invoke(cmd)
        except BusinessException as exception:
            self.message_on_failure = exception.message
            return super().form_invalid(form)

        return super().form_valid(form)


class PastExperiencesStatusView(
    AdmissionFormMixin,
    CheckListDefaultContextMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'past-experiences-status'
    urlpatterns = {'past-experiences-change-status': 'past-experiences-change-status/<str:status>'}
    permission_required = 'admission.change_checklist'
    template_name = 'admission/general_education/includes/checklist/previous_experiences.html'
    htmx_template_name = 'admission/general_education/includes/checklist/previous_experiences.html'
    form_class = StatusForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.valid_operation = False

    def get_initial(self):
        return self.admission.checklist['current']['parcours_anterieur']['statut']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['data'] = self.kwargs
        return kwargs

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                ModifierStatutChecklistParcoursAnterieurCommand(
                    uuid_proposition=self.admission_uuid,
                    statut=form.cleaned_data['status'],
                    gestionnaire=self.request.user.person.global_id,
                )
            )
            self.valid_operation = True
        except MultipleBusinessExceptions:
            return super().form_invalid(form)

        return super().form_valid(form)


class PastExperiencesAdmissionRequirementView(
    PastExperiencesMixin,
    AdmissionFormMixin,
    CheckListDefaultContextMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'past-experiences-admission-requirement'
    urlpatterns = 'past-experiences-admission-requirement'
    permission_required = 'admission.change_checklist'
    template_name = (
        'admission/general_education/includes/checklist/previous_experiences_admission_requirement_form.html'
    )
    htmx_template_name = (
        'admission/general_education/includes/checklist/previous_experiences_admission_requirement_form.html'
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['past_experiences_admission_requirement_form'] = context['form']
        return context

    def get_form(self, form_class=None):
        return self.past_experiences_admission_requirement_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                SpecifierConditionAccesPropositionCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    condition_acces=form.cleaned_data['admission_requirement'],
                    millesime_condition_acces=form.cleaned_data['admission_requirement_year']
                    and form.cleaned_data['admission_requirement_year'].year,
                    avec_complements_formation=form.cleaned_data['with_prerequisite_courses'],
                )
            )

            # The admission requirement year can be updated via the command
            form.data = {
                'admission_requirement': self.admission.admission_requirement,
                'admission_requirement_year': self.admission.admission_requirement_year_id,
                'with_prerequisite_courses': self.admission.with_prerequisite_courses,
            }

        except BusinessException as exception:
            self.message_on_failure = exception.message
            return super().form_invalid(form)

        return super().form_valid(form)


class PastExperiencesAccessTitleView(
    PastExperiencesMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'past-experiences-access-title'
    urlpatterns = 'past-experiences-access-title'
    permission_required = 'admission.checklist_select_access_title'
    template_name = 'admission/general_education/includes/checklist/parcours_row_access_title.html'
    htmx_template_name = 'admission/general_education/includes/checklist/parcours_row_access_title.html'
    form_class = Form

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checked: Optional[bool] = None
        self.experience_uuid: str = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['checked'] = self.checked
        context['url'] = self.request.get_full_path()
        context['experience_uuid'] = self.request.GET.get('experience_uuid')
        context['can_choose_access_title'] = True  # True as the user can access to the current view

        # Get the list of the selected access titles
        access_titles: Dict[str, TitreAccesSelectionnableDTO] = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=self.admission_uuid,
                seulement_selectionnes=True,
            )
        )

        if access_titles:
            command_result: ResumePropositionDTO = message_bus_instance.invoke(
                RecupererResumePropositionQuery(uuid_proposition=self.admission_uuid),
            )

            context['selected_access_titles_names'] = get_access_titles_names(
                access_titles=access_titles,
                curriculum_dto=command_result.curriculum,
                etudes_secondaires_dto=command_result.etudes_secondaires,
            )

        return context

    def form_valid(self, form):
        experience_type = self.request.GET.get('experience_type')
        self.experience_uuid = self.request.GET.get('experience_uuid')
        self.checked = 'access-title' in self.request.POST
        try:
            message_bus_instance.invoke(
                SpecifierExperienceEnTantQueTitreAccesCommand(
                    uuid_proposition=self.admission_uuid,
                    uuid_experience=self.experience_uuid,
                    selectionne=self.checked,
                    type_experience=experience_type,
                )
            )

        except BusinessException as exception:
            self.message_on_failure = exception.message
            self.checked = not self.checked
            return super().form_invalid(form)

        return super().form_valid(form)


class PastExperiencesAccessTitleEquivalencyView(
    PastExperiencesMixin,
    AdmissionFormMixin,
    CheckListDefaultContextMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'past-experiences-access-title-equivalency'
    urlpatterns = 'past-experiences-access-title-equivalency'
    permission_required = 'admission.change_checklist'
    template_name = (
        'admission/general_education/includes/checklist/previous_experiences_access_title_equivalency_form.html'
    )
    htmx_template_name = (
        'admission/general_education/includes/checklist/previous_experiences_access_title_equivalency_form.html'
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['past_experiences_admission_access_title_equivalency_form'] = context['form']
        return context

    def get_form(self, form_class=None):
        return self.past_experiences_admission_access_title_equivalency_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                SpecifierEquivalenceTitreAccesEtrangerPropositionCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    type_equivalence_titre_acces=form.cleaned_data['foreign_access_title_equivalency_type'],
                    statut_equivalence_titre_acces=form.cleaned_data['foreign_access_title_equivalency_status'],
                    etat_equivalence_titre_acces=form.cleaned_data['foreign_access_title_equivalency_state'],
                    date_prise_effet_equivalence_titre_acces=form.cleaned_data[
                        'foreign_access_title_equivalency_effective_date'
                    ],
                )
            )

        except MultipleBusinessExceptions as exception:
            self.message_on_failure = exception.exceptions.pop().message
            return super().form_invalid(form)

        return super().form_valid(form)


class ChangeStatusSerializer(serializers.Serializer):
    tab_name = serializers.CharField()
    status = serializers.ChoiceField(choices=ChoixStatutChecklist.choices(), required=False)
    extra = serializers.DictField(default={}, required=False)


def change_admission_status(tab, admission_status, extra, admission, author, replace_extra=False, global_status=None):
    """Change the status of the admission of a specific tab"""
    update_fields = ['checklist', 'last_update_author', 'modified_at']

    admission.last_update_author = author
    admission.modified_at = datetime.datetime.today()

    serializer = ChangeStatusSerializer(
        data={
            'tab_name': tab,
            'status': admission_status,
            'extra': extra,
        }
    )
    serializer.is_valid(raise_exception=True)

    if admission.checklist.get('current') is None:
        admission.checklist['current'] = {}

    admission.checklist['current'].setdefault(serializer.validated_data['tab_name'], {})
    tab_data = admission.checklist['current'][serializer.validated_data['tab_name']]
    tab_data['statut'] = serializer.validated_data['status']
    tab_data['libelle'] = ''
    tab_data.setdefault('extra', {})
    if replace_extra:
        tab_data['extra'] = serializer.validated_data['extra']
    else:
        tab_data['extra'].update(serializer.validated_data['extra'])

    if global_status is not None:
        admission.status = global_status
        update_fields.append('status')

    admission.save(update_fields=update_fields)

    return serializer.data


class ChangeStatusView(LoadDossierViewMixin, APIView):
    urlpatterns = {'change-checklist-status': 'change-checklist-status/<str:tab>/<str:status>'}
    permission_required = 'admission.change_checklist'
    parser_classes = [FormParser]
    authentication_classes = [SessionAuthentication]

    def post(self, request, *args, **kwargs):
        admission = self.get_permission_object()

        serializer_data = change_admission_status(
            tab=self.kwargs['tab'],
            admission_status=self.kwargs['status'],
            extra=request.data.dict(),
            admission=admission,
            author=self.request.user.person,
        )

        return Response(serializer_data, status=status.HTTP_200_OK)


class ChangeExtraView(AdmissionFormMixin, FormView):
    urlpatterns = {'change-checklist-extra': 'change-checklist-extra/<str:tab>'}
    permission_required = 'admission.change_checklist'
    template_name = 'admission/forms/default_form.html'

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['form_url'] = resolve_url(
            f'{self.base_namespace}:change-checklist-extra',
            uuid=self.admission_uuid,
            tab=self.kwargs['tab'],
        )
        return form_kwargs

    def get_form_class(self):
        return {
            'assimilation': AssimilationForm,
        }[self.kwargs['tab']]

    def form_valid(self, form):
        admission = self.get_permission_object()
        tab_name = self.kwargs['tab']

        if admission.checklist.get('current') is None:
            admission.checklist['current'] = {}

        admission.checklist['current'].setdefault(tab_name, {})
        tab_data = admission.checklist['current'][tab_name]
        tab_data.setdefault('extra', {})
        tab_data['extra'].update(form.cleaned_data)
        admission.modified_at = datetime.datetime.today()
        admission.last_update_author = self.request.user.person
        admission.save(update_fields=['checklist', 'modified_at', 'last_update_author'])
        return super().form_valid(form)


class SaveCommentView(AdmissionFormMixin, FormView):
    urlpatterns = {'save-comment': 'save-comment/<str:tab>'}
    form_class = CommentForm
    template_name = 'admission/forms/default_form.html'

    def get_permission_required(self):
        if f'__{COMMENT_TAG_FAC}' in self.kwargs['tab']:
            self.permission_required = 'admission.checklist_change_fac_comment'
        elif f'__{COMMENT_TAG_SIC}' in self.kwargs['tab']:
            self.permission_required = 'admission.checklist_change_sic_comment'
        elif '__authentication' in self.kwargs['tab']:
            self.permission_required = 'admission.checklist_change_past_experiences'
        else:
            self.permission_required = 'admission.checklist_change_comment'
        return super().get_permission_required()

    @cached_property
    def form_url(self):
        return resolve_url(
            f'{self.base_namespace}:save-comment',
            uuid=self.admission_uuid,
            tab=self.kwargs['tab'],
        )

    def get_prefix(self):
        return self.kwargs['tab']

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['form_url'] = self.form_url
        return form_kwargs

    def form_valid(self, form):
        comment, _ = CommentEntry.objects.update_or_create(
            object_uuid=self.admission_uuid,
            tags=self.kwargs['tab'].split('__'),
            defaults={
                'content': form.cleaned_data['comment'],
                'author': self.request.user.person,
            },
        )
        return super().form_valid(CommentForm(comment=comment, **self.get_form_kwargs()))


class ChoixFormationFormView(LoadDossierViewMixin, FormView):
    urlpatterns = 'choix-formation-update'
    permission_required = 'admission.change_checklist'
    template_name = 'admission/general_education/includes/checklist/choix_formation_form.html'
    form_class = ChoixFormationForm

    def dispatch(self, request, *args, **kwargs):
        if not request.htmx:
            return redirect(
                reverse('admission:general-education:checklist', kwargs={'uuid': self.admission_uuid})
                + '#choix_formation'
            )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['formation'] = self.proposition.formation
        return kwargs

    def get_initial(self):
        return {
            'type_demande': self.proposition.type,
            'annee_academique': self.proposition.annee_calculee,
            'formation': self.proposition.formation.sigle,
            'poursuite_cycle': self.proposition.poursuite_de_cycle,
        }

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                ModifierChecklistChoixFormationCommand(
                    uuid_proposition=str(self.kwargs['uuid']),
                    gestionnaire=self.request.user.person.global_id,
                    type_demande=form.cleaned_data['type_demande'],
                    sigle_formation=form.cleaned_data['formation'],
                    annee_formation=form.cleaned_data['annee_academique'],
                    poursuite_de_cycle=form.cleaned_data['poursuite_cycle'],
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                form.add_error(None, exception.message)
            return self.form_invalid(form)
        return HttpResponse(headers={'HX-Refresh': 'true'})


class ChoixFormationDetailView(LoadDossierViewMixin, TemplateView):
    urlpatterns = 'choix-formation-detail'
    permission_required = 'admission.change_checklist'
    template_name = 'admission/general_education/includes/checklist/choix_formation_detail.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.htmx:
            return redirect(
                reverse('admission:general-education:checklist', kwargs={'uuid': self.admission_uuid})
                + '#choix_formation'
            )
        return super().dispatch(request, *args, **kwargs)


class FinancabiliteContextMixin(CheckListDefaultContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        comment = CommentEntry.objects.filter(object_uuid=self.admission_uuid, tags__contains=['financabilite']).first()

        context['comment_forms'] = {
            'financabilite': CommentForm(
                comment=comment,
                form_url=resolve_url(
                    f'{self.base_namespace}:save-comment',
                    uuid=self.admission_uuid,
                    tab='financabilite',
                ),
                prefix='financabilite',
            )
        }

        context['financabilite_approval_form'] = FinancabiliteApprovalForm(
            instance=self.admission,
            prefix='financabilite',
        )

        return context


class FinancabiliteChangeStatusView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, TemplateView):
    urlpatterns = {'financability-change-status': 'financability-change-checklist-status/<str:status>'}
    template_name = 'admission/general_education/includes/checklist/financabilite.html'
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        admission = self.get_permission_object()

        try:
            status, extra = self.kwargs['status'].split('-')
            if status == 'GEST_BLOCAGE':
                extra = {'to_be_completed': extra}
        except ValueError:
            status = self.kwargs['status']
            extra = {}

        change_admission_status(
            tab='financabilite',
            admission_status=status,
            extra=extra,
            admission=admission,
            replace_extra=True,
            author=self.request.user.person,
        )

        if status == 'GEST_BLOCAGE' and extra.get('to_be_completed') == '0':
            admission.financability_rule_established_by = request.user.person
            admission.save(update_fields=['financability_rule_established_by'])

        return self.render_to_response(self.get_context_data())


class FinancabiliteApprovalView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, FormView):
    urlpatterns = {'financability-approval': 'financability-checklist-approval'}
    template_name = 'admission/general_education/includes/checklist/financabilite_approval_form.html'
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def get_form(self, form_class=None):
        return FinancabiliteApprovalForm(
            instance=self.admission if self.request.method != 'POST' else None,
            data=self.request.POST if self.request.method == 'POST' else None,
            prefix='financabilite',
        )

    def form_valid(self, form):
        message_bus_instance.invoke(
            SpecifierFinancabiliteRegleCommand(
                uuid_proposition=self.admission_uuid,
                financabilite_regle=form.cleaned_data['financability_rule'],
                etabli_par=self.request.user.person.uuid,
                gestionnaire=self.request.user.person.global_id,
            )
        )

        return render(
            self.request,
            'admission/general_education/includes/checklist/financabilite.html',
            context=self.get_context_data(),
        )


class FinancabiliteComputeRuleView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, TemplateView):
    urlpatterns = {'financability-compute-rule': 'financability-compute-rule'}
    template_name = 'admission/general_education/includes/checklist/financabilite.html'
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        admission = self.get_permission_object()
        admission.update_financability_computed_rule(author=self.request.user.person)
        return self.render_to_response(self.get_context_data())


class SinglePastExperienceMixin(
    PastExperiencesMixin,
    AdmissionFormMixin,
    CheckListDefaultContextMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    @cached_property
    def experience_uuid(self):
        return self.request.GET.get('identifier')

    @property
    def experience(self):
        return next(
            (
                experience
                for experience in self.admission.checklist['current']['parcours_anterieur']['enfants']
                if experience['extra']['identifiant'] == self.experience_uuid
            ),
            None,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current'] = self.experience
        context['initial'] = self.experience or {}
        authentication_comment_identifier = f'parcours_anterieur__{self.experience_uuid}__authentication'
        context.setdefault('comment_forms', {})
        context['comment_forms'][authentication_comment_identifier] = CommentForm(
            comment=CommentEntry.objects.filter(
                object_uuid=self.admission_uuid,
                tags=['parcours_anterieur', self.experience_uuid, 'authentication'],
            ).first(),
            form_url=resolve_url(
                f'{self.base_namespace}:save-comment',
                uuid=self.admission_uuid,
                tab=authentication_comment_identifier,
            ),
            prefix=authentication_comment_identifier,
            disabled=not can_edit_experience_authentication(self.experience),
            label=_('Comment about the authentication'),
        )
        context['experience_authentication_history_entry'] = (
            HistoryEntry.objects.filter(
                object_uuid=self.admission_uuid,
                tags__contains=['proposition', 'experience-authentication', 'message'],
                extra_data__experience_id=self.experience_uuid,
            )
            .order_by('-created')
            .first()
        )

        return context

    def get_success_url(self):
        return self.request.get_full_path()

    def command(self, form):
        raise NotImplementedError

    def form_valid(self, form):
        try:
            self.command(form)
        except ExperienceNonTrouveeException as exception:
            self.message_on_failure = exception.message
            return super().form_invalid(form)
        return super().form_valid(form)


class SinglePastExperienceChangeStatusView(SinglePastExperienceMixin):
    name = 'single-past-experience-change-status'
    urlpatterns = 'single-past-experience-change-status'
    permission_required = 'admission.checklist_change_past_experiences'
    template_name = 'admission/general_education/includes/checklist/previous_experience_single.html'
    htmx_template_name = 'admission/general_education/includes/checklist/previous_experience_single.html'
    form_class = ExperienceStatusForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['authentication_form'] = SinglePastExperienceAuthenticationForm(self.experience)
        return context

    def command(self, form):
        message_bus_instance.invoke(
            ModifierStatutChecklistExperienceParcoursAnterieurCommand(
                uuid_proposition=self.admission_uuid,
                uuid_experience=self.experience_uuid,
                gestionnaire=self.request.user.person.global_id,
                statut=form.cleaned_data['status'],
                statut_authentification=form.cleaned_data['authentification'],
            )
        )


class SinglePastExperienceChangeAuthenticationView(SinglePastExperienceMixin):
    name = 'single-past-experience-change-authentication'
    urlpatterns = 'single-past-experience-change-authentication'
    permission_required = 'admission.checklist_change_past_experiences'
    template_name = 'admission/general_education/includes/checklist/previous_experience_single_authentication_form.html'
    htmx_template_name = (
        'admission/general_education/includes/checklist/previous_experience_single_authentication_form.html'
    )
    form_class = SinglePastExperienceAuthenticationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['checklist_experience_data'] = self.experience
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['authentication_form'] = context['form']
        return context

    def command(self, form):
        message_bus_instance.invoke(
            ModifierAuthentificationExperienceParcoursAnterieurCommand(
                uuid_proposition=self.admission_uuid,
                uuid_experience=self.experience_uuid,
                gestionnaire=self.request.user.person.global_id,
                etat_authentification=form.cleaned_data['state'],
            )
        )
