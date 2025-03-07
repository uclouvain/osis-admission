# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from decimal import Decimal
from typing import Dict, List, Optional, Union

import attr

from admission.ddd.admission.dtos.formation import BaseFormationDTO, FormationDTO
from admission.ddd.admission.dtos.poste_diplomatique import PosteDiplomatiqueDTO
from admission.ddd.admission.dtos.profil_candidat import ProfilCandidatDTO
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model.enums import (
    STATUTS_PROPOSITION_GENERALE_NON_SOUMISE,
    DroitsInscriptionMontant,
)
from admission.ddd.admission.formation_generale.dtos.condition_approbation import (
    ConditionComplementaireApprobationDTO,
)
from admission.ddd.admission.formation_generale.dtos.motif_refus import MotifRefusDTO
from ddd.logic.learning_unit.dtos import LearningUnitSearchDTO, PartimSearchDTO
from ddd.logic.reference.dtos.bourse import BourseDTO
from osis_common.ddd import interface
from osis_profile import PLUS_5_ISO_CODES


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
    formulaire_reorientation: List[str]

    est_modification_inscription_externe: Optional[bool]
    formulaire_modification_inscription: List[str]

    est_non_resident_au_sens_decret: Optional[bool]

    poste_diplomatique: Optional[PosteDiplomatiqueDTO]

    elements_confirmation: Dict[str, str]
    pdf_recapitulatif: List[str]

    financabilite_regle_calcule: str
    financabilite_regle_calcule_situation: str
    financabilite_regle_calcule_le: Optional[datetime.datetime]
    financabilite_regle: str
    financabilite_etabli_par: str
    financabilite_etabli_le: Optional[datetime.datetime]

    financabilite_derogation_statut: str
    financabilite_derogation_premiere_notification_le: Optional[datetime.datetime]
    financabilite_derogation_premiere_notification_par: str
    financabilite_derogation_derniere_notification_le: Optional[datetime.datetime]
    financabilite_derogation_derniere_notification_par: str

    documents_demandes: Dict
    documents_libres_fac_uclouvain: List[str]
    documents_libres_sic_uclouvain: List[str]

    derogation_delegue_vrae: str
    derogation_delegue_vrae_commentaire: str
    justificatif_derogation_delegue_vrae: List[str]
    certificat_refus_fac: List[str]
    certificat_approbation_fac: List[str]
    certificat_approbation_sic: List[str]
    certificat_approbation_sic_annexe: List[str]
    certificat_refus_sic: List[str]

    doit_fournir_visa_etudes: Optional[bool]
    visa_etudes_d: List[str]
    certificat_autorisation_signe: List[str]

    type: str

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

    @property
    def est_inscription(self):
        return self.type == TypeDemande.INSCRIPTION.name

    @property
    def est_admission(self):
        return self.type == TypeDemande.ADMISSION.name


@attr.dataclass(frozen=True, slots=True)
class PropositionGestionnaireDTO(PropositionDTO):
    date_changement_statut: Optional[datetime.datetime]

    genre_candidat: str
    noma_candidat: str
    adresse_email_candidat: str
    langue_contact_candidat: str
    nationalite_candidat: str
    nationalite_candidat_fr: str
    nationalite_candidat_en: str
    nationalite_candidat_code_iso: str
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
    type_de_refus: str
    motifs_refus: List[MotifRefusDTO]

    autre_formation_choisie_fac: Optional['BaseFormationDTO']
    avec_conditions_complementaires: Optional[bool]
    conditions_complementaires: List[ConditionComplementaireApprobationDTO]
    avec_complements_formation: Optional[bool]
    complements_formation: Optional[List[Union['PartimSearchDTO', 'LearningUnitSearchDTO']]]
    commentaire_complements_formation: str
    nombre_annees_prevoir_programme: Optional[int]
    nom_personne_contact_programme_annuel_annuel: str
    email_personne_contact_programme_annuel_annuel: str
    commentaire_programme_conjoint: str
    besoin_de_derogation: str

    droits_inscription_montant: str
    droits_inscription_montant_valeur: Optional[Decimal]
    droits_inscription_montant_autre: Decimal
    dispense_ou_droits_majores: str
    tarif_particulier: str
    refacturation_ou_tiers_payant: str
    annee_de_premiere_inscription_et_statut: str
    est_mobilite: Optional[bool]
    nombre_de_mois_de_mobilite: str
    doit_se_presenter_en_sic: Optional[bool]
    communication_au_candidat: str

    # Titres et condition d'accès
    condition_acces: str
    millesime_condition_acces: Optional[int]
    type_equivalence_titre_acces: str
    statut_equivalence_titre_acces: str
    information_a_propos_de_la_restriction: str
    etat_equivalence_titre_acces: str
    date_prise_effet_equivalence_titre_acces: Optional[datetime.date]

    @property
    def candidat_a_nationalite_ue_5(self):
        return self.nationalite_ue_candidat is True or self.nationalite_candidat_code_iso in PLUS_5_ISO_CODES

    @property
    def candidat_a_nationalite_hors_ue_5(self):
        return self.nationalite_ue_candidat is False and self.nationalite_candidat_code_iso not in PLUS_5_ISO_CODES

    @property
    def droits_inscription_montant_valeur_calculee(self):
        return (
            self.droits_inscription_montant_autre
            if self.droits_inscription_montant == DroitsInscriptionMontant.AUTRE.name
            else self.droits_inscription_montant_valeur
        )
