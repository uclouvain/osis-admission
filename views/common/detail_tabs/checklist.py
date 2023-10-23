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
from typing import Dict, Set, Optional

from django.conf import settings
from django.db.models import QuerySet
from django.forms import Form
from django.http import HttpResponse
from django.shortcuts import resolve_url, redirect
from django.urls import reverse
from django.utils import translation
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _, gettext
from django.views.generic import TemplateView, FormView
from osis_comment.models import CommentEntry
from osis_history.models import HistoryEntry
from osis_mail_template.models import MailTemplate
from rest_framework import serializers, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from admission.contrib.models.online_payment import PaymentStatus, PaymentMethod
from admission.ddd import MONTANT_FRAIS_DOSSIER
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.dtos.resume import ResumeEtEmplacementsDocumentsPropositionDTO
from admission.ddd.admission.enums import Onglets, TypeItemFormulaire
from admission.ddd.admission.enums.emplacement_document import DocumentsAssimilation
from admission.ddd.admission.formation_generale.commands import (
    RecupererResumeEtEmplacementsDocumentsNonLibresPropositionQuery,
    ModifierChecklistChoixFormationCommand,
    SpecifierPaiementNecessaireCommand,
    EnvoyerRappelPaiementCommand,
    SpecifierPaiementPlusNecessaireCommand,
    RecupererQuestionsSpecifiquesQuery,
    EnvoyerPropositionAFacLorsDeLaDecisionFacultaireCommand,
    RefuserPropositionParFaculteAvecNouveauxMotifsCommand,
    SpecifierMotifsRefusPropositionParFaculteCommand,
    SpecifierInformationsAcceptationPropositionParFaculteCommand,
    ApprouverPropositionParFaculteCommand,
    RefuserPropositionParFaculteCommand,
    ApprouverPropositionParFaculteAvecNouvellesInformationsCommand,
    RecupererListePaiementsPropositionQuery,
    EnvoyerPropositionAuSicLorsDeLaDecisionFacultaireCommand,
    ModifierStatutChecklistParcoursAnterieurCommand,
    SpecifierConditionAccesPropositionCommand,
    SpecifierEquivalenceTitreAccesEtrangerPropositionCommand,
    SpecifierExperienceEnTantQueTitreAccesCommand,
    RecupererTitresAccesSelectionnablesPropositionQuery,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC,
    ChoixStatutPropositionGenerale,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_ETENDUS,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC_ETENDUS,
)
from admission.forms.admission.checklist import (
    ChoixFormationForm,
    StatusForm,
    PastExperiencesAdmissionRequirementForm,
    PastExperiencesAdmissionAccessTitleForm,
)
from admission.forms.admission.checklist import (
    CommentForm,
    AssimilationForm,
    FacDecisionRefusalForm,
    FacDecisionApprovalForm,
)
from admission.mail_templates import ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL
from admission.utils import (
    get_portal_admission_list_url,
    get_backoffice_admission_url,
    get_portal_admission_url,
)
from admission.utils import person_is_sic, person_is_fac_cdd
from admission.views.common.detail_tabs.comments import COMMENT_TAG_SIC, COMMENT_TAG_FAC
from admission.views.doctorate.mixins import LoadDossierViewMixin, AdmissionFormMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance
from osis_common.ddd.interface import BusinessException
from osis_profile.models import EducationalExperience

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
        },
        'hide_files': True,
    }

    @cached_property
    def is_sic(self):
        return person_is_sic(self.request.user.person)

    @cached_property
    def is_fac(self):
        return person_is_fac_cdd(self.request.user.person)

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
        return context


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

        # Get the email to submit
        mail_template = MailTemplate.objects.get(
            identifier=ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL,
            language=self.admission.candidate.language,
        )

        proposition = self.proposition

        # Needed to get the complete reference
        with translation.override(proposition.langue_contact_candidat):
            tokens = {
                'admission_reference': proposition.reference,
                'candidate_first_name': proposition.prenom_candidat,
                'candidate_last_name': proposition.nom_candidat,
                'training_title': {
                    settings.LANGUAGE_CODE_FR: self.admission.training.title,
                    settings.LANGUAGE_CODE_EN: self.admission.training.title_english,
                }[proposition.langue_contact_candidat],
                'admissions_link_front': get_portal_admission_list_url(),
                'admission_link_front': get_portal_admission_url('general-education', self.admission_uuid),
                'admission_link_back': get_backoffice_admission_url('general-education', self.admission_uuid),
            }

            context['request_message_subject'] = mail_template.render_subject(tokens)
            context['request_message_body'] = mail_template.body_as_html(tokens)

        return context


class PastExperiencesMixin:
    @cached_property
    def past_experiences_admission_requirement_form(self):
        return PastExperiencesAdmissionRequirementForm(instance=self.admission, data=self.request.POST or None)

    @cached_property
    def past_experiences_admission_access_title_equivalency_form(self):
        return PastExperiencesAdmissionAccessTitleForm(instance=self.admission, data=self.request.POST or None)

    @cached_property
    def access_titles(self):
        return message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=self.kwargs['uuid'],
            )
        )

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
            STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC
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
        return context

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
    permission_required = 'admission.checklist_faculty_decision_transfer_to_sic'
    template_name = 'admission/general_education/includes/checklist/fac_decision.html'
    htmx_template_name = 'admission/general_education/includes/checklist/fac_decision.html'
    form_class = Form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                ApprouverPropositionParFaculteCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
                if self.request.GET.get('approval')
                else RefuserPropositionParFaculteCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
                if self.request.GET.get('refusal')
                else EnvoyerPropositionAuSicLorsDeLaDecisionFacultaireCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
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
                'admission.checklist_faculty_decision_transfer_to_sic'
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
        }

        try:
            if 'save-transfer' in self.request.POST:
                message_bus_instance.invoke(
                    RefuserPropositionParFaculteAvecNouveauxMotifsCommand(
                        gestionnaire=self.request.user.person.global_id,
                        **base_params,
                    )
                )
                self.htmx_refresh = True
            else:
                message_bus_instance.invoke(SpecifierMotifsRefusPropositionParFaculteCommand(**base_params))
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
                'admission.checklist_faculty_decision_transfer_to_sic'
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
        }
        try:
            if 'save-transfer' in self.request.POST:
                message_bus_instance.invoke(
                    ApprouverPropositionParFaculteAvecNouvellesInformationsCommand(
                        gestionnaire=self.request.user.person.global_id,
                        **base_params,
                    )
                )
                self.htmx_refresh = True
            else:
                message_bus_instance.invoke(SpecifierInformationsAcceptationPropositionParFaculteCommand(**base_params))
        except MultipleBusinessExceptions as multiple_exceptions:
            self.message_on_failure = multiple_exceptions.exceptions.pop().message
            return self.form_invalid(form)

        return super().form_valid(form)


class ChecklistView(
    PastExperiencesMixin,
    FacultyDecisionMixin,
    RequestApplicationFeesContextDataMixin,
    TemplateView,
):
    urlpatterns = 'checklist'
    template_name = "admission/general_education/checklist.html"
    permission_required = 'admission.view_checklist'

    @classmethod
    def checklist_documents_by_tab(cls) -> Dict[str, Set[str]]:
        assimilation_documents = {
            'CARTE_IDENTITE',
            'PASSEPORT',
        }

        for document in DocumentsAssimilation:
            assimilation_documents.add(document)

        return {
            'assimilation': assimilation_documents,
            'financabilite': set(),
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
            'specificites_formation': set(),
            'decision_facultaire': {
                'ATTESTATION_ACCORD_FACULTAIRE',
                'ATTESTATION_REFUS_FACULTAIRE',
            },
        }

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

            context['questions_specifiques'] = message_bus_instance.invoke(
                RecupererQuestionsSpecifiquesQuery(
                    uuid_proposition=self.admission_uuid,
                    onglets=[Onglets.INFORMATIONS_ADDITIONNELLES.name],
                )
            )

            # Initialize forms
            tab_names = list(self.extra_context['checklist_tabs'].keys())

            comments = {
                ('__'.join(c.tags)): c
                for c in CommentEntry.objects.filter(object_uuid=self.admission_uuid, tags__overlap=tab_names)
            }

            for tab in TABS_WITH_SIC_AND_FAC_COMMENTS:
                tab_names.remove(tab)
                tab_names += [f'{tab}__{COMMENT_TAG_SIC}', f'{tab}__{COMMENT_TAG_FAC}']

            context['comment_forms'] = {
                tab_name: CommentForm(
                    comment=comments.get(tab_name, None),
                    form_url=resolve_url(f'{self.base_namespace}:save-comment', uuid=self.admission_uuid, tab=tab_name),
                    prefix=tab_name,
                    user_is_sic=self.is_sic,
                    user_is_fac=self.is_fac,
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
            question_specifiques_documents_uuids = [
                valeur
                for question in context['questions_specifiques']
                for valeur in (question.valeur if question.valeur else [])
                if question.type == TypeItemFormulaire.DOCUMENT.name
            ]

            context['documents'] = {
                tab_name: [
                    admission_document
                    for admission_document in admission_documents
                    if admission_document.identifiant.split('.')[-1] in tab_documents
                ]
                for tab_name, tab_documents in self.checklist_documents_by_tab().items()
            }
            context['documents']['specificites_formation'] += [
                document
                for document_uuid in question_specifiques_documents_uuids
                for document in admission_documents
                if document_uuid in document.document_uuids
            ]

            # Experiences
            context['experiences'] = self._get_experiences(command_result.resume)

            # Access titles
            context['access_title_url'] = self.access_title_url
            context['access_titles'] = self.access_titles

            context['past_experiences_admission_requirement_form'] = self.past_experiences_admission_requirement_form
            context[
                'past_experiences_admission_access_title_equivalency_form'
            ] = self.past_experiences_admission_access_title_equivalency_form

        return context

    def _get_experiences(self, resume):
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
                    date_courante.year
                    if date_courante.month >= IProfilCandidatTranslator.MOIS_DEBUT_ANNEE_ACADEMIQUE
                    else date_courante.year - 1
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
            elif (
                etudes_secondaires.alternative_secondaires
                and etudes_secondaires.alternative_secondaires.examen_admission_premier_cycle
            ):
                experiences.setdefault(0, []).append(etudes_secondaires)

        experiences = {annee: experiences[annee] for annee in sorted(experiences.keys(), reverse=True)}

        return experiences


class ChangeStatusSerializer(serializers.Serializer):
    tab_name = serializers.CharField()
    status = serializers.ChoiceField(choices=ChoixStatutChecklist.choices(), required=False)
    extra = serializers.DictField(default={}, required=False)


class ApplicationFeesView(
    AdmissionFormMixin,
    RequestApplicationFeesContextDataMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    name = 'application-fees'
    urlpatterns = {'application-fees': 'application-fees/<str:status>'}
    permission_required = 'admission.view_checklist'
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
    permission_required = 'admission.checklist_change_past_experiences'
    template_name = 'admission/general_education/includes/checklist/previous_experiences.html'
    htmx_template_name = 'admission/general_education/includes/checklist/previous_experiences.html'
    form_class = StatusForm

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
                )
            )
        except MultipleBusinessExceptions:
            self.message_on_failure = _(
                "To move to this state, an admission requirement must have been selected and at least one access title "
                "line must be selected in the past experience views.",
            )
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
    permission_required = 'admission.checklist_change_past_experiences'
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
                    condition_acces=form.cleaned_data['admission_requirement'],
                    millesime_condition_acces=form.cleaned_data['admission_requirement_year']
                    and form.cleaned_data['admission_requirement_year'].year,
                )
            )

            # The admission requirement year can be updated via the command
            form.data = {
                'admission_requirement': self.admission.admission_requirement,
                'admission_requirement_year': self.admission.admission_requirement_year_id,
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
    permission_required = 'admission.checklist_change_past_experiences'
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


def change_admission_status(tab, admission_status, extra, admission, replace_extra=False):
    """Change the status of the admission of a specific tab"""

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

    admission.save(update_fields=['checklist'])

    return serializer.data


class ChangeStatusView(LoadDossierViewMixin, APIView):
    urlpatterns = {'change-checklist-status': 'change-checklist-status/<str:tab>/<str:status>'}
    permission_required = 'admission.view_checklist'
    parser_classes = [FormParser]
    authentication_classes = [SessionAuthentication]

    def post(self, request, *args, **kwargs):
        admission = self.get_permission_object()

        serializer_data = change_admission_status(
            tab=self.kwargs['tab'],
            admission_status=self.kwargs['status'],
            extra=request.data.dict(),
            admission=admission,
        )

        return Response(serializer_data, status=status.HTTP_200_OK)


class ChangeExtraView(AdmissionFormMixin, FormView):
    urlpatterns = {'change-checklist-extra': 'change-checklist-extra/<str:tab>'}
    permission_required = 'admission.view_checklist'
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
        admission.save(update_fields=['checklist'])
        return super().form_valid(form)


class SaveCommentView(AdmissionFormMixin, FormView):
    urlpatterns = {'save-comment': 'save-comment/<str:tab>'}
    permission_required = 'admission.view_checklist'
    form_class = CommentForm
    template_name = 'admission/forms/default_form.html'

    @cached_property
    def form_url(self):
        return resolve_url(
            f'{self.base_namespace}:save-comment',
            uuid=self.admission_uuid,
            tab=self.kwargs['tab'],
        )

    @cached_property
    def is_sic(self):
        return person_is_sic(self.request.user.person)

    @cached_property
    def is_fac(self):
        return person_is_fac_cdd(self.request.user.person)

    def get_prefix(self):
        return self.kwargs['tab']

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['form_url'] = self.form_url
        form_kwargs['user_is_sic'] = self.is_sic
        form_kwargs['user_is_fac'] = self.is_fac
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
    permission_required = 'admission.view_checklist'
    template_name = 'admission/general_education/checklist/choix_formation_form.html'
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
        kwargs['has_success_be_experience'] = self.proposition.candidat_a_reussi_experience_academique_belge
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
    permission_required = 'admission.view_checklist'
    template_name = 'admission/general_education/checklist/choix_formation_detail.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.htmx:
            return redirect(
                reverse('admission:general-education:checklist', kwargs={'uuid': self.admission_uuid})
                + '#choix_formation'
            )
        return super().dispatch(request, *args, **kwargs)
