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
from admission.ddd.admission.dtos.profil_candidat import ProfilCandidatDTO
from admission.ddd.admission.formation_continue.domain.model.enums import (
    STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE,
)
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
    profil_soumis_candidat: Optional[ProfilCandidatDTO]

    matricule_candidat: str
    prenom_candidat: str
    nom_candidat: str
    pays_nationalite_candidat: str
    pays_nationalite_ue_candidat: Optional[bool]
    nom_pays_nationalite_candidat: str
    noma_candidat: str
    adresse_email_candidat: str
    date_changement_statut: Optional[datetime.datetime]
    candidat_a_plusieurs_demandes: bool
    langue_contact_candidat: str

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

    documents_demandes: Dict

    marque_d_interet: Optional[bool]
    aide_a_la_formation: Optional[bool]
    inscription_au_role_obligatoire: Optional[bool]
    etat_formation: str
    edition: Optional[str]
    en_ordre_de_paiement: Optional[bool]
    droits_reduits: Optional[bool]
    paye_par_cheque_formation: Optional[bool]
    cep: Optional[bool]
    etalement_des_paiments: Optional[bool]
    etalement_de_la_formation: Optional[bool]
    valorisation_des_acquis_d_experience: Optional[bool]
    a_presente_l_epreuve_d_evaluation: Optional[bool]
    a_reussi_l_epreuve_d_evaluation: Optional[bool]
    diplome_produit: Optional[bool]
    intitule_du_tff: Optional[str]

    # Decision
    decision_dernier_mail_envoye_le: Optional[datetime.datetime]
    decision_dernier_mail_envoye_par: Optional[str]
    motif_de_mise_en_attente: Optional[str]
    motif_de_mise_en_attente_autre: Optional[str]
    condition_d_approbation_par_la_faculte: Optional[str]
    motif_de_refus: Optional[str]
    motif_de_refus_autre: Optional[str]
    motif_d_annulation: Optional[str]

    @property
    def est_non_soumise(self):
        return self.statut in STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE
