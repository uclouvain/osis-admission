# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.test import TestCase

from admission.infrastructure.admission.domain.service.titres_acces import TitresAcces
from admission.tests.factories.curriculum import (
    ProfessionalExperienceFactory,
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
)
from admission.tests.factories.secondary_studies import (
    HighSchoolDiplomaAlternativeFactory,
    BelgianHighSchoolDiplomaFactory,
    ForeignHighSchoolDiplomaFactory,
)
from base.models.enums.got_diploma import GotDiploma
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.person import PersonFactory
from osis_profile.models.enums.curriculum import ActivitySector, ActivityType, Result
from reference.models.enums.cycle import Cycle
from reference.tests.factories.diploma_title import DiplomaTitleFactory


class TitresAccesTestCase(TestCase):
    def test_pas_de_diplome(self):
        person = PersonFactory()
        result = TitresAcces.conditions_remplies(person.global_id, [])
        self.assertFalse(result.diplomation_secondaire_belge)
        self.assertFalse(result.diplomation_secondaire_etranger)
        self.assertFalse(result.alternative_etudes_secondaires)
        self.assertFalse(result.potentiel_bachelier_belge_sans_diplomation)
        self.assertFalse(result.diplomation_academique_belge)
        self.assertFalse(result.diplomation_academique_etranger)
        self.assertFalse(result.potentiel_master_belge_sans_diplomation)
        self.assertFalse(result.diplomation_potentiel_master_belge)
        self.assertFalse(result.diplomation_potentiel_master_etranger)
        self.assertFalse(result.diplomation_potentiel_doctorat_belge)
        self.assertFalse(result.potentiel_acces_vae)

    def test_diplomation_secondaire_belge(self):
        with self.subTest('diplome_belge'):
            person_avec_diplome_belge = PersonFactory(
                graduated_from_high_school=GotDiploma.YES.name,
            )
            BelgianHighSchoolDiplomaFactory(person=person_avec_diplome_belge)
            result = TitresAcces.conditions_remplies(person_avec_diplome_belge.global_id, [])
            self.assertTrue(result.diplomation_secondaire_belge)

        with self.subTest('sans_diplome'):
            person_sans_diplome = PersonFactory(
                graduated_from_high_school=GotDiploma.THIS_YEAR.name,
            )
            result = TitresAcces.conditions_remplies(person_sans_diplome.global_id, [])
            self.assertTrue(result.diplomation_secondaire_belge)

    def test_diplomation_secondaire_etranger(self):
        person = PersonFactory(
            graduated_from_high_school=GotDiploma.YES.name,
        )
        ForeignHighSchoolDiplomaFactory(person=person)
        result = TitresAcces.conditions_remplies(person.global_id, [])
        self.assertTrue(result.diplomation_secondaire_etranger)

    def test_alternative_etudes_secondaires(self):
        person = PersonFactory(
            graduated_from_high_school=GotDiploma.NO.name,
        )
        HighSchoolDiplomaAlternativeFactory(person=person)
        result = TitresAcces.conditions_remplies(person.global_id, [])
        self.assertTrue(result.alternative_etudes_secondaires)

    def test_potentiel_bachelier_belge_sans_diplomation(self):
        with self.subTest('formation_premier_cycle'):
            person_avec_formation_premier_cycle = PersonFactory()
            EducationalExperienceFactory(
                person=person_avec_formation_premier_cycle,
                program=DiplomaTitleFactory(cycle=Cycle.FIRST_CYCLE.name),
                education_name='',
                country__iso_code="BE",
                obtained_diploma=False,
            )
            result = TitresAcces.conditions_remplies(person_avec_formation_premier_cycle.global_id, [])
            self.assertTrue(result.potentiel_bachelier_belge_sans_diplomation)

        with self.subTest('autre_formation'):
            person_avec_autre_formation = PersonFactory()
            EducationalExperienceFactory(
                person=person_avec_autre_formation,
                education_name='foobar',
                country__iso_code="BE",
                obtained_diploma=False,
            )
            result = TitresAcces.conditions_remplies(person_avec_autre_formation.global_id, [])
            self.assertTrue(result.potentiel_bachelier_belge_sans_diplomation)

    def test_diplomation_academique_belge(self):
        with self.subTest('resultat_en_attente'):
            person_avec_resultat_en_attente = PersonFactory()
            educational_experience = EducationalExperienceFactory(
                person=person_avec_resultat_en_attente,
                obtained_diploma=False,
                country__iso_code="BE",
            )
            EducationalExperienceYearFactory(
                result=Result.WAITING_RESULT.name,
                educational_experience=educational_experience,
            )
            result = TitresAcces.conditions_remplies(person_avec_resultat_en_attente.global_id, [])
            self.assertTrue(result.diplomation_academique_belge)

        with self.subTest('avec_diplome'):
            person_avec_diplome = PersonFactory()
            educational_experience = EducationalExperienceFactory(
                person=person_avec_diplome,
                obtained_diploma=True,
                country__iso_code="BE",
            )
            EducationalExperienceYearFactory(
                result=Result.SUCCESS.name,
                educational_experience=educational_experience,
            )
            result = TitresAcces.conditions_remplies(person_avec_diplome.global_id, [])
            self.assertTrue(result.diplomation_academique_belge)

        with self.subTest('etudiant_ucl'):
            person_etudiant_ucl = PersonFactory(
                last_registration_year=AcademicYearFactory(),
            )
            result = TitresAcces.conditions_remplies(person_etudiant_ucl.global_id, [])
            self.assertTrue(result.diplomation_academique_belge)

    def test_diplomation_academique_etranger(self):
        with self.subTest('resultat_en_attente'):
            person_avec_resultat_en_attente = PersonFactory()
            educational_experience = EducationalExperienceFactory(
                person=person_avec_resultat_en_attente,
                obtained_diploma=False,
                country__iso_code="FR",
            )
            EducationalExperienceYearFactory(
                result=Result.WAITING_RESULT.name,
                educational_experience=educational_experience,
            )
            result = TitresAcces.conditions_remplies(person_avec_resultat_en_attente.global_id, [])
            self.assertTrue(result.diplomation_academique_etranger)

        with self.subTest('avec_diplome'):
            person_avec_diplome = PersonFactory()
            educational_experience = EducationalExperienceFactory(
                person=person_avec_diplome,
                obtained_diploma=True,
                country__iso_code="FR",
            )
            EducationalExperienceYearFactory(
                result=Result.SUCCESS.name,
                educational_experience=educational_experience,
            )
            result = TitresAcces.conditions_remplies(person_avec_diplome.global_id, [])
            self.assertTrue(result.diplomation_academique_etranger)

    def test_potentiel_master_belge_sans_diplomation(self):
        with self.subTest('formation_second_cycle'):
            person_avec_formation_second_cycle = PersonFactory()
            EducationalExperienceFactory(
                person=person_avec_formation_second_cycle,
                program=DiplomaTitleFactory(cycle=Cycle.SECOND_CYCLE.name),
                education_name='',
                country__iso_code="BE",
                obtained_diploma=False,
            )
            result = TitresAcces.conditions_remplies(person_avec_formation_second_cycle.global_id, [])
            self.assertTrue(result.potentiel_master_belge_sans_diplomation)

        with self.subTest('formation_troisieme_cycle'):
            person_avec_formation_troisieme_cycle = PersonFactory()
            EducationalExperienceFactory(
                person=person_avec_formation_troisieme_cycle,
                program=DiplomaTitleFactory(cycle=Cycle.THIRD_CYCLE.name),
                education_name='',
                country__iso_code="BE",
                obtained_diploma=False,
            )
            result = TitresAcces.conditions_remplies(person_avec_formation_troisieme_cycle.global_id, [])
            self.assertTrue(result.potentiel_master_belge_sans_diplomation)

        with self.subTest('autre_formation'):
            person_avec_autre_formation = PersonFactory()
            EducationalExperienceFactory(
                person=person_avec_autre_formation,
                education_name='foobar',
                country__iso_code="BE",
                obtained_diploma=False,
            )
            result = TitresAcces.conditions_remplies(person_avec_autre_formation.global_id, [])
            self.assertTrue(result.potentiel_master_belge_sans_diplomation)

    def test_diplomation_potentiel_master_belge(self):
        with self.subTest('formation_second_cycle'):
            person_avec_formation_second_cycle = PersonFactory(
                last_registration_year=None,
            )
            educational_experience = EducationalExperienceFactory(
                person=person_avec_formation_second_cycle,
                program=DiplomaTitleFactory(cycle=Cycle.SECOND_CYCLE.name),
                education_name='',
                country__iso_code="BE",
                obtained_diploma=True,
            )
            EducationalExperienceYearFactory(
                result=Result.SUCCESS.name,
                educational_experience=educational_experience,
            )
            result = TitresAcces.conditions_remplies(person_avec_formation_second_cycle.global_id, [])
            self.assertTrue(result.diplomation_potentiel_master_belge)

        with self.subTest('autre_formation'):
            person_avec_autre_formation = PersonFactory(
                last_registration_year=None,
            )
            educational_experience = EducationalExperienceFactory(
                person=person_avec_autre_formation,
                education_name='foobar',
                country__iso_code="BE",
                obtained_diploma=True,
            )
            EducationalExperienceYearFactory(
                result=Result.SUCCESS.name,
                educational_experience=educational_experience,
            )
            result = TitresAcces.conditions_remplies(person_avec_autre_formation.global_id, [])
            self.assertTrue(result.diplomation_potentiel_master_belge)

        with self.subTest('en_attente_de_resultat'):
            person_en_attente_de_resultat = PersonFactory(
                last_registration_year=None,
            )
            educational_experience = EducationalExperienceFactory(
                person=person_en_attente_de_resultat,
                program=DiplomaTitleFactory(cycle=Cycle.SECOND_CYCLE.name),
                education_name='',
                country__iso_code="BE",
                obtained_diploma=False,
            )
            EducationalExperienceYearFactory(
                result=Result.WAITING_RESULT.name,
                educational_experience=educational_experience,
            )
            result = TitresAcces.conditions_remplies(person_en_attente_de_resultat.global_id, [])
            self.assertTrue(result.diplomation_potentiel_master_belge)

        with self.subTest('etudiant_ucl'):
            person_etudiant_ucl = PersonFactory(
                last_registration_year=AcademicYearFactory(),
            )
            result = TitresAcces.conditions_remplies(person_etudiant_ucl.global_id, [])
            self.assertTrue(result.diplomation_potentiel_master_belge)

    def test_diplomation_potentiel_master_etranger(self):
        with self.subTest('resultat_en_attente'):
            person_avec_resultat_en_attente = PersonFactory()
            educational_experience = EducationalExperienceFactory(
                person=person_avec_resultat_en_attente,
                obtained_diploma=False,
                country__iso_code="FR",
            )
            EducationalExperienceYearFactory(
                result=Result.WAITING_RESULT.name,
                educational_experience=educational_experience,
            )
            result = TitresAcces.conditions_remplies(person_avec_resultat_en_attente.global_id, ['foo'])
            self.assertFalse(result.diplomation_potentiel_master_etranger)

        with self.subTest('avec_diplome'):
            person_avec_diplome = PersonFactory()
            educational_experience = EducationalExperienceFactory(
                person=person_avec_diplome,
                obtained_diploma=True,
                country__iso_code="FR",
            )
            EducationalExperienceYearFactory(
                result=Result.SUCCESS.name,
                educational_experience=educational_experience,
            )
            result = TitresAcces.conditions_remplies(person_avec_diplome.global_id, ['foo'])
            self.assertTrue(result.diplomation_potentiel_master_etranger)

    def test_diplomation_potentiel_doctorat_belge(self):
        with self.subTest('formation_troisieme_cycle'):
            person_avec_formation_troisieme_cycle = PersonFactory(
                last_registration_year=None,
            )
            educational_experience = EducationalExperienceFactory(
                person=person_avec_formation_troisieme_cycle,
                program=DiplomaTitleFactory(cycle=Cycle.THIRD_CYCLE.name),
                education_name='',
                country__iso_code="BE",
                obtained_diploma=True,
            )
            EducationalExperienceYearFactory(
                result=Result.SUCCESS.name,
                educational_experience=educational_experience,
            )
            result = TitresAcces.conditions_remplies(person_avec_formation_troisieme_cycle.global_id, [])
            self.assertTrue(result.diplomation_potentiel_doctorat_belge)

        with self.subTest('autre_formation'):
            person_avec_autre_formation = PersonFactory(
                last_registration_year=None,
            )
            educational_experience = EducationalExperienceFactory(
                person=person_avec_autre_formation,
                education_name='foobar',
                country__iso_code="BE",
                obtained_diploma=True,
            )
            EducationalExperienceYearFactory(
                result=Result.SUCCESS.name,
                educational_experience=educational_experience,
            )
            result = TitresAcces.conditions_remplies(person_avec_autre_formation.global_id, [])
            self.assertTrue(result.diplomation_potentiel_doctorat_belge)

        with self.subTest('en_attente_de_resultat'):
            person_en_attente_de_resultat = PersonFactory(
                last_registration_year=None,
            )
            educational_experience = EducationalExperienceFactory(
                person=person_en_attente_de_resultat,
                program=DiplomaTitleFactory(cycle=Cycle.THIRD_CYCLE.name),
                education_name='',
                country__iso_code="BE",
                obtained_diploma=False,
            )
            EducationalExperienceYearFactory(
                result=Result.WAITING_RESULT.name,
                educational_experience=educational_experience,
            )
            result = TitresAcces.conditions_remplies(person_en_attente_de_resultat.global_id, [])
            self.assertTrue(result.diplomation_potentiel_doctorat_belge)

    def test_potentiel_acces_vae(self):
        person = PersonFactory()
        # 18 mois
        ProfessionalExperienceFactory(
            person=person,
            start_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2021, 7, 1),
            type=ActivityType.WORK.name,
            role='Librarian',
            sector=ActivitySector.PUBLIC.name,
            activity='Work - activity',
        )
        # 2 ans
        ProfessionalExperienceFactory(
            person=person,
            start_date=datetime.date(2018, 1, 1),
            end_date=datetime.date(2020, 1, 1),
            type=ActivityType.WORK.name,
            role='Mechanician',
            sector=ActivitySector.PRIVATE.name,
            activity='Work - activity',
        )

        result = TitresAcces.conditions_remplies(person.global_id, [])
        self.assertTrue(result.potentiel_acces_vae)
