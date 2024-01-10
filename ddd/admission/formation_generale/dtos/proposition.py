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
from admission.ddd.admission.dtos.formation import BaseFormationDTO
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.dtos.poste_diplomatique import PosteDiplomatiqueDTO
from admission.ddd.admission.dtos.profil_candidat import ProfilCandidatDTO
from admission.ddd.admission.formation_generale.domain.model.enums import STATUTS_PROPOSITION_GENERALE_NON_SOUMISE
from admission.ddd.admission.formation_generale.dtos.motif_refus import MotifRefusDTO
from ddd.logic.learning_unit.dtos import LearningUnitPartimDTO
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

    bourse_double_diplome: Optional[BourseDTO]
    bourse_internationale: Optional[BourseDTO]
    bourse_erasmus_mundus: Optional[BourseDTO]

    reponses_questions_specifiques: Dict[str, Union[str, List[str]]]

    curriculum: List[str]
    equivalence_diplome: List[str]
    documents_additionnels: List[str]

    est_bachelier_belge: Optional[bool]
    est_reorientation_inscription_externe: Optional[bool]
    attestation_inscription_reguliere: List[str]

    est_modification_inscription_externe: Optional[bool]
    formulaire_modification_inscription: List[str]

    est_non_resident_au_sens_decret: Optional[bool]

    poste_diplomatique: Optional[PosteDiplomatiqueDTO]

    elements_confirmation: Dict[str, str]
    pdf_recapitulatif: List[str]

    financabilite_regle_calcule: str
    financabilite_regle_calcule_le: Optional[datetime.datetime]
    financabilite_regle: str
    financabilite_regle_etabli_par: str

    documents_demandes: Dict
    documents_libres_fac_uclouvain: List[str]
    documents_libres_sic_uclouvain: List[str]

    certificat_refus_fac: List[str]
    certificat_approbation_fac: List[str]

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

    @property
    def est_non_soumise(self):
        return self.statut in STATUTS_PROPOSITION_GENERALE_NON_SOUMISE


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

    poursuite_de_cycle_a_specifier: bool
    poursuite_de_cycle: str

    candidat_a_plusieurs_demandes: bool

    titre_acces: str
    candidat_assimile: bool
    fraudeur_ares: bool
    non_financable: bool
    est_inscription_tardive: bool

    profil_soumis_candidat: Optional[ProfilCandidatDTO]

    # Décision fac & sic
    motifs_refus: List[MotifRefusDTO]

    autre_formation_choisie_fac: Optional['BaseFormationDTO']
    avec_conditions_complementaires: Optional[bool]
    conditions_complementaires: List[str]
    avec_complements_formation: Optional[bool]
    complements_formation: Optional[List['LearningUnitPartimDTO']]
    commentaire_complements_formation: str
    nombre_annees_prevoir_programme: Optional[int]
    nom_personne_contact_programme_annuel_annuel: str
    email_personne_contact_programme_annuel_annuel: str
    commentaire_programme_conjoint: str

    # Titres et condition d'accès
    condition_acces: str
    millesime_condition_acces: Optional[int]
    type_equivalence_titre_acces: str
    statut_equivalence_titre_acces: str
    etat_equivalence_titre_acces: str
    date_prise_effet_equivalence_titre_acces: Optional[datetime.date]
