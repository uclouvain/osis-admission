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
from dataclasses import dataclass
from typing import List, Optional

from admission.ddd.preparation.projet_doctoral.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import CandidatNonTrouveException
from admission.ddd.preparation.projet_doctoral.dtos import (
    IdentificationDTO,
    CoordonneesDTO,
    AdressePersonnelleDTO,
    CurriculumDTO,
)


@dataclass
class ProfilCandidat:
    matricule: str
    nom: Optional[str]
    prenom: Optional[str]
    prenom_d_usage: Optional[str]
    autres_prenoms: Optional[str]
    date_naissance: Optional[datetime.date]
    annee_naissance: Optional[int]
    lieu_naissance: Optional[str]
    pays_nationalite: Optional[str]
    langue_contact: Optional[str]
    sexe: Optional[str]
    genre: Optional[str]
    photo_identite: List[str]
    curriculum: List[str]
    annee_derniere_inscription_ucl: Optional[int]

    # Pièces d'identité
    carte_identite: List[str]
    passeport: List[str]
    numero_registre_national_belge: Optional[str]
    numero_carte_identite: Optional[str]
    numero_passeport: Optional[str]
    date_expiration_passeport: Optional[datetime.date]


@dataclass
class AdressePersonnelle:
    rue: Optional[str]
    code_postal: Optional[str]
    ville: Optional[str]
    pays: Optional[str]
    personne: str
    type: str


@dataclass
class CoordonneesCandidat:
    domicile_legal: Optional[AdressePersonnelle]
    adresse_correspondance = Optional[AdressePersonnelle]


@dataclass
class Langue:
    code_langue: str


@dataclass
class ConnaissanceLangue:
    personne: str
    langue: Langue


@dataclass
class DiplomeEtudeSecondaire:
    personne: str
    annee: int


@dataclass
class AnneeCurriculum:
    personne: str
    annee: int


class ProfilCandidatInMemoryTranslator(IProfilCandidatTranslator):
    matricule_candidat = '0123456789'
    annee_reference = 2020

    profil_candidats = [
        ProfilCandidat(
            matricule=matricule_candidat,
            nom='Doe',
            prenom='John',
            prenom_d_usage='Jerry',
            autres_prenoms='James',
            date_naissance=datetime.date(1990, 1, 1),
            annee_naissance=1990,
            lieu_naissance='Louvain-La-Neuve',
            pays_nationalite='BE',
            langue_contact='fr-be',
            sexe='M',
            genre='M',
            photo_identite=['uuid11'],
            carte_identite=['uuid12'],
            passeport=['uuid13'],
            numero_registre_national_belge='1001',
            numero_carte_identite='1002',
            numero_passeport='1003',
            date_expiration_passeport=datetime.date(2022, 2, 10),
            curriculum=['uuid14'],
            annee_derniere_inscription_ucl=None,
        ),
    ]
    adresses_candidats = [
        AdressePersonnelle(
            personne=matricule_candidat,
            code_postal='1348',
            ville='Louvain-La-Neuve',
            pays='BE',
            rue="Boulevard de Wallonie",
            type='RESIDENTIAL',
        ),
        AdressePersonnelle(
            personne=matricule_candidat,
            code_postal='1348',
            ville='Louvain-La-Neuve',
            pays='BE',
            rue="Place de l'Université",
            type='CONTACT',
        ),
    ]
    langues = [
        Langue(code_langue='FR'),
        Langue(code_langue='EN'),
        Langue(code_langue='NL'),
        Langue(code_langue='DE'),
    ]
    connaissances_langues = [
        ConnaissanceLangue(personne=matricule_candidat, langue=langues[0]),
        ConnaissanceLangue(personne=matricule_candidat, langue=langues[1]),
        ConnaissanceLangue(personne=matricule_candidat, langue=langues[2]),
    ]
    diplomes_etudes_secondaires_belges = []
    diplomes_etudes_secondaires_etrangers = []
    annees_curriculum = [
        AnneeCurriculum(personne=matricule_candidat, annee=2016),
        AnneeCurriculum(personne=matricule_candidat, annee=2017),
        AnneeCurriculum(personne=matricule_candidat, annee=2018),
        AnneeCurriculum(personne=matricule_candidat, annee=2019),
        AnneeCurriculum(personne=matricule_candidat, annee=2020),
    ]
    adresses_candidats = [
        AdressePersonnelle(
            personne='0123456789',
            code_postal='1348',
            ville='Louvain-La-Neuve',
            pays='BE',
            rue="Boulevard de Wallonie",
            type='RESIDENTIAL',
        ),
        AdressePersonnelle(
            personne='0123456789',
            code_postal='1348',
            ville='Louvain-La-Neuve',
            pays='BE',
            rue="Place de l'Université",
            type='CONTACT'
        )
    ]

    @classmethod
    def get_identification(cls, matricule: str) -> 'IdentificationDTO':
        try:
            candidate = next(c for c in cls.profil_candidats if c.matricule == matricule)
            return IdentificationDTO(
                matricule=matricule,
                nom=candidate.nom,
                prenom=candidate.prenom,
                date_naissance=candidate.date_naissance,
                annee_naissance=candidate.annee_naissance,
                pays_nationalite=candidate.pays_nationalite,
                langue_contact=candidate.langue_contact,
                sexe=candidate.sexe,
                genre=candidate.genre,
                photo_identite=candidate.photo_identite,
                carte_identite=candidate.carte_identite,
                passeport=candidate.passeport,
                numero_registre_national_belge=candidate.numero_registre_national_belge,
                numero_carte_identite=candidate.numero_carte_identite,
                numero_passeport=candidate.numero_passeport,
                date_expiration_passeport=candidate.date_expiration_passeport,
            )
        except StopIteration:  # pragma: no cover
            raise CandidatNonTrouveException

    @classmethod
    def get_coordonnees(cls, matricule: str) -> 'CoordonneesDTO':
        domicile_legal = next(
            (a for a in cls.adresses_candidats if a.personne == matricule and a.type == 'RESIDENTIAL'),
            None,
        )
        adresse_correspondance = next(
            (a for a in cls.adresses_candidats if a.personne == matricule and a.type == 'CONTACT'),
            None,
        )

        return CoordonneesDTO(
            domicile_legal=AdressePersonnelleDTO(
                rue=domicile_legal.rue,
                code_postal=domicile_legal.code_postal,
                ville=domicile_legal.ville,
                pays=domicile_legal.pays,
            )
            if domicile_legal
            else None,
            adresse_correspondance=AdressePersonnelleDTO(
                rue=adresse_correspondance.rue,
                code_postal=adresse_correspondance.code_postal,
                ville=adresse_correspondance.ville,
                pays=adresse_correspondance.pays,
            )
            if adresse_correspondance
            else None,
        )

    @classmethod
    def get_langues_connues(cls, matricule: str) -> int:
        nb_langues_connues_requises = sum(
            c.personne == matricule and c.langue.code_langue in cls.CODES_LANGUES_CONNUES_REQUISES
            for c in cls.connaissances_langues
        )

        return nb_langues_connues_requises

    @classmethod
    def get_curriculum(cls, matricule: str) -> 'CurriculumDTO':
        try:
            candidate = next(c for c in cls.profil_candidats if c.matricule == matricule)

            annees = set(a.annee for a in cls.annees_curriculum if a.personne == matricule)

            annee_diplome_belge = next(
                (d.annee for d in cls.diplomes_etudes_secondaires_belges if d.personne == matricule),
                None,
            )
            annee_diplome_etranger = next(
                (d.annee for d in cls.diplomes_etudes_secondaires_etrangers if d.personne == matricule),
                None,
            )

            return CurriculumDTO(
                annees=annees,
                annee_diplome_etudes_secondaires_belges=annee_diplome_belge,
                annee_diplome_etudes_secondaires_etrangeres=annee_diplome_etranger,
                annee_derniere_inscription_ucl=candidate.annee_derniere_inscription_ucl,
                fichier_pdf=candidate.curriculum,
            )
        except StopIteration:
            raise CandidatNonTrouveException
