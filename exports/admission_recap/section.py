# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
import os
from typing import Optional, List

import weasyprint
from django.conf import settings
from django.utils.translation import gettext as _, pgettext

from admission.ddd import REGIMES_LINGUISTIQUES_SANS_TRADUCTION, BE_ISO_CODE
from admission.ddd.admission.domain.model.formation import est_formation_medecine_ou_dentisterie
from admission.ddd.admission.domain.service.i_elements_confirmation import IElementsConfirmation
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.verifier_curriculum import VerifierCurriculum
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.enums import Onglets
from admission.exports.admission_recap.attachments import (
    Attachment,
    get_identification_attachments,
    get_training_choice_attachments,
    get_secondary_studies_attachments,
    get_curriculum_attachments,
    get_curriculum_academic_experience_attachments,
    get_curriculum_non_academic_experience_attachments,
    get_specific_questions_attachments,
    get_accounting_attachments,
    get_research_project_attachments,
    get_languages_attachments,
    get_cotutelle_attachments,
    get_supervision_group_attachments,
)
from admission.exports.admission_recap.constants import (
    TRAINING_TYPES_WITH_EQUIVALENCE,
    FORMATTED_RELATIONSHIPS,
    CURRICULUM_ACTIVITY_LABEL,
)
from admission.infrastructure.admission.domain.service.calendrier_inscription import CalendrierInscription
from base.models.enums.education_group_types import TrainingType
from osis_profile.models.enums.curriculum import ActivityType


class Section:
    def __init__(
        self,
        label: str,
        content_template,
        context: ResumePropositionDTO,
        extra_context: dict = None,
        attachments: Optional[List[Attachment]] = None,
    ):
        from admission.exports.utils import get_pdf_from_template

        self.attachments = attachments if attachments is not None else []
        self.label = label
        self.content = get_pdf_from_template(
            'admission/exports/recap/base_pdf.html',
            self.get_stylesheets(),
            {
                'content_template_name': content_template,
                'content_title': label,
                'identification': context.identification,
                'coordonnees': context.coordonnees,
                'curriculum': context.curriculum,
                'etudes_secondaires': context.etudes_secondaires,
                'connaissances_langues': context.connaissances_langues,
                'proposition': context.proposition,
                'comptabilite': context.comptabilite,
                'cotutelle': context.groupe_supervision.cotutelle if context.groupe_supervision else None,
                'groupe_supervision': context.groupe_supervision,
                'is_general': context.est_proposition_generale,
                'is_continuing': context.est_proposition_continue,
                'is_doctorate': context.est_proposition_doctorale,
                'for_pdf': True,
                **(extra_context or {}),
            },
        )

    @classmethod
    def get_stylesheets(cls):
        """Get the stylesheets needed to generate the pdf"""
        # Load the stylesheets once and cache them
        if not hasattr(cls, '_stylesheet'):
            setattr(
                cls,
                '_stylesheet',
                [
                    weasyprint.CSS(filename=os.path.join(settings.BASE_DIR, file_path))
                    for file_path in [
                        'base/static/css/bootstrap.min.css',
                        'admission/static/admission/admission.css',
                        'admission/static/admission/base_pdf.css',
                    ]
                ],
            )
        return getattr(cls, '_stylesheet')


def get_identification_section(context) -> Section:
    """Returns the identification section."""
    return Section(
        label=_('Identification'),
        content_template='admission/exports/recap/includes/person.html',
        context=context,
        attachments=get_identification_attachments(context),
    )


def get_coordinates_section(context) -> Section:
    """Returns the coordinates section."""
    return Section(
        label=_('Coordinates'),
        content_template='admission/exports/recap/includes/coordonnees.html',
        context=context,
    )


def get_training_choice_section(context, language, specific_questions_by_tab) -> Section:
    """Returns the training choice section."""
    return Section(
        label=_('Training choice'),
        content_template='admission/exports/recap/includes/training_choice.html',
        context=context,
        extra_context={
            'specific_questions': specific_questions_by_tab[Onglets.CHOIX_FORMATION.name],
        },
        attachments=get_training_choice_attachments(
            context,
            specific_questions_by_tab[Onglets.CHOIX_FORMATION.name],
            language,
        ),
    )


def get_secondary_studies_section(context, language, specific_questions_by_tab) -> Section:
    """Returns the secondary studies section."""
    education_extra_context = {
        'specific_questions': specific_questions_by_tab[Onglets.ETUDES_SECONDAIRES.name],
    }
    if context.etudes_secondaires.diplome_etranger:
        education_extra_context['need_translations'] = (
            context.etudes_secondaires.diplome_etranger.regime_linguistique not in REGIMES_LINGUISTIQUES_SANS_TRADUCTION
        )
        education_extra_context[
            'ue_or_assimilated'
        ] = context.etudes_secondaires.diplome_etranger.pays_membre_ue or est_formation_medecine_ou_dentisterie(
            context.proposition.formation.code_domaine
        )
    return Section(
        label=_('Secondary studies'),
        content_template='admission/exports/recap/includes/education.html',
        extra_context=education_extra_context,
        context=context,
        attachments=get_secondary_studies_attachments(
            context,
            language,
            **education_extra_context,
        ),
    )


def get_curriculum_section(context, language, specific_questions_by_tab) -> Section:
    """Returns the curriculum section."""
    formation = context.proposition.doctorat if context.est_proposition_doctorale else context.proposition.formation

    has_foreign_diploma = any(
        experience.pays != BE_ISO_CODE
        for experience in context.curriculum.experiences_academiques
        if experience.a_obtenu_diplome
    )

    curriculum_extra_context = {
        'display_equivalence': formation.type in TRAINING_TYPES_WITH_EQUIVALENCE and has_foreign_diploma,
        'display_curriculum': formation.type != TrainingType.BACHELOR.name,
        'specific_questions': specific_questions_by_tab[Onglets.CURRICULUM.name],
    }
    return Section(
        label=_('Curriculum'),
        content_template='admission/exports/recap/includes/curriculum.html',
        context=context,
        extra_context=curriculum_extra_context,
        attachments=get_curriculum_attachments(
            context=context,
            language=language,
            **curriculum_extra_context,
        ),
    )


def get_educational_experience_section(context, educational_experience) -> Section:
    """Returns the educational experience section."""
    translation_required = (
        (context.est_proposition_doctorale or context.est_proposition_generale)
        and educational_experience.regime_linguistique
        and educational_experience.regime_linguistique not in REGIMES_LINGUISTIQUES_SANS_TRADUCTION
    )
    return Section(
        label=_('Curriculum') + ' > ' + educational_experience.nom_formation,
        content_template='admission/exports/recap/includes/curriculum_educational_experience.html',
        context=context,
        extra_context={
            'experience': educational_experience,
            'is_foreign_experience': educational_experience.pays != BE_ISO_CODE,
            'is_belgian_experience': educational_experience.pays == BE_ISO_CODE,
            'translation_required': translation_required,
            'evaluation_system_with_credits': educational_experience.systeme_evaluation
            in VerifierCurriculum.SYSTEMES_EVALUATION_AVEC_CREDITS,
        },
        attachments=get_curriculum_academic_experience_attachments(
            context,
            educational_experience,
            translation_required,
        ),
    )


def get_non_educational_experience_section(context, non_educational_experience) -> Section:
    """Returns the non educational experience section."""
    return Section(
        content_template='admission/exports/recap/includes/curriculum_professional_experience.html',
        context=context,
        extra_context={
            'experience': non_educational_experience,
            'CURRICULUM_ACTIVITY_LABEL': CURRICULUM_ACTIVITY_LABEL,
        },
        attachments=get_curriculum_non_academic_experience_attachments(context, non_educational_experience),
        label=_('Curriculum') + ' > ' + ActivityType.get_value(non_educational_experience.type),
    )


def get_specific_questions_section(context, language, specific_questions_by_tab) -> Section:
    """Returns the specific questions section."""
    pools = CalendrierInscription.get_pool_ouverts() if context.est_proposition_generale else []
    eligible_for_reorientation = CalendrierInscription.eligible_a_la_reorientation(
        program=context.proposition.formation.type,
        sigle=context.proposition.formation.sigle,
        proposition=context.proposition,
        pool_ouverts=pools,
    )
    eligible_for_modification = CalendrierInscription.eligible_a_la_modification(
        program=context.proposition.formation.type,
        sigle=context.proposition.formation.sigle,
        proposition=context.proposition,
        pool_ouverts=pools,
    )
    enrolled_for_contingent_training = CalendrierInscription.inscrit_formation_contingentee(
        sigle=context.proposition.formation.sigle,
    )
    extra_context = {
        'specific_questions': specific_questions_by_tab[Onglets.INFORMATIONS_ADDITIONNELLES.name],
        'eligible_for_reorientation': eligible_for_reorientation,
        'eligible_for_modification': eligible_for_modification,
        'enrolled_for_contingent_training': enrolled_for_contingent_training,
    }
    return Section(
        label=_('Specific questions'),
        content_template='admission/exports/recap/includes/specific_question.html',
        context=context,
        extra_context=extra_context,
        attachments=get_specific_questions_attachments(
            context=context,
            specific_questions=extra_context['specific_questions'],
            eligible_for_reorientation=eligible_for_reorientation,
            eligible_for_modification=eligible_for_modification,
            language=language,
        ),
    )


def get_accounting_section(context: ResumePropositionDTO) -> Section:
    """Returns the accounting section."""
    last_fr_institutes = (
        IProfilCandidatTranslator.recuperer_derniers_etablissements_superieurs_communaute_fr_frequentes(
            experiences_academiques=context.curriculum.experiences_academiques,
            annee_minimale=context.curriculum.annee_minimum_a_remplir,
        )
    )
    with_assimilation = context.identification.pays_nationalite_europeen is False
    formatted_relationship = FORMATTED_RELATIONSHIPS.get(context.comptabilite.relation_parente)
    return Section(
        label=_('Accounting'),
        content_template='admission/exports/recap/includes/accounting.html',
        context=context,
        extra_context={
            'last_fr_institutes': last_fr_institutes,
            'with_assimilation': with_assimilation,
            'formatted_relationship': formatted_relationship,
        },
        attachments=get_accounting_attachments(
            context,
            last_fr_institutes,
            with_assimilation,
            formatted_relationship,
        ),
    )


def get_research_project_section(context) -> Section:
    """Returns the research project section."""
    return Section(
        label=_('Research project'),
        content_template='admission/exports/recap/includes/project.html',
        context=context,
        extra_context={
            # There is a bug with translated strings with percent signs
            # https://docs.djangoproject.com/en/3.2/topics/i18n/translation/#troubleshooting-gettext-incorrectly-detects-python-format-in-strings-with-percent-signs
            # xgettext:no-python-format
            'fte_label': _("Full-time equivalent (as %)"),
            # xgettext:no-python-format
            'allocated_time_label': _("Allocated time for the thesis (in %)"),
        },
        attachments=get_research_project_attachments(context),
    )


def get_languages_section(context) -> Section:
    """Returns the languages section."""
    return Section(
        label=_('Languages knowledge'),
        content_template='admission/exports/recap/includes/languages.html',
        context=context,
        attachments=get_languages_attachments(context),
    )


def get_cotutelle_section(context) -> Section:
    """Returns the cotutelle section."""
    return Section(
        label=_('Cotutelle'),
        content_template='admission/exports/recap/includes/cotutelle.html',
        context=context,
        attachments=get_cotutelle_attachments(context),
    )


def get_supervision_section(context) -> Section:
    """Returns the supervision section."""
    return Section(
        label=_('Supervision group'),
        content_template='admission/exports/recap/includes/supervision.html',
        context=context,
        attachments=get_supervision_group_attachments(context),
    )


def get_confirmation_section(context) -> Section:
    """Returns the confirmation section."""
    return Section(
        label=pgettext('tab', 'Confirmation'),
        content_template='admission/exports/recap/includes/confirmation.html',
        context=context,
        extra_context={
            'element_confirmation_title': IElementsConfirmation.TITRE_ELEMENT_CONFIRMATION,
            'undertake_declaration_fields': [
                'justificatifs',
                'declaration_sur_lhonneur',
                'droits_inscription_iufc',
            ],
        },
    )
