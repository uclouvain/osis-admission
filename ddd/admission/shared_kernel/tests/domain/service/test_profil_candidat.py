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

import datetime

import freezegun
from django.test import TestCase

from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import (
    IProfilCandidatTranslator,
)
from base.models.enums.community import CommunityEnum
from base.models.enums.teaching_type import TeachingTypeEnum
from base.tasks.synchronize_entities_addresses import UCLouvain_acronym
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import (
    AcademicYear,
    AcademicYearIdentity,
)
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import (
    AnneeExperienceAcademiqueDTO,
    ExperienceAcademiqueDTO,
)
from osis_profile import FR_ISO_CODE
from osis_profile.models.enums.curriculum import (
    EvaluationSystem,
    Grade,
    Result,
    TranscriptType,
)


class ProfilCandidatTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.default_args = {
            'uuid': 'uuid-1',
            'pays': FR_ISO_CODE,
            'nom_pays': 'France',
            'adresse_institut': 'Paris',
            'regime_linguistique': FR_ISO_CODE,
            'nom_regime_linguistique': 'Français',
            'type_releve_notes': TranscriptType.ONE_FOR_ALL_YEARS.name,
            'releve_notes': ['uuid-releve-notes'],
            'traduction_releve_notes': ['uuid-traduction-releve-notes'],
            'a_obtenu_diplome': True,
            'diplome': ['uuid-diplome'],
            'traduction_diplome': ['uuid-traduction-diplome'],
            'rang_diplome': '10',
            'date_prevue_delivrance_diplome': datetime.date(2023, 1, 1),
            'titre_memoire': 'Title',
            'note_memoire': '15',
            'resume_memoire': ['uuid-resume-memoire'],
            'grade_obtenu': Grade.GREAT_DISTINCTION.name,
            'systeme_evaluation': EvaluationSystem.ECTS_CREDITS.name,
            'nom_formation': 'Computer science',
            'type_enseignement': TeachingTypeEnum.FULL_TIME.name,
            'type_institut': '',
            'nom_formation_equivalente_communaute_fr': '',
            'cycle_formation': '',
            'est_autre_formation': None,
            'credits_acquis_bloc_1': None,
            'avec_complements': None,
            'credits_inscrits_complements': None,
            'credits_acquis_complements': None,
            'grade_academique_formation': '1',
        }
        cls.annee_academique_2022 = AcademicYear(
            entity_id=AcademicYearIdentity(year=2022),
            start_date=datetime.date(2022, 9, 15),
            end_date=datetime.date(2023, 9, 14),
        )
        cls.annee_academique_2023 = AcademicYear(
            entity_id=AcademicYearIdentity(year=2023),
            start_date=datetime.date(2023, 9, 15),
            end_date=datetime.date(2024, 9, 14),
        )

    def test_recuperer_derniers_etablissements_superieurs_communaute_fr_frequentes_sans_etablissement(self):
        self.assertIsNone(
            IProfilCandidatTranslator.recuperer_derniers_etablissements_superieurs_communaute_fr_frequentes(
                experiences_academiques=[],
                annee_minimale=2021,
            )
        )

    def test_recuperer_derniers_etablissements_superieurs_communaute_fr_frequentes_avec_etablissement_hors_delais(self):
        self.assertIsNone(
            IProfilCandidatTranslator.recuperer_derniers_etablissements_superieurs_communaute_fr_frequentes(
                experiences_academiques=[
                    ExperienceAcademiqueDTO(
                        **self.default_args,
                        nom_institut='Institut 1',
                        code_institut='I1',
                        communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
                        annees=[
                            AnneeExperienceAcademiqueDTO(
                                uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                                annee=2020,
                                resultat=Result.SUCCESS.name,
                                credits_acquis=10,
                                credits_inscrits=10,
                                traduction_releve_notes=[],
                                releve_notes=['uuid-releve-notes-1'],
                                allegement='',
                                est_reorientation_102=None,
                            )
                        ],
                    )
                ],
                annee_minimale=2021,
            )
        )

    def test_recuperer_derniers_etablissements_superieurs_communaute_fr_frequentes_avec_etablissements_valides(self):
        resultat = IProfilCandidatTranslator.recuperer_derniers_etablissements_superieurs_communaute_fr_frequentes(
            experiences_academiques=[
                # Not the last one -> Don't keep it
                ExperienceAcademiqueDTO(
                    **self.default_args,
                    nom_institut='Institut 0',
                    code_institut='I0',
                    communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
                    annees=[
                        AnneeExperienceAcademiqueDTO(
                            uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                            annee=2019,
                            resultat=Result.SUCCESS.name,
                            credits_acquis=10,
                            credits_inscrits=10,
                            traduction_releve_notes=[],
                            releve_notes=['uuid-releve-notes-0'],
                            allegement='',
                            est_reorientation_102=None,
                        )
                    ],
                ),
                # Last one -> Keep it
                ExperienceAcademiqueDTO(
                    **self.default_args,
                    nom_institut='Institut 1',
                    code_institut='I1',
                    communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
                    annees=[
                        AnneeExperienceAcademiqueDTO(
                            uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                            annee=2021,
                            resultat=Result.SUCCESS.name,
                            credits_acquis=10,
                            credits_inscrits=10,
                            traduction_releve_notes=[],
                            releve_notes=['uuid-releve-notes-1'],
                            allegement='',
                            est_reorientation_102=None,
                        )
                    ],
                ),
                # Not french speaking community -> Don't keep it
                ExperienceAcademiqueDTO(
                    **self.default_args,
                    nom_institut='Institut 2',
                    code_institut='I2',
                    communaute_institut=CommunityEnum.GERMAN_SPEAKING.name,
                    annees=[
                        AnneeExperienceAcademiqueDTO(
                            uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                            annee=2023,
                            resultat=Result.SUCCESS.name,
                            credits_acquis=10,
                            credits_inscrits=10,
                            traduction_releve_notes=[],
                            releve_notes=['uuid-releve-notes-2'],
                            allegement='',
                            est_reorientation_102=None,
                        )
                    ],
                ),
                # UCLouvain -> Don't keep it
                ExperienceAcademiqueDTO(
                    **self.default_args,
                    nom_institut='Institut 3',
                    code_institut=UCLouvain_acronym,
                    communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
                    annees=[
                        AnneeExperienceAcademiqueDTO(
                            uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                            annee=2023,
                            resultat=Result.SUCCESS.name,
                            credits_acquis=10,
                            credits_inscrits=10,
                            traduction_releve_notes=[],
                            releve_notes=['uuid-releve-notes-3'],
                            allegement='',
                            est_reorientation_102=None,
                        )
                    ],
                ),
                # Last one -> Keep it
                ExperienceAcademiqueDTO(
                    **self.default_args,
                    nom_institut='Institut 4',
                    code_institut='I4',
                    communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
                    annees=[
                        AnneeExperienceAcademiqueDTO(
                            uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                            annee=2021,
                            resultat=Result.SUCCESS.name,
                            credits_acquis=10,
                            credits_inscrits=10,
                            traduction_releve_notes=[],
                            releve_notes=['uuid-releve-notes-4'],
                            allegement='',
                            est_reorientation_102=None,
                        )
                    ],
                ),
                # Not the last one -> Don't keep it
                ExperienceAcademiqueDTO(
                    **self.default_args,
                    nom_institut='Institut 5',
                    code_institut='I5',
                    communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
                    annees=[
                        AnneeExperienceAcademiqueDTO(
                            uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                            annee=2020,
                            resultat=Result.SUCCESS.name,
                            credits_acquis=10,
                            credits_inscrits=10,
                            traduction_releve_notes=[],
                            releve_notes=['uuid-releve-notes-5'],
                            allegement='',
                            est_reorientation_102=None,
                        )
                    ],
                ),
            ],
            annee_minimale=2020,
        )
        self.assertEqual(resultat.annee, 2021)
        self.assertCountEqual(
            resultat.noms,
            [
                'Institut 1',
                'Institut 4',
            ],
        )

    def test_get_date_maximale_curriculum_retourne_par_defaut_mois_precedent_date_jour(self):
        with freezegun.freeze_time('2023-04-01'):
            self.assertEqual(
                IProfilCandidatTranslator.get_date_maximale_curriculum(),
                datetime.date(2023, 3, 1),
            )

        with freezegun.freeze_time('2023-01-31'):
            self.assertEqual(
                IProfilCandidatTranslator.get_date_maximale_curriculum(),
                datetime.date(2022, 12, 1),
            )

    def test_get_date_maximale_curriculum_retourne_mois_precedent_date_soumission(self):
        with freezegun.freeze_time('2023-01-31'):
            self.assertEqual(
                IProfilCandidatTranslator.get_date_maximale_curriculum(date_soumission=datetime.date(2022, 2, 1)),
                datetime.date(2022, 1, 1),
            )

    def test_get_date_maximale_curriculum_avec_date_soumission_et_annee_de_formation(self):
        with freezegun.freeze_time('2023-04-01'):
            self.assertEqual(
                IProfilCandidatTranslator.get_date_maximale_curriculum(
                    annee_formation=self.annee_academique_2022,
                ),
                datetime.date(2022, 8, 1),
            )
            self.assertEqual(
                IProfilCandidatTranslator.get_date_maximale_curriculum(
                    annee_formation=self.annee_academique_2023,
                ),
                datetime.date(2023, 3, 1),
            )

        with freezegun.freeze_time('2023-01-31'):
            self.assertEqual(
                IProfilCandidatTranslator.get_date_maximale_curriculum(
                    date_soumission=datetime.date(2022, 2, 1),
                    annee_formation=self.annee_academique_2022,
                ),
                datetime.date(2022, 1, 1),
            )

            self.assertEqual(
                IProfilCandidatTranslator.get_date_maximale_curriculum(
                    date_soumission=datetime.date(2022, 2, 1),
                    annee_formation=self.annee_academique_2023,
                ),
                datetime.date(2022, 1, 1),
            )
