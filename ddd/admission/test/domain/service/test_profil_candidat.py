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
from unittest import TestCase

from admission.ddd import FR_ISO_CODE
from admission.ddd.admission.doctorat.preparation.dtos import ExperienceAcademiqueDTO, AnneeExperienceAcademiqueDTO
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from base.models.enums.community import CommunityEnum
from base.models.enums.teaching_type import TeachingTypeEnum
from base.tasks.synchronize_entities_addresses import UCLouvain_acronym
from osis_profile.models.enums.curriculum import TranscriptType, Result, Grade, EvaluationSystem


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
        }

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
                                annee=2020,
                                resultat=Result.SUCCESS.name,
                                credits_acquis=10,
                                credits_inscrits=10,
                                traduction_releve_notes=[],
                                releve_notes=['uuid-releve-notes-1'],
                                avec_bloc_1=None,
                                avec_complement=None,
                                allegement='',
                                est_reorientation_102=None,
                                credits_inscrits_communaute_fr=None,
                                credits_acquis_communaute_fr=None,
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
                            annee=2019,
                            resultat=Result.SUCCESS.name,
                            credits_acquis=10,
                            credits_inscrits=10,
                            traduction_releve_notes=[],
                            releve_notes=['uuid-releve-notes-0'],
                            avec_bloc_1=None,
                            avec_complement=None,
                            allegement='',
                            est_reorientation_102=None,
                            credits_inscrits_communaute_fr=None,
                            credits_acquis_communaute_fr=None,
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
                            annee=2021,
                            resultat=Result.SUCCESS.name,
                            credits_acquis=10,
                            credits_inscrits=10,
                            traduction_releve_notes=[],
                            releve_notes=['uuid-releve-notes-1'],
                            avec_bloc_1=None,
                            avec_complement=None,
                            allegement='',
                            est_reorientation_102=None,
                            credits_inscrits_communaute_fr=None,
                            credits_acquis_communaute_fr=None,
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
                            annee=2023,
                            resultat=Result.SUCCESS.name,
                            credits_acquis=10,
                            credits_inscrits=10,
                            traduction_releve_notes=[],
                            releve_notes=['uuid-releve-notes-2'],
                            avec_bloc_1=None,
                            avec_complement=None,
                            allegement='',
                            est_reorientation_102=None,
                            credits_inscrits_communaute_fr=None,
                            credits_acquis_communaute_fr=None,
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
                            annee=2023,
                            resultat=Result.SUCCESS.name,
                            credits_acquis=10,
                            credits_inscrits=10,
                            traduction_releve_notes=[],
                            releve_notes=['uuid-releve-notes-3'],
                            avec_bloc_1=None,
                            avec_complement=None,
                            allegement='',
                            est_reorientation_102=None,
                            credits_inscrits_communaute_fr=None,
                            credits_acquis_communaute_fr=None,
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
                            annee=2021,
                            resultat=Result.SUCCESS.name,
                            credits_acquis=10,
                            credits_inscrits=10,
                            traduction_releve_notes=[],
                            releve_notes=['uuid-releve-notes-4'],
                            avec_bloc_1=None,
                            avec_complement=None,
                            allegement='',
                            est_reorientation_102=None,
                            credits_inscrits_communaute_fr=None,
                            credits_acquis_communaute_fr=None,
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
                            annee=2020,
                            resultat=Result.SUCCESS.name,
                            credits_acquis=10,
                            credits_inscrits=10,
                            traduction_releve_notes=[],
                            releve_notes=['uuid-releve-notes-5'],
                            avec_bloc_1=None,
                            avec_complement=None,
                            allegement='',
                            est_reorientation_102=None,
                            credits_inscrits_communaute_fr=None,
                            credits_acquis_communaute_fr=None,
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
