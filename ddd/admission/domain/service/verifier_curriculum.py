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
from typing import List, Dict

from ddd.logic.shared_kernel.profil.dtos.parcours_externe import ExperienceAcademiqueDTO
from osis_common.ddd import interface
from osis_profile import BE_ISO_CODE, REGIMES_LINGUISTIQUES_SANS_TRADUCTION
from osis_profile.models.enums.curriculum import TranscriptType, Result
from osis_profile.views.edit_experience_academique import (
    SYSTEMES_EVALUATION_AVEC_CREDITS,
    PREMIERE_ANNEE_AVEC_CREDITS_ECTS_BE,
)


class VerifierCurriculum(interface.DomainService):
    CHAMPS_REQUIS_SI_DIPLOME_OBTENU = ['diplome', 'grade_obtenu']

    @classmethod
    def recuperer_experiences_academiques_incompletes(
        cls,
        experiences: List[ExperienceAcademiqueDTO],
        annee_courante: int,
    ) -> Dict[str, str]:

        experiences_incompletes = {}

        for experience in experiences:
            pays_belge = experience.pays == BE_ISO_CODE
            traduction_necessaire = (
                not pays_belge and experience.regime_linguistique not in REGIMES_LINGUISTIQUES_SANS_TRADUCTION
            )
            releve_global_necessaire = experience.type_releve_notes == TranscriptType.ONE_FOR_ALL_YEARS.name

            if (
                not pays_belge
                and not experience.regime_linguistique
                or not experience.systeme_evaluation
                or not experience.type_releve_notes
                or releve_global_necessaire
                and (not experience.releve_notes or traduction_necessaire and not experience.traduction_releve_notes)
                or experience.a_obtenu_diplome
                and (
                    not all(getattr(experience, champ_requis) for champ_requis in cls.CHAMPS_REQUIS_SI_DIPLOME_OBTENU)
                    or traduction_necessaire
                    and not experience.traduction_diplome
                )
            ):
                experiences_incompletes[experience.uuid] = str(experience)
                continue

            credits_necessaires_etranger = experience.systeme_evaluation in SYSTEMES_EVALUATION_AVEC_CREDITS
            for annee in experience.annees:
                releve_annuel_manquant = not releve_global_necessaire and (
                    not annee.releve_notes or traduction_necessaire and not annee.traduction_releve_notes
                )
                doit_renseigner_credits = (
                    annee.annee >= PREMIERE_ANNEE_AVEC_CREDITS_ECTS_BE
                    if pays_belge
                    else credits_necessaires_etranger
                ) and (annee.resultat != Result.WAITING_RESULT.name or annee.annee < annee_courante)
                if (
                    not annee.resultat
                    or releve_annuel_manquant
                    or doit_renseigner_credits
                    and (annee.credits_acquis is None or annee.credits_inscrits is None)
                ):
                    experiences_incompletes[experience.uuid] = str(experience)
                    continue

        return experiences_incompletes
