##############################################################################
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
##############################################################################
import datetime
from typing import List, Optional, Set
from uuid import UUID

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class DoctoratDTO(interface.DTO):
    sigle: str
    annee: int
    intitule: str
    sigle_entite_gestion: str


@attr.dataclass(frozen=True, slots=True)
class IdentificationDTO(interface.DTO):
    matricule: str

    nom: Optional[str]
    prenom: Optional[str]
    date_naissance: Optional[datetime.date]
    annee_naissance: Optional[int]
    pays_nationalite: Optional[str]
    sexe: Optional[str]
    genre: Optional[str]
    photo_identite: List[str]

    carte_identite: List[str]
    passeport: List[str]
    numero_registre_national_belge: Optional[str]
    numero_carte_identite: Optional[str]
    numero_passeport: Optional[str]
    date_expiration_passeport: Optional[datetime.date]

    langue_contact: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class AdressePersonnelleDTO(interface.DTO):
    rue: Optional[str]
    code_postal: Optional[str]
    ville: Optional[str]
    pays: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class CoordonneesDTO(interface.DTO):
    domicile_legal: Optional[AdressePersonnelleDTO]
    adresse_correspondance: Optional[AdressePersonnelleDTO]


@attr.dataclass(frozen=True, slots=True)
class SuperieurUniversitaireBelgeDTO(interface.DTO):
    communaute_enseignement: str


@attr.dataclass(frozen=True, slots=True)
class SuperieurUniversitaireNonBelgeDTO(interface.DTO):
    communaute_enseignement: str


@attr.dataclass(frozen=True, slots=True)
class SuperieurNonUniversitaireBelgeDTO(interface.DTO):
    communaute_enseignement: str


@attr.dataclass(frozen=True, slots=True)
class SuperieurNonUniversitaireNonBelgeDTO(interface.DTO):
    communaute_enseignement: str


@attr.dataclass(frozen=True, slots=True)
class AutreOccupationDTO(interface.DTO):
    communaute_enseignement: str


@attr.dataclass(frozen=True, slots=True)
class CurriculumDTO(interface.DTO):
    fichier_pdf: List[str]
    annees: Set[int]
    annee_derniere_inscription_ucl: Optional[int]
    annee_diplome_etudes_secondaires_belges: Optional[int]
    annee_diplome_etudes_secondaires_etrangeres: Optional[int]


@attr.dataclass(frozen=True, slots=True)
class PropositionDTO(interface.DTO):
    uuid: str
    type_admission: str
    reference: str
    justification: Optional[str]
    sigle_doctorat: str
    annee_doctorat: int
    intitule_doctorat: str
    matricule_candidat: str
    code_secteur_formation: str
    commission_proximite: Optional[str]
    type_financement: Optional[str]
    type_contrat_travail: Optional[str]
    eft: Optional[int]
    bourse_recherche: Optional[str]
    duree_prevue: Optional[int]
    temps_consacre: Optional[int]
    titre_projet: Optional[str]
    resume_projet: Optional[str]
    documents_projet: List[str]
    graphe_gantt: List[str]
    proposition_programme_doctoral: List[str]
    projet_formation_complementaire: List[str]
    lettres_recommandation: List[str]
    langue_redaction_these: str
    institut_these: Optional[UUID]
    lieu_these: str
    doctorat_deja_realise: str
    institution: Optional[str]
    date_soutenance: Optional[datetime.date]
    raison_non_soutenue: Optional[str]
    statut: str


@attr.dataclass(frozen=True, slots=True)
class PropositionSearchDTO(interface.DTO):
    uuid: str
    reference: str
    type_admission: str
    sigle_doctorat: str
    intitule_doctorat: str
    matricule_candidat: str
    prenom_candidat: str
    nom_candidat: str
    code_secteur_formation: str
    intitule_secteur_formation: str
    commission_proximite: Optional[str]
    creee_le: datetime.datetime
    statut: str


@attr.dataclass(frozen=True, slots=True)
class PromoteurDTO(interface.DTO):
    matricule: str
    nom: str
    prenom: str
    email: str
    titre: str = ""
    institution: str = ""
    ville: str = ""
    pays: str = ""


@attr.dataclass(frozen=True, slots=True)
class MembreCADTO(interface.DTO):
    matricule: str
    nom: str
    prenom: str
    email: str
    titre: str = ""
    institution: str = ""
    ville: str = ""
    pays: str = ""


@attr.dataclass(frozen=True, slots=True)
class DetailSignaturePromoteurDTO(interface.DTO):
    promoteur: PromoteurDTO
    statut: str
    date: Optional[datetime.datetime] = None
    commentaire_externe: Optional[str] = ''
    commentaire_interne: Optional[str] = ''
    motif_refus: Optional[str] = ''
    pdf: List[str] = attr.Factory(list)


@attr.dataclass(frozen=True, slots=True)
class DetailSignatureMembreCADTO(interface.DTO):
    membre_CA: MembreCADTO
    statut: str
    date: Optional[datetime.datetime] = None
    commentaire_externe: Optional[str] = ''
    commentaire_interne: Optional[str] = ''
    motif_refus: Optional[str] = ''
    pdf: List[str] = attr.Factory(list)


@attr.dataclass(frozen=True, slots=True)
class GroupeDeSupervisionDTO(interface.DTO):
    signatures_promoteurs: List[DetailSignaturePromoteurDTO] = attr.Factory(list)
    signatures_membres_CA: List[DetailSignatureMembreCADTO] = attr.Factory(list)


@attr.dataclass(frozen=True, slots=True)
class CotutelleDTO(interface.DTO):
    cotutelle: Optional[bool]
    motivation: Optional[str]
    institution: Optional[str]
    demande_ouverture: List[str]
    convention: List[str]
    autres_documents: List[str]
