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
from typing import List, Optional

from admission.ddd.admission.projet_doctoral.preparation.domain.model._signature_promoteur import ChoixEtatSignature
from admission.ddd.admission.projet_doctoral.preparation.dtos import AvisDTO
from osis_common.ddd import interface


class Avis(interface.DomainService):
    @classmethod
    def construire_approbation(cls, commentaire_interne: Optional[str], commentaire_externe: Optional[str]) -> AvisDTO:
        return AvisDTO(
            etat=ChoixEtatSignature.APPROVED.name,
            commentaire_externe=commentaire_externe,
            commentaire_interne=commentaire_interne,
        )

    @classmethod
    def construire_refus(
        cls,
        commentaire_interne: Optional[str],
        commentaire_externe: Optional[str],
        motif_refus: Optional[str],
    ) -> AvisDTO:
        return AvisDTO(
            etat=ChoixEtatSignature.DECLINED.name,
            commentaire_externe=commentaire_externe,
            commentaire_interne=commentaire_interne,
            motif_refus=motif_refus,
        )

    @classmethod
    def construire_avis_pdf(cls, pdf: List[str]) -> AvisDTO:
        return AvisDTO(
            etat=ChoixEtatSignature.APPROVED.name,
            pdf=pdf,
        )
