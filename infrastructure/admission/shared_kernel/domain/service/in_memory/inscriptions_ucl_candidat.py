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
import datetime

from admission.ddd.admission.shared_kernel.domain.service.i_annee_inscription_formation import (
    CalendrierAcademique,
    IAnneeInscriptionFormationTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_ucl_candidat import (
    IInscriptionsUCLCandidatService,
)
from admission.ddd.admission.shared_kernel.dtos.inscription_ucl_candidat import (
    InscriptionUCLCandidatDTO,
    PeriodeReinscriptionDTO,
)


class InscriptionsUCLCandidatInMemoryService(IInscriptionsUCLCandidatService):
    @classmethod
    def recuperer(
        cls,
        matricule_candidat: str,
        annees: list[int] | None = None,
    ) -> list[InscriptionUCLCandidatDTO]:
        return []

    @classmethod
    def est_inscrit_recemment(
        cls,
        matricule_candidat: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> bool:
        annee_administrative = annee_inscription_formation_translator.recuperer_calendrier_administratif_courant().annee
        inscriptions = cls.recuperer(
            matricule_candidat=matricule_candidat,
            annees=[
                annee_administrative,
                annee_administrative - 1,
            ],
        )
        return bool(inscriptions)

    @classmethod
    def est_en_poursuite(
        cls,
        matricule_candidat: str,
        sigle_formation: str,
    ) -> bool:
        inscriptions = cls.recuperer(matricule_candidat=matricule_candidat)
        return any(inscription for inscription in inscriptions if inscription.sigle_formation == sigle_formation)

    @classmethod
    def est_en_poursuite_directe(
        cls,
        matricule_candidat: str,
        sigle_formation: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> bool:
        annee_administrative = annee_inscription_formation_translator.recuperer_calendrier_administratif_courant().annee
        inscriptions = cls.recuperer(matricule_candidat=matricule_candidat, annees=[annee_administrative - 1])
        return any(inscription for inscription in inscriptions if inscription.sigle_formation == sigle_formation)

    @classmethod
    def est_delibere(
        cls,
        matricule_candidat: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
        calendrier_administratif: CalendrierAcademique | None = None,
    ) -> bool:
        return True

    @classmethod
    def recuperer_informations_periode_de_reinscription(
        cls,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> PeriodeReinscriptionDTO:
        calendrier_administratif = annee_inscription_formation_translator.recuperer_calendrier_administratif_courant()

        if calendrier_administratif is None:
            raise

        return PeriodeReinscriptionDTO(
            date_debut=datetime.date(year=calendrier_administratif.annee - 1, month=6, day=15),
            date_fin=calendrier_administratif.date_fin,
            annee_formation=calendrier_administratif.annee,
        )
