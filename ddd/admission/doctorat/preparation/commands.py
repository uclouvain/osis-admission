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
from typing import Dict, List, Optional

import attr

from admission.ddd.admission import commands
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixDoctoratDejaRealise,
    ChoixLangueRedactionThese,
)
from admission.ddd.interface import SortedQueryRequest
from osis_common.ddd import interface

UUID = str


@attr.dataclass(frozen=True, slots=True)
class InitierPropositionCommand(interface.CommandRequest):
    type_admission: str
    sigle_formation: str
    annee_formation: int
    matricule_candidat: str
    justification: Optional[str] = ''
    commission_proximite: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class CompleterPropositionCommand(interface.CommandRequest):
    uuid: str
    justification: Optional[str] = ''
    commission_proximite: Optional[str] = ''
    type_financement: Optional[str] = ''
    type_contrat_travail: Optional[str] = ''
    eft: Optional[int] = None
    bourse_recherche: Optional[str] = ''
    autre_bourse_recherche: Optional[str] = ''
    bourse_date_debut: Optional[datetime.date] = None
    bourse_date_fin: Optional[datetime.date] = None
    bourse_preuve: List[str] = attr.Factory(list)
    duree_prevue: Optional[int] = None
    temps_consacre: Optional[int] = None
    est_lie_fnrs_fria_fresh_csc: Optional[bool] = None
    commentaire_financement: Optional[str] = ''
    titre_projet: Optional[str] = ''
    resume_projet: Optional[str] = ''
    documents_projet: List[str] = attr.Factory(list)
    graphe_gantt: List[str] = attr.Factory(list)
    proposition_programme_doctoral: List[str] = attr.Factory(list)
    projet_formation_complementaire: List[str] = attr.Factory(list)
    lettres_recommandation: List[str] = attr.Factory(list)
    langue_redaction_these: str = ChoixLangueRedactionThese.UNDECIDED.name
    institut_these: Optional[str] = ''
    lieu_these: Optional[str] = ''
    projet_doctoral_deja_commence: Optional[bool] = None
    projet_doctoral_institution: Optional[str] = ''
    projet_doctoral_date_debut: Optional[datetime.date] = None
    doctorat_deja_realise: str = ChoixDoctoratDejaRealise.NO.name
    institution: Optional[str] = ''
    domaine_these: Optional[str] = ''
    date_soutenance: Optional[datetime.date] = None
    raison_non_soutenue: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class RechercherDoctoratQuery(interface.QueryRequest):
    sigle_secteur_entite_gestion: str
    terme_de_recherche: Optional[str] = ''
    campus: Optional[str] = ''
    annee: Optional[int] = None


@attr.dataclass(frozen=True, slots=True)
class RecupererResumePropositionQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class IdentifierPromoteurCommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: Optional[str]
    prenom: Optional[str]
    nom: Optional[str]
    email: Optional[str]
    est_docteur: Optional[bool]
    institution: Optional[str]
    ville: Optional[str]
    pays: Optional[str]
    langue: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class IdentifierMembreCACommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: Optional[str]
    prenom: Optional[str]
    nom: Optional[str]
    email: Optional[str]
    est_docteur: Optional[bool]
    institution: Optional[str]
    ville: Optional[str]
    pays: Optional[str]
    langue: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class ModifierMembreSupervisionExterneCommand(interface.CommandRequest):
    uuid_proposition: str
    uuid_membre: str
    prenom: Optional[str]
    nom: Optional[str]
    email: Optional[str]
    est_docteur: Optional[bool]
    institution: Optional[str]
    ville: Optional[str]
    pays: Optional[str]
    langue: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class DemanderSignaturesCommand(interface.CommandRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class RenvoyerInvitationSignatureExterneCommand(interface.CommandRequest):
    uuid_proposition: str
    uuid_membre: str


@attr.dataclass(frozen=True, slots=True)
class VerifierPropositionQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class VerifierProjetQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class SupprimerPromoteurCommand(interface.CommandRequest):
    uuid_proposition: str
    uuid_promoteur: str


@attr.dataclass(frozen=True, slots=True)
class DesignerPromoteurReferenceCommand(interface.CommandRequest):
    uuid_proposition: str
    uuid_promoteur: str


@attr.dataclass(frozen=True, slots=True)
class SupprimerMembreCACommand(interface.CommandRequest):
    uuid_proposition: str
    uuid_membre_ca: str


@attr.dataclass(frozen=True, slots=True)
class ApprouverPropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    uuid_membre: str
    institut_these: Optional[str] = ''
    commentaire_interne: Optional[str] = ''
    commentaire_externe: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class RefuserPropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    uuid_membre: str
    motif_refus: str
    commentaire_interne: Optional[str] = ''
    commentaire_externe: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class SoumettrePropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    annee: int
    pool: str
    elements_confirmation: Dict[str, str]


@attr.dataclass(frozen=True, slots=True)
class DefinirCotutelleCommand(interface.CommandRequest):
    uuid_proposition: str
    motivation: Optional[str] = ''
    institution_fwb: Optional[bool] = None
    institution: Optional[str] = ''
    autre_institution_nom: Optional[str] = ''
    autre_institution_adresse: Optional[str] = ''
    demande_ouverture: List[str] = attr.Factory(list)
    convention: List[str] = attr.Factory(list)
    autres_documents: List[str] = attr.Factory(list)


@attr.dataclass(frozen=True, slots=True)
class ListerPropositionsCandidatQuery(interface.QueryRequest):
    matricule_candidat: str


@attr.dataclass(frozen=True, slots=True)
class ListerPropositionsSuperviseesQuery(interface.QueryRequest):
    matricule_membre: str


@attr.dataclass(frozen=True, slots=True)
class GetPropositionCommand(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class GetGroupeDeSupervisionCommand(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class GetCotutelleCommand(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class SupprimerPropositionCommand(interface.CommandRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class ApprouverPropositionParPdfCommand(interface.CommandRequest):
    uuid_proposition: str
    uuid_membre: str
    pdf: List[str] = attr.Factory(list)


@attr.dataclass(frozen=True, slots=True)
class GetComptabiliteQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class CompleterComptabilitePropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    auteur_modification: str

    # Absence de dettes
    attestation_absence_dette_etablissement: List[str]

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
class ModifierTypeAdmissionCommand(interface.CommandRequest):
    uuid_proposition: str

    type_admission: str
    sigle_formation: str
    annee_formation: int
    commission_proximite: Optional[str] = ''

    justification: Optional[str] = ''

    reponses_questions_specifiques: Dict = attr.Factory(dict)


@attr.dataclass(frozen=True, slots=True)
class CompleterCurriculumCommand(interface.CommandRequest):
    uuid_proposition: str
    auteur_modification: str

    curriculum: List[str] = attr.Factory(list)
    reponses_questions_specifiques: Dict = attr.Factory(dict)


@attr.dataclass(frozen=True, slots=True)
class VerifierCurriculumQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class DeterminerAnneeAcademiqueEtPotQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class RecupererElementsConfirmationQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class RecupererQuestionsSpecifiquesQuery(commands.RecupererQuestionsSpecifiquesQuery):
    pass


@attr.dataclass(frozen=True, slots=True)
class RecupererDocumentsPropositionQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class RecupererDocumentsReclamesPropositionQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class RecalculerEmplacementsDocumentsNonLibresPropositionCommand(interface.CommandRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class CompleterEmplacementsDocumentsParCandidatCommand(interface.CommandRequest):
    uuid_proposition: str
    reponses_documents_a_completer: Dict[str, List[str]]


@attr.dataclass(frozen=True, slots=True)
class AnnulerReclamationDocumentsAuCandidatCommand(interface.CommandRequest):
    uuid_proposition: str
    auteur: str
    type_gestionnaire: str


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
class RetyperDocumentCommand(interface.CommandRequest):
    uuid_proposition: str
    identifiant_source: str
    identifiant_cible: str
    auteur: str


@attr.dataclass(frozen=True, slots=True)
class ReclamerDocumentsAuCandidatCommand(interface.CommandRequest):
    uuid_proposition: str
    identifiants_emplacements: List[str]
    a_echeance_le: datetime.date
    objet_message: str
    corps_message: str
    auteur: str
    type_gestionnaire: str


@attr.dataclass(frozen=True, slots=True)
class ListerDemandesQuery(SortedQueryRequest):
    annee_academique: Optional[int] = None
    numero: Optional[int] = None
    matricule_candidat: Optional[str] = ''
    nationalite: Optional[str] = ''
    etats: Optional[List[str]] = None
    type: Optional[str] = ''
    cdds: Optional[List[str]] = None
    commission_proximite: Optional[str] = ''
    sigles_formations: Optional[List[str]] = None
    matricule_promoteur: Optional[str] = ''
    type_financement: Optional[str] = ''
    bourse_recherche: Optional[str] = ''
    cotutelle: Optional[bool] = None
    date_soumission_debut: Optional[datetime.date] = None
    date_soumission_fin: Optional[datetime.date] = None
    mode_filtres_etats_checklist: Optional[str] = ''
    filtres_etats_checklist: Optional[Dict[str, List[str]]] = None
    demandeur: Optional[str] = ''
    fnrs_fria_fresh: Optional[bool] = None


@attr.dataclass(frozen=True, slots=True)
class RecupererPropositionGestionnaireQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class ModifierChoixFormationParGestionnaireCommand(interface.CommandRequest):
    uuid_proposition: str
    auteur: str

    type_admission: str
    commission_proximite: str
    justification: str

    reponses_questions_specifiques: Dict


@attr.dataclass(frozen=True, slots=True)
class EnvoyerMessageCandidatCommand(interface.CommandRequest):
    matricule_emetteur: str
    proposition_uuid: str
    sujet: str
    message: str
    cc_promoteurs: bool
    cc_membres_ca: bool


@attr.dataclass(frozen=True, slots=True)
class RecupererResumeEtEmplacementsDocumentsPropositionQuery(interface.QueryRequest):
    uuid_proposition: str
    avec_document_libres: bool = False


@attr.dataclass(frozen=True, slots=True)
class ModifierStatutChecklistExperienceParcoursAnterieurCommand(interface.CommandRequest):
    uuid_proposition: str
    uuid_experience: str
    gestionnaire: str
    statut: str
    statut_authentification: Optional[bool]


@attr.dataclass(frozen=True, slots=True)
class EnvoyerPropositionAFacLorsDeLaDecisionFacultaireCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str


@attr.dataclass(frozen=True, slots=True)
class EnvoyerPropositionAuSicLorsDeLaDecisionFacultaireCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    envoi_par_fac: bool


@attr.dataclass(frozen=True, slots=True)
class RefuserPropositionParFaculteCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    objet_message: str
    corps_message: str


@attr.dataclass(frozen=True, slots=True)
class ApprouverPropositionParFaculteCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    objet_message: str
    corps_message: str


@attr.dataclass(frozen=True, slots=True)
class ModifierChecklistChoixFormationCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str

    type_demande: str
    sigle_formation: str
    annee_formation: int


@attr.dataclass(frozen=True, slots=True)
class SpecifierInformationsAcceptationPropositionParFaculteCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    avec_complements_formation: Optional[bool] = None
    uuids_complements_formation: List[str] = attr.Factory(list)
    commentaire_complements_formation: str = ''
    nombre_annees_prevoir_programme: Optional[int] = None
    nom_personne_contact_programme_annuel: str = ''
    email_personne_contact_programme_annuel: str = ''
    commentaire_programme_conjoint: str = ''


@attr.dataclass(frozen=True, slots=True)
class ModifierStatutChecklistParcoursAnterieurCommand(interface.CommandRequest):
    uuid_proposition: str
    statut: str
    gestionnaire: str


@attr.dataclass(frozen=True, slots=True)
class SpecifierConditionAccesPropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    condition_acces: str = ''
    millesime_condition_acces: Optional[int] = None
    avec_complements_formation: Optional[bool] = None


@attr.dataclass(frozen=True, slots=True)
class SpecifierEquivalenceTitreAccesEtrangerPropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    type_equivalence_titre_acces: str = ''
    statut_equivalence_titre_acces: str = ''
    etat_equivalence_titre_acces: str = ''
    information_a_propos_de_la_restriction: str = ''
    date_prise_effet_equivalence_titre_acces: Optional[datetime.date] = None


@attr.dataclass(frozen=True, slots=True)
class SpecifierFinancabiliteResultatCalculCommand(interface.CommandRequest):
    uuid_proposition: str
    financabilite_regle_calcule: str
    financabilite_regle_calcule_situation: str


@attr.dataclass(frozen=True, slots=True)
class SpecifierFinancabiliteRegleCommand(interface.CommandRequest):
    uuid_proposition: str
    financabilite_regle: str
    etabli_par: str
    gestionnaire: str


@attr.dataclass(frozen=True, slots=True)
class SpecifierFinancabiliteNonConcerneeCommand(interface.CommandRequest):
    uuid_proposition: str
    etabli_par: str
    gestionnaire: str


@attr.dataclass(frozen=True, slots=True)
class SpecifierDerogationFinancabiliteCommand(interface.CommandRequest):
    uuid_proposition: str
    statut: str
    gestionnaire: str
    refus_uuids_motifs: List[str] = attr.Factory(list)
    refus_autres_motifs: List[str] = attr.Factory(list)


@attr.dataclass(frozen=True, slots=True)
class NotifierCandidatDerogationFinancabiliteCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    objet_message: str
    corps_message: str


@attr.dataclass(frozen=True, slots=True)
class ModifierStatutChecklistExperienceParcoursAnterieurCommand(interface.CommandRequest):
    uuid_proposition: str
    uuid_experience: str
    gestionnaire: str
    statut: str
    statut_authentification: Optional[bool]


@attr.dataclass(frozen=True, slots=True)
class ModifierAuthentificationExperienceParcoursAnterieurCommand(interface.CommandRequest):
    uuid_proposition: str
    uuid_experience: str
    gestionnaire: str
    etat_authentification: str


@attr.dataclass(frozen=True, slots=True)
class SpecifierBesoinDeDerogationSicCommand(interface.CommandRequest):
    uuid_proposition: str
    besoin_de_derogation: str
    gestionnaire: str


@attr.dataclass(frozen=True, slots=True)
class SpecifierInformationsAcceptationPropositionParSicCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    avec_complements_formation: Optional[bool] = None
    uuids_complements_formation: List[str] = attr.Factory(list)
    commentaire_complements_formation: str = ''
    nombre_annees_prevoir_programme: Optional[int] = None
    nom_personne_contact_programme_annuel: str = ''
    email_personne_contact_programme_annuel: str = ''
    droits_inscription_montant: str = ''
    droits_inscription_montant_autre: Optional[float] = None
    dispense_ou_droits_majores: str = ''
    est_mobilite: Optional[bool] = None
    nombre_de_mois_de_mobilite: str = ''
    doit_se_presenter_en_sic: Optional[bool] = None
    communication_au_candidat: str = ''
    doit_fournir_visa_etudes: Optional[bool] = None


@attr.dataclass(frozen=True, slots=True)
class SpecifierInformationsAcceptationInscriptionParSicCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    avec_complements_formation: Optional[bool] = None
    uuids_complements_formation: List[str] = attr.Factory(list)
    commentaire_complements_formation: str = ''
    nombre_annees_prevoir_programme: Optional[int] = None
    nom_personne_contact_programme_annuel: str = ''
    email_personne_contact_programme_annuel: str = ''


@attr.dataclass(frozen=True, slots=True)
class ApprouverAdmissionParSicCommand(interface.CommandRequest):
    uuid_proposition: str
    objet_message: str
    corps_message: str
    auteur: str


@attr.dataclass(frozen=True, slots=True)
class ApprouverInscriptionParSicCommand(interface.CommandRequest):
    uuid_proposition: str
    objet_message: str
    corps_message: str
    auteur: str


@attr.dataclass(frozen=True, slots=True)
class EnvoyerEmailApprobationInscriptionAuCandidatCommand(interface.CommandRequest):
    uuid_proposition: str
    objet_message: str
    corps_message: str
    auteur: str


@attr.dataclass(frozen=True, slots=True)
class RecupererPdfTemporaireDecisionSicQuery(interface.QueryRequest):
    uuid_proposition: str
    pdf: str
    auteur: str


@attr.dataclass(frozen=True, slots=True)
class VerifierCurriculumApresSoumissionQuery(interface.QueryRequest):
    uuid_proposition: str
