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
from typing import Optional, List, Dict

import weasyprint
from django.conf import settings
from django.utils import formats
from django.utils.translation import gettext as _, pgettext, override

from admission.ddd import REGIMES_LINGUISTIQUES_SANS_TRADUCTION, BE_ISO_CODE
from admission.ddd.admission.doctorat.preparation.dtos import ExperienceAcademiqueDTO
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import ExperienceNonAcademiqueDTO
from admission.ddd.admission.domain.model.formation import est_formation_medecine_ou_dentisterie
from admission.ddd.admission.domain.service.i_elements_confirmation import IElementsConfirmation
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.verifier_curriculum import VerifierCurriculum
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.enums import Onglets
from admission.ddd.admission.enums.emplacement_document import OngletsDemande, IdentifiantBaseEmplacementDocument
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
    get_documents_attachments,
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
        identifier,
        content_template,
        context: ResumePropositionDTO,
        sub_identifier='',
        sub_identifier_label='',
        sub_identifier_dates='',
        extra_context: dict = None,
        attachments: Optional[List[Attachment]] = None,
        load_content=False,
    ):
        self.base_identifier = identifier
        self.identifier = f'{identifier.name}.{sub_identifier}' if sub_identifier else identifier.name
        self.label = self._get_label(identifier.value, sub_identifier_label, sub_identifier_dates)
        self.attachments = attachments if attachments is not None else []

        with override(language=context.identification.langue_contact):
            self.candidate_language_label = str(
                self._get_label(
                    identifier.value,
                    sub_identifier_label,
                    sub_identifier_dates,
                )
            )

        if load_content:
            from admission.exports.utils import get_pdf_from_template

            self.content = get_pdf_from_template(
                'admission/exports/recap/base_pdf.html',
                self.get_stylesheets(),
                {
                    'content_template_name': content_template,
                    'content_title': self.label,
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
        else:
            self.content = None

    @staticmethod
    def _get_label(base_label: str, sub_label: str, sub_dates: str):
        label = base_label
        if sub_label:
            label += f' > {sub_label}'
        if sub_dates:
            label += f' ({sub_dates})'
        return label

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


def get_identification_section(context: ResumePropositionDTO, load_content: bool) -> Section:
    """Returns the identification section."""
    return Section(
        identifier=OngletsDemande.IDENTIFICATION,
        content_template='admission/exports/recap/includes/person.html',
        context=context,
        attachments=get_identification_attachments(context),
        load_content=load_content,
    )


def get_coordinates_section(context: ResumePropositionDTO, load_content: bool) -> Section:
    """Returns the coordinates section."""
    return Section(
        identifier=OngletsDemande.COORDONNEES,
        content_template='admission/exports/recap/includes/coordonnees.html',
        context=context,
        load_content=load_content,
    )


def get_training_choice_section(
    context: ResumePropositionDTO,
    specific_questions_by_tab: Dict[str, List[QuestionSpecifiqueDTO]],
    load_content: bool,
) -> Section:
    """Returns the training choice section."""
    return Section(
        identifier=OngletsDemande.CHOIX_FORMATION,
        content_template='admission/exports/recap/includes/training_choice.html',
        context=context,
        extra_context={
            'specific_questions': specific_questions_by_tab[Onglets.CHOIX_FORMATION.name],
        },
        attachments=get_training_choice_attachments(
            specific_questions_by_tab[Onglets.CHOIX_FORMATION.name],
        ),
        load_content=load_content,
    )


def get_secondary_studies_section(
    context: ResumePropositionDTO,
    specific_questions_by_tab: Dict[str, List[QuestionSpecifiqueDTO]],
    load_content: bool,
) -> Section:
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
        identifier=OngletsDemande.ETUDES_SECONDAIRES,
        content_template='admission/exports/recap/includes/education.html',
        extra_context=education_extra_context,
        context=context,
        attachments=get_secondary_studies_attachments(
            context,
            **education_extra_context,
        ),
        load_content=load_content,
    )


def get_curriculum_section(
    context: ResumePropositionDTO,
    specific_questions_by_tab: Dict[str, List[QuestionSpecifiqueDTO]],
    load_content: bool,
) -> Section:
    """Returns the curriculum section."""
    formation = context.proposition.doctorat if context.est_proposition_doctorale else context.proposition.formation

    has_foreign_diploma = any(
        experience.pays != BE_ISO_CODE
        for experience in context.curriculum.experiences_academiques
        if experience.a_obtenu_diplome
    )

    all_foreign_diploma = has_foreign_diploma and all(
        experience.pays != BE_ISO_CODE
        for experience in context.curriculum.experiences_academiques
        if experience.a_obtenu_diplome
    )

    curriculum_extra_context = {
        'display_equivalence': formation.type in TRAINING_TYPES_WITH_EQUIVALENCE and has_foreign_diploma,
        'require_equivalence': formation.type
        in [
            TrainingType.AGGREGATION.name,
            TrainingType.CAPAES.name,
        ]
        and all_foreign_diploma,
        'display_curriculum': formation.type != TrainingType.BACHELOR.name,
        'require_curriculum': formation.type != TrainingType.BACHELOR.name
        and (context.est_proposition_doctorale or context.est_proposition_generale),
        'specific_questions': specific_questions_by_tab[Onglets.CURRICULUM.name],
    }
    return Section(
        identifier=OngletsDemande.CURRICULUM,
        content_template='admission/exports/recap/includes/curriculum.html',
        context=context,
        extra_context=curriculum_extra_context,
        attachments=get_curriculum_attachments(
            context=context,
            **curriculum_extra_context,
        ),
        load_content=load_content,
    )


def get_educational_experience_section(
    context: ResumePropositionDTO,
    educational_experience: ExperienceAcademiqueDTO,
    load_content: bool,
) -> Section:
    """Returns the educational experience section."""
    translation_required = (
        (context.est_proposition_doctorale or context.est_proposition_generale)
        and educational_experience.regime_linguistique
        and educational_experience.regime_linguistique not in REGIMES_LINGUISTIQUES_SANS_TRADUCTION
    )
    min_year = min(educational_experience_year.annee for educational_experience_year in educational_experience.annees)
    max_year = 1 + max(
        educational_experience_year.annee for educational_experience_year in educational_experience.annees
    )
    return Section(
        identifier=OngletsDemande.CURRICULUM,
        sub_identifier=educational_experience.uuid,
        sub_identifier_label=educational_experience.nom_formation,
        sub_identifier_dates=f'{min_year}-{max_year}',
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
        load_content=load_content,
    )


def get_non_educational_experience_section(
    context: ResumePropositionDTO,
    non_educational_experience: ExperienceNonAcademiqueDTO,
    load_content: bool,
) -> Section:
    """Returns the non educational experience section."""
    start_date = formats.date_format(non_educational_experience.date_debut, "m/Y")
    end_date = formats.date_format(non_educational_experience.date_fin, "m/Y")
    return Section(
        identifier=OngletsDemande.CURRICULUM,
        sub_identifier=non_educational_experience.uuid,
        sub_identifier_label=ActivityType.get_value(non_educational_experience.type),
        sub_identifier_dates=f'{start_date} - {end_date}' if start_date != end_date else start_date,
        content_template='admission/exports/recap/includes/curriculum_professional_experience.html',
        context=context,
        extra_context={
            'experience': non_educational_experience,
            'CURRICULUM_ACTIVITY_LABEL': CURRICULUM_ACTIVITY_LABEL,
        },
        attachments=get_curriculum_non_academic_experience_attachments(context, non_educational_experience),
        load_content=load_content,
    )


def get_specific_questions_section(
    context: ResumePropositionDTO,
    specific_questions_by_tab: Dict[str, List[QuestionSpecifiqueDTO]],
    load_content: bool,
) -> Section:
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
        identifier=OngletsDemande.INFORMATIONS_ADDITIONNELLES,
        content_template='admission/exports/recap/includes/specific_question.html',
        context=context,
        extra_context=extra_context,
        attachments=get_specific_questions_attachments(
            context=context,
            specific_questions=extra_context['specific_questions'],
            eligible_for_reorientation=eligible_for_reorientation,
            eligible_for_modification=eligible_for_modification,
        ),
        load_content=load_content,
    )


def get_accounting_section(context: ResumePropositionDTO, load_content: bool) -> Section:
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
        identifier=OngletsDemande.COMPTABILITE,
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
        load_content=load_content,
    )


def get_research_project_section(context, load_content: bool) -> Section:
    """Returns the research project section."""
    return Section(
        identifier=OngletsDemande.PROJET,
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
        load_content=load_content,
    )


def get_languages_section(context: ResumePropositionDTO, load_content: bool) -> Section:
    """Returns the languages section."""
    return Section(
        identifier=OngletsDemande.LANGUES,
        content_template='admission/exports/recap/includes/languages.html',
        context=context,
        attachments=get_languages_attachments(context),
        load_content=load_content,
    )


def get_cotutelle_section(context: ResumePropositionDTO, load_content: bool) -> Section:
    """Returns the cotutelle section."""
    return Section(
        identifier=OngletsDemande.COTUTELLE,
        content_template='admission/exports/recap/includes/cotutelle.html',
        context=context,
        attachments=get_cotutelle_attachments(context),
        load_content=load_content,
    )


def get_supervision_section(context: ResumePropositionDTO, load_content: bool) -> Section:
    """Returns the supervision section."""
    return Section(
        identifier=OngletsDemande.SUPERVISION,
        content_template='admission/exports/recap/includes/supervision.html',
        context=context,
        attachments=get_supervision_group_attachments(context),
        load_content=load_content,
    )


def get_confirmation_section(context: ResumePropositionDTO, load_content: bool) -> Section:
    """Returns the confirmation section."""
    return Section(
        identifier=OngletsDemande.CONFIRMATION,
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
        load_content=load_content,
    )


def get_document_section(
    context: ResumePropositionDTO,
    specific_questions_by_tab: Dict[str, List[QuestionSpecifiqueDTO]],
    load_content: bool,
) -> Section:
    """Returns the requestable free documents."""
    return Section(
        identifier=IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT,
        content_template='admission/exports/recap/includes/documents.html',
        context=context,
        extra_context={
            'specific_questions': specific_questions_by_tab[Onglets.DOCUMENTS.name],
        },
        attachments=get_documents_attachments(
            specific_questions_by_tab[Onglets.DOCUMENTS.name],
        ),
        load_content=load_content,
    )


def get_sections(
    context: ResumePropositionDTO,
    specific_questions: List[QuestionSpecifiqueDTO],
    load_content=False,
    with_free_requestable_documents=False,
):
    specific_questions_by_tab = get_dynamic_questions_by_tab(specific_questions)

    # The PDF contains several sections, each one containing the data following by the related attachments
    pdf_sections = [
        get_identification_section(context, load_content),
        get_coordinates_section(context, load_content),
        get_training_choice_section(context, specific_questions_by_tab, load_content),
    ]

    if context.est_proposition_continue or context.est_proposition_generale:
        pdf_sections.append(get_secondary_studies_section(context, specific_questions_by_tab, load_content))

    if context.est_proposition_doctorale:
        pdf_sections.append(get_languages_section(context, load_content))

    pdf_sections.append(get_curriculum_section(context, specific_questions_by_tab, load_content))

    for educational_experience in context.curriculum.experiences_academiques:
        pdf_sections.append(get_educational_experience_section(context, educational_experience, load_content))

    for non_educational_experience in context.curriculum.experiences_non_academiques:
        pdf_sections.append(get_non_educational_experience_section(context, non_educational_experience, load_content))

    if context.est_proposition_generale or context.est_proposition_continue:
        pdf_sections.append(get_specific_questions_section(context, specific_questions_by_tab, load_content))

    if context.est_proposition_doctorale or context.est_proposition_generale:
        pdf_sections.append(get_accounting_section(context, load_content))

    if context.est_proposition_doctorale:
        pdf_sections += [
            get_research_project_section(context, load_content),
            get_cotutelle_section(context, load_content),
            get_supervision_section(context, load_content),
        ]

    pdf_sections.append(get_confirmation_section(context, load_content))

    if with_free_requestable_documents:
        # Section containing the additional requested documents
        pdf_sections.append(get_document_section(context, specific_questions_by_tab, load_content))

    return pdf_sections


def get_dynamic_questions_by_tab(
    specific_questions: List[QuestionSpecifiqueDTO],
) -> Dict[str, List[QuestionSpecifiqueDTO]]:
    """Returns the dynamic questions by tab."""
    lists = {tab: [] for tab in Onglets.get_names()}
    for question in specific_questions:
        lists[question.onglet].append(question)
    return lists
