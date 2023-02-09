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
from typing import Dict, Optional, List

import attr
from django.utils.timezone import now

from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.domain.service.i_bourse import BourseIdentity
from admission.ddd.admission.enums import (
    TypeSituationAssimilation,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    ChoixAffiliationSport,
    ChoixTypeCompteBancaire,
    LienParente,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model._comptabilite import comptabilite_non_remplie, Comptabilite
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutProposition
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class PropositionIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True, hash=False, eq=False)
class Proposition(interface.RootEntity):
    entity_id: 'PropositionIdentity'
    formation_id: 'FormationIdentity'
    matricule_candidat: str
    reference: int
    annee_calculee: Optional[int] = None
    pot_calcule: Optional[AcademicCalendarTypes] = None
    statut: ChoixStatutProposition = ChoixStatutProposition.IN_PROGRESS
    type_demande: 'TypeDemande' = TypeDemande.ADMISSION

    creee_le: Optional[datetime.datetime] = None
    modifiee_le: Optional[datetime.datetime] = None
    soumise_le: Optional[datetime.datetime] = None

    comptabilite: 'Comptabilite' = comptabilite_non_remplie

    bourse_double_diplome_id: Optional[BourseIdentity] = None
    bourse_internationale_id: Optional[BourseIdentity] = None
    bourse_erasmus_mundus_id: Optional[BourseIdentity] = None

    est_bachelier_belge: Optional[bool] = None
    est_reorientation_inscription_externe: Optional[bool] = None
    attestation_inscription_reguliere: List[str] = attr.Factory(list)

    est_modification_inscription_externe: Optional[bool] = None
    formulaire_modification_inscription: List[str] = attr.Factory(list)

    est_non_resident_au_sens_decret: Optional[bool] = None

    reponses_questions_specifiques: Dict = attr.Factory(dict)

    continuation_cycle_bachelier: Optional[bool] = None
    attestation_continuation_cycle_bachelier: List[str] = attr.Factory(list)
    curriculum: List[str] = attr.Factory(list)
    equivalence_diplome: List[str] = attr.Factory(list)
    elements_confirmation: Dict[str, str] = attr.Factory(dict)

    def modifier_choix_formation(
        self,
        formation_id: FormationIdentity,
        bourses_ids: Dict[str, BourseIdentity],
        bourse_double_diplome: Optional[str],
        bourse_internationale: Optional[str],
        bourse_erasmus_mundus: Optional[str],
        reponses_questions_specifiques: Dict,
    ):
        self.formation_id = formation_id
        self.reponses_questions_specifiques = reponses_questions_specifiques
        self.bourse_double_diplome_id = bourses_ids.get(bourse_double_diplome) if bourse_double_diplome else None
        self.bourse_internationale_id = bourses_ids.get(bourse_internationale) if bourse_internationale else None
        self.bourse_erasmus_mundus_id = bourses_ids.get(bourse_erasmus_mundus) if bourse_erasmus_mundus else None

    def supprimer(self):
        self.statut = ChoixStatutProposition.CANCELLED

    def soumettre(
        self,
        formation_id: FormationIdentity,
        pool: 'AcademicCalendarTypes',
        elements_confirmation: Dict[str, str],
        type_demande: TypeDemande,
    ):
        self.statut = ChoixStatutProposition.SUBMITTED
        self.type_demande = type_demande
        self.annee_calculee = formation_id.annee
        self.formation_id = formation_id
        self.pot_calcule = pool
        self.elements_confirmation = elements_confirmation
        self.soumise_le = now()
        if pool != AcademicCalendarTypes.ADMISSION_POOL_HUE_UCL_PATHWAY_CHANGE:
            self.attestation_inscription_reguliere = []
        if pool != AcademicCalendarTypes.ADMISSION_POOL_EXTERNAL_ENROLLMENT_CHANGE:
            self.formulaire_modification_inscription = []

    def completer_curriculum(
        self,
        continuation_cycle_bachelier: Optional[bool],
        attestation_continuation_cycle_bachelier: List[str],
        curriculum: List[str],
        equivalence_diplome: List[str],
        reponses_questions_specifiques: Dict,
    ):
        self.continuation_cycle_bachelier = continuation_cycle_bachelier
        self.attestation_continuation_cycle_bachelier = attestation_continuation_cycle_bachelier
        self.curriculum = curriculum
        self.equivalence_diplome = equivalence_diplome
        self.reponses_questions_specifiques = reponses_questions_specifiques

    def completer_comptabilite(
        self,
        attestation_absence_dette_etablissement: List[str],
        demande_allocation_etudes_fr_be: Optional[bool],
        enfant_personnel: Optional[bool],
        attestation_enfant_personnel: List[str],
        type_situation_assimilation: Optional[str],
        sous_type_situation_assimilation_1: Optional[str],
        carte_resident_longue_duree: List[str],
        carte_cire_sejour_illimite_etranger: List[str],
        carte_sejour_membre_ue: List[str],
        carte_sejour_permanent_membre_ue: List[str],
        sous_type_situation_assimilation_2: Optional[str],
        carte_a_b_refugie: List[str],
        annexe_25_26_refugies_apatrides: List[str],
        attestation_immatriculation: List[str],
        carte_a_b: List[str],
        decision_protection_subsidiaire: List[str],
        decision_protection_temporaire: List[str],
        sous_type_situation_assimilation_3: Optional[str],
        titre_sejour_3_mois_professionel: List[str],
        fiches_remuneration: List[str],
        titre_sejour_3_mois_remplacement: List[str],
        preuve_allocations_chomage_pension_indemnite: List[str],
        attestation_cpas: List[str],
        relation_parente: Optional[str],
        sous_type_situation_assimilation_5: Optional[str],
        composition_menage_acte_naissance: List[str],
        acte_tutelle: List[str],
        composition_menage_acte_mariage: List[str],
        attestation_cohabitation_legale: List[str],
        carte_identite_parent: List[str],
        titre_sejour_longue_duree_parent: List[str],
        annexe_25_26_protection_parent: List[str],
        titre_sejour_3_mois_parent: List[str],
        fiches_remuneration_parent: List[str],
        attestation_cpas_parent: List[str],
        sous_type_situation_assimilation_6: Optional[str],
        decision_bourse_cfwb: List[str],
        attestation_boursier: List[str],
        titre_identite_sejour_longue_duree_ue: List[str],
        titre_sejour_belgique: List[str],
        affiliation_sport: Optional[str],
        etudiant_solidaire: Optional[bool],
        type_numero_compte: Optional[str],
        numero_compte_iban: Optional[str],
        iban_valide: Optional[bool],
        numero_compte_autre_format: Optional[str],
        code_bic_swift_banque: Optional[str],
        prenom_titulaire_compte: Optional[str],
        nom_titulaire_compte: Optional[str],
    ):
        self.comptabilite = Comptabilite(
            attestation_absence_dette_etablissement=attestation_absence_dette_etablissement,
            demande_allocation_d_etudes_communaute_francaise_belgique=demande_allocation_etudes_fr_be,
            enfant_personnel=enfant_personnel,
            attestation_enfant_personnel=attestation_enfant_personnel,
            type_situation_assimilation=TypeSituationAssimilation[type_situation_assimilation]
            if type_situation_assimilation
            else None,
            sous_type_situation_assimilation_1=ChoixAssimilation1[sous_type_situation_assimilation_1]
            if sous_type_situation_assimilation_1
            else None,
            carte_resident_longue_duree=carte_resident_longue_duree,
            carte_cire_sejour_illimite_etranger=carte_cire_sejour_illimite_etranger,
            carte_sejour_membre_ue=carte_sejour_membre_ue,
            carte_sejour_permanent_membre_ue=carte_sejour_permanent_membre_ue,
            sous_type_situation_assimilation_2=ChoixAssimilation2[sous_type_situation_assimilation_2]
            if sous_type_situation_assimilation_2
            else None,
            carte_a_b_refugie=carte_a_b_refugie,
            annexe_25_26_refugies_apatrides=annexe_25_26_refugies_apatrides,
            attestation_immatriculation=attestation_immatriculation,
            carte_a_b=carte_a_b,
            decision_protection_subsidiaire=decision_protection_subsidiaire,
            decision_protection_temporaire=decision_protection_temporaire,
            sous_type_situation_assimilation_3=ChoixAssimilation3[sous_type_situation_assimilation_3]
            if sous_type_situation_assimilation_3
            else None,
            titre_sejour_3_mois_professionel=titre_sejour_3_mois_professionel,
            fiches_remuneration=fiches_remuneration,
            titre_sejour_3_mois_remplacement=titre_sejour_3_mois_remplacement,
            preuve_allocations_chomage_pension_indemnite=preuve_allocations_chomage_pension_indemnite,
            attestation_cpas=attestation_cpas,
            relation_parente=LienParente[relation_parente] if relation_parente else None,
            sous_type_situation_assimilation_5=ChoixAssimilation5[sous_type_situation_assimilation_5]
            if sous_type_situation_assimilation_5
            else None,
            composition_menage_acte_naissance=composition_menage_acte_naissance,
            acte_tutelle=acte_tutelle,
            composition_menage_acte_mariage=composition_menage_acte_mariage,
            attestation_cohabitation_legale=attestation_cohabitation_legale,
            carte_identite_parent=carte_identite_parent,
            titre_sejour_longue_duree_parent=titre_sejour_longue_duree_parent,
            annexe_25_26_refugies_apatrides_decision_protection_parent=annexe_25_26_protection_parent,
            titre_sejour_3_mois_parent=titre_sejour_3_mois_parent,
            fiches_remuneration_parent=fiches_remuneration_parent,
            attestation_cpas_parent=attestation_cpas_parent,
            sous_type_situation_assimilation_6=ChoixAssimilation6[sous_type_situation_assimilation_6]
            if sous_type_situation_assimilation_6
            else None,
            decision_bourse_cfwb=decision_bourse_cfwb,
            attestation_boursier=attestation_boursier,
            titre_identite_sejour_longue_duree_ue=titre_identite_sejour_longue_duree_ue,
            titre_sejour_belgique=titre_sejour_belgique,
            affiliation_sport=ChoixAffiliationSport[affiliation_sport] if affiliation_sport else None,
            etudiant_solidaire=etudiant_solidaire,
            type_numero_compte=ChoixTypeCompteBancaire[type_numero_compte] if type_numero_compte else None,
            numero_compte_iban=numero_compte_iban,
            iban_valide=iban_valide,
            numero_compte_autre_format=numero_compte_autre_format,
            code_bic_swift_banque=code_bic_swift_banque,
            prenom_titulaire_compte=prenom_titulaire_compte,
            nom_titulaire_compte=nom_titulaire_compte,
        )
