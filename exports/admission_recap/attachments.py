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
from io import BytesIO
from typing import List, Optional, Dict

import img2pdf
from django.conf import settings
from django.utils.translation import gettext as _

from admission.constants import IMAGE_MIME_TYPES, DEFAULT_MIME_TYPES
from admission.contrib.models import AdmissionFormItemInstantiation
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixTypeFinancement
from admission.ddd.admission.doctorat.preparation.dtos import ExperienceAcademiqueDTO
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import ExperienceNonAcademiqueDTO
from admission.ddd.admission.domain.validator._should_comptabilite_etre_completee import recuperer_champs_requis_dto
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.enums import TypeItemFormulaire
from admission.exports.admission_recap.constants import CURRICULUM_ACTIVITY_LABEL, ACCOUNTING_LABEL
from base.models.enums.education_group_types import TrainingType
from base.models.enums.got_diploma import GotDiploma
from osis_document.api.utils import get_raw_content_remotely
from osis_profile.models.enums.curriculum import TranscriptType, ActivityType
from osis_profile.models.enums.education import ForeignDiplomaTypes, Equivalence


class Attachment:
    def __init__(self, label: str, uuids: List[str]):
        self.label = label
        self.uuids = uuids

    def get_raw(self, token: Optional[str], metadata: Optional[Dict], default_content: BytesIO) -> BytesIO:
        """
        Returns the raw content of an attachment if a token is specified and the mimetype is supported else a default
        content.
        """
        if token and metadata and metadata.get('mimetype') in DEFAULT_MIME_TYPES:
            raw_content = get_raw_content_remotely(token)
            if not raw_content:
                return default_content
            if metadata.get('mimetype') in IMAGE_MIME_TYPES:
                raw_content = img2pdf.convert(raw_content)
            return BytesIO(raw_content)
        return default_content

    def __eq__(self, other):
        return self.label == other.label and self.uuids == other.uuids if isinstance(other, Attachment) else False


def get_identification_attachments(context: ResumePropositionDTO) -> List[Attachment]:
    """Returns the identification attachments."""
    attachments = [Attachment(_('Identity picture'), context.identification.photo_identite)]
    if context.identification.numero_carte_identite or context.identification.numero_registre_national_belge:
        attachments.append(Attachment(_('Identity card (both sides)'), context.identification.carte_identite))
    if context.identification.numero_passeport:
        attachments.append(Attachment(_('Passport'), context.identification.passeport))
    return attachments


def get_secondary_studies_attachments(
    context: ResumePropositionDTO,
    language: str,
    specific_questions: List[AdmissionFormItemInstantiation],
    need_translations: bool = None,
    ue_or_assimilated: bool = None,
) -> List[Attachment]:
    """Returns the secondary studies attachments."""
    attachments = []
    if context.proposition.formation.type == TrainingType.BACHELOR.name:
        if context.etudes_secondaires.diplome_belge:
            attachments.append(Attachment(_('High school diploma'), context.etudes_secondaires.diplome_belge.diplome))
            if context.etudes_secondaires.diplome_etudes_secondaires == GotDiploma.THIS_YEAR.name:
                attachments.append(
                    Attachment(
                        _('Certificate of enrolment or school attendance'),
                        context.etudes_secondaires.diplome_belge.certificat_inscription,
                    )
                )
        elif context.etudes_secondaires.diplome_etranger:
            if context.etudes_secondaires.diplome_etranger.type_diplome == ForeignDiplomaTypes.NATIONAL_BACHELOR.name:
                if ue_or_assimilated:
                    if context.etudes_secondaires.diplome_etranger.equivalence == Equivalence.YES.name:
                        attachments.append(
                            Attachment(
                                _('A double-sided copy of the final equivalence decision'),
                                context.etudes_secondaires.diplome_etranger.decision_final_equivalence_ue,
                            )
                        )
                    elif context.etudes_secondaires.diplome_etranger.equivalence == Equivalence.PENDING.name:
                        attachments.append(
                            Attachment(
                                _('Proof of the final equivalence decision'),
                                context.etudes_secondaires.diplome_etranger.preuve_decision_equivalence,
                            )
                        )
                else:
                    attachments.append(
                        Attachment(
                            _('A double-sided copy of the final equivalence decision'),
                            context.etudes_secondaires.diplome_etranger.decision_final_equivalence_hors_ue,
                        )
                    )

            attachments.append(
                Attachment(_('High school diploma'), context.etudes_secondaires.diplome_etranger.diplome),
            )
            if need_translations:
                attachments.append(
                    Attachment(
                        _('A certified translation of your high school diploma'),
                        context.etudes_secondaires.diplome_etranger.traduction_diplome,
                    )
                )

            if context.etudes_secondaires.diplome_etudes_secondaires == GotDiploma.THIS_YEAR.name and ue_or_assimilated:
                attachments.append(
                    Attachment(
                        _('Certificate of enrolment or school attendance'),
                        context.etudes_secondaires.diplome_etranger.certificat_inscription,
                    )
                )
                if need_translations:
                    attachments.append(
                        Attachment(
                            _('A certified translation of your certificate of enrolment or school attendance'),
                            context.etudes_secondaires.diplome_etranger.traduction_certificat_inscription,
                        )
                    )

            attachments.append(
                Attachment(
                    _('A transcript or your last year at high school'),
                    context.etudes_secondaires.diplome_etranger.releve_notes,
                )
            )
            if need_translations:
                attachments.append(
                    Attachment(
                        _(
                            'A certified translation of your official transcript of marks for your final year of '
                            'secondary education'
                        ),
                        context.etudes_secondaires.diplome_etranger.traduction_releve_notes,
                    )
                )

        elif context.etudes_secondaires.alternative_secondaires:
            attachments.append(
                Attachment(
                    _(
                        'Certificate of successful completion of the admission test for the first cycle of higher '
                        'education'
                    ),
                    context.etudes_secondaires.alternative_secondaires.examen_admission_premier_cycle,
                )
            )

    attachments.extend(get_dynamic_questions_attachments(specific_questions, context, language))

    return attachments


def get_languages_attachments(context: ResumePropositionDTO) -> List[Attachment]:
    """Returns the languages attachments."""
    return [
        Attachment(_('Certificate of language knowledge') + f' - {language.nom_langue}', language.certificat)
        for language in context.connaissances_langues
    ]


def get_curriculum_attachments(
    context: ResumePropositionDTO,
    specific_questions: List[AdmissionFormItemInstantiation],
    language: str,
    display_equivalence: bool,
    display_curriculum: bool,
    **kwargs,
) -> List[Attachment]:
    """Returns the curriculum attachments."""
    attachments = []

    if display_equivalence:
        attachments.append(
            Attachment(
                _(
                    'Decision of equivalence for your diploma(s) giving access to the training, '
                    'if this(these) has(have) been obtained outside Belgium'
                ),
                context.proposition.equivalence_diplome,
            )
        )

    if display_curriculum:
        attachments.append(Attachment(_('Curriculum vitae detailed, dated and signed'), context.proposition.curriculum))

    attachments.extend(get_dynamic_questions_attachments(specific_questions, context, language))

    return attachments


def get_curriculum_academic_experience_attachments(
    context: ResumePropositionDTO,
    experience: ExperienceAcademiqueDTO,
    translation_required: bool,
) -> List[Attachment]:
    """Returns the academic experience attachments."""
    attachments = []
    if context.est_proposition_doctorale or context.est_proposition_generale:
        if experience.type_releve_notes == TranscriptType.ONE_FOR_ALL_YEARS.name:
            attachments.append(Attachment(_('Transcript'), experience.releve_notes))
            if translation_required:
                attachments.append(Attachment(_('Transcript translation'), experience.traduction_releve_notes))
        elif experience.type_releve_notes == TranscriptType.ONE_A_YEAR.name:
            for annee in experience.annees:
                suffix = f' - {annee.annee}'
                attachments.append(Attachment(_('Transcript') + suffix, annee.releve_notes))
                if translation_required:
                    attachments.append(
                        Attachment(
                            _('Transcript translation') + suffix,
                            annee.traduction_releve_notes,
                        )
                    )

    if context.est_proposition_doctorale:
        attachments.append(Attachment(_('Dissertation summary'), experience.resume_memoire))

    attachments.append(Attachment(_('Graduate degree'), experience.diplome))

    if translation_required:
        attachments.append(Attachment(_('Graduate degree translation'), experience.traduction_diplome))

    return attachments


def get_curriculum_non_academic_experience_attachments(
    context: ResumePropositionDTO,
    experience: ExperienceNonAcademiqueDTO,
) -> List[Attachment]:
    """Returns the non academic experience attachments."""
    attachments = []
    if context.est_proposition_doctorale or context.est_proposition_generale:
        if experience.type != ActivityType.OTHER.name:
            attachments.append(Attachment(CURRICULUM_ACTIVITY_LABEL[experience.type], experience.certificat))
        return attachments


def get_specific_questions_attachments(
    context: ResumePropositionDTO,
    specific_questions: List[AdmissionFormItemInstantiation],
    eligible_for_reorientation: bool,
    eligible_for_modification: bool,
    language: str,
) -> List[Attachment]:
    """Returns the specific questions attachments."""
    attachments = []
    if context.est_proposition_continue and context.proposition.pays_nationalite_ue_candidat is False:
        attachments.append(
            Attachment(
                _(
                    'Copy of the residence permit covering the entire course, including the evaluation test '
                    '(except for courses organised online)'
                ),
                context.proposition.copie_titre_sejour,
            )
        )

    if eligible_for_reorientation and context.proposition.est_reorientation_inscription_externe:
        attachments.append(
            Attachment(
                _('Certificate of regular enrolment'),
                context.proposition.attestation_inscription_reguliere,
            )
        )
    if eligible_for_modification and context.proposition.est_modification_inscription_externe:
        attachments.append(
            Attachment(
                _('Registration modification form'),
                context.proposition.formulaire_modification_inscription,
            )
        )
    attachments.extend(get_dynamic_questions_attachments(specific_questions, context, language))
    return attachments


def get_accounting_attachments(
    context: ResumePropositionDTO,
    in_french_institute_during_last_years: bool,
    with_assimilation: bool,
    formatted_relationship: str,
) -> List[Attachment]:
    """Returns the accounting attachments."""
    attachments = []

    if in_french_institute_during_last_years:
        attachments.append(
            Attachment(
                _(
                    'Certificate stating the absence of debts towards the last institution(s) of the French community '
                    'attended since %(year)s'
                )
                % {'year': context.curriculum.annee_minimum_a_remplir},
                context.comptabilite.attestation_absence_dette_etablissement,
            )
        )

    if getattr(context.comptabilite, 'enfant_personnel', None):
        attachments.append(Attachment(_('Staff child certificate'), context.comptabilite.attestation_enfant_personnel))

    if with_assimilation:
        fields = recuperer_champs_requis_dto(
            nom_champ='type_situation_assimilation',
            comptabilite=context.comptabilite,
        )
        for field in fields:
            if field in ACCOUNTING_LABEL:
                label = ACCOUNTING_LABEL[field] % {'person_concerned': formatted_relationship}
                attachments.append(Attachment(label, getattr(context.comptabilite, field)))

    return attachments


def get_research_project_attachments(context: ResumePropositionDTO) -> List[Attachment]:
    """Returns the research project attachments."""
    attachments = []
    if context.proposition.type_financement == ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name:
        attachments.append(Attachment(_('Scholarship proof'), context.proposition.bourse_preuve))

    attachments += [
        Attachment(_('Research project'), context.proposition.documents_projet),
        Attachment(_("Doctoral program proposition"), context.proposition.proposition_programme_doctoral),
        Attachment(_("Complementary training proposition"), context.proposition.projet_formation_complementaire),
        Attachment(_("Gantt graph"), context.proposition.graphe_gantt),
        Attachment(_("Recommendation letters"), context.proposition.lettres_recommandation),
    ]

    return attachments


def get_cotutelle_attachments(context: ResumePropositionDTO) -> List[Attachment]:
    """Returns the cotutelle attachments."""
    attachments = []
    if (
        context.groupe_supervision
        and context.groupe_supervision.cotutelle
        and context.groupe_supervision.cotutelle.cotutelle
    ):
        attachments += [
            Attachment(_('Cotutelle opening request'), context.groupe_supervision.cotutelle.demande_ouverture),
            Attachment(_('Cotutelle convention'), context.groupe_supervision.cotutelle.convention),
            Attachment(
                _('Other documents concerning cotutelle'),
                context.groupe_supervision.cotutelle.autres_documents,
            ),
        ]
    return attachments


def get_supervision_group_attachments(context: ResumePropositionDTO) -> List[Attachment]:
    """Returns the supervision group attachments."""
    attachments = []
    for supervision_member in context.groupe_supervision.signatures_promoteurs:
        attachments.append(
            Attachment(
                _('Approbation by pdf of %(member)s')
                % {'member': f'{supervision_member.promoteur.prenom} {supervision_member.promoteur.nom}'},
                supervision_member.pdf,
            )
        )
    for supervision_member in context.groupe_supervision.signatures_membres_CA:
        attachments.append(
            Attachment(
                _('Approbation by pdf of %(member)s')
                % {'member': f'{supervision_member.membre_CA.prenom} {supervision_member.membre_CA.nom}'},
                supervision_member.pdf,
            )
        )
    return attachments


def get_dynamic_questions_attachments(
    specific_questions: List[AdmissionFormItemInstantiation],
    context: ResumePropositionDTO,
    language: str,
):
    """Returns the dynamic questions attachments."""
    return [
        Attachment(
            question.form_item.title.get(language, settings.LANGUAGE_CODE_FR),
            context.proposition.reponses_questions_specifiques.get(str(question.form_item.uuid), []),
        )
        for question in specific_questions
        if question.form_item.type == TypeItemFormulaire.DOCUMENT.name
    ]


def get_training_choice_attachments(
    context: ResumePropositionDTO,
    specific_questions: List[AdmissionFormItemInstantiation],
    language,
) -> List[Attachment]:
    """Returns the training choice attachments."""
    return get_dynamic_questions_attachments(specific_questions, context, language)
