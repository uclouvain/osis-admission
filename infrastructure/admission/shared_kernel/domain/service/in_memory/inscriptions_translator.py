# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.shared_kernel.domain.model.assimilation import Assimilation
from admission.ddd.admission.shared_kernel.domain.service.i_annee_inscription_formation import (
    IAnneeInscriptionFormationTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_translator import (
    IInscriptionsTranslatorService,
)
from admission.ddd.admission.shared_kernel.dtos.inscription import InscriptionDTO


class InscriptionsInMemoryTranslator(IInscriptionsTranslatorService):
    @classmethod
    def recuperer(
        cls,
        matricule_candidat: str,
        annees: list[int] | None = None,
    ) -> list[InscriptionDTO]:
        return []

    @classmethod
    def recuperer_inscriptions_deliberables(cls, matricule_candidat: str, annee: int) -> list[InscriptionDTO]:
        return []

    @classmethod
    def est_inscrit_recemment(
        cls,
        matricule_candidat: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> bool:
        return False

    @classmethod
    def candidat_est_inscrit_annee_precedente(
        cls,
        matricule_candidat: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> bool:
        return False

    @classmethod
    def est_en_poursuite(
        cls,
        matricule_candidat: str,
        sigle_formation: str,
    ) -> bool:
        return False

    @classmethod
    def est_en_poursuite_directe(
        cls,
        matricule_candidat: str,
        sigle_formation: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> bool:
        return False

    @classmethod
    def recuperer_derniere_inscription(
        cls,
        matricule_candidat: str,
    ) -> InscriptionDTO | None:
        return None

    @classmethod
    def recuperer_assimilation_inscription_formation_annee_precedente(
        cls,
        matricule_candidat: str,
        sigle_formation: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> Assimilation | None:
        return None
