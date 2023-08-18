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
from dataclasses import dataclass
from typing import Dict, List, Optional

import attr

from admission.ddd import BE_ISO_CODE
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import CandidatNonTrouveException
from admission.ddd.admission.doctorat.preparation.dtos import (
    AnneeExperienceAcademiqueDTO,
    ConditionsComptabiliteDTO,
    CurriculumAExperiencesDTO,
    CurriculumDTO,
    ExperienceAcademiqueDTO,
    ConnaissanceLangueDTO,
)
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import ExperienceNonAcademiqueDTO
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.dtos import AdressePersonnelleDTO, CoordonneesDTO, EtudesSecondairesDTO, IdentificationDTO
from admission.ddd.admission.dtos.etudes_secondaires import DiplomeBelgeEtudesSecondairesDTO
from admission.ddd.admission.dtos.resume import ResumeCandidatDTO
from base.models.enums.civil_state import CivilState
from base.models.enums.community import CommunityEnum
from base.models.enums.education_group_types import TrainingType
from base.models.enums.got_diploma import GotDiploma
from base.models.enums.person_address_type import PersonAddressType
from base.models.enums.teaching_type import TeachingTypeEnum
from osis_profile.models.enums.curriculum import (
    Result,
    TranscriptType,
    Grade,
    EvaluationSystem,
    ActivityType,
    ActivitySector,
)


class UnfrozenDTO:
    # Trick to make this "unfrozen" just for tests
    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)

    def __delattr__(self, item):
        object.__delattr__(self, item)


@attr.dataclass
class _IdentificationDTO(UnfrozenDTO, IdentificationDTO):
    pass


@attr.dataclass
class _EtudesSecondairesDTO(UnfrozenDTO, EtudesSecondairesDTO):
    pass


@dataclass
class AdressePersonnelle:
    rue: Optional[str]
    code_postal: Optional[str]
    ville: Optional[str]
    pays: Optional[str]
    nom_pays: Optional[str]
    numero_rue: Optional[str]
    boite_postale: Optional[str]
    personne: str
    type: str


@dataclass
class CoordonneesCandidat:
    personne: str
    domicile_legal: Optional[AdressePersonnelle] = None
    adresse_correspondance: Optional[AdressePersonnelle] = None
    adresse_email_privee: str = ''
    numero_mobile: str = ''
    numero_contact_urgence: str = ''


@dataclass
class Langue:
    code_langue: str
    nom_langue: str


@dataclass
class ConnaissanceLangue:
    personne: str
    langue: Langue
    comprehension_orale: str
    capacite_orale: str
    capacite_ecriture: str
    certificat: List[str]


@dataclass
class DiplomeEtudeSecondaire:
    personne: str
    annee: int


@dataclass
class AnneeExperienceAcademique:
    annee: int
    resultat: str
    releve_notes: List[str]
    traduction_releve_notes: List[str]
    credits_inscrits: Optional[float]
    credits_acquis: Optional[float]


@dataclass
class ExperienceAcademique:
    uuid: str
    personne: str
    communaute_fr: bool
    pays: str
    annees: List[AnneeExperienceAcademique]
    regime_linguistique: str
    type_releve_notes: str
    releve_notes: List[str]
    traduction_releve_notes: List[str]
    diplome: List[str]
    traduction_diplome: List[str]
    a_obtenu_diplome: bool
    rang_diplome: str
    date_prevue_delivrance_diplome: Optional[datetime.date]
    titre_memoire: str
    note_memoire: str
    resume_memoire: List[str]
    grade_obtenu: str
    systeme_evaluation: str
    nom_formation: str
    adresse_institut: str
    code_institut: str
    communaute_institut: str
    nom_institut: str
    nom_pays: str
    nom_regime_linguistique: str
    type_enseignement: str


@dataclass
class ExperienceNonAcademique:
    personne: str
    date_debut: datetime.date
    date_fin: datetime.date
    uuid: str
    employeur: str
    type: str
    certificat: List[str]
    fonction: str
    secteur: str
    autre_activite: str


class ProfilCandidatInMemoryTranslator(IProfilCandidatTranslator):
    matricule_candidat = '0123456789'
    annee_reference = 2020
    profil_candidats: List[_IdentificationDTO] = []
    adresses_candidats: List[AdressePersonnelle] = []
    coordonnees_candidats: List[CoordonneesCandidat] = []
    langues: List[Langue] = []
    connaissances_langues: List[ConnaissanceLangue] = []
    diplomes_etudes_secondaires_belges: List[DiplomeEtudeSecondaire] = []
    diplomes_etudes_secondaires_etrangers: List[DiplomeEtudeSecondaire] = []
    etudes_secondaires = {}
    experiences_academiques: List[ExperienceAcademique] = []
    experiences_non_academiques: List[ExperienceNonAcademique] = []
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
                pays_nationalite_europeen=True,
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
                autres_prenoms='Joe, James',
                nom_pays_nationalite='Belgique',
                nom_pays_naissance='Belgique',
                nom_langue_contact='Français',
                date_expiration_passeport=datetime.date(2020, 1, 1),
                date_expiration_carte_identite=datetime.date(2020, 1, 1),
            ),
            _IdentificationDTO(
                matricule="0000000001",
                nom='Smith',
                prenom='Jane',
                date_naissance=datetime.date(1990, 1, 1),
                annee_naissance=None,
                lieu_naissance='Louvain-La-Neuve',
                pays_nationalite='BE',
                pays_nationalite_europeen=True,
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
                autres_prenoms='Jessy',
                nom_pays_nationalite='Belgique',
                nom_pays_naissance='Belgique',
                nom_langue_contact='Français',
                date_expiration_passeport=datetime.date(2020, 1, 1),
                date_expiration_carte_identite=datetime.date(2020, 1, 1),
            ),
            _IdentificationDTO(
                matricule="0000000002",
                nom='My',
                prenom='Jim',
                date_naissance=datetime.date(1990, 1, 1),
                annee_naissance=None,
                lieu_naissance='Louvain-La-Neuve',
                pays_nationalite_europeen=True,
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
                autres_prenoms='Jack',
                nom_pays_nationalite='Belgique',
                nom_pays_naissance='Belgique',
                nom_langue_contact='Français',
                date_expiration_passeport=datetime.date(2020, 1, 1),
                date_expiration_carte_identite=datetime.date(2020, 1, 1),
            ),
            _IdentificationDTO(
                matricule="0000000003",
                nom='Foreign',
                prenom='Individual',
                date_naissance=datetime.date(1990, 1, 1),
                annee_naissance=None,
                lieu_naissance='Louvain-La-Neuve',
                pays_nationalite_europeen=True,
                pays_nationalite='AR',
                langue_contact='en',
                sexe='M',
                genre='M',
                photo_identite=['uuid11'],
                carte_identite=['uuid12'],
                passeport=['uuid13'],
                numero_registre_national_belge='',
                numero_carte_identite='',
                numero_passeport='1003',
                annee_derniere_inscription_ucl=None,
                noma_derniere_inscription_ucl='',
                email='john.doe@ucl.be',
                pays_naissance='BE',
                etat_civil=CivilState.MARRIED.name,
                pays_residence="BE",
                nom_langue_contact='Anglais',
                autres_prenoms='',
                nom_pays_nationalite='Argentine',
                nom_pays_naissance='Belgique',
                date_expiration_passeport=datetime.date(2020, 1, 1),
                date_expiration_carte_identite=datetime.date(2020, 1, 1),
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
                numero_rue='10',
                boite_postale='B1',
                nom_pays='Belgique',
            ),
            AdressePersonnelle(
                personne=cls.matricule_candidat,
                code_postal='1348',
                ville='Louvain-La-Neuve',
                pays='BE',
                rue="Place de l'Université",
                type='CONTACT',
                numero_rue='14',
                boite_postale='B2',
                nom_pays='Belgique',
            ),
            AdressePersonnelle(
                personne="0000000001",
                code_postal='1348',
                ville='Louvain-La-Neuve',
                pays='BE',
                rue="Place de l'Université",
                type='RESIDENTIAL',
                numero_rue='14',
                boite_postale='B2',
                nom_pays='Belgique',
            ),
            AdressePersonnelle(
                personne="0000000002",
                code_postal='1348',
                ville='Louvain-La-Neuve',
                pays='BE',
                rue="Place de l'Université",
                type='RESIDENTIAL',
                numero_rue='14',
                boite_postale='B2',
                nom_pays='Belgique',
            ),
        ]
        cls.coordonnees_candidats = [
            CoordonneesCandidat(
                personne=cls.matricule_candidat,
                domicile_legal=cls.adresses_candidats[0],
                adresse_correspondance=cls.adresses_candidats[1],
                adresse_email_privee='john.doe@example.be.',
            ),
            CoordonneesCandidat(
                personne='0000000001',
                domicile_legal=cls.adresses_candidats[2],
                adresse_email_privee='john.doe@example.be.',
            ),
            CoordonneesCandidat(
                personne='0000000002',
                domicile_legal=cls.adresses_candidats[3],
                adresse_email_privee='john.doe@example.be.',
            ),
        ]
        cls.langues = [
            Langue(code_langue='FR', nom_langue='Français'),
            Langue(code_langue='EN', nom_langue='Anglais'),
            Langue(code_langue='NL', nom_langue='Néerlandais'),
            Langue(code_langue='DE', nom_langue='Allemand'),
        ]

        cls.connaissances_langues = [
            ConnaissanceLangue(
                personne=cls.matricule_candidat,
                langue=cls.langues[0],
                comprehension_orale='C2',
                capacite_orale='C2',
                capacite_ecriture='C2',
                certificat=[],
            ),
            ConnaissanceLangue(
                personne=cls.matricule_candidat,
                langue=cls.langues[1],
                comprehension_orale='B2',
                capacite_orale='B2',
                capacite_ecriture='B2',
                certificat=[],
            ),
            ConnaissanceLangue(
                personne=cls.matricule_candidat,
                langue=cls.langues[2],
                comprehension_orale='B2',
                capacite_orale='B2',
                capacite_ecriture='B2',
                certificat=[],
            ),
        ]

        cls.experiences_academiques = [
            ExperienceAcademique(
                uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee1',
                personne=cls.matricule_candidat,
                communaute_fr=False,
                pays='FR',
                annees=[
                    AnneeExperienceAcademique(
                        annee=2016,
                        resultat=Result.SUCCESS.name,
                        releve_notes=['releve1.pdf'],
                        traduction_releve_notes=['traduction_releve1.pdf'],
                        credits_acquis=10,
                        credits_inscrits=10,
                    ),
                    AnneeExperienceAcademique(
                        annee=2017,
                        resultat=Result.SUCCESS.name,
                        releve_notes=['releve2.pdf'],
                        traduction_releve_notes=['traduction_releve2.pdf'],
                        credits_acquis=10,
                        credits_inscrits=10,
                    ),
                    AnneeExperienceAcademique(
                        annee=2019,
                        resultat=Result.SUCCESS.name,
                        releve_notes=['releve3.pdf'],
                        traduction_releve_notes=['traduction_releve3.pdf'],
                        credits_acquis=10,
                        credits_inscrits=10,
                    ),
                ],
                regime_linguistique='FR',
                type_releve_notes=TranscriptType.ONE_FOR_ALL_YEARS.name,
                releve_notes=['releve_notes.pdf'],
                traduction_releve_notes=['traduction_releve_notes.pdf'],
                diplome=['diplome.pdf'],
                traduction_diplome=['traduction_diplome.pdf'],
                a_obtenu_diplome=True,
                rang_diplome='10',
                date_prevue_delivrance_diplome=datetime.date(2020, 2, 2),
                titre_memoire='Titre',
                note_memoire='15 sur 20',
                resume_memoire=['resume_memoire.pdf'],
                grade_obtenu=Grade.GREAT_DISTINCTION.name,
                systeme_evaluation=EvaluationSystem.NO_CREDIT_SYSTEM.name,
                nom_formation='Formation A',
                adresse_institut='Louvain-La-Neuve',
                code_institut='UCL',
                communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
                nom_institut='Université Catholique de Louvain',
                nom_pays='Belgique',
                nom_regime_linguistique='Français',
                type_enseignement=TeachingTypeEnum.FULL_TIME.name,
            ),
            ExperienceAcademique(
                uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                personne=cls.matricule_candidat,
                communaute_fr=True,
                pays=BE_ISO_CODE,
                annees=[
                    AnneeExperienceAcademique(
                        annee=2020,
                        resultat=Result.SUCCESS.name,
                        releve_notes=['releve1.pdf'],
                        traduction_releve_notes=['traduction_releve1.pdf'],
                        credits_acquis=10,
                        credits_inscrits=10,
                    ),
                ],
                regime_linguistique='',
                type_releve_notes=TranscriptType.ONE_FOR_ALL_YEARS.name,
                releve_notes=['releve_notes.pdf'],
                traduction_releve_notes=['traduction_releve_notes.pdf'],
                diplome=['diplome.pdf'],
                traduction_diplome=['traduction_diplome.pdf'],
                a_obtenu_diplome=True,
                rang_diplome='10',
                date_prevue_delivrance_diplome=datetime.date(2020, 2, 2),
                titre_memoire='Titre',
                note_memoire='15 sur 20',
                resume_memoire=['resume_memoire.pdf'],
                grade_obtenu=Grade.GREAT_DISTINCTION.name,
                systeme_evaluation=EvaluationSystem.NO_CREDIT_SYSTEM.name,
                nom_formation='Formation B',
                adresse_institut='Louvain-La-Neuve',
                code_institut='UCL',
                communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
                nom_institut='Université Catholique de Louvain',
                nom_pays='Belgique',
                nom_regime_linguistique='Français',
                type_enseignement=TeachingTypeEnum.FULL_TIME.name,
            ),
            ExperienceAcademique(
                uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee3',
                personne='0000000001',
                communaute_fr=False,
                pays='FR',
                annees=[
                    AnneeExperienceAcademique(
                        annee=2016,
                        resultat=Result.SUCCESS.name,
                        releve_notes=['releve1.pdf'],
                        traduction_releve_notes=['traduction_releve1.pdf'],
                        credits_acquis=10,
                        credits_inscrits=10,
                    ),
                    AnneeExperienceAcademique(
                        annee=2017,
                        resultat=Result.SUCCESS.name,
                        releve_notes=['releve2.pdf'],
                        traduction_releve_notes=['traduction_releve2.pdf'],
                        credits_acquis=10,
                        credits_inscrits=10,
                    ),
                    AnneeExperienceAcademique(
                        annee=2019,
                        resultat=Result.SUCCESS.name,
                        releve_notes=['releve3.pdf'],
                        traduction_releve_notes=['traduction_releve3.pdf'],
                        credits_acquis=10,
                        credits_inscrits=10,
                    ),
                ],
                regime_linguistique='FR',
                type_releve_notes=TranscriptType.ONE_FOR_ALL_YEARS.name,
                releve_notes=['releve_notes.pdf'],
                traduction_releve_notes=['traduction_releve_notes.pdf'],
                diplome=['diplome.pdf'],
                traduction_diplome=['traduction_diplome.pdf'],
                a_obtenu_diplome=True,
                rang_diplome='10',
                date_prevue_delivrance_diplome=datetime.date(2020, 2, 2),
                titre_memoire='Titre',
                note_memoire='15 sur 20',
                resume_memoire=['resume_memoire.pdf'],
                grade_obtenu=Grade.GREAT_DISTINCTION.name,
                systeme_evaluation=EvaluationSystem.NO_CREDIT_SYSTEM.name,
                nom_formation='Formation C',
                adresse_institut='Louvain-La-Neuve',
                code_institut='UCL',
                communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
                nom_institut='Université Catholique de Louvain',
                nom_pays='Belgique',
                nom_regime_linguistique='Français',
                type_enseignement=TeachingTypeEnum.FULL_TIME.name,
            ),
            ExperienceAcademique(
                uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee4',
                personne='0000000001',
                communaute_fr=True,
                pays=BE_ISO_CODE,
                annees=[
                    AnneeExperienceAcademique(
                        annee=2020,
                        resultat=Result.SUCCESS.name,
                        releve_notes=['releve1.pdf'],
                        traduction_releve_notes=['traduction_releve1.pdf'],
                        credits_acquis=10,
                        credits_inscrits=10,
                    ),
                ],
                regime_linguistique='FR',
                type_releve_notes=TranscriptType.ONE_FOR_ALL_YEARS.name,
                releve_notes=['releve_notes.pdf'],
                traduction_releve_notes=['traduction_releve_notes.pdf'],
                diplome=['diplome.pdf'],
                traduction_diplome=['traduction_diplome.pdf'],
                a_obtenu_diplome=True,
                rang_diplome='10',
                date_prevue_delivrance_diplome=datetime.date(2020, 2, 2),
                titre_memoire='Titre',
                note_memoire='15 sur 20',
                resume_memoire=['resume_memoire.pdf'],
                grade_obtenu=Grade.GREAT_DISTINCTION.name,
                systeme_evaluation=EvaluationSystem.NO_CREDIT_SYSTEM.name,
                nom_formation='Formation D',
                adresse_institut='Louvain-La-Neuve',
                code_institut='UCL',
                communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
                nom_institut='Université Catholique de Louvain',
                nom_pays='Belgique',
                nom_regime_linguistique='Français',
                type_enseignement=TeachingTypeEnum.FULL_TIME.name,
            ),
            ExperienceAcademique(
                uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee5',
                personne='0000000002',
                communaute_fr=False,
                pays='FR',
                annees=[
                    AnneeExperienceAcademique(
                        annee=2016,
                        resultat=Result.SUCCESS.name,
                        releve_notes=['releve1.pdf'],
                        traduction_releve_notes=['traduction_releve1.pdf'],
                        credits_acquis=10,
                        credits_inscrits=10,
                    ),
                    AnneeExperienceAcademique(
                        annee=2017,
                        resultat=Result.SUCCESS.name,
                        releve_notes=['releve2.pdf'],
                        traduction_releve_notes=['traduction_releve2.pdf'],
                        credits_acquis=10,
                        credits_inscrits=10,
                    ),
                    AnneeExperienceAcademique(
                        annee=2018,
                        resultat=Result.SUCCESS.name,
                        releve_notes=['releve3.pdf'],
                        traduction_releve_notes=['traduction_releve3.pdf'],
                        credits_acquis=10,
                        credits_inscrits=10,
                    ),
                    AnneeExperienceAcademique(
                        annee=2019,
                        resultat=Result.SUCCESS.name,
                        releve_notes=['releve4.pdf'],
                        traduction_releve_notes=['traduction_releve4.pdf'],
                        credits_acquis=10,
                        credits_inscrits=10,
                    ),
                    AnneeExperienceAcademique(
                        annee=2020,
                        resultat=Result.SUCCESS.name,
                        releve_notes=['releve5.pdf'],
                        traduction_releve_notes=['traduction_releve5.pdf'],
                        credits_acquis=10,
                        credits_inscrits=10,
                    ),
                ],
                regime_linguistique='FR',
                type_releve_notes=TranscriptType.ONE_FOR_ALL_YEARS.name,
                releve_notes=['releve_notes.pdf'],
                traduction_releve_notes=['traduction_releve_notes.pdf'],
                diplome=['diplome.pdf'],
                traduction_diplome=['traduction_diplome.pdf'],
                a_obtenu_diplome=True,
                rang_diplome='10',
                date_prevue_delivrance_diplome=datetime.date(2020, 2, 2),
                titre_memoire='Titre',
                note_memoire='15 sur 20',
                resume_memoire=['resume_memoire.pdf'],
                grade_obtenu=Grade.GREAT_DISTINCTION.name,
                systeme_evaluation=EvaluationSystem.NO_CREDIT_SYSTEM.name,
                nom_formation='Formation E',
                adresse_institut='Louvain-La-Neuve',
                code_institut='UCL',
                communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
                nom_institut='Université Catholique de Louvain',
                nom_pays='Belgique',
                nom_regime_linguistique='Français',
                type_enseignement=TeachingTypeEnum.FULL_TIME.name,
            ),
        ]

        cls.experiences_non_academiques = [
            ExperienceNonAcademique(
                personne=cls.matricule_candidat,
                date_debut=datetime.date(2019, 5, 1),
                date_fin=datetime.date(2019, 8, 31),
                uuid='1cbdf4db-2454-4cbf-9e48-55d2a9881ee1',
                employeur='UCL',
                type=ActivityType.WORK.name,
                certificat=['uuid-certificate'],
                fonction='Librarian',
                secteur=ActivitySector.PRIVATE.name,
                autre_activite='',
            ),
            ExperienceNonAcademique(
                personne=cls.matricule_candidat,
                date_debut=datetime.date(2018, 7, 1),
                date_fin=datetime.date(2019, 4, 30),
                uuid='1cbdf4db-2454-4cbf-9e48-55d2a9881ee1',
                employeur='',
                type=ActivityType.OTHER.name,
                certificat=[],
                fonction='',
                secteur='',
                autre_activite='Other',
            ),
            ExperienceNonAcademique(
                personne='0000000001',
                date_debut=datetime.date(2019, 5, 1),
                date_fin=datetime.date(2019, 8, 31),
                uuid='1cbdf4db-2454-4cbf-9e48-55d2a9881ee1',
                employeur='UCL',
                type=ActivityType.INTERNSHIP.name,
                certificat=['uuid-certificate'],
                fonction='Computer scientist',
                secteur=ActivitySector.PRIVATE.name,
                autre_activite='',
            ),
            ExperienceNonAcademique(
                personne='0000000001',
                date_debut=datetime.date(2018, 7, 1),
                date_fin=datetime.date(2019, 4, 30),
                uuid='1cbdf4db-2454-4cbf-9e48-55d2a9881ee1',
                employeur='',
                type=ActivityType.LANGUAGE_TRAVEL.name,
                certificat=['uuid-certificate'],
                fonction='',
                secteur='',
                autre_activite='',
            ),
        ]

        cls.diplomes_etudes_secondaires_belges = []
        cls.diplomes_etudes_secondaires_etrangers = []
        cls.etudes_secondaires = {
            cls.matricule_candidat: _EtudesSecondairesDTO(
                diplome_belge=DiplomeBelgeEtudesSecondairesDTO(
                    certificat_inscription=['certificat_inscription.pdf'],
                    diplome=['diplome.pdf'],
                ),
                diplome_etudes_secondaires=GotDiploma.YES.name,
                annee_diplome_etudes_secondaires=2022,
            ),
            "0123456789": _EtudesSecondairesDTO(
                diplome_belge=DiplomeBelgeEtudesSecondairesDTO(
                    certificat_inscription=['certificat_inscription.pdf'],
                    diplome=['diplome.pdf'],
                ),
                diplome_etudes_secondaires=GotDiploma.YES.name,
                annee_diplome_etudes_secondaires=2022,
            ),
            "0000000001": _EtudesSecondairesDTO(
                diplome_belge=DiplomeBelgeEtudesSecondairesDTO(
                    certificat_inscription=['certificat_inscription.pdf'],
                    diplome=['diplome.pdf'],
                ),
                diplome_etudes_secondaires=GotDiploma.YES.name,
                annee_diplome_etudes_secondaires=2022,
            ),
            "0000000002": _EtudesSecondairesDTO(
                diplome_belge=DiplomeBelgeEtudesSecondairesDTO(
                    certificat_inscription=['certificat_inscription.pdf'],
                    diplome=['diplome.pdf'],
                ),
                diplome_etudes_secondaires=GotDiploma.YES.name,
                annee_diplome_etudes_secondaires=2022,
            ),
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
                pays_nationalite_europeen=candidate.pays_nationalite in cls.pays_union_europeenne,
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
                autres_prenoms=candidate.autres_prenoms,
                nom_pays_nationalite=candidate.nom_pays_nationalite,
                nom_langue_contact=candidate.nom_langue_contact,
                nom_pays_naissance=candidate.nom_pays_naissance,
                date_expiration_passeport=candidate.date_expiration_passeport,
                date_expiration_carte_identite=candidate.date_expiration_carte_identite,
            )
        except StopIteration:  # pragma: no cover
            raise CandidatNonTrouveException

    @classmethod
    def get_coordonnees(cls, matricule: str) -> 'CoordonneesDTO':
        coordonnees = next(
            (coord for coord in cls.coordonnees_candidats if coord.personne == matricule),
            None,
        )

        if not coordonnees:
            return CoordonneesDTO(
                domicile_legal=None,
                adresse_correspondance=None,
                numero_mobile='',
                adresse_email_privee='',
                numero_contact_urgence='',
            )

        domicile_legal = coordonnees.domicile_legal
        adresse_correspondance = coordonnees.adresse_correspondance
        adresse_email_privee = coordonnees.adresse_email_privee
        numero_mobile = coordonnees.numero_mobile
        numero_contact_urgence = coordonnees.numero_contact_urgence

        return CoordonneesDTO(
            domicile_legal=AdressePersonnelleDTO(
                rue=domicile_legal.rue,
                code_postal=domicile_legal.code_postal,
                ville=domicile_legal.ville,
                pays=domicile_legal.pays,
                numero_rue=domicile_legal.numero_rue,
                boite_postale=domicile_legal.boite_postale,
                nom_pays=domicile_legal.nom_pays,
            )
            if domicile_legal
            else None,
            adresse_correspondance=AdressePersonnelleDTO(
                rue=adresse_correspondance.rue,
                code_postal=adresse_correspondance.code_postal,
                ville=adresse_correspondance.ville,
                pays=adresse_correspondance.pays,
                numero_rue=adresse_correspondance.numero_rue,
                boite_postale=adresse_correspondance.boite_postale,
                nom_pays=adresse_correspondance.nom_pays,
            )
            if adresse_correspondance
            else None,
            adresse_email_privee=adresse_email_privee,
            numero_mobile=numero_mobile,
            numero_contact_urgence=numero_contact_urgence,
        )

    @classmethod
    def get_langues_connues(cls, matricule: str) -> List[str]:
        return [c.langue.code_langue for c in cls.connaissances_langues if c.personne == matricule]

    @classmethod
    def get_etudes_secondaires(cls, matricule: str, type_formation: TrainingType) -> 'EtudesSecondairesDTO':
        return cls.etudes_secondaires.get(matricule) or EtudesSecondairesDTO()

    @classmethod
    def get_curriculum(cls, matricule: str, annee_courante: int) -> 'CurriculumDTO':
        try:
            candidate = next(c for c in cls.profil_candidats if c.matricule == matricule)

            experiences_dtos = []
            for experience in cls.experiences_academiques:
                if experience.personne == matricule:
                    experiences_dtos.append(
                        ExperienceAcademiqueDTO(
                            uuid=experience.uuid,
                            pays=experience.pays,
                            annees=[
                                AnneeExperienceAcademiqueDTO(
                                    annee=annee.annee,
                                    resultat=annee.resultat,
                                    releve_notes=annee.releve_notes,
                                    traduction_releve_notes=annee.traduction_releve_notes,
                                    credits_acquis=annee.credits_inscrits,
                                    credits_inscrits=annee.credits_acquis,
                                )
                                for annee in experience.annees
                            ],
                            regime_linguistique=experience.regime_linguistique,
                            type_releve_notes=experience.type_releve_notes,
                            releve_notes=experience.releve_notes,
                            traduction_releve_notes=experience.traduction_releve_notes,
                            diplome=experience.diplome,
                            traduction_diplome=experience.traduction_diplome,
                            a_obtenu_diplome=experience.a_obtenu_diplome,
                            rang_diplome=experience.rang_diplome,
                            date_prevue_delivrance_diplome=experience.date_prevue_delivrance_diplome,
                            titre_memoire=experience.titre_memoire,
                            note_memoire=experience.note_memoire,
                            resume_memoire=experience.resume_memoire,
                            grade_obtenu=experience.grade_obtenu,
                            systeme_evaluation=experience.systeme_evaluation,
                            nom_formation=experience.nom_formation,
                            adresse_institut=experience.adresse_institut,
                            code_institut=experience.code_institut,
                            communaute_institut=experience.communaute_institut,
                            nom_institut=experience.nom_institut,
                            nom_pays=experience.nom_pays,
                            nom_regime_linguistique=experience.nom_regime_linguistique,
                            type_enseignement=experience.type_enseignement,
                        ),
                    )

            experiences_non_academiques = [
                ExperienceNonAcademiqueDTO(
                    uuid=experience.uuid,
                    employeur=experience.employeur,
                    date_debut=experience.date_debut,
                    date_fin=experience.date_fin,
                    type=experience.type,
                    certificat=experience.certificat,
                    fonction=experience.fonction,
                    secteur=experience.secteur,
                    autre_activite=experience.autre_activite,
                )
                for experience in cls.experiences_non_academiques
                if experience.personne == matricule
            ]

            etudes_secondaires = cls.etudes_secondaires.get(matricule)
            annee_etudes_secondaires = etudes_secondaires and etudes_secondaires.annee_diplome_etudes_secondaires

            return CurriculumDTO(
                experiences_academiques=experiences_dtos,
                annee_diplome_etudes_secondaires=annee_etudes_secondaires,
                annee_derniere_inscription_ucl=candidate.annee_derniere_inscription_ucl,
                experiences_non_academiques=experiences_non_academiques,
                annee_minimum_a_remplir=cls.get_annee_minimale_a_completer_cv(
                    annee_courante=datetime.date.today().year,
                    annee_diplome_etudes_secondaires=annee_etudes_secondaires,
                    annee_derniere_inscription_ucl=candidate.annee_derniere_inscription_ucl,
                ),
            )
        except StopIteration:
            raise CandidatNonTrouveException

    @classmethod
    def get_existence_experiences_curriculum(cls, matricule: str) -> 'CurriculumAExperiencesDTO':
        return CurriculumAExperiencesDTO(
            a_experience_non_academique=any(
                experience.personne == matricule for experience in cls.experiences_non_academiques
            ),
            a_experience_academique=any(experience.personne == matricule for experience in cls.experiences_academiques),
        )

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
    def get_changements_etablissement(cls, matricule: str, annees: List[int]) -> Dict[int, bool]:
        return {annee: False for annee in annees}

    @classmethod
    def est_potentiel_vae(cls, matricule: str) -> bool:
        curriculum = cls.get_curriculum(matricule, datetime.date.today().year)
        return curriculum.candidat_est_potentiel_vae

    @classmethod
    def etudes_secondaires_valorisees(cls, matricule: str) -> bool:
        etudes_secondaires = cls.etudes_secondaires.get(matricule)
        if etudes_secondaires:
            return etudes_secondaires.valorisees is True
        return False

    @classmethod
    def get_connaissances_langues(cls, matricule: str) -> List[ConnaissanceLangueDTO]:
        return [
            ConnaissanceLangueDTO(
                nom_langue_fr=connaissance.langue.nom_langue,
                nom_langue_en=connaissance.langue.nom_langue,
                langue=connaissance.langue.code_langue,
                comprehension_orale=connaissance.comprehension_orale,
                capacite_orale=connaissance.capacite_orale,
                capacite_ecriture=connaissance.capacite_ecriture,
                certificat=connaissance.certificat,
            )
            for connaissance in cls.connaissances_langues
            if connaissance.personne == matricule
        ]

    @classmethod
    def recuperer_toutes_informations_candidat(
        cls,
        matricule: str,
        formation: str,
        annee_courante: int,
    ) -> ResumeCandidatDTO:
        return ResumeCandidatDTO(
            identification=cls.get_identification(matricule),
            coordonnees=cls.get_coordonnees(matricule),
            curriculum=cls.get_curriculum(matricule, annee_courante),
            etudes_secondaires=cls.get_etudes_secondaires(matricule, TrainingType[formation]),
            connaissances_langues=cls.get_connaissances_langues(matricule),
        )
