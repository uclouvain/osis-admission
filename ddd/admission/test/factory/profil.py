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
from typing import List

import factory
from attr import dataclass

from admission.ddd.admission.doctorat.preparation.dtos import ConditionsComptabiliteDTO, CurriculumDTO
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import (
    ExperienceAcademiqueDTO,
    AnneeExperienceAcademiqueDTO,
)
from admission.ddd.admission.dtos import AdressePersonnelleDTO, CoordonneesDTO, EtudesSecondairesDTO, IdentificationDTO
from base.models.enums.civil_state import CivilState
from base.tests.factories.person import generate_global_id


class IdentificationDTOFactory(factory.Factory):
    class Meta:
        model = IdentificationDTO
        abstract = False

    matricule = factory.LazyFunction(generate_global_id)
    nom = factory.Faker('last_name')
    prenom = factory.Faker('first_name')
    date_naissance = factory.Faker('date_of_birth')
    annee_naissance = factory.Faker('year')
    pays_nationalite = factory.Faker('country_code')
    sexe = "M"
    genre = "M"
    photo_identite = ['uuid14']
    pays_naissance = factory.Faker('country_code')
    pays_nationalite_europeen = False
    lieu_naissance = factory.Faker('city')
    carte_identite = ['uuid12']
    passeport = ['uuid13']
    numero_registre_national_belge = '1001'
    numero_carte_identite = '1002'
    numero_passeport = '1003'
    annee_derniere_inscription_ucl = None
    noma_derniere_inscription_ucl = ''
    email = 'john.doe@ucl.be'
    etat_civil = CivilState.MARRIED.name
    pays_residence = "BE"
    langue_contact = "fr-be"


class AdressePersonnelleDTOFactory(factory.Factory):
    class Meta:
        model = AdressePersonnelleDTO
        abstract = False

    rue = factory.Faker('street_name')
    code_postal = factory.Faker('postcode')
    ville = factory.Faker('city')
    pays = factory.Faker('country_code')
    lieu_dit = ''
    numero_rue = 1
    boite_postale = ''


class CoordonneesDTOFactory(factory.Factory):
    domicile_legal = factory.SubFactory(AdressePersonnelleDTOFactory)
    adresse_correspondance = factory.SubFactory(AdressePersonnelleDTOFactory)

    class Meta:
        model = CoordonneesDTO
        abstract = False


class EtudesSecondairesDTOFactory(factory.Factory):
    class Meta:
        model = EtudesSecondairesDTO
        abstract = False

    presence_etudes_secondaires_belges = False
    presence_etudes_secondaires_etrangeres = False
    presence_examen_admission_premier_cycle = False


class AnneeExperienceAcademiqueDTOFactory(factory.Factory):
    class Meta:
        model = AnneeExperienceAcademiqueDTO
        abstract = False


class ExperienceAcademiqueDTOFactory(factory.Factory):
    annees: List[AnneeExperienceAcademiqueDTOFactory] = []

    class Meta:
        model = ExperienceAcademiqueDTO
        abstract = False


class CurriculumDTOFactory(factory.Factory):
    class Meta:
        model = CurriculumDTO
        abstract = False

    dates_experiences_non_academiques: List[int] = []
    experiences_academiques: List[ExperienceAcademiqueDTOFactory] = []
    annee_derniere_inscription_ucl = factory.Faker('year')
    annee_diplome_etudes_secondaires_belges = factory.Faker('year')
    annee_diplome_etudes_secondaires_etrangeres = factory.Faker('year')


class ConditionsComptabiliteDTOFactory(factory.Factory):
    class Meta:
        model = ConditionsComptabiliteDTO
        abstract = False

    pays_nationalite_ue = None
    a_frequente_recemment_etablissement_communaute_fr = None


@dataclass
class _ProfilCandidat:
    matricule: str
    identification: IdentificationDTOFactory
    coordonnees: IdentificationDTOFactory
    langues_connues: List[str]
    etudes_secondaires: EtudesSecondairesDTOFactory
    curriculum: CurriculumDTOFactory
    conditions_comptabilite: ConditionsComptabiliteDTOFactory


class ProfilCandidatFactory(factory.Factory):
    class Meta:
        model = _ProfilCandidat
        abstract = False

    matricule = factory.LazyFunction(generate_global_id)
    identification = factory.SubFactory(IdentificationDTOFactory, matricule=factory.SelfAttribute('..matricule'))
    coordonnees = factory.SubFactory(CoordonneesDTOFactory)
    langues_connues = factory.Faker('random_choices', elements=["FR", "EN", "NL", "DE"])
    etudes_secondaires = factory.SubFactory(EtudesSecondairesDTOFactory)
    curriculum = factory.SubFactory(CurriculumDTOFactory)
    conditions_comptabilite = factory.SubFactory(ConditionsComptabiliteDTOFactory)
