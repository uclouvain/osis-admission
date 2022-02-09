##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from uuid import UUID
from typing import List, Optional, Union

import attr

from admission.ddd.preparation.projet_doctoral.domain.model._candidat_signaletique import CHOIX_LANGUE_CONTACT
from osis_common.ddd import interface


@attr.s(frozen=True, slots=True)
class DoctoratDTO(interface.DTO):
    sigle = attr.ib(type=str)
    annee = attr.ib(type=int)
    intitule_fr = attr.ib(type=str)
    intitule_en = attr.ib(type=str)
    sigle_entite_gestion = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class CountryDTO(interface.DTO):
    id = attr.ib(type=str)
    iso_code = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class IdentificationDTO(interface.DTO):
    matricule = attr.ib(type=str)

    nom = attr.ib(type=Optional[str])
    prenom = attr.ib(type=Optional[str])
    date_naissance = attr.ib(type=Optional[datetime.date])
    annee_naissance = attr.ib(type=Optional[int])
    pays_nationalite = attr.ib(type=Optional[CountryDTO])
    sexe = attr.ib(type=Optional[str])
    genre = attr.ib(type=Optional[str])
    photo_identite = attr.ib(type=List[str])

    carte_identite = attr.ib(type=List[str])
    passeport = attr.ib(type=List[str])
    numero_registre_national_belge = attr.ib(type=Optional[str])
    numero_carte_identite = attr.ib(type=Optional[str])
    numero_passeport = attr.ib(type=Optional[str])
    date_expiration_passeport = attr.ib(type=Optional[datetime.date])

    langue_contact = attr.ib(type=CHOIX_LANGUE_CONTACT, default='')


@attr.s(frozen=True, slots=True)
class CoordonneesDTO(interface.DTO):
    email = attr.ib(type=str)
    # TODO completer les champs en fonction de base.Person


@attr.s(frozen=True, slots=True)
class SuperieurUniversitaireBelgeDTO(interface.DTO):
    communaute_enseignement = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class SuperieurUniversitaireNonBelgeDTO(interface.DTO):
    communaute_enseignement = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class SuperieurNonUniversitaireBelgeDTO(interface.DTO):
    communaute_enseignement = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class SuperieurNonUniversitaireNonBelgeDTO(interface.DTO):
    communaute_enseignement = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class AutreOccupationDTO(interface.DTO):
    communaute_enseignement = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class CurriculumDTO(interface.DTO):
    fichier_pdf = attr.ib(type=str)
    occupations = attr.ib(
        type=List[
            Union[
                SuperieurUniversitaireBelgeDTO,
                SuperieurUniversitaireNonBelgeDTO,
                SuperieurNonUniversitaireBelgeDTO,
                SuperieurNonUniversitaireNonBelgeDTO,
                AutreOccupationDTO,
            ]
        ]
    )


@attr.s(frozen=True, slots=True)
class PropositionDTO(interface.DTO):
    uuid = attr.ib(type=str)
    type_admission = attr.ib(type=str)
    reference = attr.ib(type=str)
    justification = attr.ib(type=Optional[str])
    sigle_doctorat = attr.ib(type=str)
    annee_doctorat = attr.ib(type=int)
    intitule_doctorat_fr = attr.ib(type=str)
    intitule_doctorat_en = attr.ib(type=str)
    matricule_candidat = attr.ib(type=str)
    code_secteur_formation = attr.ib(type=str)
    commission_proximite = attr.ib(type=Optional[str])
    type_financement = attr.ib(type=Optional[str])
    type_contrat_travail = attr.ib(type=Optional[str])
    eft = attr.ib(type=Optional[int])
    bourse_recherche = attr.ib(type=Optional[str])
    duree_prevue = attr.ib(type=Optional[int])
    temps_consacre = attr.ib(type=Optional[int])
    titre_projet = attr.ib(type=Optional[str])
    resume_projet = attr.ib(type=Optional[str])
    documents_projet = attr.ib(type=List[str])  # str == UUID
    graphe_gantt = attr.ib(type=List[str])
    proposition_programme_doctoral = attr.ib(type=List[str])
    projet_formation_complementaire = attr.ib(type=List[str])
    lettres_recommandation = attr.ib(type=List[str])
    langue_redaction_these = attr.ib(type=str)
    institut_these = attr.ib(type=Optional[UUID])
    lieu_these = attr.ib(type=str)
    autre_lieu_these = attr.ib(type=str)
    doctorat_deja_realise = attr.ib(type=str)
    institution = attr.ib(type=Optional[str])
    date_soutenance = attr.ib(type=Optional[datetime.date])
    raison_non_soutenue = attr.ib(type=Optional[str])
    statut = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class PropositionSearchDTO(interface.DTO):
    uuid = attr.ib(type=str)
    reference = attr.ib(type=str)
    type_admission = attr.ib(type=str)
    sigle_doctorat = attr.ib(type=str)
    intitule_doctorat_fr = attr.ib(type=str)
    intitule_doctorat_en = attr.ib(type=str)
    matricule_candidat = attr.ib(type=str)
    code_secteur_formation = attr.ib(type=str)
    intitule_secteur_formation = attr.ib(type=str)
    commission_proximite = attr.ib(type=Optional[str])
    creee_le = attr.ib(type=datetime.datetime)
    statut = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class PromoteurDTO(interface.DTO):
    matricule = attr.ib(type=str)
    nom = attr.ib(type=str)
    prenom = attr.ib(type=str)
    email = attr.ib(type=str)
    titre = attr.ib(type=str, default="")
    institution = attr.ib(type=str, default="")
    ville = attr.ib(type=str, default="")
    pays = attr.ib(type=str, default="")


@attr.s(frozen=True, slots=True)
class MembreCADTO(interface.DTO):
    matricule = attr.ib(type=str)
    nom = attr.ib(type=str)
    prenom = attr.ib(type=str)
    email = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class DetailSignaturePromoteurDTO(interface.DTO):
    promoteur = attr.ib(type=PromoteurDTO)
    status = attr.ib(type=str)
    commentaire_externe = attr.ib(type=Optional[str], default='')


@attr.s(frozen=True, slots=True)
class DetailSignatureMembreCADTO(interface.DTO):
    membre_CA = attr.ib(type=MembreCADTO)
    status = attr.ib(type=str)
    commentaire_externe = attr.ib(type=Optional[str], default='')


@attr.s(frozen=True, slots=True)
class GroupeDeSupervisionDTO(interface.DTO):
    signatures_promoteurs = attr.ib(type=List[DetailSignaturePromoteurDTO], factory=list)
    signatures_membres_CA = attr.ib(type=List[DetailSignatureMembreCADTO], factory=list)


@attr.s(frozen=True, slots=True)
class CotutelleDTO(interface.DTO):
    cotutelle = attr.ib(type=Optional[bool])
    motivation = attr.ib(type=Optional[str])
    institution = attr.ib(type=Optional[str])
    demande_ouverture = attr.ib(type=List[str])
    convention = attr.ib(type=List[str])
    autres_documents = attr.ib(type=List[str])
