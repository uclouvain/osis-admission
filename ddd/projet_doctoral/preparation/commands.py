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
import datetime
from typing import List, Optional

import attr

from admission.ddd.projet_doctoral.preparation.domain.model._detail_projet import ChoixLangueRedactionThese
from admission.ddd.projet_doctoral.preparation.domain.model._experience_precedente_recherche import (
    ChoixDoctoratDejaRealise,
)
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
    type_financement: Optional[str] = ''
    type_contrat_travail: Optional[str] = ''
    eft: Optional[int] = None
    bourse_recherche: Optional[str] = ''
    bourse_date_debut: Optional[datetime.date] = None
    bourse_date_fin: Optional[datetime.date] = None
    bourse_preuve: List[str] = attr.Factory(list)
    duree_prevue: Optional[int] = None
    temps_consacre: Optional[int] = None
    titre_projet: Optional[str] = ''
    resume_projet: Optional[str] = ''
    institut_these: Optional[str] = ''
    lieu_these: Optional[str] = ''
    documents_projet: List[str] = attr.Factory(list)
    graphe_gantt: List[str] = attr.Factory(list)
    proposition_programme_doctoral: List[str] = attr.Factory(list)
    projet_formation_complementaire: List[str] = attr.Factory(list)
    lettres_recommandation: List[str] = attr.Factory(list)
    langue_redaction_these: str = ChoixLangueRedactionThese.UNDECIDED.name
    doctorat_deja_realise: str = ChoixDoctoratDejaRealise.NO.name
    institution: Optional[str] = ''
    domaine_these: Optional[str] = ''
    date_soutenance: Optional[datetime.date] = None
    raison_non_soutenue: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class CompleterPropositionCommand(interface.CommandRequest):
    uuid: str
    type_admission: str
    justification: Optional[str] = ''
    commission_proximite: Optional[str] = ''
    type_financement: Optional[str] = ''
    type_contrat_travail: Optional[str] = ''
    eft: Optional[int] = None
    bourse_recherche: Optional[str] = ''
    bourse_date_debut: Optional[datetime.date] = None
    bourse_date_fin: Optional[datetime.date] = None
    bourse_preuve: List[str] = attr.Factory(list)
    duree_prevue: Optional[int] = None
    temps_consacre: Optional[int] = None
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
    doctorat_deja_realise: str = ChoixDoctoratDejaRealise.NO.name
    institution: Optional[str] = ''
    domaine_these: Optional[str] = ''
    date_soutenance: Optional[datetime.date] = None
    raison_non_soutenue: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class RechercherDoctoratCommand(interface.QueryRequest):
    sigle_secteur_entite_gestion: str


@attr.dataclass(frozen=True, slots=True)
class IdentifierPromoteurCommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: str


@attr.dataclass(frozen=True, slots=True)
class IdentifierMembreCACommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: str


@attr.dataclass(frozen=True, slots=True)
class DemanderSignaturesCommand(interface.CommandRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class VerifierPropositionCommand(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class VerifierProjetCommand(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class SupprimerPromoteurCommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: str


@attr.dataclass(frozen=True, slots=True)
class DesignerPromoteurReferenceCommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: str


@attr.dataclass(frozen=True, slots=True)
class SupprimerMembreCACommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: str


@attr.dataclass(frozen=True, slots=True)
class ApprouverPropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: str
    institut_these: Optional[str] = ''
    commentaire_interne: Optional[str] = ''
    commentaire_externe: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class RefuserPropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    matricule: str
    motif_refus: str
    commentaire_interne: Optional[str] = ''
    commentaire_externe: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class SoumettrePropositionCommand(interface.CommandRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class DefinirCotutelleCommand(interface.CommandRequest):
    uuid_proposition: str
    motivation: Optional[str] = ''
    institution_fwb: Optional[bool] = None
    institution: Optional[str] = ''
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
    matricule: str
    pdf: List[str] = attr.Factory(list)


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
    carte_a_b: List[str]
    decision_protection_subsidiaire: List[str]
    decision_protection_temporaire: List[str]

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
    numero_compte_autre_format: Optional[str]
    code_bic_swift_banque: Optional[str]
    prenom_titulaire_compte: Optional[str]
    nom_titulaire_compte: Optional[str]
