# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.admission.dtos.bourse import BourseDTO
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.dtos.profil_candidat import ProfilCandidatDTO
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
    login_candidat: str

    bourse_double_diplome: Optional[BourseDTO]
    bourse_internationale: Optional[BourseDTO]
    bourse_erasmus_mundus: Optional[BourseDTO]

    reponses_questions_specifiques: Dict[str, Union[str, List[str]]]

    curriculum: List[str]
    equivalence_diplome: List[str]

    est_bachelier_belge: Optional[bool]
    est_reorientation_inscription_externe: Optional[bool]
    attestation_inscription_reguliere: List[str]

    est_modification_inscription_externe: Optional[bool]
    formulaire_modification_inscription: List[str]

    est_non_resident_au_sens_decret: Optional[bool]

    elements_confirmation: Dict[str, str]
    pdf_recapitulatif: List[str]

    documents_demandes: Dict
    documents_libres_fac_candidats: List[str]
    documents_libres_sic_candidats: List[str]
    documents_libres_fac_uclouvain: List[str]
    documents_libres_sic_uclouvain: List[str]


@attr.dataclass(frozen=True, slots=True)
class PropositionGestionnaireDTO(PropositionDTO):
    type: str
    date_changement_statut: Optional[datetime.datetime]

    genre_candidat: str
    noma_candidat: str
    adresse_email_candidat: str
    langue_contact_candidat: str
    nationalite_candidat: str
    nationalite_ue_candidat: Optional[bool]
    photo_identite_candidat: List[str]

    candidat_a_plusieurs_demandes: bool

    titre_access: str
    candidat_assimile: bool
    fraudeur_ares: bool
    non_financable: bool
    est_inscription_tardive: bool

    profil_soumis_candidat: Optional[ProfilCandidatDTO]

    @property
    def candidat_vip(self) -> bool:
        return any(
            bourse
            for bourse in [
                self.bourse_internationale,
                self.bourse_double_diplome,
                self.bourse_erasmus_mundus,
            ]
        )
