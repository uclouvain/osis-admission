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
from typing import Dict, List, Optional, Union

import attr

from admission.ddd.admission.dtos import AdressePersonnelleDTO
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.formation_continue.domain.model.enums import STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class PropositionDTO(interface.DTO):
    uuid: str
    formation: FormationDTO
    reference: str
    annee_calculee: Optional[int]
    pot_calcule: Optional[str]
    date_fin_pot: Optional[datetime.date]
    creee_le: datetime.datetime
    modifiee_le: datetime.datetime
    soumise_le: Optional[datetime.datetime]
    erreurs: List[Dict[str, str]]
    statut: str

    matricule_candidat: str
    prenom_candidat: str
    nom_candidat: str
    pays_nationalite_candidat: str
    pays_nationalite_ue_candidat: Optional[bool]

    reponses_questions_specifiques: Dict[str, Union[str, List[str]]]

    curriculum: List[str]
    equivalence_diplome: List[str]
    copie_titre_sejour: List[str]
    documents_additionnels: List[str]

    inscription_a_titre: Optional[str]
    nom_siege_social: Optional[str]
    numero_unique_entreprise: Optional[str]
    numero_tva_entreprise: Optional[str]
    adresse_mail_professionnelle: Optional[str]
    type_adresse_facturation: Optional[str]
    adresse_facturation: Optional[AdressePersonnelleDTO]
    elements_confirmation: Dict[str, str]
    pdf_recapitulatif: List[str]

    motivations: str
    moyens_decouverte_formation: List[str]

    @property
    def est_non_soumise(self):
        return self.statut in STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE
