# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Set

from admission.ddd import BE_ISO_CODE, REGIMES_LINGUISTIQUES_SANS_TRADUCTION
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import ExperienceAcademiqueDTO
from osis_common.ddd import interface
from osis_profile.models.enums.curriculum import TranscriptType


class VerifierCurriculum(interface.DomainService):
    CHAMPS_REQUIS_SI_DIPLOME_OBTENU = [
        'diplome',
    ]

    @classmethod
    def recuperer_experiences_academiques_incompletes(cls, experiences: List[ExperienceAcademiqueDTO]) -> Set[str]:
        experiences_incompletes = set()

        for experience in experiences:
            traduction_necessaire = (
                experience.pays != BE_ISO_CODE
                and experience.regime_linguistique not in REGIMES_LINGUISTIQUES_SANS_TRADUCTION
            )

            # Vérifier le relevé de notes (annualisé ou global)
            if experience.type_releve_notes == TranscriptType.ONE_A_YEAR.name:
                if traduction_necessaire:
                    if not all(annee.releve_notes and annee.traduction_releve_notes for annee in experience.annees):
                        experiences_incompletes.add(experience.uuid)
                elif not all(annee.releve_notes for annee in experience.annees):
                    experiences_incompletes.add(experience.uuid)
            elif not experience.releve_notes or traduction_necessaire and not experience.traduction_releve_notes:
                experiences_incompletes.add(experience.uuid)

            # Vérifier les champs requis lors de l'obtention du diplôme
            if experience.a_obtenu_diplome:
                if not all(
                    getattr(experience, champ_requis) for champ_requis in cls.CHAMPS_REQUIS_SI_DIPLOME_OBTENU
                ) or (traduction_necessaire and not experience.traduction_diplome):
                    experiences_incompletes.add(experience.uuid)

        return experiences_incompletes
