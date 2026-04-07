# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from collections import defaultdict
from typing import Dict, List, Set

from django.db.models import Q, ExpressionWrapper, BooleanField, Case, When, F, Value, CharField, Subquery, OuterRef, \
    IntegerField
from django.db.models.functions import Concat
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView
from osis_comment.models import CommentEntry

from admission.ddd.admission.doctorat.preparation.domain.model.enums import STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE, \
    ChoixStatutPropositionDoctorale
from admission.ddd.admission.formation_continue.commands import RecupererResumeEtEmplacementsDocumentsPropositionQuery
from admission.ddd.admission.formation_continue.domain.model.enums import OngletsChecklist, \
    STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE, ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import STATUTS_PROPOSITION_GENERALE_NON_SOUMISE, \
    PoursuiteDeCycle, ChoixStatutPropositionGenerale
from admission.ddd.admission.shared_kernel.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.shared_kernel.dtos.resume import ResumeEtEmplacementsDocumentsPropositionDTO
from admission.exports.admission_recap.section import get_dynamic_questions_by_tab
from admission.forms.admission.checklist import AdmissionCommentForm
from admission.forms.admission.continuing_education.checklist import StudentReportForm
from admission.models.base import BaseAdmission
from admission.views.common.detail_tabs.checklist import PropositionFromResumeMixin
from admission.views.common.mixins import AdmissionFormMixin, LoadDossierViewMixin
from base.models.enums.academic_type import AcademicTypes
from base.models.enums.education_group_types import TrainingType
from base.utils.htmx import HtmxPermissionRequiredMixin
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from epc.models.inscription_programme_annuel import InscriptionProgrammeAnnuel
from infrastructure.messages_bus import message_bus_instance
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

        context['can_update_checklist_tab'] = self.can_update_checklist_tab
        context['can_change_payment'] = self.request.user.has_perm('admission.change_payment', self.admission)
        context['can_change_faculty_decision'] = self.request.user.has_perm(
            'admission.checklist_change_faculty_decision',
            self.admission,
        )
        context['student_report_form'] = StudentReportForm(instance=self.admission)
        return context


class ChecklistView(
    PropositionFromResumeMixin,
    CheckListDefaultContextMixin,
    TemplateView,
):
    urlpatterns = 'checklist'
    template_name = "admission/continuing_education/checklist.html"
    permission_required = 'admission.view_checklist'

    @cached_property
    def proposition_resume(self) -> ResumeEtEmplacementsDocumentsPropositionDTO:
        return message_bus_instance.invoke(
            RecupererResumeEtEmplacementsDocumentsPropositionQuery(uuid_proposition=self.admission_uuid)
        )

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


    @cached_property
    def dossiers_admission_annee(self) -> defaultdict[int, list]:
        qs = (
            BaseAdmission.objects
            .filter(
                candidate=self.admission.candidate,
                determined_academic_year=self.admission.determined_academic_year,
            )
            .exclude(
                Q(generaleducationadmission__status__in=STATUTS_PROPOSITION_GENERALE_NON_SOUMISE)
                | Q(continuingeducationadmission__status__in=STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE)
                | Q(doctorateadmission__status__in=STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE)
            )
            .annotate_training_management_entity()
            .annotate_training_management_faculty()
            .annotate_with_reference()
            .annotate(
                est_premiere_annee_bachelier=ExpressionWrapper(
                    Q(training__education_group_type__name=TrainingType.BACHELOR.name)
                    & ~Q(generaleducationadmission__cycle_pursuit=PoursuiteDeCycle.YES.name),
                    output_field=BooleanField(),
                ),
            )
            .annotate(
                training_acronym=Case(
                    When(
                        est_premiere_annee_bachelier=True,
                        then=Concat(
                            F("training__acronym"),
                            Value("-1"),
                        ),
                    ),
                    default=F("training__acronym"),
                    output_field=CharField(),
                ),
                training_full_title=F('training__title'),
                status=Case(
                    When(
                        generaleducationadmission__isnull=False,
                        then=F('generaleducationadmission__status'),
                    ),
                    When(
                        doctorateadmission__isnull=False,
                        then=F('doctorateadmission__status'),
                    ),
                    When(
                        continuingeducationadmission__isnull=False,
                        then=F('continuingeducationadmission__status'),
                    ),
                    default=Value(''),
                    output_field=CharField(),
                ),
                # pas sûr pour ceci (raccourci trop simple pour déterminer la dernière modification de l'état)
                status_date=F('modified_at'),
                admission_type=Case(
                    When(generaleducationadmission__isnull=False, then=Value('generale')),
                    When(doctorateadmission__isnull=False, then=Value('doctorat')),
                    When(continuingeducationadmission__isnull=False, then=Value('continue')),
                    default=Value(''),
                    output_field=CharField(),
                ),
                epc_inscription_status=Subquery(
                    InscriptionProgrammeAnnuel.objects.filter(
                        admission_uuid=OuterRef('uuid'),
                    ).values('etat_inscription')[:1]
                ),
                epc_inscription_date=Subquery(
                    InscriptionProgrammeAnnuel.objects.filter(
                        admission_uuid=OuterRef('uuid'),
                    ).values('date_inscription')[:1]
                ),
                currently_viewed_admission_sort_order=Case(
                    When(uuid=self.admission.uuid, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                ),
                academic_type_order=Case(
                    When(
                        training__academic_type__in=[
                            AcademicTypes.ACADEMIC.name,
                            AcademicTypes.NON_ACADEMIC_CREF.name
                        ], then=Value(0)
                    ),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )).values(
            'uuid',
            'determined_academic_year__year',
            'training_acronym',
            'training_full_title',
            'formatted_reference',
            'submitted_at',
            'status',
            'status_date',
            'admission_type',
            'epc_inscription_status',
            'epc_inscription_date',
            'currently_viewed_admission_sort_order',
            'academic_type_order',
        ).order_by('currently_viewed_admission_sort_order', 'academic_type_order', 'submitted_at', 'training__acronym')

        _status_enums = {
            'generale': ChoixStatutPropositionGenerale,
            'doctorat': ChoixStatutPropositionDoctorale,
            'continue': ChoixStatutPropositionContinue,
        }

        rows_by_year = defaultdict(list)
        for row in qs:
            row = dict(row)
            year = row['determined_academic_year__year']
            admission_type = row.get('admission_type', '')
            status_val = row.get('status', '')
            enum_cls = _status_enums.get(admission_type)
            if enum_cls and status_val:
                try:
                    row['status_display'] = enum_cls.get_value(status_val)
                except Exception:
                    row['status_display'] = status_val
            else:
                row['status_display'] = status_val

            epc_status = row.get('epc_inscription_status', '')
            if epc_status:
                try:
                    row['epc_status_display'] = EtatInscriptionFormation.get_value(epc_status)
                except Exception:
                    row['epc_status_display'] = epc_status
            else:
                row['epc_status_display'] = ''

            rows_by_year[year].append(row)
        return dict(rows_by_year)

    def _get_statuts_epc_autorises(self) -> list[str]:
        return [
            EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            EtatInscriptionFormation.PROVISOIRE.name
        ]

    def _get_statuts_epc_refuses(self) -> list[str]:
        return [
            EtatInscriptionFormation.CESSATION.name,
            EtatInscriptionFormation.EXCLUSION.name,
            EtatInscriptionFormation.DECES.name,
            # ajouter CESSATION FORCEE
            EtatInscriptionFormation.REFUS.name
        ]

    def _get_statuts_epc_en_cours(self) -> list[str]:
        return [
            EtatInscriptionFormation.EN_DEMANDE.name,
            EtatInscriptionFormation.DEMANDE_INCOMPLETE.name,
            # verifier si correspond à demande en ligne
            EtatInscriptionFormation.DEMANDE_INSCRIPTION.name,
            EtatInscriptionFormation.REINSCRIPTION_WEB.name
        ]

    def _get_statuts_epc_erreur(self) -> list[str]:
        return [
            EtatInscriptionFormation.ERREUR.name,
            EtatInscriptionFormation.ANNULATION_IP.name,
            EtatInscriptionFormation.ANNULATION_ETD.name,
            # specifier tout autre relicat EPC
        ]

    def _get_statuts_osis_autorises(self) -> list[str]:
        return [
            ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
            ChoixStatutPropositionContinue.INSCRIPTION_AUTORISEE.name,
            ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
        ]

    def _get_statuts_osis_refuses(self) -> list[str]:
        return [
            ChoixStatutPropositionGenerale.INSCRIPTION_REFUSEE.name,
            ChoixStatutPropositionContinue.INSCRIPTION_REFUSEE.name,
            ChoixStatutPropositionDoctorale.INSCRIPTION_REFUSEE.name,
        ]

    def _get_statuts_osis_en_cours(self) -> list[str]:
        return [
            ChoixStatutPropositionGenerale.CONFIRMEE.name,
            ChoixStatutPropositionContinue.CONFIRMEE.name,
            ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
            ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_SIC.name,
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name,
            ChoixStatutPropositionContinue.A_COMPLETER_POUR_FAC.name,
            ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC.name,
            ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC.name,
            ChoixStatutPropositionContinue.COMPLETEE_POUR_FAC.name,
            ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC.name,
            ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC.name,
            ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC.name,
            ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name,
            ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
            ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name,
            ChoixStatutPropositionDoctorale.RETOUR_DE_FAC.name,
            ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION.name,
            ChoixStatutPropositionDoctorale.ATTENTE_VALIDATION_DIRECTION.name,
            # vérifier Mise en attente et CA à compléter
        ]

    def _get_statuts_osis_erreur(self) -> list[str]:
        return [
            ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
            ChoixStatutPropositionGenerale.CLOTUREE.name,
            ChoixStatutPropositionContinue.CLOTUREE.name,
            ChoixStatutPropositionDoctorale.CLOTUREE.name,
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.htmx:
            # Retrieve data related to the proposition
            command_result = self.proposition_resume

            context['resume_proposition'] = command_result.resume

            specific_questions = command_result.resume.questions_specifiques_dtos

            context['specific_questions_by_tab'] = get_dynamic_questions_by_tab(specific_questions)

            # Initialize forms
            profile_tabs = [
                OngletsChecklist.donnees_personnelles.name,
            ]
            admission_tabs = list(tab for tab in self.extra_context['checklist_tabs'] if tab not in profile_tabs)

            comments = {
                ('__'.join(c.tags)): c
                for c in CommentEntry.objects.filter(
                    Q(
                        object_uuid=self.admission_uuid,
                        tags__overlap=admission_tabs,
                    )
                    | Q(
                        object_uuid=self.admission.candidate.uuid,
                        tags__overlap=profile_tabs,
                    ),
                )
            }

            context['comment_forms'] = {
                tab_name: AdmissionCommentForm(
                    comment=comments.get(tab_name, None),
                    form_url=resolve_url(
                        f'{self.base_namespace}:save-comment',
                        uuid=self.admission_uuid,
                        object_uuid=self.admission.candidate.uuid if tab_name in profile_tabs else self.admission_uuid,
                        tab=tab_name,
                    ),
                    prefix=tab_name,
                )
                for tab_name in itertools.chain(admission_tabs, profile_tabs)
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
                        or admission_document.onglet_checklist_associe == tab_name
                    ],
                    key=lambda doc: (not doc.est_emplacement_document_libre, doc.libelle),
                )
                for tab_name, tab_documents in documents_by_tab.items()
            }

        context['dossiers_admission_annee'] = self.dossiers_admission_annee
        context.update(**{
            'statuts_epc_autorises': self._get_statuts_epc_autorises(),
            'statuts_epc_refuses': self._get_statuts_epc_refuses(),
            'statuts_epc_en_cours': self._get_statuts_epc_en_cours(),
            'statuts_epc_erreur': self._get_statuts_epc_erreur(),
            'statuts_osis_autorises': self._get_statuts_osis_autorises(),
            'statuts_osis_refuses': self._get_statuts_osis_refuses(),
            'statuts_osis_en_cours': self._get_statuts_osis_en_cours(),
            'statuts_osis_erreur': self._get_statuts_osis_erreur(),
        })

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
        form.instance.last_update_author = self.request.user.person
        form.save()
        return super().form_valid(form)
