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
import datetime
from typing import Dict, List, Optional

import attr

from admission.ddd.admission import commands
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True, auto_attribs=True)
class RechercherFormationGeneraleQuery(interface.QueryRequest):
    intitule_formation: Optional[str] = ''
    sigle: Optional[str] = ''
    terme_de_recherche: Optional[str] = ''
    type_formation: Optional[str] = ''
    campus: Optional[str] = ''
    annee: Optional[int] = None


@attr.dataclass(frozen=True, slots=True)
class InitierPropositionCommand(interface.CommandRequest):
    sigle_formation: str
    annee_formation: int
    matricule_candidat: str

    bourse_double_diplome: Optional[str] = ''
    bourse_internationale: Optional[str] = ''
    bourse_erasmus_mundus: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class ListerPropositionsCandidatQuery(interface.QueryRequest):
    matricule_candidat: str


@attr.dataclass(frozen=True, slots=True)
class RecupererPropositionQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class RecupererResumePropositionQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class ModifierChoixFormationCommand(interface.CommandRequest):
    uuid_proposition: str

    sigle_formation: str
    annee_formation: int

    bourse_double_diplome: Optional[str] = ''
    bourse_internationale: Optional[str] = ''
    bourse_erasmus_mundus: Optional[str] = ''

    reponses_questions_specifiques: Dict = attr.Factory(dict)


@attr.dataclass(frozen=True, slots=True)
class ModifierChoixFormationParGestionnaireCommand(interface.CommandRequest):
    uuid_proposition: str

    bourse_double_diplome: Optional[str] = ''
    bourse_internationale: Optional[str] = ''
    bourse_erasmus_mundus: Optional[str] = ''

    reponses_questions_specifiques: Dict = attr.Factory(dict)


@attr.dataclass(frozen=True, slots=True)
class ModifierChecklistChoixFormationCommand(interface.CommandRequest):
    uuid_proposition: str

    type_demande: str
    sigle_formation: str
    annee_formation: int
    poursuite_de_cycle: str


@attr.dataclass(frozen=True, slots=True)
class SupprimerPropositionCommand(interface.CommandRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class VerifierPropositionQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class SoumettrePropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    annee: int
    pool: str
    elements_confirmation: Dict[str, str]


@attr.dataclass(frozen=True, slots=True)
class CompleterCurriculumCommand(interface.CommandRequest):
    uuid_proposition: str

    curriculum: List[str] = attr.Factory(list)
    equivalence_diplome: List[str] = attr.Factory(list)
    reponses_questions_specifiques: Dict = attr.Factory(dict)


@attr.dataclass(frozen=True, slots=True)
class VerifierCurriculumQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class DeterminerAnneeAcademiqueEtPotQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class GetComptabiliteQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class CompleterComptabilitePropositionCommand(interface.CommandRequest):
    uuid_proposition: str

    # Absence de dettes
    attestation_absence_dette_etablissement: List[str]

    # Réduction des droits d'inscription
    demande_allocation_d_etudes_communaute_francaise_belgique: Optional[bool]
    enfant_personnel: Optional[bool]
    attestation_enfant_personnel: List[str]

    # Assimilation
    type_situation_assimilation: Optional[str]

    # Assimilation 1
    sous_type_situation_assimilation_1: Optional[str]
    carte_resident_longue_duree: List[str]
    carte_cire_sejour_illimite_etranger: List[str]
    carte_sejour_membre_ue: List[str]
    carte_sejour_permanent_membre_ue: List[str]

    # Assimilation 2
    sous_type_situation_assimilation_2: Optional[str]
    carte_a_b_refugie: List[str]
    annexe_25_26_refugies_apatrides: List[str]
    attestation_immatriculation: List[str]
    preuve_statut_apatride: List[str]
    carte_a_b: List[str]
    decision_protection_subsidiaire: List[str]
    decision_protection_temporaire: List[str]
    carte_a: List[str]

    # Assimilation 3
    sous_type_situation_assimilation_3: Optional[str]
    titre_sejour_3_mois_professionel: List[str]
    fiches_remuneration: List[str]
    titre_sejour_3_mois_remplacement: List[str]
    preuve_allocations_chomage_pension_indemnite: List[str]

    # Assimilation 4
    attestation_cpas: List[str]

    # Assimilation 5
    relation_parente: Optional[str]
    sous_type_situation_assimilation_5: Optional[str]
    composition_menage_acte_naissance: List[str]
    acte_tutelle: List[str]
    composition_menage_acte_mariage: List[str]
    attestation_cohabitation_legale: List[str]
    carte_identite_parent: List[str]
    titre_sejour_longue_duree_parent: List[str]
    annexe_25_26_refugies_apatrides_decision_protection_parent: List[str]
    titre_sejour_3_mois_parent: List[str]
    fiches_remuneration_parent: List[str]
    attestation_cpas_parent: List[str]

    # Assimilation 6
    sous_type_situation_assimilation_6: Optional[str]
    decision_bourse_cfwb: List[str]
    attestation_boursier: List[str]

    # Assimilation 7
    titre_identite_sejour_longue_duree_ue: List[str]
    titre_sejour_belgique: List[str]

    # Affiliations
    affiliation_sport: Optional[str]
    etudiant_solidaire: Optional[bool]

    # Compte bancaire
    type_numero_compte: Optional[str]
    numero_compte_iban: Optional[str]
    iban_valide: Optional[bool]
    numero_compte_autre_format: Optional[str]
    code_bic_swift_banque: Optional[str]
    prenom_titulaire_compte: Optional[str]
    nom_titulaire_compte: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class CompleterQuestionsSpecifiquesCommand(interface.CommandRequest):
    uuid_proposition: str

    reponses_questions_specifiques: Dict = attr.Factory(dict)
    documents_additionnels: List[str] = attr.Factory(list)
    poste_diplomatique: Optional[int] = None


@attr.dataclass(frozen=True, slots=True)
class CompleterQuestionsSpecifiquesParGestionnaireCommand(interface.CommandRequest):
    uuid_proposition: str

    reponses_questions_specifiques: Dict = attr.Factory(dict)
    documents_additionnels: List[str] = attr.Factory(list)

    poste_diplomatique: Optional[int] = None

    est_bachelier_belge: Optional[bool] = None
    est_reorientation_inscription_externe: Optional[bool] = None
    attestation_inscription_reguliere: List[str] = attr.Factory(list)

    est_modification_inscription_externe: Optional[bool] = None
    formulaire_modification_inscription: List[str] = attr.Factory(list)

    est_non_resident_au_sens_decret: Optional[bool] = None


@attr.dataclass(frozen=True, slots=True)
class RecupererElementsConfirmationQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class RecupererPropositionGestionnaireQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class RecupererDocumentsPropositionQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class RecupererDocumentsReclamesPropositionQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class RecupererQuestionsSpecifiquesQuery(commands.RecupererQuestionsSpecifiquesQuery):
    pass


@attr.dataclass(frozen=True, slots=True)
class RecalculerEmplacementsDocumentsNonLibresPropositionCommand(interface.CommandRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class ReclamerDocumentsAuCandidatParSICCommand(interface.CommandRequest):
    uuid_proposition: str
    identifiants_emplacements: List[str]
    a_echeance_le: datetime.date
    objet_message: str
    corps_message: str
    auteur: str


@attr.dataclass(frozen=True, slots=True)
class ReclamerDocumentsAuCandidatParFACCommand(interface.CommandRequest):
    uuid_proposition: str
    identifiants_emplacements: List[str]
    a_echeance_le: datetime.date
    objet_message: str
    corps_message: str
    auteur: str


@attr.dataclass(frozen=True, slots=True)
class CompleterEmplacementsDocumentsParCandidatCommand(interface.CommandRequest):
    uuid_proposition: str
    reponses_documents_a_completer: Dict[str, List[str]]


@attr.dataclass(frozen=True, slots=True)
class InitialiserEmplacementDocumentLibreNonReclamableCommand(
    commands.InitialiserEmplacementDocumentLibreNonReclamableCommand
):
    pass


@attr.dataclass(frozen=True, slots=True)
class InitialiserEmplacementDocumentLibreAReclamerCommand(commands.InitialiserEmplacementDocumentLibreAReclamerCommand):
    pass


@attr.dataclass(frozen=True, slots=True)
class InitialiserEmplacementDocumentAReclamerCommand(commands.InitialiserEmplacementDocumentAReclamerCommand):
    pass


@attr.dataclass(frozen=True, slots=True)
class ModifierReclamationEmplacementDocumentCommand(commands.ModifierReclamationEmplacementDocumentCommand):
    pass


@attr.dataclass(frozen=True, slots=True)
class AnnulerReclamationEmplacementDocumentCommand(commands.AnnulerReclamationEmplacementDocumentCommand):
    pass


@attr.dataclass(frozen=True, slots=True)
class SupprimerEmplacementDocumentCommand(commands.SupprimerEmplacementDocumentCommand):
    pass


@attr.dataclass(frozen=True, slots=True)
class RemplacerEmplacementDocumentCommand(commands.RemplacerEmplacementDocumentCommand):
    pass


@attr.dataclass(frozen=True, slots=True)
class RemplirEmplacementDocumentParGestionnaireCommand(commands.RemplirEmplacementDocumentParGestionnaireCommand):
    pass


@attr.dataclass(frozen=True, slots=True)
class RecupererResumeEtEmplacementsDocumentsNonLibresPropositionQuery(interface.QueryRequest):
    uuid_proposition: str


# Paiement des frais de dossier
@attr.dataclass(frozen=True, slots=True)
class SpecifierPaiementNecessaireCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str


@attr.dataclass(frozen=True, slots=True)
class EnvoyerRappelPaiementCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str


@attr.dataclass(frozen=True, slots=True)
class SpecifierPaiementPlusNecessaireCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    statut_checklist_frais_dossier: str


@attr.dataclass(frozen=True, slots=True)
class PayerFraisDossierPropositionSuiteSoumissionCommand(interface.CommandRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class SpecifierPaiementVaEtreOuvertParCandidatCommand(interface.CommandRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class PayerFraisDossierPropositionSuiteDemandeCommand(interface.CommandRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class EnvoyerPropositionAFacLorsDeLaDecisionFacultaireCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str


@attr.dataclass(frozen=True, slots=True)
class EnvoyerPropositionAuSicLorsDeLaDecisionFacultaireCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str


@attr.dataclass(frozen=True, slots=True)
class RefuserPropositionParFaculteCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str


@attr.dataclass(frozen=True, slots=True)
class RefuserPropositionParFaculteAvecNouveauxMotifsCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    uuids_motifs: List[str] = attr.Factory(list)
    autres_motifs: List[str] = attr.Factory(list)


@attr.dataclass(frozen=True, slots=True)
class SpecifierMotifsRefusPropositionParFaculteCommand(interface.CommandRequest):
    uuid_proposition: str
    uuids_motifs: List[str] = attr.Factory(list)
    autres_motifs: List[str] = attr.Factory(list)


@attr.dataclass(frozen=True, slots=True)
class ApprouverPropositionParFaculteCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str


@attr.dataclass(frozen=True, slots=True)
class SpecifierInformationsAcceptationPropositionParFaculteCommand(interface.CommandRequest):
    uuid_proposition: str
    sigle_autre_formation: str = ''
    uuids_conditions_complementaires_existantes: List[str] = attr.Factory(list)
    avec_conditions_complementaires: Optional[bool] = None
    conditions_complementaires_libres: List[str] = attr.Factory(list)
    avec_complements_formation: Optional[bool] = None
    uuids_complements_formation: List[str] = attr.Factory(list)
    commentaire_complements_formation: str = ''
    nombre_annees_prevoir_programme: Optional[int] = None
    nom_personne_contact_programme_annuel: str = ''
    email_personne_contact_programme_annuel: str = ''
    commentaire_programme_conjoint: str = ''


@attr.dataclass(frozen=True, slots=True)
class ApprouverPropositionParFaculteAvecNouvellesInformationsCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    sigle_autre_formation: str = ''
    avec_conditions_complementaires: Optional[bool] = None
    uuids_conditions_complementaires_existantes: List[str] = attr.Factory(list)
    conditions_complementaires_libres: List[str] = attr.Factory(list)
    avec_complements_formation: Optional[bool] = None
    uuids_complements_formation: List[str] = attr.Factory(list)
    commentaire_complements_formation: str = ''
    nombre_annees_prevoir_programme: Optional[int] = None
    nom_personne_contact_programme_annuel: str = ''
    email_personne_contact_programme_annuel: str = ''
    commentaire_programme_conjoint: str = ''


@attr.dataclass(frozen=True, slots=True)
class RecupererListePaiementsPropositionQuery(interface.QueryRequest):
    uuid_proposition: str
