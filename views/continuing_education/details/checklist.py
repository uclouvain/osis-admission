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

from typing import Dict, Set, List

from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, FormView
from osis_comment.models import CommentEntry

from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.dtos.resume import (
    ResumeEtEmplacementsDocumentsPropositionDTO,
)
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.formation_continue.commands import (
    RecupererResumeEtEmplacementsDocumentsNonLibresPropositionQuery,
    RecupererQuestionsSpecifiquesQuery,
)
from admission.exports.admission_recap.section import get_dynamic_questions_by_tab
from admission.forms.admission.checklist import (
    CommentForm,
)
from admission.forms.admission.continuing_education.checklist import StudentReportForm
from admission.views.common.detail_tabs.comments import COMMENT_TAG_FAC
from admission.views.common.mixins import LoadDossierViewMixin, AdmissionFormMixin
from base.utils.htmx import HtmxPermissionRequiredMixin
from osis_role.templatetags.osis_role import has_perm

__namespace__ = False

__all__ = [
    'ChecklistView',
    'FicheEtudiantFormView',
]


class CheckListDefaultContextMixin(LoadDossierViewMixin):
    extra_context = {
        'checklist_tabs': {
            'fiche_etudiant': _("Student report"),
            'decision': _("Decision"),
        },
        'hide_files': True,
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
        context['student_report_form'] = StudentReportForm(instance=self.admission)
        return context


class ChecklistView(
    CheckListDefaultContextMixin,
    TemplateView,
):
    urlpatterns = 'checklist'
    template_name = "admission/continuing_education/checklist.html"
    permission_required = 'admission.view_checklist'

    @classmethod
    def checklist_documents_by_tab(cls, specific_questions: List[QuestionSpecifiqueDTO]) -> Dict[str, Set[str]]:
        documents_by_tab = {
            'fiche_etudiant': {
                'CARTE_IDENTITE',
                'PASSEPORT',
                'COPIE_TITRE_SEJOUR',
                'DOSSIER_ANALYSE',
            }
        }

        # # Add documents from the specific questions
        # checklist_target_tab_by_specific_question_tab = {
        # }
        #
        # for specific_question in specific_questions:
        #     if (
        #         specific_question.type == TypeItemFormulaire.DOCUMENT.name
        #         and specific_question.onglet in checklist_target_tab_by_specific_question_tab
        #     ):
        #         documents_by_tab[checklist_target_tab_by_specific_question_tab[specific_question.onglet]].add(
        #             specific_question.uuid
        #         )

        return documents_by_tab

    def get_template_names(self):
        if self.request.htmx:
            return ["admission/continuing_education/checklist_menu.html"]
        return ["admission/continuing_education/checklist.html"]

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

            # Initialize forms
            tab_names = list(self.extra_context['checklist_tabs'].keys())

            comments = {
                ('__'.join(c.tags)): c
                for c in CommentEntry.objects.filter(object_uuid=self.admission_uuid, tags__overlap=tab_names)
            }

            context['comment_forms'] = {
                tab_name: CommentForm(
                    comment=comments.get(tab_name, None),
                    form_url=resolve_url(f'{self.base_namespace}:save-comment', uuid=self.admission_uuid, tab=tab_name),
                    prefix=tab_name,
                )
                for tab_name in tab_names
            }

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

        return context


class FicheEtudiantFormView(CheckListDefaultContextMixin, AdmissionFormMixin, HtmxPermissionRequiredMixin, FormView):
    name = 'fiche-etudiant'
    urlpatterns = 'fiche-etudiant'
    template_name = 'admission/continuing_education/includes/checklist/fiche_etudiant_form.html'
    htmx_template_name = 'admission/continuing_education/includes/checklist/fiche_etudiant_form.html'
    permission_required = 'admission.view_checklist'
    form_class = StudentReportForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.admission
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
