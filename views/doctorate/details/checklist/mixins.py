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
from typing import List, Set

from django.conf import settings
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _, override
from osis_comment.models import CommentEntry
from osis_mail_template.models import MailTemplate

from admission.ddd import MAIL_VERIFICATEUR_CURSUS
from admission.ddd.admission.commands import ListerToutesDemandesQuery
from admission.ddd.admission.doctorat.preparation.commands import (
    VerifierCurriculumApresSoumissionQuery,
    RecupererResumeEtEmplacementsDocumentsPropositionQuery,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
    OngletsChecklist,
)
from admission.ddd.admission.doctorat.preparation.dtos import PropositionGestionnaireDTO
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO
from admission.ddd.admission.dtos.resume import ResumeEtEmplacementsDocumentsPropositionDTO
from admission.ddd.admission.enums.statut import (
    STATUTS_TOUTE_PROPOSITION_SOUMISE,
    STATUTS_TOUTE_PROPOSITION_SOUMISE_HORS_FRAIS_DOSSIER_OU_ANNULEE,
    STATUTS_TOUTE_PROPOSITION_AUTORISEE,
)
from admission.utils import get_portal_admission_list_url, get_portal_admission_url, get_backoffice_admission_url
from admission.views.common.detail_tabs.comments import COMMENT_TAG_CDD_FOR_SIC
from admission.views.common.mixins import LoadDossierViewMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.entity_version import EntityVersion
from base.models.person_merge_proposal import PersonMergeStatus
from ddd.logic.shared_kernel.profil.commands import RecupererExperiencesParcoursInterneQuery
from ddd.logic.shared_kernel.profil.dtos.parcours_interne import ExperienceParcoursInterneDTO
from epc.models.enums.condition_acces import ConditionAcces
from infrastructure.messages_bus import message_bus_instance
from osis_role.templatetags.osis_role import has_perm


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

    @cached_property
    def missing_curriculum_periods(self):
        try:
            message_bus_instance.invoke(VerifierCurriculumApresSoumissionQuery(uuid_proposition=self.admission_uuid))
            return []
        except MultipleBusinessExceptions as exc:
            return [e.message for e in sorted(exc.exceptions, key=lambda exception: exception.periode[0], reverse=True)]

    @cached_property
    def management_entity_title(self):
        entity = EntityVersion.objects.filter(acronym=self.proposition.formation.sigle_entite_gestion).first()
        return entity.title if entity else ''

    @cached_property
    def proposition_resume(self) -> ResumeEtEmplacementsDocumentsPropositionDTO:
        return message_bus_instance.invoke(
            RecupererResumeEtEmplacementsDocumentsPropositionQuery(uuid_proposition=self.admission_uuid),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        checklist_additional_icons = {}
        checklist_additional_icons_title = {}

        # A SIC user has an additional icon for the decision of the faculty if a fac manager wrote a comment
        if self.is_sic:
            has_comment = (
                CommentEntry.objects.filter(
                    object_uuid=self.admission_uuid,
                    tags__contains=['decision_cdd', COMMENT_TAG_CDD_FOR_SIC],
                )
                .exclude(content='')
                .exists()
            )
            if has_comment:
                checklist_additional_icons['decision_cdd'] = 'fa-regular fa-comment'

        person_merge_proposal = getattr(self.admission.candidate, 'personmergeproposal', None)
        if person_merge_proposal and (
            person_merge_proposal.status in PersonMergeStatus.quarantine_statuses()
            or not person_merge_proposal.validation.get('valid', True)
        ):
            # Cas display warning when quarantaine
            # (cf. admission/infrastructure/admission/domain/service/lister_toutes_demandes.py)
            checklist_additional_icons['donnees_personnelles'] = 'fas fa-warning text-warning'

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


def get_internal_experiences(matricule_candidat: str) -> List[ExperienceParcoursInterneDTO]:
    return message_bus_instance.invoke(RecupererExperiencesParcoursInterneQuery(matricule=matricule_candidat))


def get_email(template_identifier, language, proposition_dto: PropositionGestionnaireDTO, extra_tokens: dict = None):
    mail_template = MailTemplate.objects.filter(
        identifier=template_identifier,
        language=language,
    ).first()

    if not mail_template:
        return '', ''

    if not extra_tokens:
        extra_tokens = {}

    with override(language):
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
            'admission_link_front': get_portal_admission_url('doctorate', str(proposition_dto.uuid)),
            'admission_link_back': get_backoffice_admission_url('doctorate', str(proposition_dto.uuid)),
            'training_campus': proposition_dto.formation.campus.nom,
            'academic_year': proposition_dto.formation.annee,
            **extra_tokens,
        }

        return (
            mail_template.render_subject(tokens),
            mail_template.body_as_html(tokens),
        )
