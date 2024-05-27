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

from typing import Dict, List, Optional

import attr

from admission.ddd.admission import commands
from admission.ddd.interface import SortedQueryRequest
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True, auto_attribs=True)
class RechercherFormationContinueQuery(interface.QueryRequest):
    terme_de_recherche: str
    campus: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True, auto_attribs=True)
class RecupererFormationContinueQuery(interface.QueryRequest):
    sigle: str
    annee: int


@attr.dataclass(frozen=True, slots=True)
class InitierPropositionCommand(interface.CommandRequest):
    sigle_formation: str
    annee_formation: int
    matricule_candidat: str
    motivations: str
    moyens_decouverte_formation: List[str]
    marque_d_interet: Optional[bool] = None


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

    motivations: str
    moyens_decouverte_formation: List[str]

    marque_d_interet: Optional[bool] = None
    reponses_questions_specifiques: Dict = attr.Factory(dict)


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
class DeterminerAnneeAcademiqueEtPotQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class CompleterComptabilitePropositionCommand(interface.CommandRequest):
    uuid_proposition: str

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
class RecupererElementsConfirmationQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class CompleterQuestionsSpecifiquesCommand(interface.CommandRequest):
    uuid_proposition: str

    inscription_a_titre: Optional[str] = ''
    nom_siege_social: Optional[str] = ''
    numero_unique_entreprise: Optional[str] = ''
    numero_tva_entreprise: Optional[str] = ''
    adresse_mail_professionnelle: Optional[str] = ''

    # Adresse facturation
    type_adresse_facturation: Optional[str] = ''
    adresse_facturation_rue: Optional[str] = ''
    adresse_facturation_numero_rue: Optional[str] = ''
    adresse_facturation_code_postal: Optional[str] = ''
    adresse_facturation_ville: Optional[str] = ''
    adresse_facturation_pays: Optional[str] = ''
    adresse_facturation_destinataire: Optional[str] = ''
    adresse_facturation_boite_postale: Optional[str] = ''

    reponses_questions_specifiques: Dict = attr.Factory(dict)
    copie_titre_sejour: List[str] = attr.Factory(list)
    documents_additionnels: List[str] = attr.Factory(list)


@attr.dataclass(frozen=True, slots=True)
class RecupererQuestionsSpecifiquesQuery(commands.RecupererQuestionsSpecifiquesQuery):
    pass


@attr.dataclass(frozen=True, slots=True)
class RecupererDocumentsPropositionQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class RecupererResumeEtEmplacementsDocumentsNonLibresPropositionQuery(interface.QueryRequest):
    uuid_proposition: str


@attr.dataclass(frozen=True, slots=True)
class RetyperDocumentCommand(interface.CommandRequest):
    uuid_proposition: str
    identifiant_source: str
    identifiant_cible: str
    auteur: str


@attr.dataclass(frozen=True, slots=True)
class MettreEnAttenteCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    objet_message: str
    corps_message: str
    motif: str
    autre_motif: str


@attr.dataclass(frozen=True, slots=True)
class ApprouverParFacCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    objet_message: str
    corps_message: str
    condition: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class RefuserPropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    objet_message: str
    corps_message: str
    motif: str
    autre_motif: str


@attr.dataclass(frozen=True, slots=True)
class AnnulerPropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    objet_message: str
    corps_message: str
    motif: str


@attr.dataclass(frozen=True, slots=True)
class ValiderPropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str
    objet_message: str
    corps_message: str


@attr.dataclass(frozen=True, slots=True)
class CloturerPropositionCommand(interface.CommandRequest):
    uuid_proposition: str
    gestionnaire: str


@attr.dataclass(frozen=True, slots=True)
class ListerDemandesQuery(SortedQueryRequest):
    annee_academique: Optional[int] = None
    edition: Optional[str] = ''
    numero: Optional[int] = None
    matricule_candidat: Optional[str] = ''
    etats: Optional[List[str]] = None
    facultes: Optional[List[str]] = None
    types_formation: Optional[List[str]] = None
    sigles_formations: Optional[List[str]] = None
    inscription_requise: Optional[bool] = None
    paye: Optional[bool] = None
    demandeur: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class ModifierChoixFormationParGestionnaireCommand:
    uuid_proposition: str
    gestionnaire: str
    sigle_formation: str
    annee_formation: int
    reponses_questions_specifiques: Dict
    motivations: str
    moyens_decouverte_formation: List[str]
    marque_d_interet: Optional[bool]
