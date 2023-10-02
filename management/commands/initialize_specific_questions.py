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
import bisect

import itertools
from django.conf import settings
from django.core.management import BaseCommand
from django.utils.translation import ngettext

from admission.contrib.models import AdmissionFormItem, AdmissionFormItemInstantiation
from admission.ddd.admission.domain.enums import TypeFormation
from admission.ddd.admission.enums import (
    TypeItemFormulaire,
    CritereItemFormulaireFormation,
    Onglets,
    CritereItemFormulaireLangueEtudes,
    CleConfigurationItemFormulaire,
    TypeChampTexteFormulaire,
    TypeChampSelectionFormulaire,
    CritereItemFormulaireNationaliteCandidat,
    CritereItemFormulaireVIP,
    CritereItemFormulaireNationaliteDiplome,
)
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.models.academic_year import AcademicYear
from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import TrainingType
from osis_document.enums import ChoiceEnum


class SpecificQuestionToInit(ChoiceEnum):
    MOTIVATION_LETTER = "Lettre de motivation"
    FRENCH_LANGUAGE_PROFICIENCY_EXAM = "Examen de maitrise de la langue française"
    B2_FRENCH_LEVEL = "Niveau de Français B2"
    B1_FRENCH_LEVEL = "Niveau de Français B1"
    C1_FRENCH_LEVEL = "Niveau de Français C1"
    LSM_ENGLISH_LEVEL = "Niveau d'Anglais LSM"
    ECON_ENGLISH_LEVEL = "Niveau d'Anglais ECON"
    EPL_ENGLISH_LEVEL = "Niveau d'Anglais EPL"
    B2_ENGLISH_LEVEL = "Niveau d'Anglais B2"
    BELGIAN_RESIDENT_MESSAGE = "Résident belge"
    DISSERTATION_SUMMARY = "Résumé mémoire"
    DISSERTATION_DATE = "Date de soutenance du mémoire"
    PORTFOLIO = "Port-folio"
    GMAT = "GMAT"
    SCHOOL_COMMITMENT = "Engagement école"
    GERMANIC_LANGUAGE_CHOICE = "Choix de langue germanique"
    MEDICAL_ENTRANCE_PROOF = "Concours médecine et dentisterie"
    DENTISTRY_SPECIALIZATION_PROOF = "Attestation de sélection spécialisation dentisterie"
    ENGINEERING_ENTRANCE_EXAM_PROOF = "Attestation d'admission - partie mathématique"
    RESIDENT_STUDENT_FORM = "dossier résident - contingentement"


class EducationGroupNotFoundException(Exception):
    def __init__(self, education_groups, *args):
        list_of_education_groups = ', '.join(sorted(education_groups))
        self.message = ngettext(
            'One education group could not be found: %(education_groups)s.'
            % {'education_groups': list_of_education_groups},
            'Several education groups could not be found: %(education_groups)s.'
            % {
                'education_groups': list_of_education_groups,
            },
            len(education_groups),
        )
        super().__init__(*args)


class Command(BaseCommand):
    """Command to initialize the specific questions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.not_found_education_group_years = set()
        self.education_group_years = {}
        self.academic_year = None
        self.master_education_group_years = []
        self.master_education_group_years_len = 0

    def add_arguments(self, parser):
        parser.add_argument("year", type=int, help="Academic year")

    def instantiate_education_group_question(self, acronym, **kwargs):
        """Instantiate an education group question based on a acronym and display criteria."""
        if acronym in self.education_group_years:
            AdmissionFormItemInstantiation.objects.create(
                **kwargs,
                academic_year=self.academic_year,
                education_group_id=self.education_group_years[acronym],
                tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
                display_according_education=CritereItemFormulaireFormation.UNE_FORMATION.name,
            )
        else:
            self.not_found_education_group_years.add(acronym)

    def get_matched_acronyms(self, acronym_beginnings):
        """
        Return the list of acronyms that match the beginnings of the acronym.

        :param acronym_beginnings: list of acronym beginnings.
        :return: list of acronyms that match the beginnings of the acronyms.
        """
        matched_acronyms = []

        if not acronym_beginnings:
            return []

        not_found_acronym_beginning = set(acronym_beginnings)
        sorted_acronym_beginnings = sorted(acronym_beginnings)

        # The list of acronyms is sorted so we only search inside a portion of it
        min_index = bisect.bisect_left(
            a=self.master_education_group_years,
            x=sorted_acronym_beginnings[0][0],
            hi=self.master_education_group_years_len,
        )
        max_index = bisect.bisect_right(
            a=self.master_education_group_years,
            x=chr(ord(sorted_acronym_beginnings[-1][0]) + 1),
            lo=min_index,
            hi=self.master_education_group_years_len,
        )

        for acronym in itertools.islice(self.master_education_group_years, min_index, max_index):
            for acronym_beginning in acronym_beginnings:
                if acronym.startswith(acronym_beginning):
                    matched_acronyms.append(acronym)
                    not_found_acronym_beginning.discard(acronym_beginning)
                    break

        for acronym in not_found_acronym_beginning:
            self.not_found_education_group_years.add(f'{acronym}/*')

        return matched_acronyms

    def handle(self, *args, **options):
        self.academic_year = AcademicYear.objects.get(year=options["year"])

        AdmissionFormItemInstantiation.objects.filter(
            academic_year=self.academic_year,
            form_item__internal_label__in=SpecificQuestionToInit.get_values(),
        ).delete()

        # Education group types by category
        education_group_types = {
            education_group_type.name: education_group_type
            for education_group_type in EducationGroupType.objects.filter(
                category=Categories.TRAINING.name,
            )
        }

        # All education group years
        education_group_years_result = (
            EducationGroupYear.objects.filter(
                academic_year=self.academic_year,
                education_group_type__category=Categories.TRAINING.name,
                enrollment_enabled=True,
            )
            .order_by('acronym')
            .values('acronym', 'education_group_id', 'education_group_type__name')
        )

        masters_types = {
            TrainingType.MASTER_MA_120.name,
            TrainingType.MASTER_MD_120.name,
            TrainingType.MASTER_MS_120.name,
            TrainingType.MASTER_MS_180_240.name,
        }

        for education_group_year in education_group_years_result:
            # Build a dictionary that maps education group years to education group
            self.education_group_years[education_group_year['acronym']] = education_group_year['education_group_id']

            # Build a list of master education group years
            if education_group_year['education_group_type__name'] in masters_types:
                self.master_education_group_years.append(education_group_year['acronym'])
                self.master_education_group_years_len += 1

        # Motivation letter
        motivation_letter, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.MOTIVATION_LETTER.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: 'Motivation letter',
                    settings.LANGUAGE_CODE_FR: 'Une lettre de motivation',
                },
                'text': {
                    settings.LANGUAGE_CODE_EN: 'Depending on the programme you are applying for, please specify in '
                    'your cover letter your focus, specialisation, language combination or '
                    'electives, if necessary. Your letter should also include the reasons '
                    'for your proposed course of study.',
                    settings.LANGUAGE_CODE_FR: 'En fonction du programme sollicité, veuillez préciser dans votre '
                    'lettre de motivation votre choix de finalité, spécialité, combinaison '
                    'de langues ou options si nécessaires. Votre lettre doit également '
                    'inclure les motivations de votre projet d’études.',
                },
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        # > All masters, specialized masters, PHD, CAPAES and certificates
        for education_type in (
            AnneeInscriptionFormationTranslator.OSIS_ADMISSION_EDUCATION_TYPES_MAPPING[TypeFormation.MASTER.name]
            + AnneeInscriptionFormationTranslator.OSIS_ADMISSION_EDUCATION_TYPES_MAPPING[TypeFormation.DOCTORAT.name]
            + [TrainingType.CAPAES.name, TrainingType.CERTIFICATE.name]
        ):
            AdmissionFormItemInstantiation.objects.create(
                form_item=motivation_letter,
                academic_year=self.academic_year,
                weight=0,
                required=True,
                display_according_education=CritereItemFormulaireFormation.TYPE_DE_FORMATION.name,
                education_group_type=education_group_types[education_type],
                tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
            )

        # French language proficiency exam
        french_language_proficiency_exam, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.FRENCH_LANGUAGE_PROFICIENCY_EXAM.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: (
                        "Proof of passing the bachelor's level French language proficiency exam "
                        "(https://uclouvain.be/en/study/inscriptions/french-language-master-teaching.html)"
                    ),
                    settings.LANGUAGE_CODE_FR: "Attestation de réussite du test de 2ème cycle de l'examen de maîtrise "
                    "de la langue française (informations :"
                    " https://uclouvain.be/fr/etudier/inscriptions/emlf-aess.html)",
                },
                'text': {},
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        # > Didactic masters and aggregations
        for education_type in [
            TrainingType.MASTER_MD_120.name,
            TrainingType.AGGREGATION.name,
        ]:
            AdmissionFormItemInstantiation.objects.create(
                form_item=french_language_proficiency_exam,
                academic_year=self.academic_year,
                weight=0,
                required=False,
                display_according_education=CritereItemFormulaireFormation.TYPE_DE_FORMATION.name,
                education_group_type=education_group_types[education_type],
                diploma_nationality=CritereItemFormulaireNationaliteDiplome.NON_BELGE.name,
                tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
            )

        # B2 French level
        b2_french_level, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.B2_FRENCH_LEVEL.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "Proof of passing a French language proficiency test"
                    " (DALF, DELF, TCT, etc.) with a minimum B2 level.",
                    settings.LANGUAGE_CODE_FR: "Une attestation de réussite d'un test de maîtrise de la langue "
                    "française ( type DALF,DELF, TCT,...) attestant au minimum d'un niveau "
                    "B2.",
                },
                'text': {},
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        matched_acronyms = self.get_matched_acronyms(
            [
                'EDPH2M',
                'MOTR2M',
            ],
        )
        for acronym in ['KINE2M1'] + matched_acronyms:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=b2_french_level,
                weight=1,
                required=True,
                candidate_nationality=CritereItemFormulaireNationaliteCandidat.NON_UE.name,
            )

        matched_acronyms = self.get_matched_acronyms(
            [
                'GEHM2M',
                'GEHC2M',
                'FEHC2M',
            ]
        )

        for acronym in matched_acronyms + [
            'GEHM2M1',
            'GEHC2M1',
        ]:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=b2_french_level,
                weight=1,
                required=True,
                study_language=CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_FR.name,
                candidate_nationality=CritereItemFormulaireNationaliteCandidat.NON_UE.name,
                vip_candidate=CritereItemFormulaireVIP.NON_VIP.name,
            )

        matched_acronyms = self.get_matched_acronyms(
            [
                'SBIM2M',
                'FARM2M',
            ],
        )
        for acronym in matched_acronyms:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=b2_french_level,
                weight=1,
                required=True,
                diploma_nationality=CritereItemFormulaireNationaliteDiplome.NON_BELGE.name,
                study_language=CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_FR.name,
                vip_candidate=CritereItemFormulaireVIP.NON_VIP.name,
            )

        # B1 French level
        b1_french_level, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.B1_FRENCH_LEVEL.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "Proof of passing a French language proficiency test "
                    "(DALF, DELF, TCT, etc.) with a minimum B1 level.",
                    settings.LANGUAGE_CODE_FR: "Une attestation de réussite d'un test de maîtrise de la "
                    "langue française ( type DALF,DELF, TCT,...) attestant au minimum "
                    "d'un niveau B1.",
                },
                'text': {},
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        matched_acronyms = self.get_matched_acronyms(
            [
                'COMM2M',
                'PRIM2M',
                'ADPM2M',
                'COHM2M',
                'COAM2M',
                'APHM2M',
                'SPHM2M',
            ]
        )

        for acronym in [
            'COMM2M1',
            'SPOM2M1',
            'SPHM2M1',
        ] + matched_acronyms:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=b1_french_level,
                weight=1,
                required=True,
                study_language=CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_FR.name,
                candidate_nationality=CritereItemFormulaireNationaliteCandidat.NON_UE.name,
                vip_candidate=CritereItemFormulaireVIP.NON_VIP.name,
            )

        # C1 French level
        c1_french_level, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.C1_FRENCH_LEVEL.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "Proof of passing a French language proficiency test "
                    "(DALF, DELF, TCT, etc.) with a minimum C1 level. ",
                    settings.LANGUAGE_CODE_FR: "Une attestation de réussite d'un test de maîtrise de la langue "
                    "française ( type DALF,DELF, TCT,...) attestant au minimum d'un "
                    "niveau C1.",
                },
                'text': {},
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        matched_acronyms = self.get_matched_acronyms(
            [
                'CORP2M',
                'COMU2M',
                'EJL2M',
                'STIC2M',
            ],
        )
        for acronym in ['COMU2M1'] + matched_acronyms:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=c1_french_level,
                weight=1,
                required=True,
                candidate_nationality=CritereItemFormulaireNationaliteCandidat.NON_UE.name,
                vip_candidate=CritereItemFormulaireVIP.NON_VIP.name,
            )

        # English lsm level
        english_lsm_level, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.LSM_ENGLISH_LEVEL.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "Proof of English language proficiency (minimum 89 for TOEFL iBT "
                    "or minimum 6.5 for IELTS Academic).",
                    settings.LANGUAGE_CODE_FR: "Une preuve de maitrise de la langue anglaise (minimum 89 pour le "
                    "TOEFL iBT ou minimum 6,5 pour l'IELTS académique).",
                },
                'text': {
                    settings.LANGUAGE_CODE_EN: "You may be exempted from the English test if you can prove that you "
                    "completed your entire bachelor's degree course in English.",
                    settings.LANGUAGE_CODE_FR: "Vous pouvez être exempté·e du test d'anglais si vous pouvez prouver "
                    "que vous avez effectué l'intégralité de votre bachelier en anglais.",
                },
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        matched_acronyms = self.get_matched_acronyms(
            [
                'GESA2M',
                'GESM2M',
                'GEST2M',
                'INGE2M',
                'INGM2M',
            ],
        )
        for acronym in [
            'GEST2M/1',
        ] + matched_acronyms:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=english_lsm_level,
                weight=1,
                required=True,
                diploma_nationality=CritereItemFormulaireNationaliteDiplome.NON_BELGE.name,
                vip_candidate=CritereItemFormulaireVIP.NON_VIP.name,
            )

        for acronym in [
            'EBEP2MC',
        ]:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=english_lsm_level,
                weight=1,
                required=True,
                diploma_nationality=CritereItemFormulaireNationaliteDiplome.NON_BELGE.name,
                study_language=CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_EN.name,
                vip_candidate=CritereItemFormulaireVIP.NON_VIP.name,
            )

        # English econ level
        english_econ_level, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.ECON_ENGLISH_LEVEL.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "Proof of English language proficiency (minimum 79 for TOEFL iBT or "
                    "minimum 6.5 for IELTS Academic).",
                    settings.LANGUAGE_CODE_FR: "Une preuve de maitrise de la langue anglaise (minimum 79 pour le TOEFL "
                    "iBT ou minimum 6,5 pour l'IELTS académique).",
                },
                'text': {
                    settings.LANGUAGE_CODE_EN: "You may be exempted from the English test if you can provide a "
                    "transcript proving the successful completion of at least three "
                    "economics courses in English during your previous university "
                    "course(s).",
                    settings.LANGUAGE_CODE_FR: "Vous pouvez être exempté·e du test d'anglais si vous pouvez "
                    "fournir un un relevé de note prouvant la réussite de minimum 3 cours "
                    "d’économie en anglais durant votre parcours universitaire antérieur.",
                },
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        matched_acronyms = self.get_matched_acronyms(
            [
                'ECON2M',
                'ETRI2M',
            ],
        )
        for acronym in [
            'ECON2M1',
        ] + matched_acronyms:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=english_econ_level,
                weight=1,
                required=True,
                diploma_nationality=CritereItemFormulaireNationaliteDiplome.NON_BELGE.name,
                vip_candidate=CritereItemFormulaireVIP.NON_VIP.name,
                study_language=CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_EN.name,
            )

        # English epl level
        english_epl_level, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.EPL_ENGLISH_LEVEL.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "Proof of English language proficiency (minimum score of 80 for "
                    "TOEFL iBT, 6.5 for IELTS Academic or 740 TOEIC or successful "
                    "completion of the Cambridge Advanced English exam).",
                    settings.LANGUAGE_CODE_FR: "Une preuve de maitrise de la langue anglaise (score de minimum "
                    "80 pour le TOEFL iBT, 6,5 pour l'IELTS académique ou 740 TOEIC ou la "
                    "réussite de l'examen Cambridge Advanced English).",
                },
                'text': {
                    settings.LANGUAGE_CODE_EN: "You may be exempted from the English test if you can prove that "
                    "you have completed all of your academic studies in English.",
                    settings.LANGUAGE_CODE_FR: "Vous pouvez être exempté·e du test d'anglais si vous pouvez prouver "
                    "que vous avez effectué l'intégralité de votre cursus académique "
                    "en anglais.",
                },
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        matched_acronyms = self.get_matched_acronyms(
            [
                'SINF2M',
                'NRGY2M',
                'MAP2M',
                'MECA2M',
                'GCE2M',
                'INFO2M',
                'GBIO2M',
                'ELME2M',
                'DATI2M',
                'DATE2M',
            ],
        )
        for acronym in [
            'SINF2M1',
        ] + matched_acronyms:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=english_epl_level,
                weight=1,
                required=True,
                diploma_nationality=CritereItemFormulaireNationaliteDiplome.NON_BELGE.name,
                vip_candidate=CritereItemFormulaireVIP.NON_VIP.name,
            )

        # English b2 level
        english_b2_level, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.B2_ENGLISH_LEVEL.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "Certificate of passing an English language test with a minimum B2 "
                    "level.",
                    settings.LANGUAGE_CODE_FR: "Une attestation de réussite d'un test de maîtrise de la langue "
                    "anglaise attestant au minimum d'un niveau B2.",
                },
                'text': {},
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        matched_acronyms = self.get_matched_acronyms(
            [
                'SBIM2M',
                'FARM2M',
            ],
        )
        for acronym in matched_acronyms:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=english_b2_level,
                weight=2,
                required=True,
                diploma_nationality=CritereItemFormulaireNationaliteDiplome.NON_BELGE.name,
                study_language=CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_EN.name,
                vip_candidate=CritereItemFormulaireVIP.NON_VIP.name,
            )

        # Belgian resident message
        belgian_resident_message, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.BELGIAN_RESIDENT_MESSAGE.value,
            defaults={
                'type': TypeItemFormulaire.MESSAGE.name,
                'title': {},
                'text': {
                    settings.LANGUAGE_CODE_EN: "The programme is open only to people who are active in Belgium "
                    "(or border regions). Students who do not reside in Belgium (or border "
                    "regions) are not eligible for this programme.",
                    settings.LANGUAGE_CODE_FR: "Le programme s'adresse uniquement à des personnes qui ont des "
                    "activités en Belgique (ou dans les régions frontalières). Les "
                    "étudiants qui ne résident pas en Belgique (ou dans les régions "
                    "frontalières) ne sont pas admis à ce programme.",
                },
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        matched_acronyms = self.get_matched_acronyms(
            [
                'OPES2M',
            ],
        )

        for acronym in matched_acronyms:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=belgian_resident_message,
                weight=1,
                required=True,
            )

        # Dissertation summary and date
        dissertation_summary, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.DISSERTATION_SUMMARY.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "A one-page summary of your dissertation",
                    settings.LANGUAGE_CODE_FR: "Un résumé de votre mémoire en 1 page.",
                },
                'text': {},
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        dissertation_date, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.DISSERTATION_DATE.value,
            defaults={
                'type': TypeItemFormulaire.TEXTE.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "Indicate the date on which your dissertation is due to be defended.",
                    settings.LANGUAGE_CODE_FR: "Veuillez renseigner la date de soutenance de votre mémoire (travail "
                    "d'études).",
                },
                'text': {},
                'help_text': {},
                'values': [],
                'configuration': {
                    CleConfigurationItemFormulaire.TAILLE_TEXTE.name: TypeChampTexteFormulaire.COURT.name,
                },
            },
        )

        for acronym in ['ENVI2MC']:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=dissertation_summary,
                weight=1,
                required=True,
                vip_candidate=CritereItemFormulaireVIP.NON_VIP.name,
            )

            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=dissertation_date,
                weight=2,
                required=False,
                vip_candidate=CritereItemFormulaireVIP.NON_VIP.name,
            )

        portfolio, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.PORTFOLIO.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "A portfolio of your work at your home institute of architecture "
                    "(or engineering school).",
                    settings.LANGUAGE_CODE_FR: "Un port-folio reprenant vos travaux réalisés dans votre institut "
                    "d'architecture (ou école d'ingénieur) d'origine.",
                },
                'text': {},
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        matched_acronyms = self.get_matched_acronyms(
            [
                'ARCB2M',
                'ARCT2M',
                'ARCH2M',
            ],
        )
        for acronym in matched_acronyms:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=portfolio,
                weight=1,
                required=True,
            )

        # GMAT
        gmat, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.GMAT.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "Your results on one of the following standardised tests: GMAT "
                    "(min. score: 550), TageMage (min. score: 240) or GRE (min. score: 155 "
                    "in quantitative reasoning).",
                    settings.LANGUAGE_CODE_FR: "Vos résultats à l'un des tests standardisés suivants : GMAT "
                    "(score min. : 550), TageMage (score min. : 240) ou GRE (score min. : "
                    "155 en raisonnement quantitatif).",
                },
                'text': {
                    settings.LANGUAGE_CODE_EN: "You may be exempted from these tests if you have obtained a bachelor's "
                    "degree in business engineering from a CEMS school or a dual degree "
                    "partner school.",
                    settings.LANGUAGE_CODE_FR: "Vous pouvez être exempté·e de ces tests si vous avez obtenu un diplôme "
                    "de bachelier en ingénieur de gestion dans une école  CEMS ou un "
                    "école partenaire de double diplôme.",
                },
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        matched_acronyms = self.get_matched_acronyms(
            [
                'GESA2M',
                'GESM2M',
                'GEST2M',
                'INGE2M',
                'INGM2M',
            ],
        )
        for acronym in matched_acronyms:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=gmat,
                weight=2,
                required=True,
                diploma_nationality=CritereItemFormulaireNationaliteDiplome.NON_BELGE.name,
                vip_candidate=CritereItemFormulaireVIP.NON_VIP.name,
            )

        # School commitment
        school_commitment, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.SCHOOL_COMMITMENT.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "Proof of professional experience (teaching, pedagogical support, "
                    "pedagogical management, etc.) in a higher education establishment "
                    "(university, college, EPS) in Belgium.",
                    settings.LANGUAGE_CODE_FR: "Attestation démontrant les preuves d'une pratique professionnelle "
                    "(enseignement, accompagnement pédagogique, gestion pédagogique, …) "
                    "dans un établissement d’enseignement supérieur (université, "
                    "haute école, EPS) en Belgique.",
                },
                'text': {},
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        for acronym in [
            'EDUC2MC',
        ]:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=school_commitment,
                weight=1,
                required=False,
            )

        # Germanic language choice
        germanic_language_choice, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.GERMANIC_LANGUAGE_CHOICE.value,
            defaults={
                'type': TypeItemFormulaire.SELECTION.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "Choose the two Germanic languages you wish to study.",
                    settings.LANGUAGE_CODE_FR: "Veuillez choisir les deux langues germaniques que vous désirez "
                    "étudier.",
                },
                'text': {},
                'help_text': {},
                'values': [
                    {
                        settings.LANGUAGE_CODE_EN: "German",
                        settings.LANGUAGE_CODE_FR: "Allemand",
                        'key': 'german',
                    },
                    {
                        settings.LANGUAGE_CODE_EN: "English",
                        settings.LANGUAGE_CODE_FR: "Anglais",
                        'key': 'english',
                    },
                    {
                        settings.LANGUAGE_CODE_EN: "Dutch",
                        settings.LANGUAGE_CODE_FR: "Néerlandais",
                        'key': 'dutch',
                    },
                ],
                'configuration': {
                    CleConfigurationItemFormulaire.TYPE_SELECTION.name: TypeChampSelectionFormulaire.CASES_A_COCHER.name
                },
            },
        )

        matched_acronyms = self.get_matched_acronyms(
            [
                'GERM2M',
            ],
        )
        for acronym in matched_acronyms:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=germanic_language_choice,
                weight=1,
                required=True,
            )

        # Medical entrance exam
        medical_entrance_proof, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.MEDICAL_ENTRANCE_PROOF.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "Proof of passing the medical entrance exam for UCLouvain "
                    "(https://www.mesetudes.be/concoursmd/).",
                    settings.LANGUAGE_CODE_FR: "Attestation de réussite au concours d'entrée en médecine pour "
                    "l'UCLouvain (https://www.mesetudes.be/concoursmd/).",
                },
                'text': {
                    settings.LANGUAGE_CODE_EN: "If you have not yet taken the competitive exam, please provide proof "
                    "of registration for it. If you have not yet registered for it, "
                    "you do not need to enclose any documents at this stage.",
                    settings.LANGUAGE_CODE_FR: "Si vous n'avez pas encore présenté le concours, veuillez fournir "
                    "la preuve d'inscription au concours. Si vous n'êtes pas encore "
                    "inscrit·e au concours, vous ne devez joindre aucun document à ce "
                    "stade.",
                },
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        for acronym in [
            'MD1BA',
            'DENT1BA',
        ]:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=medical_entrance_proof,
                weight=1,
                required=False,
            )

        matched_acronyms = self.get_matched_acronyms(
            [
                'MD2M',
                'DENT2M',
            ]
        )

        for acronym in matched_acronyms:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=medical_entrance_proof,
                weight=1,
                required=False,
                diploma_nationality=CritereItemFormulaireNationaliteDiplome.NON_BELGE.name,
            )

        # Dentistry specialization exam
        dentistry_specialization_proof, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.DENTISTRY_SPECIALIZATION_PROOF.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "Proof of selection by the faculty for the chosen specialisation based "
                    "on the results of the competitive entrance exam.",
                    settings.LANGUAGE_CODE_FR: "Attestation de sélection fournie par la faculté donnant accès à la "
                    "spécialisation choisie en fonction des résultats du concours.",
                },
                'text': {},
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        for acronym in [
            'DEGE2MC',
            'ORTD2MC',
            'PARO2MC',
        ]:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=dentistry_specialization_proof,
                weight=1,
                required=True,
            )

        # Engineering entrance exam proof
        engineering_entrance_exam_proof, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.ENGINEERING_ENTRANCE_EXAM_PROOF.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: "Proof of passing the engineering entrance exam.",
                    settings.LANGUAGE_CODE_FR: "Attestation de réussite de l’examen d’accès aux études d’ingénieur.",
                },
                'text': {
                    settings.LANGUAGE_CODE_EN: "If you have not yet taken the engineering entrance exam, provide "
                    "proof of registration for it. If you have not yet registered for "
                    "it, you do not need to enclose any documents at this stage.",
                    settings.LANGUAGE_CODE_FR: "Si vous n'avez pas encore présenté l'examen d'accès aux études "
                    "d'ingénieur, veuillez fournir la preuve d'inscription. Si vous "
                    "n'êtes pas encore inscrit·e à l'examen, vous ne devez joindre "
                    "aucun document à ce stade.",
                },
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        for acronym in [
            'FSA1BA',
            'ARCH1BA',
        ]:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=engineering_entrance_exam_proof,
                weight=1,
                required=True,
            )

        # Resident student form
        resident_student_form, _ = AdmissionFormItem.objects.update_or_create(
            internal_label=SpecificQuestionToInit.RESIDENT_STUDENT_FORM.value,
            defaults={
                'type': TypeItemFormulaire.DOCUMENT.name,
                'title': {
                    settings.LANGUAGE_CODE_EN: (
                        "The \"ETUDIANT·E RESIDENT·E\" (\"resident student\") form (Annex 2), "
                        "duly completed and signed in accordance with the specific terms and "
                        "conditions for a limited-enrolment course, available at: "
                        "https://uclouvain.be/fr/etudier/inscriptions/etudes-contingentees.html."
                    ),
                    settings.LANGUAGE_CODE_FR: (
                        "Le dossier résident (Annexe 2) dûment complété et signé conformément "
                        "aux modalités particulières prévues pour les études contingentées "
                        "reprises à l'adresse suivante : "
                        "https://uclouvain.be/fr/etudier/inscriptions/etudes-contingentees.html."
                    ),
                },
                'text': {},
                'help_text': {},
                'values': [],
                'configuration': {},
            },
        )

        for acronym in [
            'KINE1BA',
            'LOGO1BA',
            'VETE1BA',
        ]:
            self.instantiate_education_group_question(
                acronym=acronym,
                form_item=resident_student_form,
                weight=1,
                required=True,
            )

        if self.not_found_education_group_years:
            exception = EducationGroupNotFoundException(self.not_found_education_group_years)
            self.stderr.write(exception.message)
            raise exception
