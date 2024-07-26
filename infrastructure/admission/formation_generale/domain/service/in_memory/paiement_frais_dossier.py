##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
from typing import List

from admission.models.online_payment import PaymentStatus
from admission.ddd.admission.formation_generale.domain.service.i_paiement_frais_dossier import IPaiementFraisDossier
from admission.ddd.admission.formation_generale.dtos.paiement import PaiementDTO
from admission.ddd.admission.formation_generale.test.factory.paiement import Paiement, PaiementFactory


class PaiementFraisDossierInMemoryRepository(IPaiementFraisDossier):
    paiements: List[Paiement]

    @classmethod
    def paiement_realise(cls, proposition_uuid: str) -> bool:
        return any(
            paiement
            for paiement in cls.paiements
            if paiement.uuid_proposition == proposition_uuid and paiement.statut == PaymentStatus.PAID.name
        )

    @classmethod
    def ouvrir_paiement(cls, proposition_uuid: str) -> PaiementDTO:
        paiements_proposition = cls.recuperer_paiements_proposition(proposition_uuid)
        paiement_en_cours = next(
            (paiement for paiement in paiements_proposition if paiement.statut == PaymentStatus.OPEN.name),
            None,
        )
        if not paiement_en_cours:
            paiement_en_cours = PaiementFactory(uuid_proposition=proposition_uuid, statut=PaymentStatus.OPEN.name)
            cls.paiements.append(paiement_en_cours)
        return cls._to_dto(paiement_en_cours)

    @classmethod
    def _to_dto(cls, paiement: Paiement) -> PaiementDTO:
        return PaiementDTO(
            identifiant_paiement=paiement.identifiant_paiement,
            statut=paiement.statut,
            methode=paiement.methode,
            montant=paiement.montant,
            url_checkout=paiement.url_checkout,
            date_creation=paiement.date_creation,
            date_mise_a_jour=paiement.date_mise_a_jour,
            date_expiration=paiement.date_expiration,
        )

    @classmethod
    def recuperer_paiements_proposition(cls, proposition_uuid: str) -> List[PaiementDTO]:
        return [cls._to_dto(paiement) for paiement in cls.paiements if paiement.uuid_proposition == proposition_uuid]
