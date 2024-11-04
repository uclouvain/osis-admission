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
import itertools
from typing import Dict, Optional, Union

from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import resolve_url
from django.utils import translation, timezone
from django.utils.formats import date_format
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _, ngettext
from django.views.generic import TemplateView, FormView
from django.views.generic.base import RedirectView
from osis_comment.models import CommentEntry
from osis_history.models import HistoryEntry
from osis_history.utilities import add_history_entry
from osis_mail_template.exceptions import EmptyMailTemplateContent
from osis_mail_template.models import MailTemplate

from admission.ddd.admission.commands import RechercherParcoursAnterieurQuery
from admission.ddd.admission.doctorat.preparation.commands import (
    RecupererDocumentsPropositionQuery,
    SpecifierInformationsAcceptationPropositionParSicCommand,
    SpecifierInformationsAcceptationInscriptionParSicCommand,
    ApprouverAdmissionParSicCommand,
    ApprouverInscriptionParSicCommand,
    SpecifierBesoinDeDerogationSicCommand,
    RecupererPdfTemporaireDecisionSicQuery,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
    OngletsChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT,
    onglet_decision_sic,
)
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import CurriculumAdmissionDTO
from admission.ddd.admission.enums.emplacement_document import (
    OngletsDemande,
)
from admission.ddd.admission.enums.emplacement_document import (
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.forms.admission.checklist import (
    CommentForm,
    SicDecisionFinalApprovalForm,
    DoctorateSicDecisionApprovalForm,
)
from admission.forms.admission.checklist import (
    SicDecisionDerogationForm,
    SicDecisionApprovalDocumentsForm,
)
from admission.infrastructure.utils import CHAMPS_DOCUMENTS_EXPERIENCES_CURRICULUM
from admission.mail_templates import (
    EMAIL_TEMPLATE_ENROLLMENT_GENERATED_NOMA_TOKEN,
    ADMISSION_EMAIL_SIC_APPROVAL_EU_DOCTORATE,
    ADMISSION_EMAIL_SIC_APPROVAL_DOCTORATE,
    INSCRIPTION_EMAIL_SIC_APPROVAL_DOCTORATE,
)
from admission.mail_templates.checklist import (
    EMAIL_TEMPLATE_ENROLLMENT_AUTHORIZATION_DOCUMENT_URL_DOCTORATE_TOKEN,
    EMAIL_TEMPLATE_VISA_APPLICATION_DOCUMENT_URL_DOCTORATE_TOKEN,
    EMAIL_TEMPLATE_CDD_ANNEX_DOCUMENT_URL_DOCTORATE_TOKEN,
)
from admission.utils import (
    get_backoffice_admission_url,
    get_portal_admission_url,
    get_salutation_prefix,
    format_academic_year,
    get_training_url,
)
from admission.views.common.detail_tabs.checklist import change_admission_status
from admission.views.common.mixins import LoadDossierViewMixin, AdmissionFormMixin
from admission.views.doctorate.details.checklist.mixins import CheckListDefaultContextMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.enums.mandate_type import MandateTypes
from base.models.person import Person
from base.utils.htmx import HtmxPermissionRequiredMixin
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import ExperienceNonAcademiqueDTO, ExperienceAcademiqueDTO
from infrastructure.messages_bus import message_bus_instance
from osis_common.ddd.interface import BusinessException
from osis_document.utils import get_file_url

__all__ = [
    'SicApprovalDecisionView',
    'SicApprovalEnrolmentDecisionView',
    'SicApprovalFinalDecisionView',
    'SicDecisionApprovalPanelView',
    'SicDecisionDispensationView',
    'SicDecisionChangeStatusView',
    'SicDecisionPdfPreviewView',
]


__namespace__ = False


ENTITY_SIC = 'SIC'


class SicDecisionMixin(CheckListDefaultContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
                and not ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT[OngletsChecklist.decision_cdd.name][
                    'REFUS'
                ].matches_dict(current_checklist.get(OngletsChecklist.decision_cdd.name, {}))
                # The enrolment is financeable
                and not ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT[OngletsChecklist.financabilite.name][
                    'NON_FINANCABLE'
                ].matches_dict(current_checklist.get(OngletsChecklist.financabilite.name, {}))
            )

        return display_panel

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
            context=self.current_context,
        )

    @cached_property
    def sic_decision_approval_form(self):
        return DoctorateSicDecisionApprovalForm(
            academic_year=self.admission.determined_academic_year.year,
            instance=self.admission,
            data=self.request.POST
            if self.request.method == 'POST'
            and 'sic-decision-approval-program_planned_years_number' in self.request.POST
            else None,
            prefix='sic-decision-approval',
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
            'enrollment_authorization_document_link': (
                EMAIL_TEMPLATE_ENROLLMENT_AUTHORIZATION_DOCUMENT_URL_DOCTORATE_TOKEN
            ),
            'visa_application_document_link': EMAIL_TEMPLATE_VISA_APPLICATION_DOCUMENT_URL_DOCTORATE_TOKEN,
            'cdd_annex_document_link': EMAIL_TEMPLATE_CDD_ANNEX_DOCUMENT_URL_DOCTORATE_TOKEN,
            'greetings': get_salutation_prefix(self.admission.candidate),
            'training_title': training_title,
            'admission_link_front': get_portal_admission_url('doctorate', self.admission_uuid),
            'admission_link_back': get_backoffice_admission_url('doctorate', self.admission_uuid),
            'training_campus': self.proposition.formation.campus.nom,
            'training_acronym': self.proposition.formation.sigle,
        }

        if self.proposition.type == TypeDemande.ADMISSION.name:
            if self.admission.candidate.country_of_citizenship.european_union:
                template_name = ADMISSION_EMAIL_SIC_APPROVAL_EU_DOCTORATE
            else:
                template_name = ADMISSION_EMAIL_SIC_APPROVAL_DOCTORATE
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
                curriculum: CurriculumAdmissionDTO = message_bus_instance.invoke(
                    RechercherParcoursAnterieurQuery(
                        global_id=self.proposition.matricule_candidat,
                        uuid_proposition=self.proposition.uuid,
                    )
                )

                experiences_curriculum_par_uuid: Dict[
                    str, Union[ExperienceNonAcademiqueDTO, ExperienceAcademiqueDTO]
                ] = {
                    str(experience.uuid): experience
                    for experience in itertools.chain(
                        curriculum.experiences_non_academiques,
                        curriculum.experiences_academiques,
                    )
                }

                documents_names = []

                for document in self.sic_decision_approval_form_requestable_documents:
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

            tokens.update(
                {
                    'noma': self.proposition.noma_candidat or EMAIL_TEMPLATE_ENROLLMENT_GENERATED_NOMA_TOKEN,
                    'contact_person_paragraph': contact_person_paragraph,
                    'planned_years_paragraph': planned_years_paragraph,
                    'prerequisite_courses_paragraph': prerequisite_courses_paragraph,
                    'prerequisite_courses_detail_paragraph': prerequisite_courses_detail_paragraph,
                    'required_documents_paragraph': required_documents_paragraph,
                }
            )

            template_name = INSCRIPTION_EMAIL_SIC_APPROVAL_DOCTORATE

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        context['sic_decision_approval_documents_form'] = self.sic_decision_approval_documents_form
        context['sic_decision_approval_form'] = self.sic_decision_approval_form
        return context

    def get_form(self, form_class=None):
        return self.sic_decision_approval_form

    def get_common_command_kwargs(self, form):
        return dict(
            uuid_proposition=self.admission_uuid,
            gestionnaire=self.request.user.person.global_id,
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

    def dispatch(self, request, *args, **kwargs):
        if self.admission.is_in_quarantine:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sic_decision_approval_final_form'] = self.sic_decision_approval_final_form
        context['a_des_documents_requis_immediat'] = any(
            document.statut_reclamation == StatutReclamationEmplacementDocument.IMMEDIATEMENT.name
            for document in self.sic_decision_approval_form_requestable_documents
        )
        return context

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
            global_status = ChoixStatutPropositionDoctorale.CLOTUREE.name
        else:
            global_status = ChoixStatutPropositionDoctorale.CONFIRMEE.name

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
            admission_status = ChoixStatutPropositionDoctorale.get_value(global_status)

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['requested_documents_dtos'] = self.sic_decision_approval_form_requestable_documents
        return context


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
