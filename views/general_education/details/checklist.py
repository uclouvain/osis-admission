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
import itertools
from typing import Dict, Set, Optional, List, Union

import attr
from django.conf import settings
from django.db.models import QuerySet
from django.forms import Form
from django.forms.formsets import formset_factory
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import resolve_url, redirect
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils import translation, timezone
from django.utils.formats import date_format
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _, ngettext, pgettext, override
from django.views.generic import TemplateView, FormView
from django.views.generic.base import RedirectView, View
from django_htmx.http import HttpResponseClientRefresh
from osis_comment.models import CommentEntry
from osis_document.utils import get_file_url
from osis_history.models import HistoryEntry
from osis_history.utilities import add_history_entry
from osis_mail_template.exceptions import EmptyMailTemplateContent
from osis_mail_template.models import MailTemplate

from admission.contrib.models import EPCInjection
from admission.contrib.models.epc_injection import EPCInjectionStatus, EPCInjectionType
from admission.contrib.models.online_payment import PaymentStatus, PaymentMethod
from admission.ddd import MAIL_VERIFICATEUR_CURSUS
from admission.ddd import MONTANT_FRAIS_DOSSIER
from admission.ddd.admission.commands import (
    ListerToutesDemandesQuery,
    GetStatutTicketPersonneQuery,
    RechercherParcoursAnterieurQuery,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixGenre
from admission.ddd.admission.domain.model.enums.condition_acces import TypeTitreAccesSelectionnable
from admission.ddd.admission.domain.validator.exceptions import ExperienceNonTrouveeException
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO
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
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.enums.emplacement_document import (
    OngletsDemande,
    DocumentsEtudesSecondaires,
)
from admission.ddd.admission.enums.statut import (
    STATUTS_TOUTE_PROPOSITION_SOUMISE,
    STATUTS_TOUTE_PROPOSITION_AUTORISEE,
    STATUTS_TOUTE_PROPOSITION_SOUMISE_HORS_FRAIS_DOSSIER_OU_ANNULEE,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.commands import (
    RecupererResumeEtEmplacementsDocumentsPropositionQuery,
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
    ApprouverInscriptionTardiveParFaculteCommand,
    SpecifierInformationsAcceptationInscriptionParSicCommand,
    SpecifierDerogationFinancabiliteCommand,
    NotifierCandidatDerogationFinancabiliteCommand, SpecifierFinancabiliteNonConcerneeCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC,
    ChoixStatutPropositionGenerale,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_ETENDUS,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC_ETENDUS,
    PoursuiteDeCycle,
    STATUTS_PROPOSITION_GENERALE_ENVOYABLE_EN_FAC_POUR_DECISION,
    TypeDeRefus,
    OngletsChecklist,
    DerogationFinancement,
)
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT,
)
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import onglet_decision_sic
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.ddd.admission.formation_generale.dtos.proposition import PropositionGestionnaireDTO
from admission.ddd.admission.shared_kernel.email_destinataire.domain.validator.exceptions import (
    InformationsDestinatairePasTrouvee,
)
from admission.ddd.admission.shared_kernel.email_destinataire.queries import RecupererInformationsDestinataireQuery
from admission.exports.admission_recap.section import get_dynamic_questions_by_tab
from admission.forms import disable_unavailable_forms
from admission.forms.admission.checklist import (
    ChoixFormationForm,
    SicDecisionDerogationForm,
    FinancabiliteApprovalForm,
    SicDecisionApprovalDocumentsForm,
    FreeAdditionalApprovalConditionForm,
    FinancabiliteDispensationForm,
    FinancabilityDispensationRefusalForm,
    FinancabiliteNotificationForm,
    FinancabiliteNotFinanceableForm,
)
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
from admission.infrastructure.utils import CHAMPS_DOCUMENTS_EXPERIENCES_CURRICULUM
from admission.mail_templates import (
    ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL,
    ADMISSION_EMAIL_FINANCABILITY_DISPENSATION_NOTIFICATION,
    INSCRIPTION_EMAIL_SIC_APPROVAL,
)
from admission.mail_templates.checklist import (
    ADMISSION_EMAIL_SIC_REFUSAL,
    ADMISSION_EMAIL_SIC_APPROVAL,
    ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CHECKERS,
    ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CANDIDATE,
    EMAIL_TEMPLATE_ENROLLMENT_AUTHORIZATION_DOCUMENT_URL_TOKEN,
    EMAIL_TEMPLATE_VISA_APPLICATION_DOCUMENT_URL_TOKEN,
    ADMISSION_EMAIL_SIC_APPROVAL_EU,
)
from admission.templatetags.admission import authentication_css_class, bg_class_by_checklist_experience
from admission.utils import (
    add_close_modal_into_htmx_response,
    get_portal_admission_list_url,
    get_backoffice_admission_url,
    get_portal_admission_url,
    get_access_titles_names,
    get_salutation_prefix,
    format_academic_year,
    get_training_url,
)
from admission.views.common.detail_tabs.checklist import change_admission_status
from admission.views.common.detail_tabs.comments import COMMENT_TAG_SIC, COMMENT_TAG_FAC
from admission.views.common.mixins import LoadDossierViewMixin, AdmissionFormMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.models.enums.mandate_type import MandateTypes
from base.models.person import Person
from base.models.person_merge_proposal import PersonMergeStatus
from base.models.student import Student
from base.utils.htmx import HtmxPermissionRequiredMixin
from ddd.logic.shared_kernel.profil.commands import RecupererExperiencesParcoursInterneQuery
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import ExperienceNonAcademiqueDTO, ExperienceAcademiqueDTO
from ddd.logic.shared_kernel.profil.dtos.parcours_interne import ExperienceParcoursInterneDTO
from epc.models.enums.condition_acces import ConditionAcces
from infrastructure.messages_bus import message_bus_instance
from osis_common.ddd.interface import BusinessException
from osis_profile.models import EducationalExperience
from osis_profile.utils.curriculum import groupe_curriculum_par_annee_decroissante
from osis_role.templatetags.osis_role import has_perm

__all__ = [
    'ChecklistView',
    'ChangeExtraView',
    'ApplicationFeesView',
    'ChoixFormationFormView',
    'ChoixFormationDetailView',
    'FacultyDecisionView',
    'FacultyDecisionSendToFacultyView',
    'FacultyRefusalDecisionView',
    'FacultyApprovalDecisionView',
    'FacultyDecisionSendToSicView',
    'LateFacultyApprovalDecisionView',
    'PastExperiencesStatusView',
    'PastExperiencesAdmissionRequirementView',
    'PastExperiencesAccessTitleEquivalencyView',
    'PastExperiencesAccessTitleView',
    'FinancabiliteComputeRuleView',
    'FinancabiliteChangeStatusView',
    'FinancabiliteApprovalView',
    'FinancabiliteDerogationNonConcerneView',
    'FinancabiliteDerogationNotificationView',
    'FinancabiliteDerogationAbandonCandidatView',
    'FinancabiliteDerogationRefusView',
    'FinancabiliteDerogationAccordView',
    'FinancabiliteApprovalSetRuleView',
    'FinancabiliteNotFinanceableSetRuleView',
    'FinancabiliteNotFinanceableView',
    'FinancabiliteNotConcernedView',
    'SinglePastExperienceChangeStatusView',
    'SinglePastExperienceChangeAuthenticationView',
    'SicApprovalDecisionView',
    'SicApprovalEnrolmentDecisionView',
    'SicApprovalFinalDecisionView',
    'SicDecisionApprovalPanelView',
    'SicRefusalDecisionView',
    'SicRefusalFinalDecisionView',
    'SicDecisionDispensationView',
    'SicDecisionChangeStatusView',
    'SicDecisionPdfPreviewView',
]


__namespace__ = False


TABS_WITH_SIC_AND_FAC_COMMENTS = {'decision_facultaire'}
ENTITY_SIC = 'SIC'
EMAIL_TEMPLATE_DOCUMENT_URL_TOKEN = 'SERA_AUTOMATIQUEMENT_REMPLACE_PAR_LE_LIEN'


class CheckListDefaultContextMixin(LoadDossierViewMixin):
    extra_context = {
        'checklist_tabs': {
            tab_name: OngletsChecklist[tab_name].value
            for tab_name in OngletsChecklist.get_names_except(OngletsChecklist.experiences_parcours_anterieur)
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
        checklist_additional_icons_title = {}

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

        person_merge_proposal = getattr(self.admission.candidate, 'personmergeproposal', None)
        if person_merge_proposal and (
                person_merge_proposal.status in PersonMergeStatus.quarantine_statuses()
                or not person_merge_proposal.validation.get('valid', True)
        ):
            # Cas display warning when quarantaine
            # (cf. admission/infrastructure/admission/domain/service/lister_toutes_demandes.py)
            checklist_additional_icons['donnees_personnelles'] = 'fas fa-warning text-warning'


        if self.proposition.type == TypeDemande.INSCRIPTION.name and self.proposition.est_inscription_tardive:
            checklist_additional_icons['choix_formation'] = 'fa-regular fa-calendar-clock'

        candidate_admissions: List[DemandeRechercheDTO] = message_bus_instance.invoke(
            ListerToutesDemandesQuery(
                matricule_candidat=self.admission.candidate.global_id,
                etats=STATUTS_TOUTE_PROPOSITION_SOUMISE,
                champ_tri='date_confirmation',
                tri_inverse=True,
            )
        )

        submitted_for_the_current_year_admissions: List[DemandeRechercheDTO] = []

        for admission in candidate_admissions:
            if (
                admission.etat_demande in STATUTS_TOUTE_PROPOSITION_SOUMISE_HORS_FRAIS_DOSSIER_OU_ANNULEE
                and admission.annee_demande == self.admission.determined_academic_year.year
                and admission.uuid != self.admission_uuid
            ):
                submitted_for_the_current_year_admissions.append(admission)

        context['toutes_les_demandes'] = candidate_admissions
        context['autres_demandes'] = submitted_for_the_current_year_admissions

        if any(
            admission
            for admission in submitted_for_the_current_year_admissions
            if admission.etat_demande in STATUTS_TOUTE_PROPOSITION_AUTORISEE
        ):
            checklist_additional_icons['choix_formation'] = 'fa-solid fa-square-2'
            checklist_additional_icons_title['choix_formation'] = _(
                'Another admission has been authorized for this candidate for this academic year.'
            )

        if any(
            admission
            for admission in submitted_for_the_current_year_admissions
            if admission.sigle_formation == self.proposition.formation.sigle
        ):
            checklist_additional_icons['choix_formation'] = 'fa-solid fa-triangle-exclamation'
            checklist_additional_icons_title['choix_formation'] = _(
                'The candidate has already applied for this course for this academic year.'
            )

        context['checklist_additional_icons'] = checklist_additional_icons
        context['checklist_additional_icons_title'] = checklist_additional_icons_title
        context['can_update_checklist_tab'] = self.can_update_checklist_tab
        context['can_change_payment'] = self.request.user.has_perm('admission.change_payment', self.admission)
        context['can_change_faculty_decision'] = self.request.user.has_perm(
            'admission.checklist_change_faculty_decision',
            self.admission,
        )
        context['past_experiences_are_sufficient'] = (
            self.admission.checklist.get('current', {}).get('parcours_anterieur', {}).get('statut', '')
            == ChoixStatutChecklist.GEST_REUSSITE.name
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
        context['fac_decision_free_approval_condition_formset'] = self.fac_decision_free_approval_condition_formset
        context['program_faculty_email'] = self.program_faculty_email.email if self.program_faculty_email else None

        return context

    @cached_property
    def program_faculty_email(self):
        try:
            return message_bus_instance.invoke(
                RecupererInformationsDestinataireQuery(
                    sigle_formation=self.admission.training.acronym,
                    est_premiere_annee=bool(
                        self.proposition.poursuite_de_cycle_a_specifier
                        and self.proposition.poursuite_de_cycle != PoursuiteDeCycle.YES.name,
                    ),
                    annee=self.admission.determined_academic_year.year,
                )
            )
        except InformationsDestinatairePasTrouvee:
            return None

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
    def candidate_cv_program_names_by_experience_uuid(self):
        experiences: QuerySet[EducationalExperience] = EducationalExperience.objects.select_related('program').filter(
            person=self.admission.candidate
        )
        return {
            str(experience.uuid): experience.program.title if experience.program else experience.education_name
            for experience in experiences
        }

    @cached_property
    def fac_decision_approval_form(self):
        return FacDecisionApprovalForm(
            academic_year=self.admission.determined_academic_year.year,
            instance=self.admission if self.request.method != 'POST' else None,
            data=self.request.POST if self.request.method == 'POST' else None,
            prefix='fac-decision-approval',
            educational_experience_program_name_by_uuid=self.candidate_cv_program_names_by_experience_uuid,
            current_training_uuid=str(self.admission.training.uuid),
        )

    @cached_property
    def fac_decision_free_approval_condition_formset(self):
        FreeApprovalConditionFormSet = formset_factory(
            form=FreeAdditionalApprovalConditionForm,
            extra=0,
        )

        formset = FreeApprovalConditionFormSet(
            prefix='fac-decision',
            initial=self.admission.freeadditionalapprovalcondition_set.filter(
                related_experience__isnull=True,
            ).values('name_fr', 'name_en')
            if self.request.method != 'POST'
            else None,
            data=self.request.POST if self.request.method == 'POST' else None,
            form_kwargs={
                'candidate_language': self.admission.candidate.language,
            },
        )

        return formset


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

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        formset = self.fac_decision_free_approval_condition_formset

        # Cross validation
        if form.is_valid() and formset.is_valid():
            with_additional_conditions = form.cleaned_data['with_additional_approval_conditions']

            if with_additional_conditions and (
                not form.cleaned_data['additional_approval_conditions']
                and not form.cleaned_data['cv_experiences_additional_approval_conditions']
                and not any(subform.is_valid() for subform in formset)
            ):
                form.add_error('all_additional_approval_conditions', FIELD_REQUIRED_MESSAGE)

        form.all_required_forms_are_valid = form.is_valid() and (
            not form.cleaned_data['with_additional_approval_conditions'] or formset.is_valid()
        )

        if form.all_required_forms_are_valid:
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form(self, form_class=None):
        return self.fac_decision_approval_form

    def form_valid(self, form):
        base_params = {
            'uuid_proposition': self.admission_uuid,
            'sigle_autre_formation': form.cleaned_data['other_training_accepted_by_fac'].acronym
            if form.cleaned_data['other_training_accepted_by_fac']
            else '',
            'avec_conditions_complementaires': form.cleaned_data['with_additional_approval_conditions'],
            'uuids_conditions_complementaires_existantes': [
                condition for condition in form.cleaned_data['additional_approval_conditions']
            ],
            'conditions_complementaires_libres': (
                [
                    sub_form.cleaned_data
                    for sub_form in self.fac_decision_free_approval_condition_formset.forms
                    if sub_form.is_valid()
                ]
                if form.cleaned_data['with_additional_approval_conditions']
                else []
            )
            + form.cleaned_data['cv_experiences_additional_approval_conditions'],
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


class LateFacultyApprovalDecisionView(
    FacultyDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'late-fac-decision-approval'
    urlpatterns = {'late-fac-decision-approval': 'fac-decision/late-fac-decision-approval'}
    template_name = 'admission/general_education/includes/checklist/late_fac_decision_approval_form.html'
    htmx_template_name = 'admission/general_education/includes/checklist/late_fac_decision_approval_form.html'
    permission_required = 'admission.checklist_faculty_decision_transfer_to_sic_with_decision'
    form_class = Form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                ApprouverInscriptionTardiveParFaculteCommand(
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
        context['sic_decision_approval_documents_form'] = self.sic_decision_approval_documents_form
        context['sic_decision_approval_form'] = self.sic_decision_approval_form
        context['sic_decision_free_approval_condition_formset'] = self.sic_decision_free_approval_condition_formset
        context['sic_decision_refusal_final_form'] = self.sic_decision_refusal_final_form
        context['sic_decision_approval_final_form'] = self.sic_decision_approval_final_form
        context['display_sic_decision_approval_info_panel'] = self.display_sic_decision_approval_info_panel()

        # Get information about the decision sending by the SIC if any and only in the final statuses
        sic_decision_status = self.admission.checklist.get('current', {}).get('decision_sic', {})

        if sic_decision_status:
            history_tags = None
            if sic_decision_status.get('statut') == ChoixStatutChecklist.GEST_REUSSITE.name:
                history_tags = [
                    'proposition',
                    'sic-decision',
                    'approval',
                    'message' if self.admission.type_demande == TypeDemande.ADMISSION.name else 'status-changed',
                ]
            elif (
                sic_decision_status.get('statut') == ChoixStatutChecklist.GEST_BLOCAGE.name
                and sic_decision_status.get('extra', {}).get('blocage') == 'refusal'
            ):
                history_tags = ['proposition', 'sic-decision', 'refusal', 'message']

            if history_tags:
                history_entry: Optional[HistoryEntry] = (
                    HistoryEntry.objects.filter(
                        tags__contains=history_tags,
                        object_uuid=self.admission_uuid,
                    )
                    .order_by('-created')
                    .first()
                )

                if history_entry:
                    context['sic_decision_sent_at'] = history_entry.created
                    context['sic_decision_sent_by'] = history_entry.author
                    context['sic_decision_sent_with_email'] = 'message' in history_entry.tags

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
        context['requested_documents_dtos'] = self.sic_decision_approval_form_requestable_documents
        context['a_des_documents_requis_immediat'] = any(
            document.statut_reclamation == StatutReclamationEmplacementDocument.IMMEDIATEMENT.name
            for document in self.sic_decision_approval_form_requestable_documents
        )

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
                    prefix='decision_sic',
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

    def display_sic_decision_approval_info_panel(self):
        """Return true if the sic decision approval info panel should be displayed."""
        admission = self.admission

        current_checklist = admission.checklist.get('current', {})
        sic_checklist = current_checklist.get('decision_sic', {})
        sic_checklist_statuses = ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT[OngletsChecklist.decision_sic.name]

        # The panel is only display in some sic checklist statuses
        display_panel = any(
            sic_checklist_statuses[value].matches_dict(sic_checklist)
            for value in [
                'A_TRAITER',
                'A_COMPLETER',
                'BESOIN_DEROGATION',
                'AUTORISATION_A_VALIDER',
                'AUTORISE',
            ]
        )

        if admission.type_demande == TypeDemande.INSCRIPTION.name:
            return (
                display_panel
                # The faculty does not refuse the enrolment
                and not ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT[OngletsChecklist.decision_facultaire.name][
                    'REFUS'
                ].matches_dict(current_checklist.get(OngletsChecklist.decision_facultaire.name, {}))
                # The enrolment is financeable
                and not ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT[OngletsChecklist.financabilite.name][
                    'NON_FINANCABLE'
                ].matches_dict(current_checklist.get(OngletsChecklist.financabilite.name, {}))
            )

        return display_panel

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

    @cached_property
    def sic_decision_free_approval_condition_formset(self):
        FreeApprovalConditionFormSet = formset_factory(
            form=FreeAdditionalApprovalConditionForm,
            extra=0,
        )

        formset = FreeApprovalConditionFormSet(
            prefix='sic-decision',
            initial=self.admission.freeadditionalapprovalcondition_set.filter(
                related_experience__isnull=True,
            ).values('name_fr', 'name_en')
            if self.request.method != 'POST'
            else None,
            data=self.request.POST if self.request.method == 'POST' else None,
            form_kwargs={
                'candidate_language': self.admission.candidate.language,
            },
        )

        return formset

    @property
    def candidate_cv_program_names_by_experience_uuid(self):
        experiences: QuerySet[EducationalExperience] = EducationalExperience.objects.select_related('program').filter(
            person=self.admission.candidate
        )
        return {
            str(experience.uuid): experience.program.title if experience.program else experience.education_name
            for experience in experiences
        }

    @cached_property
    def sic_decision_approval_form_requestable_documents(self):
        documents = message_bus_instance.invoke(
            RecupererDocumentsPropositionQuery(
                uuid_proposition=self.admission_uuid,
            )
        )
        return [document for document in documents if document.est_reclamable and document.est_a_reclamer]

    @cached_property
    def sic_decision_approval_documents_form(self):
        return SicDecisionApprovalDocumentsForm(
            instance=self.admission,
            documents=self.sic_decision_approval_form_requestable_documents,
        )

    @cached_property
    def sic_decision_approval_form(self):
        return SicDecisionApprovalForm(
            academic_year=self.admission.determined_academic_year.year,
            instance=self.admission,
            data=self.request.POST
            if self.request.method == 'POST'
            and 'sic-decision-approval-program_planned_years_number' in self.request.POST
            else None,
            prefix='sic-decision-approval',
            educational_experience_program_name_by_uuid=self.candidate_cv_program_names_by_experience_uuid,
            candidate_nationality_is_no_ue_5=self.proposition.candidat_a_nationalite_hors_ue_5,
        )

    @cached_property
    def sic_director(self) -> Optional[Person]:
        now = timezone.now()
        director = (
            Person.objects.filter(
                mandatary__mandate__entity__entityversion__acronym=ENTITY_SIC,
                mandatary__mandate__function=MandateTypes.DIRECTOR.name,
            )
            .filter(
                mandatary__start_date__lte=now,
                mandatary__end_date__gte=now,
            )
            .first()
        )
        return director

    @cached_property
    def sic_decision_refusal_final_form(self):
        with_email = self.proposition.type_de_refus != TypeDeRefus.REFUS_LIBRE.name
        subject = ''
        body = ''

        if with_email:
            tokens = {
                "admission_reference": self.proposition.reference,
                "candidate": (
                    f"{self.proposition.profil_soumis_candidat.prenom} "
                    f"{self.proposition.profil_soumis_candidat.nom}"
                )
                if self.proposition.profil_soumis_candidat
                else "",
                "academic_year": f"{self.proposition.formation.annee}-{self.proposition.formation.annee + 1}",
                "admission_training": f"{self.proposition.formation.sigle} / {self.proposition.formation.intitule}",
                "document_link": EMAIL_TEMPLATE_DOCUMENT_URL_TOKEN,
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
            if self.request.method == 'POST' and 'sic-decision-refusal-final-submitted' in self.request.POST
            else None,
            prefix='sic-decision-refusal-final',
            initial={
                'subject': subject,
                'body': body,
            },
            with_email=with_email,
        )

    @cached_property
    def sic_decision_approval_final_form(self):
        candidate = self.admission.candidate

        training_title = {
            settings.LANGUAGE_CODE_FR: self.proposition.formation.intitule_fr,
            settings.LANGUAGE_CODE_EN: self.proposition.formation.intitule,
        }[candidate.language]

        tokens = {
            'admission_reference': self.proposition.reference,
            'candidate_first_name': self.proposition.prenom_candidat,
            'candidate_last_name': self.proposition.nom_candidat,
            'academic_year': format_academic_year(self.proposition.formation.annee),
            'academic_year_start_date': date_format(self.proposition.formation.date_debut),
            'admission_email': self.proposition.formation.campus_inscription.email_inscription_sic,
            'enrollment_authorization_document_link': EMAIL_TEMPLATE_ENROLLMENT_AUTHORIZATION_DOCUMENT_URL_TOKEN,
            'visa_application_document_link': EMAIL_TEMPLATE_VISA_APPLICATION_DOCUMENT_URL_TOKEN,
            'greetings': get_salutation_prefix(self.admission.candidate),
            'training_title': training_title,
            'admission_link_front': get_portal_admission_url('general-education', self.admission_uuid),
            'admission_link_back': get_backoffice_admission_url('general-education', self.admission_uuid),
            'training_campus': self.proposition.formation.campus.nom,
            'training_acronym': self.proposition.formation.sigle,
        }

        if self.proposition.type == TypeDemande.ADMISSION.name:
            if self.admission.candidate.country_of_citizenship.european_union:
                template_name = ADMISSION_EMAIL_SIC_APPROVAL_EU
            else:
                template_name = ADMISSION_EMAIL_SIC_APPROVAL
        else:
            with translation.override(self.admission.candidate.language):
                contact_person_paragraph = ''
                nom = self.proposition.nom_personne_contact_programme_annuel_annuel
                email = self.proposition.email_personne_contact_programme_annuel_annuel
                if nom or email:
                    contact = ''
                    if nom:
                        contact = nom
                    if nom and email:
                        contact += ', '
                    if email:
                        contact += f'<a href="{email}">{email}</a>'

                    contact_person_paragraph = _(
                        "<p>Contact person for setting up your annual programme: {contact}</p>"
                    ).format(contact=contact)

                planned_years_paragraph = ''
                years = self.proposition.nombre_annees_prevoir_programme
                if years:
                    planned_years_paragraph = ngettext(
                        "<p>Course duration: 1 year</p>",
                        "<p>Course duration: {years} years</p>",
                        years,
                    ).format(years=years)

                prerequisite_courses_paragraph = ''
                if self.proposition.avec_complements_formation:
                    link = get_training_url(
                        training_type=self.admission.training.education_group_type.name,
                        training_acronym=self.admission.training.acronym,
                        partial_training_acronym=self.admission.training.partial_acronym,
                        suffix='cond_adm',
                    )
                    prerequisite_courses_paragraph = _(
                        "<p>Depending on your previous experience, your faculty will supplement your annual programme "
                        "with additional classes (for more information: <a href=\"{link}\">{link}</a>).</p>"
                    ).format(link=link)

                prerequisite_courses_detail_paragraph = ''
                if self.proposition.complements_formation:
                    prerequisite_courses_detail_paragraph = "<ul>"
                    for complement_formation in self.proposition.complements_formation:
                        prerequisite_courses_detail_paragraph += f"<li>{complement_formation.code} "
                        if candidate.language == settings.LANGUAGE_CODE_EN and complement_formation.full_title_en:
                            prerequisite_courses_detail_paragraph += complement_formation.full_title_en
                        else:
                            prerequisite_courses_detail_paragraph += complement_formation.full_title
                        if complement_formation.credits:
                            prerequisite_courses_detail_paragraph += f"({complement_formation.full_title} ECTS)"
                        prerequisite_courses_detail_paragraph += '</li>'
                    prerequisite_courses_detail_paragraph += "</ul>"
                if self.proposition.commentaire_complements_formation:
                    prerequisite_courses_detail_paragraph += self.proposition.commentaire_complements_formation

                # Documents
                documents_resume: ResumeEtEmplacementsDocumentsPropositionDTO = message_bus_instance.invoke(
                    RecupererResumeEtEmplacementsDocumentsPropositionQuery(
                        uuid_proposition=self.admission_uuid,
                        avec_document_libres=True,
                    )
                )

                experiences_curriculum_par_uuid: Dict[
                    str, Union[ExperienceNonAcademiqueDTO, ExperienceAcademiqueDTO]
                ] = {
                    str(experience.uuid): experience
                    for experience in itertools.chain(
                        documents_resume.resume.curriculum.experiences_non_academiques,
                        documents_resume.resume.curriculum.experiences_academiques,
                    )
                }

                documents = documents_resume.emplacements_documents
                documents_names = []

                for document in documents:
                    if document.est_a_reclamer:
                        document_identifier = document.identifiant.split('.')

                        if (
                            document_identifier[0] == OngletsDemande.CURRICULUM.name
                            and (document_identifier[-1] in CHAMPS_DOCUMENTS_EXPERIENCES_CURRICULUM)
                            and document_identifier[1] in experiences_curriculum_par_uuid
                        ):
                            # For the curriculum experiences, we would like to get the name of the experience
                            documents_names.append(
                                '{document_label} : {cv_xp_label}. {document_communication}'.format(
                                    document_label=document.libelle_langue_candidat,
                                    cv_xp_label=experiences_curriculum_par_uuid[
                                        document_identifier[1]
                                    ].titre_pdf_decision_sic,
                                    document_communication=document.justification_gestionnaire,
                                )
                            )

                        else:
                            documents_names.append(
                                '{document_label}. {document_communication}'.format(
                                    document_label=document.libelle_langue_candidat,
                                    document_communication=document.justification_gestionnaire,
                                )
                            )

                required_documents_paragraph = ''
                if documents_names:
                    required_documents_paragraph = _(
                        "<p>We also wish to inform you that the additional documents below should be sent as soon "
                        "as possible to <a href=\"mailto:{mail}\">{mail}</a>:</p>"
                    ).format(mail=tokens['admission_email'])
                    required_documents_paragraph += '<ul>'
                    for document_name in documents_names:
                        required_documents_paragraph += f'<li>{document_name}</li>'
                    required_documents_paragraph += '</ul>'

                noma = ''
                student = Student.objects.filter(person=self.admission.candidate).values('registration_id').first()
                if student is not None:
                    noma = student['registration_id']

            tokens.update(
                {
                    'noma': noma,
                    'contact_person_paragraph': contact_person_paragraph,
                    'planned_years_paragraph': planned_years_paragraph,
                    'prerequisite_courses_paragraph': prerequisite_courses_paragraph,
                    'prerequisite_courses_detail_paragraph': prerequisite_courses_detail_paragraph,
                    'required_documents_paragraph': required_documents_paragraph,
                }
            )

            template_name = INSCRIPTION_EMAIL_SIC_APPROVAL

        try:
            mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
                template_name,
                self.admission.candidate.language,
            )

            subject = mail_template.render_subject(tokens=tokens)
            body = mail_template.body_as_html(tokens=tokens)
        except EmptyMailTemplateContent:
            subject = ''
            body = ''

        return SicDecisionFinalApprovalForm(
            data=self.request.POST if 'sic-decision-approval-final-subject' in self.request.POST else None,
            prefix='sic-decision-approval-final',
            initial={
                'subject': subject,
                'body': body,
            },
        )


class SicApprovalDecisionView(
    SicDecisionMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'sic-decision-approval'
    urlpatterns = {'sic-decision-approval': 'sic-decision/sic-decision-approval'}
    template_name = 'admission/general_education/includes/checklist/sic_decision_approval_form_for_admission.html'
    htmx_template_name = 'admission/general_education/includes/checklist/sic_decision_approval_form_for_admission.html'
    permission_required = 'admission.checklist_change_sic_decision'

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        formset = self.sic_decision_free_approval_condition_formset

        # Cross validation
        if form.is_valid() and formset.is_valid():
            with_additional_conditions = form.cleaned_data['with_additional_approval_conditions']

            if with_additional_conditions and (
                not form.cleaned_data['additional_approval_conditions']
                and not form.cleaned_data['cv_experiences_additional_approval_conditions']
                and not any(subform.is_valid() for subform in formset)
            ):
                form.add_error('all_additional_approval_conditions', FIELD_REQUIRED_MESSAGE)

        form.all_required_forms_are_valid = form.is_valid() and (
            not form.cleaned_data['with_additional_approval_conditions'] or formset.is_valid()
        )

        if form.all_required_forms_are_valid:
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form(self, form_class=None):
        return self.sic_decision_approval_form

    def get_common_command_kwargs(self, form):
        return dict(
            uuid_proposition=self.admission_uuid,
            gestionnaire=self.request.user.person.global_id,
            avec_conditions_complementaires=form.cleaned_data['with_additional_approval_conditions'],
            uuids_conditions_complementaires_existantes=[
                condition for condition in form.cleaned_data['additional_approval_conditions']
            ],
            conditions_complementaires_libres=(
                [
                    sub_form.cleaned_data
                    for sub_form in self.sic_decision_free_approval_condition_formset.forms
                    if sub_form.is_valid()
                ]
                if form.cleaned_data['with_additional_approval_conditions']
                else []
            )
            + form.cleaned_data['cv_experiences_additional_approval_conditions'],
            avec_complements_formation=form.cleaned_data['with_prerequisite_courses'],
            uuids_complements_formation=form.cleaned_data['prerequisite_courses'],
            commentaire_complements_formation=form.cleaned_data['prerequisite_courses_fac_comment'],
            nombre_annees_prevoir_programme=form.cleaned_data['program_planned_years_number'],
            nom_personne_contact_programme_annuel=form.cleaned_data['annual_program_contact_person_name'],
            email_personne_contact_programme_annuel=form.cleaned_data['annual_program_contact_person_email'],
        )

    def launch_command(self, form):
        message_bus_instance.invoke(
            SpecifierInformationsAcceptationPropositionParSicCommand(
                **self.get_common_command_kwargs(form),
                droits_inscription_montant=form.cleaned_data['tuition_fees_amount'],
                droits_inscription_montant_autre=form.cleaned_data.get('tuition_fees_amount_other', None),
                dispense_ou_droits_majores=form.cleaned_data['tuition_fees_dispensation'],
                tarif_particulier=form.cleaned_data.get('particular_cost', ''),
                refacturation_ou_tiers_payant=form.cleaned_data.get('rebilling_or_third_party_payer', ''),
                annee_de_premiere_inscription_et_statut=form.cleaned_data.get('first_year_inscription_and_status', ''),
                est_mobilite=form.cleaned_data.get('is_mobility', ''),
                nombre_de_mois_de_mobilite=form.cleaned_data.get('mobility_months_amount', ''),
                doit_se_presenter_en_sic=form.cleaned_data.get('must_report_to_sic', False),
                communication_au_candidat=form.cleaned_data['communication_to_the_candidate'],
                doit_fournir_visa_etudes=form.cleaned_data.get('must_provide_student_visa_d', False),
            )
        )

    def form_valid(self, form):
        try:
            self.launch_command(form)
            self.htmx_refresh = True
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        # Reset cached proposition
        del self.proposition
        return super().form_valid(form)


class SicApprovalEnrolmentDecisionView(SicApprovalDecisionView):
    name = 'sic-decision-enrolment-approval'
    urlpatterns = {'sic-decision-enrolment-approval': 'sic-decision/sic-decision-enrolment-approval'}
    template_name = 'admission/general_education/includes/checklist/sic_decision_approval_form_for_enrolment.html'
    htmx_template_name = 'admission/general_education/includes/checklist/sic_decision_approval_form_for_enrolment.html'
    permission_required = 'admission.checklist_change_sic_decision'

    def launch_command(self, form):
        message_bus_instance.invoke(
            SpecifierInformationsAcceptationInscriptionParSicCommand(**self.get_common_command_kwargs(form))
        )


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
            self.htmx_refresh = True
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
                        objet_message=form.cleaned_data.get('subject', ''),
                        corps_message=form.cleaned_data.get('body', ''),
                        auteur=self.request.user.person.global_id,
                    )
                )
            else:
                message_bus_instance.invoke(
                    RefuserInscriptionParSicCommand(
                        uuid_proposition=self.admission_uuid,
                        objet_message=form.cleaned_data.get('subject', ''),
                        corps_message=form.cleaned_data.get('body', ''),
                        auteur=self.request.user.person.global_id,
                    )
                )
            self.htmx_refresh = True
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
                        objet_message=form.cleaned_data['subject'],
                        corps_message=form.cleaned_data['body'],
                        auteur=self.request.user.person.global_id,
                    )
                )
            self.htmx_refresh = True
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        # Invalidate cached_property for status update
        del self.proposition
        return super().form_valid(form)


class SicDecisionDispensationView(
    CheckListDefaultContextMixin,
    AdmissionFormMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'sic-decision-dispensation'
    urlpatterns = {'sic-decision-dispensation': 'sic-decision/dispensation'}
    permission_required = 'admission.checklist_change_sic_decision'
    form_class = SicDecisionDerogationForm
    template_name = 'admission/general_education/includes/checklist/sic_decision_dispensation_needed_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sic_decision_dispensation_form'] = context['form']
        context['reload_sic_statuses'] = True
        return context

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

        # Define checklist info
        try:
            status, extra = self.kwargs['status'].split('-')
            if status == 'GEST_BLOCAGE':
                extra = {'blocage': extra}
            elif status == 'GEST_EN_COURS':
                extra = {'en_cours': extra}
        except ValueError:
            status = self.kwargs['status']
            extra = {}

        # Define global status
        if status == 'GEST_BLOCAGE' and extra == {'blocage': 'closed'}:
            global_status = ChoixStatutPropositionGenerale.CLOTUREE.name
        else:
            global_status = ChoixStatutPropositionGenerale.CONFIRMEE.name

        admission_status_has_changed = admission.status != global_status

        # Save the new statuses
        change_admission_status(
            tab='decision_sic',
            admission_status=status,
            extra=extra,
            replace_extra=True,
            admission=admission,
            global_status=global_status,
            author=self.request.user.person,
        )

        response = self.render_to_response(self.get_context_data())

        # Historize the change of global status
        if admission_status_has_changed:
            checklist_status = onglet_decision_sic.get_status(status=status, extra=extra)
            admission_status = ChoixStatutPropositionGenerale.get_value(global_status)

            checklist_status_labels = {}
            admission_status_labels = {}
            for language in [settings.LANGUAGE_CODE_EN, settings.LANGUAGE_CODE_FR]:
                with translation.override(language):
                    checklist_status_labels[language] = str(checklist_status.libelle if checklist_status else '')
                    admission_status_labels[language] = str(admission_status)

            add_history_entry(
                admission.uuid,
                'Le statut de la proposition a évolué au cours du processus de décision SIC : {} ({}).'.format(
                    admission_status_labels[settings.LANGUAGE_CODE_FR],
                    checklist_status_labels[settings.LANGUAGE_CODE_FR],
                ),
                'The status of the proposal has changed during the SIC decision process: {} ({}).'.format(
                    admission_status_labels[settings.LANGUAGE_CODE_EN],
                    checklist_status_labels[settings.LANGUAGE_CODE_EN],
                ),
                '{first_name} {last_name}'.format(
                    first_name=self.request.user.person.first_name,
                    last_name=self.request.user.person.last_name,
                ),
                tags=['proposition', 'sic-decision', 'status-changed'],
            )
            response.headers['HX-Refresh'] = 'true'
        return response


class SicDecisionApprovalPanelView(HtmxPermissionRequiredMixin, SicDecisionMixin, TemplateView):
    urlpatterns = {'sic-decision-approval-panel': 'sic-decision-approval-panel'}
    template_name = 'admission/general_education/includes/checklist/sic_decision_approval_panel.html'
    htmx_template_name = 'admission/general_education/includes/checklist/sic_decision_approval_panel.html'
    permission_required = 'admission.view_checklist'


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


def get_internal_experiences(matricule_candidat: str) -> List[ExperienceParcoursInterneDTO]:
    return message_bus_instance.invoke(RecupererExperiencesParcoursInterneQuery(matricule=matricule_candidat))


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

    def reset_form_data(self, form):
        form.data = {
            'admission_requirement': self.admission.admission_requirement,
            'admission_requirement_year': self.admission.admission_requirement_year_id,
            'with_prerequisite_courses': self.admission.with_prerequisite_courses,
        }

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
            self.reset_form_data(form)

        except (BusinessException, MultipleBusinessExceptions) as exception:
            self.message_on_failure = (
                exception.exceptions.pop().message
                if isinstance(exception, MultipleBusinessExceptions)
                else exception.message
            )

            self.reset_form_data(form)

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

            internal_experiences = []

            if any(
                title.type_titre == TypeTitreAccesSelectionnable.EXPERIENCE_PARCOURS_INTERNE.name
                for title in access_titles.values()
            ):
                internal_experiences = get_internal_experiences(
                    matricule_candidat=command_result.proposition.matricule_candidat,
                )

            context['selected_access_titles_names'] = get_access_titles_names(
                access_titles=access_titles,
                curriculum_dto=command_result.curriculum,
                etudes_secondaires_dto=command_result.etudes_secondaires,
                internal_experiences=internal_experiences,
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
                    information_a_propos_de_la_restriction=form.cleaned_data[
                        'foreign_access_title_equivalency_restriction_about'
                    ],
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
    @cached_property
    def financability_dispensation_refusal_form(self):
        form_kwargs = {
            'prefix': 'financability-dispensation-refusal',
        }
        if self.request.method == 'POST' and 'financability-dispensation-refusal-reasons' in self.request.POST:
            form_kwargs['data'] = self.request.POST
        else:
            form_kwargs['initial'] = {
                'reasons': [reason.uuid for reason in self.admission.refusal_reasons.all()]
                + self.admission.other_refusal_reasons,
            }

        return FinancabilityDispensationRefusalForm(**form_kwargs)

    @cached_property
    def financability_dispensation_notification_form(self):
        candidate = self.admission.candidate

        training_title = {
            settings.LANGUAGE_CODE_FR: self.proposition.formation.intitule_fr,
            settings.LANGUAGE_CODE_EN: self.proposition.formation.intitule,
        }[candidate.language]

        with override(language=candidate.language):
            greetings = {
                ChoixGenre.H.name: pgettext('male gender', 'Dear'),
                ChoixGenre.F.name: pgettext('female gender', 'Dear'),
                ChoixGenre.X.name: _("For the attention of"),
            }.get(candidate.gender or ChoixGenre.X.name)

            greetings_ends = {
                ChoixGenre.H.name: _('Sir'),
                ChoixGenre.F.name: _('Madam'),
                ChoixGenre.X.name: _("Sir, Madam"),
            }.get(candidate.gender or ChoixGenre.X.name)

        tokens = {
            'admission_reference': self.proposition.reference,
            'candidate_first_name': self.proposition.prenom_candidat,
            'candidate_last_name': self.proposition.nom_candidat,
            'academic_year': format_academic_year(self.proposition.formation.annee),
            'training_title': training_title,
            'training_acronym': self.proposition.formation.sigle,
            'training_campus': self.proposition.formation.campus.nom,
            'greetings': greetings,
            'greetings_end': greetings_ends,
            'contact_link': get_training_url(
                training_type=self.admission.training.education_group_type.name,
                training_acronym=self.admission.training.acronym,
                partial_training_acronym=self.admission.training.partial_acronym,
                suffix='contacts',
            ),
        }

        try:
            mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
                ADMISSION_EMAIL_FINANCABILITY_DISPENSATION_NOTIFICATION,
                self.admission.candidate.language,
            )

            subject = mail_template.render_subject(tokens=tokens)
            body = mail_template.body_as_html(tokens=tokens)
        except EmptyMailTemplateContent:
            subject = ''
            body = ''

        form_kwargs = {
            'prefix': 'financability-dispensation-notification',
        }
        if self.request.method == 'POST' and 'financability-dispensation-notification-body' in self.request.POST:
            form_kwargs['data'] = self.request.POST
        else:
            form_kwargs['initial'] = {
                'subject': subject,
                'body': body,
            }

        return FinancabiliteNotificationForm(**form_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        admission = self.get_permission_object()

        context['financabilite_show_verdict_different_alert'] = (
            (
                admission.checklist['current']['financabilite']['statut']
                in {
                    ChoixStatutChecklist.INITIAL_NON_CONCERNE.name,
                    ChoixStatutChecklist.GEST_REUSSITE.name,
                }
                or (
                    admission.checklist['current']['financabilite']['statut'] == ChoixStatutChecklist.GEST_BLOCAGE.name
                    and admission.checklist['current']['financabilite']['extra'].get('to_be_completed') == '0'
                )
            )
            and admission.financability_rule
            and admission.financability_computed_rule_situation != admission.financability_rule
        )

        context['financabilite_approval_form'] = FinancabiliteApprovalForm(
            instance=self.admission,
            prefix='financabilite-approval',
        )
        context['financabilite_not_financeable_form'] = FinancabiliteNotFinanceableForm(
            instance=self.admission,
            prefix='financabilite-not-financeable',
        )

        context['financability_dispensation_form'] = FinancabiliteDispensationForm(
            is_central_manager=self.request.user.has_perm(
                'admission.checklist_financability_dispensation',
                self.admission,
            ),
            is_program_manager=self.request.user.has_perm(
                'admission.checklist_financability_dispensation_fac',
                self.admission,
            ),
            initial={
                'dispensation_status': self.admission.financability_dispensation_status,
            },
            prefix='financabilite_derogation',
        )

        context['financability_dispensation_refusal_form'] = self.financability_dispensation_refusal_form
        context['financability_dispensation_notification_form'] = self.financability_dispensation_notification_form

        if self.request.htmx:
            comment = CommentEntry.objects.filter(
                object_uuid=self.admission_uuid, tags__contains=['financabilite']
            ).first()
            comment_derogation = CommentEntry.objects.filter(
                object_uuid=self.admission_uuid, tags__contains=['financabilite__derogation']
            ).first()

            context['comment_forms'] = {
                'financabilite': CommentForm(
                    comment=comment,
                    form_url=resolve_url(
                        f'{self.base_namespace}:save-comment',
                        uuid=self.admission_uuid,
                        tab='financabilite',
                    ),
                    prefix='financabilite',
                ),
                'financabilite__derogation': CommentForm(
                    comment=comment_derogation,
                    form_url=resolve_url(
                        f'{self.base_namespace}:save-comment', uuid=self.admission_uuid, tab='financabilite__derogation'
                    ),
                    prefix='financabilite__derogation',
                    label=_('Faculty comment about financability dispensation'),
                    permission='admission.checklist_change_fac_comment',
                ),
            }
            disable_unavailable_forms(
                {
                    comment_form: self.request.user.has_perm(
                        comment_form.permission,
                        self.admission,
                    )
                    for comment_form in context['comment_forms'].values()
                }
            )

        return context


class FinancabiliteComputeRuleView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, TemplateView):
    urlpatterns = {'financability-compute-rule': 'financability-compute-rule'}
    template_name = 'admission/general_education/includes/checklist/financabilite.html'
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        admission = self.get_permission_object()
        admission.update_financability_computed_rule(author=self.request.user.person)
        return self.render_to_response(self.get_context_data())


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
            elif status == 'GEST_EN_COURS':
                extra = {'en_cours': extra}
            elif status == 'GEST_REUSSITE':
                extra = {'reussite': extra}
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

        admission.financability_rule = ''
        admission.financability_rule_established_by = None
        admission.save(update_fields=['financability_rule', 'financability_rule_established_by'])

        return HttpResponseClientRefresh()


class FinancabiliteApprovalSetRuleView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, FormView):
    urlpatterns = {'financability-approval-set-rule': 'financability-checklist-approval-set-rule'}
    template_name = 'admission/general_education/includes/checklist/financabilite_approval_form.html'
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def get_form(self, form_class=None):
        return FinancabiliteApprovalForm(
            instance=self.admission if self.request.method != 'POST' else None,
            data=self.request.POST if self.request.method == 'POST' else None,
            prefix='financabilite-approval',
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

        return HttpResponseClientRefresh()


class FinancabiliteApprovalView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, View):
    urlpatterns = {'financability-approval': 'financability-approval'}
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        message_bus_instance.invoke(
            SpecifierFinancabiliteRegleCommand(
                uuid_proposition=self.admission_uuid,
                financabilite_regle=self.admission.financability_computed_rule_situation,
                etabli_par=self.request.user.person.uuid,
                gestionnaire=self.request.user.person.global_id,
            )
        )

        return HttpResponseClientRefresh()


class FinancabiliteNotFinanceableSetRuleView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, FormView):
    urlpatterns = {'financability-not-financeable-set-rule': 'financability-checklist-not-financeable-set-rule'}
    template_name = 'admission/general_education/includes/checklist/financabilite_non_financable_form.html'
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def get_form(self, form_class=None):
        return FinancabiliteNotFinanceableForm(
            instance=self.admission if self.request.method != 'POST' else None,
            data=self.request.POST if self.request.method == 'POST' else None,
            prefix='financabilite-not-financeable',
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

        return HttpResponseClientRefresh()


class FinancabiliteNotFinanceableView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, View):
    urlpatterns = {'financability-not-financeable': 'financability-not-financeable'}
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        message_bus_instance.invoke(
            SpecifierFinancabiliteRegleCommand(
                uuid_proposition=self.admission_uuid,
                financabilite_regle=self.admission.financability_computed_rule_situation,
                etabli_par=self.request.user.person.uuid,
                gestionnaire=self.request.user.person.global_id,
            )
        )

        return HttpResponseClientRefresh()


class FinancabiliteNotConcernedView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, View):
    urlpatterns = {'financability-not-concerned': 'financability-checklist-not-concerned'}
    template_name = 'admission/general_education/includes/checklist/financabilite.html'
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        message_bus_instance.invoke(
            SpecifierFinancabiliteNonConcerneeCommand(
                uuid_proposition=self.admission_uuid,
                etabli_par=self.request.user.person.uuid,
                gestionnaire=self.request.user.person.global_id,
            )
        )
        return HttpResponseClientRefresh()


class FinancabiliteDerogationNonConcerneView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, TemplateView):
    urlpatterns = {'financability-derogation-non-concerne': 'financability-derogation-non-concerne'}
    template_name = 'admission/general_education/includes/checklist/financabilite.html'
    permission_required = 'admission.checklist_financability_dispensation'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        message_bus_instance.invoke(
            SpecifierDerogationFinancabiliteCommand(
                uuid_proposition=self.admission_uuid,
                statut=DerogationFinancement.NON_CONCERNE.name,
                gestionnaire=self.request.user.person.global_id,
            )
        )

        response = self.render_to_response(self.get_context_data())
        add_close_modal_into_htmx_response(response=response)
        return response


class FinancabiliteDerogationNotificationView(
    AdmissionFormMixin,
    FinancabiliteContextMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    urlpatterns = {'financability-derogation-notification': 'financability-derogation-notification'}
    permission_required = 'admission.checklist_financability_dispensation'
    template_name = (
        htmx_template_name
    ) = 'admission/general_education/includes/checklist/financabilite_derogation_candidat_notifie_form.html'
    htmx_template_name = (
        'admission/general_education/includes/checklist/financabilite_derogation_candidat_notifie_form.html'
    )

    def get_form(self, form_class=None):
        return self.financability_dispensation_notification_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                NotifierCandidatDerogationFinancabiliteCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    objet_message=form.cleaned_data['subject'],
                    corps_message=form.cleaned_data['body'],
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                form.add_error(None, exception.message)
            return self.form_invalid(form)

        return super().form_valid(form)


class FinancabiliteDerogationAbandonCandidatView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, TemplateView):
    urlpatterns = {'financability-derogation-abandon': 'financability-derogation-abandon'}
    template_name = 'admission/general_education/includes/checklist/financabilite.html'
    permission_required = 'admission.checklist_financability_dispensation_fac'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        message_bus_instance.invoke(
            SpecifierDerogationFinancabiliteCommand(
                uuid_proposition=self.admission_uuid,
                statut=DerogationFinancement.ABANDON_DU_CANDIDAT.name,
                gestionnaire=self.request.user.person.global_id,
            )
        )

        response = self.render_to_response(self.get_context_data())
        add_close_modal_into_htmx_response(response=response)
        return response


class FinancabiliteDerogationRefusView(
    AdmissionFormMixin,
    FinancabiliteContextMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    urlpatterns = {'financability-derogation-refus': 'financability-derogation-refus'}
    permission_required = 'admission.checklist_financability_dispensation_fac'
    template_name = (
        htmx_template_name
    ) = 'admission/general_education/includes/checklist/financabilite_derogation_refus_form.html'
    htmx_template_name = 'admission/general_education/includes/checklist/financabilite_derogation_refus_form.html'

    def get_form(self, form_class=None):
        return self.financability_dispensation_refusal_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                SpecifierDerogationFinancabiliteCommand(
                    uuid_proposition=self.admission_uuid,
                    statut=DerogationFinancement.REFUS_DE_DEROGATION_FACULTAIRE.name,
                    gestionnaire=self.request.user.person.global_id,
                    refus_uuids_motifs=form.cleaned_data['reasons'],
                    refus_autres_motifs=form.cleaned_data['other_reasons'],
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                form.add_error(None, exception.message)
            return self.form_invalid(form)

        self.htmx_refresh = True
        return super().form_valid(form)


class FinancabiliteDerogationAccordView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, TemplateView):
    urlpatterns = {'financability-derogation-accord': 'financability-derogation-accord'}
    template_name = 'admission/general_education/includes/checklist/financabilite.html'
    permission_required = 'admission.checklist_financability_dispensation_fac'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        message_bus_instance.invoke(
            SpecifierDerogationFinancabiliteCommand(
                uuid_proposition=self.admission_uuid,
                statut=DerogationFinancement.ACCORD_DE_DEROGATION_FACULTAIRE.name,
                gestionnaire=self.request.user.person.global_id,
            )
        )

        response = self.render_to_response(self.get_context_data())
        add_close_modal_into_htmx_response(response=response)
        response.headers['HX-Refresh'] = 'true'
        return response


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


class ChecklistView(
    PastExperiencesMixin,
    FacultyDecisionMixin,
    FinancabiliteContextMixin,
    SicDecisionMixin,
    RequestApplicationFeesContextDataMixin,
    TemplateView,
):
    urlpatterns = 'checklist'
    template_name = "admission/general_education/checklist.html"
    permission_required = 'admission.view_checklist'

    @cached_property
    def internal_experiences(self) -> List[ExperienceParcoursInterneDTO]:
        return get_internal_experiences(matricule_candidat=self.proposition.matricule_candidat)

    @classmethod
    def checklist_documents_by_tab(cls, specific_questions: List[QuestionSpecifiqueDTO]) -> Dict[str, Set[str]]:
        assimilation_documents = {
            'CARTE_IDENTITE',
            'PASSEPORT',
        }

        for document in DocumentsAssimilation:
            assimilation_documents.add(document)

        secondary_studies_attachments = set(DocumentsEtudesSecondaires.keys())

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
                'DIPLOME_EQUIVALENCE',
                'CURRICULUM',
                'ADDITIONAL_DOCUMENTS',
                *secondary_studies_attachments,
            },
            'donnees_personnelles': assimilation_documents,
            'specificites_formation': {
                'ADDITIONAL_DOCUMENTS',
            },
            'decision_facultaire': {
                'ATTESTATION_ACCORD_FACULTAIRE',
                'ATTESTATION_REFUS_FACULTAIRE',
            },
            f'parcours_anterieur__{OngletsDemande.ETUDES_SECONDAIRES.name}': secondary_studies_attachments,
            'decision_sic': {
                'ATTESTATION_ACCORD_SIC',
                'ATTESTATION_ACCORD_ANNEXE_SIC',
                'ATTESTATION_REFUS_SIC',
                'ATTESTATION_ACCORD_FACULTAIRE',
                'ATTESTATION_REFUS_FACULTAIRE',
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

    @property
    def injection_signaletique(self):
        return EPCInjection.objects.filter(
            admission=self.admission,
            status__in=[
                EPCInjectionStatus.PENDING.name,
                EPCInjectionStatus.NO_SENT.name,
                EPCInjectionStatus.ERROR.name,
            ],
            type=EPCInjectionType.SIGNALETIQUE.name,
        ).first()

    def get_context_data(self, **kwargs):
        from infrastructure.messages_bus import message_bus_instance

        context = super().get_context_data(**kwargs)
        if not self.request.htmx:
            # Retrieve data related to the proposition
            command_result: ResumeEtEmplacementsDocumentsPropositionDTO = message_bus_instance.invoke(
                RecupererResumeEtEmplacementsDocumentsPropositionQuery(uuid_proposition=self.admission_uuid),
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
            tab_names.append('financabilite__derogation')

            comments_labels = {
                'decision_sic__derogation': _('Comment about dispensation'),
                'financabilite__derogation': _('Faculty comment about financability dispensation'),
            }
            comments_permissions = {
                'financabilite__derogation': 'admission.checklist_change_fac_comment',
            }

            context['comment_forms'] = {
                tab_name: CommentForm(
                    comment=comments.get(tab_name, None),
                    form_url=resolve_url(f'{self.base_namespace}:save-comment', uuid=self.admission_uuid, tab=tab_name),
                    prefix=tab_name,
                    label=comments_labels.get(tab_name, None),
                    permission=comments_permissions.get(tab_name, None),
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

            # Documents
            admission_documents = command_result.emplacements_documents

            documents_by_tab = self.checklist_documents_by_tab(specific_questions=specific_questions)

            context['documents'] = {
                tab_name: [
                    admission_document
                    for admission_document in admission_documents
                    if admission_document.identifiant.split('.')[-1] in tab_documents
                ]
                for tab_name, tab_documents in documents_by_tab.items()
            }

            # Experiences
            if self.proposition_fusion:
                merge_curex = (
                    self.proposition_fusion.educational_curex_uuids + self.proposition_fusion.professional_curex_uuids
                )
                self._merge_with_known_curriculum(merge_curex, command_result.resume)
                context['curex_a_fusionner'] = merge_curex

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
                internal_experiences=self.internal_experiences,
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
            last_valuated_admission_by_experience_uuid = {}
            not_valuated_by_current_admission_experiences_uuids = set()

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
                context['authentication_forms'].setdefault(
                    experience_uuid,
                    SinglePastExperienceAuthenticationForm(experience_checklist_info),
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

                # Get the last valuated admission for this experience
                valuated_admissions = getattr(current_experience, 'valorisee_par_admissions', [])

                if valuated_admissions and self.admission_uuid not in valuated_admissions:
                    not_valuated_by_current_admission_experiences_uuids.add(experience_uuid)
                    last_valuated_admission_by_experience_uuid[experience_uuid] = next(
                        (
                            admission
                            for admission in context['toutes_les_demandes']
                            if admission.uuid in valuated_admissions
                        ),
                        None,
                    )

            context['last_valuated_admission_by_experience_uuid'] = last_valuated_admission_by_experience_uuid

            # Remove the experiences that we had in the checklist that have been removed
            children[:] = [child for child in children if child['extra']['identifiant'] in experiences_by_uuid]

            # Order the experiences in chronological order
            ordered_experiences = {}
            if children:
                order = 0

                for annee, experience_list in experiences.items():
                    for experience in experience_list:
                        experience_uuid = str(experience.uuid)
                        if experience_uuid not in ordered_experiences:
                            ordered_experiences[experience_uuid] = order
                            order += 1

                children.sort(key=lambda x: ordered_experiences.get(x['extra']['identifiant'], 0))

            prefixed_past_experiences_documents = []
            documents_from_not_valuated_experiences = []
            context['read_only_documents'] = documents_from_not_valuated_experiences

            # Add the documents related to cv experiences
            for admission_document in admission_documents:
                document_tab_identifier = admission_document.onglet.split('.')

                if document_tab_identifier[0] == OngletsDemande.CURRICULUM.name and len(document_tab_identifier) > 1:
                    tab_identifier = f'parcours_anterieur__{document_tab_identifier[1]}'

                    if document_tab_identifier[1] in not_valuated_by_current_admission_experiences_uuids:
                        documents_from_not_valuated_experiences.append(admission_document.identifiant)

                    if tab_identifier not in context['documents']:
                        context['documents'][tab_identifier] = [admission_document]
                    else:
                        context['documents'][tab_identifier].append(admission_document)

                    prefixed_past_experiences_documents.append(
                        attr.evolve(
                            admission_document,
                            libelle='{experience_name} > {document_name}'.format(
                                experience_name=context['checklist_tabs'].get(tab_identifier, ''),  # Experience name
                                document_name=admission_document.libelle,  # Document name
                            ),
                        )
                    )

            # Sort the documents by label
            for documents in context['documents'].values():
                documents.sort(key=lambda doc: doc.libelle)

            # Some tabs also contain the documents of each experience
            context['documents']['parcours_anterieur'].extend(prefixed_past_experiences_documents)
            context['documents']['financabilite'].extend(prefixed_past_experiences_documents)

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

            context['digit_ticket'] = message_bus_instance.invoke(
                GetStatutTicketPersonneQuery(global_id=self.proposition.matricule_candidat)
            )

            if self.proposition_fusion:
                context['proposition_fusion'] = self.proposition_fusion

        context['injection_signaletique'] = self.injection_signaletique
        return context

    def _merge_with_known_curriculum(self, curex_a_fusionner, resume):
        if curex_a_fusionner:
            curex_existant = message_bus_instance.invoke(
                RechercherParcoursAnterieurQuery(
                    global_id=self.proposition_fusion.matricule,
                    uuid_proposition=self.admission_uuid,
                )
            )
            for experience_non_academique in curex_existant.experiences_non_academiques:
                if str(experience_non_academique.uuid) in curex_a_fusionner:
                    resume.curriculum.experiences_non_academiques.append(experience_non_academique)
            for experience_academique in curex_existant.experiences_academiques:
                if str(experience_academique.uuid) in curex_a_fusionner:
                    resume.curriculum.experiences_academiques.append(experience_academique)

    def _get_experiences(self, resume: ResumePropositionDTO):
        return groupe_curriculum_par_annee_decroissante(
            experiences_academiques=resume.curriculum.experiences_academiques,
            experiences_professionnelles=resume.curriculum.experiences_non_academiques,
            etudes_secondaires=resume.etudes_secondaires,
            experiences_parcours_interne=self.internal_experiences,
        )

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
