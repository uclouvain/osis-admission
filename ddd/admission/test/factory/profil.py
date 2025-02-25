# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid
from typing import List

import factory
from attr import dataclass

from admission.ddd.admission.doctorat.preparation.dtos import ConditionsComptabiliteDTO
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import (
    CurriculumAdmissionDTO,
)
from admission.ddd.admission.dtos import (
    AdressePersonnelleDTO,
    CoordonneesDTO,
    IdentificationDTO,
)
from admission.ddd.admission.dtos.etudes_secondaires import (
    EtudesSecondairesAdmissionDTO,
)
from base.models.enums.civil_state import CivilState
from base.tests.factories.person import generate_global_id
from ddd.logic.shared_kernel.profil.dtos.etudes_secondaires import (
    ValorisationEtudesSecondairesDTO,
)
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import (
    AnneeExperienceAcademiqueDTO,
    ExperienceAcademiqueDTO,
    ExperienceNonAcademiqueDTO,
)


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
    autres_prenoms = factory.Faker('first_name')
    nom_pays_nationalite = factory.Faker('country')
    nom_pays_naissance = factory.Faker('country')
    nom_langue_contact = 'Français'
    date_expiration_passeport = factory.Faker('date')
    date_expiration_carte_identite = factory.Faker('date')


class AdressePersonnelleDTOFactory(factory.Factory):
    class Meta:
        model = AdressePersonnelleDTO
        abstract = False

    rue = factory.Faker('street_name')
    code_postal = factory.Faker('postcode')
    ville = factory.Faker('city')
    pays = factory.Faker('country_code')
    numero_rue = 1
    boite_postale = ''
    nom_pays = factory.Faker('country')


class CoordonneesDTOFactory(factory.Factory):
    domicile_legal = factory.SubFactory(AdressePersonnelleDTOFactory)
    adresse_correspondance = factory.SubFactory(AdressePersonnelleDTOFactory)
    numero_mobile = factory.Faker('phone_number')
    adresse_email_privee = factory.Faker('email')
    numero_contact_urgence = factory.Faker('phone_number')

    class Meta:
        model = CoordonneesDTO
        abstract = False


class ValorisationEtudesSecondairesDTOFactory(factory.Factory):
    est_valorise_par_epc = False
    types_formations_admissions_valorisees = []

    class Meta:
        model = ValorisationEtudesSecondairesDTO
        abstract = False


class EtudesSecondairesDTOFactory(factory.Factory):

    valorisation = factory.SubFactory(ValorisationEtudesSecondairesDTOFactory)

    class Meta:
        model = EtudesSecondairesAdmissionDTO
        abstract = False


class AnneeExperienceAcademiqueDTOFactory(factory.Factory):
    class Meta:
        model = AnneeExperienceAcademiqueDTO
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    annee = 2020
    resultat = ''
    releve_notes = []
    traduction_releve_notes = []
    credits_inscrits = None
    credits_acquis = None
    allegement = ''
    est_reorientation_102 = None


class ExperienceAcademiqueDTOFactory(factory.Factory):
    class Meta:
        model = ExperienceAcademiqueDTO
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    pays = ''
    nom_pays = ''
    nom_institut = ''
    adresse_institut = ''
    code_institut = ''
    communaute_institut = ''
    type_institut = ''
    regime_linguistique = ''
    nom_regime_linguistique = ''
    type_releve_notes = ''
    releve_notes = []
    traduction_releve_notes = []
    annees: List[AnneeExperienceAcademiqueDTOFactory] = []
    a_obtenu_diplome = False
    diplome = []
    traduction_diplome = []
    rang_diplome = ''
    date_prevue_delivrance_diplome = None
    titre_memoire = ''
    note_memoire = ''
    resume_memoire = []
    grade_obtenu = ''
    systeme_evaluation = ''
    nom_formation = ''
    type_enseignement = ''
    nom_formation_equivalente_communaute_fr = ''
    cycle_formation = ''
    est_autre_formation = None
    credits_acquis_bloc_1 = None
    avec_complements = None
    credits_inscrits_complements = None
    credits_acquis_complements = None


class ExperienceNonAcademiqueDTOFactory(factory.Factory):
    class Meta:
        model = ExperienceNonAcademiqueDTO
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    employeur = ''
    date_debut = datetime.date(2020, 9, 1)
    date_fin = datetime.date(2020, 10, 15)
    type = ''
    certificat = []
    fonction = ''
    secteur = ''
    autre_activite = ''


class CurriculumDTOFactory(factory.Factory):
    class Meta:
        model = CurriculumAdmissionDTO
        abstract = False

    experiences_non_academiques: List[ExperienceNonAcademiqueDTOFactory] = []
    experiences_academiques: List[ExperienceAcademiqueDTOFactory] = []
    annee_derniere_inscription_ucl = factory.Faker('year')
    annee_diplome_etudes_secondaires = factory.Faker('year')
    annee_minimum_a_remplir = factory.Faker('year')


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
