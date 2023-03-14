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
from abc import abstractmethod
from typing import Optional, List

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from osis_common.ddd import interface


class IListerToutesDemandes(interface.DomainService):
    DEFAULT_STATUSES_TO_FILTER = {
        ChoixStatutPropositionGenerale.ANNULEE.name,
        ChoixStatutPropositionGenerale.EN_BROUILLON.name,
        ChoixStatutPropositionDoctorale.ANNULEE.name,
        ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
        ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
        ChoixStatutPropositionContinue.ANNULEE.name,
        ChoixStatutPropositionContinue.EN_BROUILLON.name,
    }

    @classmethod
    @abstractmethod
    def filtrer(
        cls,
        annee_academique: Optional[int] = None,
        numero: Optional[int] = None,
        noma: Optional[str] = '',
        matricule_candidat: Optional[str] = '',
        etat: Optional[str] = '',
        type: Optional[str] = '',
        site_inscription: Optional[str] = '',
        entites: Optional[List[str]] = None,
        types_formation: Optional[List[str]] = None,
        formation: Optional[str] = '',
        bourse_internationale: Optional[str] = '',
        bourse_erasmus_mundus: Optional[str] = '',
        bourse_double_diplomation: Optional[str] = '',
        demandeur: Optional[str] = '',
    ) -> List[DemandeRechercheDTO]:
        raise NotImplementedError
