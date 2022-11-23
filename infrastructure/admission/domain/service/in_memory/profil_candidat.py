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

import attr

from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import CandidatNonTrouveException
from admission.ddd.admission.doctorat.preparation.dtos import ConditionsComptabiliteDTO, CurriculumDTO
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.dtos import AdressePersonnelleDTO, CoordonneesDTO, EtudesSecondairesDTO, IdentificationDTO
from base.models.enums.civil_state import CivilState
from base.models.enums.person_address_type import PersonAddressType


@attr.dataclass
class _IdentificationDTO(IdentificationDTO):
    # Trick to make this "unfrozen" just for tests
    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)

    def __delattr__(self, item):
        object.__delattr__(self, item)


@dataclass
class AdressePersonnelle:
    rue: Optional[str]
    code_postal: Optional[str]
    ville: Optional[str]
    pays: Optional[str]
    lieu_dit: Optional[str]
    numero_rue: Optional[str]
    boite_postale: Optional[str]
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
class ExperienceAcademique:
    personne: str
    annee: int
    communaute_fr: bool


@dataclass
class ExperienceNonAcademique:
    personne: str
    date_debut: datetime.date
    date_fin: datetime.date


class ProfilCandidatInMemoryTranslator(IProfilCandidatTranslator):
    matricule_candidat = '0123456789'
    annee_reference = 2020
    profil_candidats = []
    adresses_candidats = []
    langues = []
    connaissances_langues = []
    diplomes_etudes_secondaires_belges = []
    diplomes_etudes_secondaires_etrangers = []
    etudes_secondaires = {}
    experiences_academiques = []
    experiences_non_academiques = []
    cv_files = {"0123456789": ['uuid14']}
    pays_union_europeenne = {
        "AT",
        "BE",
        "BG",
        "HR",
        "CY",
        "CZ",
        "DK",
        "EE",
        "FI",
        "FR",
        "DE",
        "GR",
        "HU",
        "IE",
        "IT",
        "LV",
        "LT",
        "LU",
        "MT",
        "NL",
        "PL",
        "PT",
        "RO",
        "SK",
        "SI",
        "ES",
        "SE",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reset()

    @classmethod
    def reset(cls):
        cls.profil_candidats = [
            _IdentificationDTO(
                matricule=cls.matricule_candidat,
                nom='Doe',
                prenom='John',
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
                annee_derniere_inscription_ucl=None,
                noma_derniere_inscription_ucl='',
                email='john.doe@ucl.be',
                pays_naissance='BE',
                etat_civil=CivilState.MARRIED.name,
                pays_residence="BE",
            ),
            _IdentificationDTO(
                matricule="0000000001",
                nom='Smith',
                prenom='Jane',
                date_naissance=datetime.date(1990, 1, 1),
                annee_naissance=None,
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
                annee_derniere_inscription_ucl=None,
                noma_derniere_inscription_ucl='',
                email='john.doe@ucl.be',
                pays_naissance='BE',
                etat_civil=CivilState.MARRIED.name,
                pays_residence="BE",
            ),
        ]
        cls.adresses_candidats = [
            AdressePersonnelle(
                personne=cls.matricule_candidat,
                code_postal='1348',
                ville='Louvain-La-Neuve',
                pays='BE',
                rue="Boulevard de Wallonie",
                type='RESIDENTIAL',
                lieu_dit='',
                numero_rue='10',
                boite_postale='B1',
            ),
            AdressePersonnelle(
                personne=cls.matricule_candidat,
                code_postal='1348',
                ville='Louvain-La-Neuve',
                pays='BE',
                rue="Place de l'Université",
                type='CONTACT',
                lieu_dit='',
                numero_rue='14',
                boite_postale='B2',
            ),
            AdressePersonnelle(
                personne="0000000001",
                code_postal='1348',
                ville='Louvain-La-Neuve',
                pays='BE',
                rue="Place de l'Université",
                type='RESIDENTIAL',
                lieu_dit='',
                numero_rue='14',
                boite_postale='B2',
            ),
        ]
        cls.langues = [
            Langue(code_langue='FR'),
            Langue(code_langue='EN'),
            Langue(code_langue='NL'),
            Langue(code_langue='DE'),
        ]

        cls.connaissances_langues = [
            ConnaissanceLangue(personne=cls.matricule_candidat, langue=cls.langues[0]),
            ConnaissanceLangue(personne=cls.matricule_candidat, langue=cls.langues[1]),
            ConnaissanceLangue(personne=cls.matricule_candidat, langue=cls.langues[2]),
        ]

        cls.experiences_academiques = [
            ExperienceAcademique(personne=cls.matricule_candidat, annee=2016, communaute_fr=False),
            ExperienceAcademique(personne=cls.matricule_candidat, annee=2017, communaute_fr=False),
            ExperienceAcademique(personne=cls.matricule_candidat, annee=2019, communaute_fr=False),
            ExperienceAcademique(personne=cls.matricule_candidat, annee=2020, communaute_fr=True),
        ]

        cls.experiences_non_academiques = [
            ExperienceNonAcademique(
                personne=cls.matricule_candidat,
                date_debut=datetime.date(2019, 5, 1),
                date_fin=datetime.date(2019, 8, 31),
            ),
            ExperienceNonAcademique(
                personne=cls.matricule_candidat,
                date_debut=datetime.date(2018, 7, 1),
                date_fin=datetime.date(2019, 4, 30),
            ),
        ]

        cls.diplomes_etudes_secondaires_belges = []
        cls.diplomes_etudes_secondaires_etrangers = []
        cls.etudes_secondaires = {
            cls.matricule_candidat: EtudesSecondairesDTO(True, False, False),
            "0123456789": EtudesSecondairesDTO(True, False, False),
            "0000000001": EtudesSecondairesDTO(True, False, False),
        }

    @classmethod
    def get_identification(cls, matricule: str) -> 'IdentificationDTO':
        domicile_legal = next(
            (
                a
                for a in cls.adresses_candidats
                if a.personne == matricule and a.type == PersonAddressType.RESIDENTIAL.name
            ),
            None,
        )

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
                email=candidate.email,
                pays_naissance=candidate.pays_naissance,
                lieu_naissance=candidate.lieu_naissance,
                etat_civil=candidate.etat_civil,
                annee_derniere_inscription_ucl=candidate.annee_derniere_inscription_ucl,
                noma_derniere_inscription_ucl=candidate.noma_derniere_inscription_ucl,
                pays_residence=domicile_legal.pays if domicile_legal else None,
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
                lieu_dit=domicile_legal.lieu_dit,
                numero_rue=domicile_legal.numero_rue,
                boite_postale=domicile_legal.boite_postale,
            )
            if domicile_legal
            else None,
            adresse_correspondance=AdressePersonnelleDTO(
                rue=adresse_correspondance.rue,
                code_postal=adresse_correspondance.code_postal,
                ville=adresse_correspondance.ville,
                pays=adresse_correspondance.pays,
                lieu_dit=adresse_correspondance.lieu_dit,
                numero_rue=adresse_correspondance.numero_rue,
                boite_postale=adresse_correspondance.boite_postale,
            )
            if adresse_correspondance
            else None,
        )

    @classmethod
    def get_langues_connues(cls, matricule: str) -> List[str]:
        return [c.langue.code_langue for c in cls.connaissances_langues if c.personne == matricule]

    @classmethod
    def get_etudes_secondaires(cls, matricule: str) -> 'EtudesSecondairesDTO':
        return cls.etudes_secondaires.get(matricule) or EtudesSecondairesDTO(False, False, False)

    @classmethod
    def get_curriculum(cls, matricule: str, annee_courante: int) -> 'CurriculumDTO':
        try:
            candidate = next(c for c in cls.profil_candidats if c.matricule == matricule)

            annees_experiences_academiques = [
                experience.annee for experience in cls.experiences_academiques if experience.personne == matricule
            ]

            dates_experiences_non_academiques = [
                (experience.date_debut, experience.date_fin)
                for experience in cls.experiences_non_academiques
                if experience.personne == matricule
            ]

            annee_diplome_belge = next(
                (d.annee for d in cls.diplomes_etudes_secondaires_belges if d.personne == matricule),
                None,
            )
            annee_diplome_etranger = next(
                (d.annee for d in cls.diplomes_etudes_secondaires_etrangers if d.personne == matricule),
                None,
            )

            return CurriculumDTO(
                annees_experiences_academiques=annees_experiences_academiques,
                annee_diplome_etudes_secondaires_belges=annee_diplome_belge,
                annee_diplome_etudes_secondaires_etrangeres=annee_diplome_etranger,
                annee_derniere_inscription_ucl=candidate.annee_derniere_inscription_ucl,
                dates_experiences_non_academiques=dates_experiences_non_academiques,
            )
        except StopIteration:
            raise CandidatNonTrouveException

    @classmethod
    def get_conditions_comptabilite(
        cls,
        matricule: str,
        annee_courante: int,
    ) -> 'ConditionsComptabiliteDTO':
        try:
            candidate = next(c for c in cls.profil_candidats if c.matricule == matricule)
            return ConditionsComptabiliteDTO(
                pays_nationalite_ue=candidate.pays_nationalite in cls.pays_union_europeenne
                if candidate.pays_nationalite
                else None,
                a_frequente_recemment_etablissement_communaute_fr=any(
                    experience.communaute_fr
                    for experience in cls.experiences_academiques
                    if experience.personne == matricule
                ),
            )
        except StopIteration:
            raise CandidatNonTrouveException

    @classmethod
    def est_changement_etablissement(cls, matricule: str, annee_courante: int) -> bool:
        return False
