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
import json
from typing import Dict, Optional, Union, List

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Value
from django.db.models.functions import Concat
from django.shortcuts import resolve_url
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin

from admission.auth.roles.program_manager import ProgramManager
from admission.constants import (
    COMMENT_TAG_FAC,
    COMMENT_TAG_GLOBAL,
    COMMENT_TAG_SIC,
    CONTEXT_CONTINUING,
    CONTEXT_DOCTORATE,
    CONTEXT_GENERAL,
)
from admission.ddd.admission.doctorat.preparation.commands import (
    GetCotutelleCommand,
    RecupererAdmissionDoctoratQuery,
)
from admission.ddd.admission.doctorat.preparation.commands import (
    RecupererPropositionGestionnaireQuery as RecupererPropositionDoctoraleGestionnaireQuery,
)
from admission.ddd.admission.doctorat.preparation.commands import (
    RecupererQuestionsSpecifiquesQuery as RecupererQuestionsSpecifiquesPropositionDoctoraleQuery,
)
from admission.ddd.admission.doctorat.preparation.dtos import (
    CotutelleDTO,
    PropositionDTO,
)
from admission.ddd.admission.doctorat.preparation.dtos.doctorat import DoctoratDTO
from admission.ddd.admission.doctorat.validation.commands import RecupererDemandeQuery
from admission.ddd.admission.doctorat.validation.dtos import DemandeDTO
from admission.ddd.admission.domain.model.enums.type_gestionnaire import (
    TypeGestionnaire,
)
from admission.ddd.admission.dtos.proposition_fusion_personne import (
    PropositionFusionPersonneDTO,
)
from admission.ddd.admission.dtos.titre_acces_selectionnable import (
    TitreAccesSelectionnableDTO,
)
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.formation_continue.commands import (
    RecupererPropositionQuery,
)
from admission.ddd.admission.formation_continue.commands import (
    RecupererQuestionsSpecifiquesQuery as RecupererQuestionsSpecifiquesPropositionContinueQuery,
)
from admission.ddd.admission.formation_continue.dtos.proposition import (
    PropositionDTO as PropositionContinueDTO,
)
from admission.ddd.admission.formation_generale.commands import (
    RecupererPropositionGestionnaireQuery,
)
from admission.ddd.admission.formation_generale.commands import (
    RecupererQuestionsSpecifiquesQuery as RecupererQuestionsSpecifiquesPropositionGeneraleQuery,
)
from admission.ddd.admission.formation_generale.commands import (
    RecupererTitresAccesSelectionnablesPropositionQuery,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.dtos.proposition import (
    PropositionGestionnaireDTO,
)
from admission.models import (
    ContinuingEducationAdmission,
    DoctorateAdmission,
    EPCInjection,
    GeneralEducationAdmission,
)
from admission.models.base import AdmissionViewer, BaseAdmission
from admission.models.epc_injection import EPCInjectionStatus, EPCInjectionType
from admission.utils import (
    access_title_country,
    add_close_modal_into_htmx_response,
    add_messages_into_htmx_response,
    get_cached_admission_perm_obj,
    get_cached_continuing_education_admission_perm_obj,
    get_cached_general_education_admission_perm_obj,
    person_is_fac_cdd,
    person_is_sic,
)
from admission.views.list import BaseAdmissionList
from base.models.person_merge_proposal import PersonMergeStatus
from ddd.logic.financabilite.domain.model.enums.etat import EtatFinancabilite
from ddd.logic.gestion_des_comptes.dto.periode_soumission_ticket import PeriodeSoumissionTicketDigitDTO
from ddd.logic.gestion_des_comptes.queries import GetPropositionFusionQuery, GetPeriodeActiveSoumissionTicketQuery
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import PermissionRequiredMixin


class AdmissionViewMixin(LoginRequiredMixin, PermissionRequiredMixin, ContextMixin):
    @property
    def admission_uuid(self) -> str:
        return self.kwargs.get('uuid', '')

    @property
    def current_context(self):
        return self.request.resolver_match.namespaces[1]

    @cached_property
    def formatted_current_context(self):
        return self.current_context.replace('-', '_')

    @cached_property
    def base_namespace(self):
        return ':'.join(self.request.resolver_match.namespaces[:2])

    @property
    def admission(self) -> Union[DoctorateAdmission, GeneralEducationAdmission, ContinuingEducationAdmission]:
        return {
            CONTEXT_DOCTORATE: get_cached_admission_perm_obj,
            CONTEXT_GENERAL: get_cached_general_education_admission_perm_obj,
            CONTEXT_CONTINUING: get_cached_continuing_education_admission_perm_obj,
        }[self.current_context](self.admission_uuid)

    def get_permission_object(self):
        return self.admission

    @property
    def is_doctorate(self):
        return self.current_context == CONTEXT_DOCTORATE

    @property
    def is_continuing(self):
        return self.current_context == CONTEXT_CONTINUING

    @property
    def is_general(self):
        return self.current_context == CONTEXT_GENERAL

    @cached_property
    def is_sic(self):
        return person_is_sic(self.request.user.person)

    @cached_property
    def is_fac(self):
        return person_is_fac_cdd(self.request.user.person)

    @cached_property
    def manager_type(self):
        if self.is_sic:
            return TypeGestionnaire.SIC.name

        if self.is_fac:
            return TypeGestionnaire.FAC.name

    @cached_property
    def selectable_access_titles(self) -> Dict[str, TitreAccesSelectionnableDTO]:
        return message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=self.admission_uuid,
            )
        )

    @cached_property
    def selected_access_titles(self):
        return message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=self.admission_uuid,
                seulement_selectionnes=True,
            )
        )

    def get_access_title_country(self):
        return access_title_country(self.selected_access_titles.values())

    @property
    def current_user_name(self):
        return f'{self.request.user.person.first_name} {self.request.user.person.last_name}'

    @cached_property
    def admission_program_managers_names(self):
        return ', '.join(
            ProgramManager.objects.filter(
                education_group_id=self.admission.training.education_group_id,
            )
            .annotate(
                person_name=Concat('person__first_name', Value(' '), 'person__last_name'),
            )
            .values_list('person_name', flat=True)
        )


class LoadDossierViewMixin(AdmissionViewMixin):
    specific_questions_tab: Optional[Onglets] = None

    @cached_property
    def proposition(self) -> Union[PropositionDTO, PropositionGestionnaireDTO, PropositionContinueDTO]:
        cmd = {
            CONTEXT_DOCTORATE: RecupererPropositionDoctoraleGestionnaireQuery(uuid_proposition=self.admission_uuid),
            CONTEXT_CONTINUING: RecupererPropositionQuery(uuid_proposition=self.admission_uuid),
            CONTEXT_GENERAL: RecupererPropositionGestionnaireQuery(uuid_proposition=self.admission_uuid),
        }[self.current_context]
        return message_bus_instance.invoke(cmd)

    @cached_property
    def proposition_fusion(self) -> Optional['PropositionFusionPersonneDTO']:
        return message_bus_instance.invoke(GetPropositionFusionQuery(matricule=self.admission.candidate.global_id))

    @cached_property
    def dossier(self) -> 'DemandeDTO':
        return message_bus_instance.invoke(RecupererDemandeQuery(uuid=self.admission_uuid))

    @cached_property
    def doctorate(self) -> 'DoctoratDTO':
        return message_bus_instance.invoke(RecupererAdmissionDoctoratQuery(doctorat_uuid=self.admission_uuid))

    @cached_property
    def cotutelle(self) -> 'CotutelleDTO':
        return message_bus_instance.invoke(GetCotutelleCommand(uuid_proposition=self.admission_uuid))

    @cached_property
    def specific_questions(self):
        cmd = {
            CONTEXT_DOCTORATE: RecupererQuestionsSpecifiquesPropositionDoctoraleQuery,
            CONTEXT_CONTINUING: RecupererQuestionsSpecifiquesPropositionContinueQuery,
            CONTEXT_GENERAL: RecupererQuestionsSpecifiquesPropositionGeneraleQuery,
        }[self.current_context]

        return message_bus_instance.invoke(
            cmd(
                uuid_proposition=self.admission_uuid,
                onglets=[self.specific_questions_tab.name] if self.specific_questions_tab else None,
            )
        )

    def update_current_admission_on_form_valid(self, form, admission):
        pass

    @cached_property
    def next_url(self):
        url = self.request.GET.get('next', '')
        hash_url = self.request.GET.get('next_hash_url', '')
        return f'{url}#{hash_url}' if hash_url else url

    @property
    def injection_inscription(self):
        return EPCInjection.objects.filter(
            admission=self.admission,
            status__in=[
                EPCInjectionStatus.PENDING.name,
                EPCInjectionStatus.NO_SENT.name,
                EPCInjectionStatus.ERROR.name,
                EPCInjectionStatus.OSIS_ERROR.name,
            ],
            type=EPCInjectionType.DEMANDE.name,
        ).first()

    @property
    def injection_possible(self):
        # Leave this test first so we are sure the other information are available.
        if self.admission.status != ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name:
            return False, "Le dossier doit être en 'Inscription autorisée'"
        periodes_actives = message_bus_instance.invoke(
            GetPeriodeActiveSoumissionTicketQuery()
        )  # type: List[PeriodeSoumissionTicketDigitDTO]
        annees_ouvertes = [p.annee for p in periodes_actives]
        if annees_ouvertes and self.admission.determined_academic_year.year not in annees_ouvertes:
            return False, f"Seules les inscriptions en {annees_ouvertes} sont autorisées"
        contexte = self.admission.get_admission_context()
        if contexte == CONTEXT_GENERAL:
            financabilite_checklist = self.admission.checklist.get('current', {}).get('financabilite', {})
            etat_financabilite = {
                'INITIAL_NON_CONCERNE': EtatFinancabilite.NON_CONCERNE.name,
                'GEST_REUSSITE': EtatFinancabilite.FINANCABLE.name,
            }.get(financabilite_checklist.get('statut'))
            a_une_derogation = financabilite_checklist.get('extra', {}).get('reussite') == 'derogation'
            if etat_financabilite is None:
                return False, "La financabilité doit être 'Financable', 'Non concernée' ou 'Autorisé à poursuivre'"
            elif etat_financabilite == EtatFinancabilite.FINANCABLE.name and (
                (self.admission.financability_rule == '' and not a_une_derogation)
                or self.admission.financability_established_on is None
                or self.admission.financability_established_by_id is None
            ):
                return (
                    False,
                    "Il manque soit la situation de financabilité, soit la date ou l'auteur de la financabilité",
                )
        elif contexte == CONTEXT_CONTINUING:
            if not self.admission.training.specificiufcinformations.registration_required:
                return False, "La formation doit avoir l'inscription au rôle requise"
        personmergeproposal = getattr(self.admission.candidate, 'personmergeproposal', None)
        if not (personmergeproposal and personmergeproposal.registration_id_sent_to_digit):
            return False, "Il manque le noma"
        if not self.admission.candidate.global_id.startswith('00'):
            return False, "Le compte interne n'a pas encore été créé"
        if 'uclouvain.be' not in self.admission.candidate.email:
            return False, "Le candidat n'a toujours pas d'email uclouvain"
        if self.admission.sent_to_epc:
            return False, "La demande a déjà été envoyée dans EPC"
        if self.demande_est_en_quarantaine:
            return False, "La demande est en quarantaine"
        return True, ''

    @cached_property
    def demande_est_en_quarantaine(self) -> bool:
        person_merge_proposal = getattr(self.admission.candidate, 'personmergeproposal', None)
        if person_merge_proposal and (
            person_merge_proposal.status in PersonMergeStatus.quarantine_statuses()
            or not person_merge_proposal.validation.get('valid', True)
        ):
            # Cas display warning when quarantaine
            # (cf. admission/infrastructure/admission/domain/service/lister_toutes_demandes.py)
            return True
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_namespace'] = self.base_namespace
        context['base_template'] = f'admission/{self.formatted_current_context}/tab_layout.html'
        context['original_admission'] = self.admission
        context['next_url'] = self.next_url

        # Get the next and previous admissions from the last computed listing
        cached_admissions_list = cache.get(BaseAdmissionList.cache_key_for_result(user_id=self.request.user.id))

        if cached_admissions_list and self.admission_uuid in cached_admissions_list:
            current_admission = cached_admissions_list[self.admission_uuid]
            for key in ['previous', 'next']:
                if current_admission[key]:
                    context[f'{key}_admission_url'] = resolve_url('admission:base', uuid=current_admission[key])

        context['tab_label_suffixes'] = self.get_tab_label_suffixes()

        if self.specific_questions_tab:
            context['specific_questions'] = self.specific_questions

        if self.is_doctorate:
            context['is_doctorate'] = True
            context['admission'] = self.proposition
        elif self.is_general:
            context['admission'] = self.proposition
            context['access_title_country'] = None  # Will be computed later
        elif self.is_continuing:
            context['admission'] = self.proposition
            context['is_continuing'] = True
        else:
            context['admission'] = self.admission
        context['injection_inscription'] = self.injection_inscription
        context['injection_possible'] = self.injection_possible[0]
        context['raison_injection_impossible'] = self.injection_possible[1]
        context['demande_est_en_quarantaine'] = self.demande_est_en_quarantaine
        context['outil_de_comparaison_et_fusion_url'] = self.get_outil_de_comparaison_et_fusion_url()
        return context

    def get_outil_de_comparaison_et_fusion_url(self) -> str:
        return resolve_url(
            'admission:services:gestion-des-comptes:outil-comparaison-et-fusion', uuid=self.admission_uuid
        )

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'GET' and self.admission_uuid and getattr(request.user, 'person', None) and self.is_sic:
            AdmissionViewer.add_viewer(person=request.user.person, admission=self.admission)

        return super().dispatch(request, *args, **kwargs)

    def get_tab_label_suffixes(self):
        """
        Get elements that will be added after the parent tab labels.
        :return: A dictionary whose the keys are the ids of the parent tabs and the values the content to display.
        """
        tab_label_suffixes = {}

        # Add the number of comments related to the admission
        comments_url = ''
        if self.is_sic:
            comments_url = (
                f"{resolve_url(f'admission:{self.current_context}:sic-comments', uuid=self.admission_uuid)}"
                f"?tags={COMMENT_TAG_SIC},{COMMENT_TAG_GLOBAL}"
            )
        elif self.is_fac:
            comments_url = (
                f"{resolve_url(f'admission:{self.current_context}:fac-comments', uuid=self.admission_uuid)}"
                f"?tags={COMMENT_TAG_FAC},{COMMENT_TAG_GLOBAL}"
            )

        if comments_url:
            tab_label_suffixes['comments'] = mark_safe(
                render_to_string(
                    template_name='admission/includes/badges/comment.html',
                    context={'comments_url': comments_url},
                )
            )

        # Add icon when folder in quarantine
        if self.demande_est_en_quarantaine:
            tab_label_suffixes['person'] = mark_safe('<span class="fa fa-fas fa-warning text-warning"></span>')

        return tab_label_suffixes


class AdmissionFormMixin(AdmissionViewMixin):
    message_on_success = _('Your data have been saved.')
    message_on_failure = _('Some errors have been encountered.')
    update_admission_author = False
    default_htmx_trigger_form_extra = {}
    close_modal_on_htmx_request = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_headers = {}
        self.htmx_refresh = False
        self.htmx_trigger_form_extra = {**self.default_htmx_trigger_form_extra}

    def htmx_trigger_form(self, is_valid: bool):
        """Add a JS event to listen for when the form is submitted through HTMX."""
        self.custom_headers = {
            'HX-Trigger': {
                "formValidation": {
                    "is_valid": is_valid,
                    "message": str(self.message_on_success if is_valid else self.message_on_failure),
                    **self.htmx_trigger_form_extra,
                }
            }
        }

    def update_current_admission_on_form_valid(self, form, admission):
        """Override this method to update the current admission on form valid."""
        pass

    def form_valid(self, form):
        messages.success(self.request, str(self.message_on_success))

        # Update the last update author of the admission
        author = getattr(self.request.user, 'person')
        if self.update_admission_author and author:
            admission = BaseAdmission.objects.get(uuid=self.admission_uuid)
            admission.last_update_author = author
            # Additional updates if needed
            self.update_current_admission_on_form_valid(form, admission)
            admission.save()

        if self.request.htmx:
            self.htmx_trigger_form(is_valid=True)
            response = self.render_to_response(self.get_context_data(form=form))
            if self.htmx_refresh:
                response.headers['HX-Refresh'] = 'true'
            else:
                add_messages_into_htmx_response(request=self.request, response=response)
                if self.close_modal_on_htmx_request:
                    add_close_modal_into_htmx_response(response=response)
            return response

        return super().form_valid(form)

    def get_checklist_redirect_url(self):
        # If specified, return to the correct checklist tab
        if 'next' in self.request.GET:
            url = resolve_url(f'admission:{self.current_context}:checklist', uuid=self.admission_uuid)
            return f"{url}#{self.request.GET['next']}"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        # Add custom headers
        for header_key, header_value in self.custom_headers.items():
            current_data_str = response.headers.get(header_key)
            if current_data_str:
                current_data = json.loads(current_data_str)
                current_data.update(header_value)
            else:
                current_data = header_value
            response.headers[header_key] = json.dumps(current_data)
        return response

    def form_invalid(self, form):
        messages.error(self.request, str(self.message_on_failure))
        response = super().form_invalid(form)
        if self.request.htmx:
            self.htmx_trigger_form(is_valid=False)
            add_messages_into_htmx_response(request=self.request, response=response)
        return response
