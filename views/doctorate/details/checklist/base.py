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
from typing import List, Dict, Set

import attr
from django.conf import settings
from django.shortcuts import resolve_url
from django.template.defaultfilters import truncatechars
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, FormView
from osis_comment.models import CommentEntry
from osis_history.models import HistoryEntry

from admission.contrib.models.epc_injection import EPCInjection
from admission.contrib.models.epc_injection import EPCInjectionStatus, EPCInjectionType
from admission.ddd.admission.commands import GetStatutTicketPersonneQuery, RechercherParcoursAnterieurQuery
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import OngletsChecklist
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.dtos.resume import (
    ResumePropositionDTO,
    ResumeCandidatDTO,
)
from admission.ddd.admission.enums import Onglets, TypeItemFormulaire
from admission.ddd.admission.enums.emplacement_document import (
    DocumentsAssimilation,
    DocumentsEtudesSecondaires,
    OngletsDemande,
)
from admission.ddd.admission.utils import initialiser_checklist_experience
from admission.exports.admission_recap.section import get_dynamic_questions_by_tab
from admission.forms import disable_unavailable_forms
from admission.forms.admission.checklist import (
    SinglePastExperienceAuthenticationForm,
    CommentForm,
    can_edit_experience_authentication,
    AssimilationForm,
)
from admission.forms.doctorate.cdd.send_mail import CddDoctorateSendMailForm
from admission.mail_templates import (
    ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CHECKERS_DOCTORATE,
    ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CANDIDATE_DOCTORATE,
)
from admission.templatetags.admission import authentication_css_class, bg_class_by_checklist_experience
from admission.utils import (
    get_access_titles_names,
)
from admission.views.common.detail_tabs.comments import (
    COMMENT_TAG_SIC_FOR_CDD,
    COMMENT_TAG_CDD_FOR_SIC,
)
from admission.views.common.mixins import AdmissionFormMixin
from admission.views.doctorate.details.checklist.fac_decision import FacultyDecisionMixin
from admission.views.doctorate.details.checklist.financeability import FinancabiliteContextMixin
from admission.views.doctorate.details.checklist.mixins import get_internal_experiences, get_email
from admission.views.doctorate.details.checklist.past_experiences import PastExperiencesMixin
from admission.views.doctorate.details.checklist.sic_decision import SicDecisionMixin
from ddd.logic.shared_kernel.profil.dtos.parcours_interne import ExperienceParcoursInterneDTO
from infrastructure.messages_bus import message_bus_instance
from osis_profile.utils.curriculum import groupe_curriculum_par_annee_decroissante

__namespace__ = False

__all__ = [
    'ChecklistView',
    'ChangeExtraView',
]


TABS_WITH_SIC_AND_FAC_COMMENTS: Set[str] = {'decision_facultaire'}


class ChecklistView(
    PastExperiencesMixin,
    FacultyDecisionMixin,
    FinancabiliteContextMixin,
    SicDecisionMixin,
    TemplateView,
):
    urlpatterns = 'checklist'
    template_name = "admission/doctorate/checklist.html"
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

        documents_by_tab = {
            OngletsChecklist.assimilation.name: assimilation_documents,
            OngletsChecklist.financabilite.name: {
                'DIPLOME_EQUIVALENCE',
                'DIPLOME_BELGE_CERTIFICAT_INSCRIPTION',
                'DIPLOME_ETRANGER_CERTIFICAT_INSCRIPTION',
                'DIPLOME_ETRANGER_TRADUCTION_CERTIFICAT_INSCRIPTION',
                'CURRICULUM',
            },
            OngletsChecklist.choix_formation.name: {},
            OngletsChecklist.parcours_anterieur.name: {
                'ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT',
                'DIPLOME_EQUIVALENCE',
                'CURRICULUM',
                'ADDITIONAL_DOCUMENTS',
            },
            OngletsChecklist.donnees_personnelles.name: assimilation_documents,
            OngletsChecklist.decision_facultaire.name: {
                'ATTESTATION_ACCORD_FACULTAIRE',
            },
            OngletsChecklist.decision_sic.name: {
                'ATTESTATION_ACCORD_SIC',
                'ATTESTATION_ACCORD_ANNEXE_SIC',
                'ATTESTATION_ACCORD_FACULTAIRE',
            },
            'send-email': set(),
        }

        # Add documents from the specific questions
        checklist_target_tab_by_specific_question_tab = {
            Onglets.CURRICULUM.name: OngletsChecklist.parcours_anterieur.name,
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
            return ["admission/doctorate/checklist_menu.html"]
        return ["admission/doctorate/checklist.html"]

    @property
    def injection_signaletique(self):
        return EPCInjection.objects.filter(
            admission=self.admission,
            status__in=[
                EPCInjectionStatus.PENDING.name,
                EPCInjectionStatus.NO_SENT.name,
                EPCInjectionStatus.ERROR.name,
                EPCInjectionStatus.OSIS_ERROR.name,
            ],
            type=EPCInjectionType.SIGNALETIQUE.name,
        ).first()

    def get_context_data(self, **kwargs):
        from infrastructure.messages_bus import message_bus_instance

        context = super().get_context_data(**kwargs)

        if not self.request.htmx:
            # Retrieve data related to the proposition
            command_result = self.proposition_resume

            context['resume_proposition'] = command_result.resume

            context['specific_questions_by_tab'] = get_dynamic_questions_by_tab(
                command_result.resume.questions_specifiques_dtos
            )

            # Initialize forms
            tab_names = list(self.extra_context['checklist_tabs'].keys())

            comments = {
                ('__'.join(c.tags)): c
                for c in CommentEntry.objects.filter(object_uuid=self.admission_uuid, tags__overlap=tab_names)
            }

            for tab in TABS_WITH_SIC_AND_FAC_COMMENTS:
                tab_names.remove(tab)
                tab_names += [f'{tab}__{COMMENT_TAG_SIC_FOR_CDD}', f'{tab}__{COMMENT_TAG_CDD_FOR_SIC}']
            tab_names.append('decision_sic__derogation')
            tab_names.append('financabilite__derogation')

            comments_labels = {
                'decision_sic__derogation': _('Comment about dispensation'),
                'financabilite__derogation': _('Faculty comment about financability dispensation'),
            }
            comments_permissions = {
                'financabilite__derogation': 'admission.checklist_change_fac_comment',
            }

            # Add forms
            context['send_email_form'] = CddDoctorateSendMailForm(
                admission=self.admission,
                view_url=resolve_url('admission:doctorate:send-mail', self.admission_uuid),
            )

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

            documents_by_tab = self.checklist_documents_by_tab(
                specific_questions=command_result.resume.questions_specifiques_dtos
            )

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
                template_identifier=ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CHECKERS_DOCTORATE,
                language=settings.LANGUAGE_CODE_FR,
                proposition_dto=self.proposition,
            )
            context['check_authentication_mail_to_candidate'] = get_email(
                template_identifier=ADMISSION_EMAIL_CHECK_BACKGROUND_AUTHENTICATION_TO_CANDIDATE_DOCTORATE,
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

            # Past experiences
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
                    experience_checklist_info = initialiser_checklist_experience(experience_uuid).to_dict()
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
            read_only_documents = []
            context['read_only_documents'] = read_only_documents

            # Add the documents related to cv experiences
            for admission_document in admission_documents:
                if admission_document.lecture_seule:
                    read_only_documents.append(admission_document.identifiant)
                document_tab_identifier = admission_document.onglet.split('.')

                if document_tab_identifier[0] == OngletsDemande.CURRICULUM.name and len(document_tab_identifier) > 1:
                    tab_identifier = f'parcours_anterieur__{document_tab_identifier[1]}'

                    if document_tab_identifier[1] in not_valuated_by_current_admission_experiences_uuids:
                        read_only_documents.append(admission_document.identifiant)

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
            context['can_choose_access_title_tooltip'] = (
                _(
                    'Changes for the access title are not available when the state of the Previous experience '
                    'is "Sufficient".'
                )
                if context.get('past_experiences_are_sufficient')
                else ''
            )

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
        return experiences


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
