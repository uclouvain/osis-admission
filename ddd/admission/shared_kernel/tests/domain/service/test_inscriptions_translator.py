# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from functools import partial

import freezegun
from django.test import TestCase

from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.shared_kernel.domain.model.assimilation import Assimilation
from admission.ddd.admission.shared_kernel.enums import (
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    LienParente,
    TypeSituationAssimilation,
)
from admission.infrastructure.admission.shared_kernel.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from admission.infrastructure.admission.shared_kernel.domain.service.inscriptions import InscriptionsTranslatorService
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.academic_type import AcademicTypes
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from epc.models.enums.assimilation import Assimilation as AssimilationEnum
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from epc.models.enums.statut_inscription_programme_annuel import StatutInscriptionProgrammAnnuel
from epc.tests.factories.inscription_programme_annuel import InscriptionProgrammeAnnuelFactory


@freezegun.freeze_time(datetime.date(2025, 1, 1))
class IsRecentlyEnrolledTestCase(TestCase):
    is_recently_enrolled = partial(
        InscriptionsTranslatorService.est_inscrit_recemment,
        annee_inscription_formation_translator=AnneeInscriptionFormationTranslator(),
    )

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.academic_years = {year: AcademicYearFactory(year=year) for year in [2023, 2024, 2025, 2026]}

        cls.administrative_calendar = AcademicCalendarFactory(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            start_date=datetime.date(2024, 11, 1),
            end_date=datetime.date(2025, 10, 31),
            data_year=cls.academic_years[2025],
        )

    def setUp(self):
        super().setUp()

        self.enrolment = InscriptionProgrammeAnnuelFactory(
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            programme__offer__academic_type=AcademicTypes.ACADEMIC.name,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            programme__root_group__academic_year=self.academic_years[2025],
        )

        self.student = self.enrolment.programme_cycle.etudiant.person

    def test_with_no_enrolment(self):
        result = self.is_recently_enrolled(matricule_candidat='UNKNOWN')

        self.assertFalse(result)

    def test_depends_on_enrolment_state(self):
        valid_values = {
            EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            EtatInscriptionFormation.PROVISOIRE.name,
            EtatInscriptionFormation.CESSATION.name,
        }

        for value in EtatInscriptionFormation:
            self.enrolment.etat_inscription = value.name
            self.enrolment.save()

            result = self.is_recently_enrolled(matricule_candidat=self.student.global_id)

            self.assertEqual(result, value.name in valid_values)

    def test_depends_on_academic_type(self):
        valid_values = {
            AcademicTypes.ACADEMIC.name,
            AcademicTypes.NON_ACADEMIC_CREF.name,
        }

        for value in AcademicTypes:
            self.enrolment.programme.offer.academic_type = value.name
            self.enrolment.programme.offer.save()

            result = self.is_recently_enrolled(matricule_candidat=self.student.global_id)

            self.assertEqual(result, value.name in valid_values)

    def test_depends_on_status(self):
        valid_values = {
            StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
        }

        for value in StatutInscriptionProgrammAnnuel:
            self.enrolment.statut = value.name
            self.enrolment.save()

            result = self.is_recently_enrolled(matricule_candidat=self.student.global_id)

            self.assertEqual(result, value.name in valid_values)

    def test_depends_on_academic_year(self):
        valid_values = {
            2024,
            2025,
        }

        for year, academic_year in self.academic_years.items():
            self.enrolment.programme.offer.academic_year = academic_year
            self.enrolment.programme.offer.save()

            result = self.is_recently_enrolled(matricule_candidat=self.student.global_id)

            self.assertEqual(result, year in valid_values)


@freezegun.freeze_time(datetime.date(2025, 1, 1))
class IsInPursuitTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.academic_years = {year: AcademicYearFactory(year=year) for year in [2023, 2024, 2025, 2026]}

        cls.administrative_calendar = AcademicCalendarFactory(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            start_date=datetime.date(2024, 11, 1),
            end_date=datetime.date(2025, 10, 31),
            data_year=cls.academic_years[2025],
        )

    def setUp(self):
        super().setUp()

        self.enrolment = InscriptionProgrammeAnnuelFactory(
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            programme__offer__academic_type=AcademicTypes.ACADEMIC.name,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            programme__root_group__academic_year=self.academic_years[2025],
        )

        self.student = self.enrolment.programme_cycle.etudiant.person
        self.training = self.enrolment.programme.offer

    def test_with_no_enrolment(self):
        result = InscriptionsTranslatorService.est_en_poursuite(
            matricule_candidat='UNKNOWN',
            sigle_formation=self.training.acronym,
        )

        self.assertFalse(result)

    def test_depends_on_training(self):
        result = InscriptionsTranslatorService.est_en_poursuite(
            matricule_candidat=self.student.global_id,
            sigle_formation=self.training.acronym,
        )

        self.assertTrue(result)

        result = InscriptionsTranslatorService.est_en_poursuite(
            matricule_candidat=self.student.global_id,
            sigle_formation='ABCD',
        )

        self.assertFalse(result)

    def test_depends_on_enrolment_state(self):
        valid_values = {
            EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            EtatInscriptionFormation.PROVISOIRE.name,
            EtatInscriptionFormation.CESSATION.name,
        }

        for value in EtatInscriptionFormation:
            self.enrolment.etat_inscription = value.name
            self.enrolment.save()

            result = InscriptionsTranslatorService.est_en_poursuite(
                matricule_candidat=self.student.global_id,
                sigle_formation=self.training.acronym,
            )

            self.assertEqual(result, value.name in valid_values)

    def test_depends_on_academic_type(self):
        valid_values = {
            AcademicTypes.ACADEMIC.name,
            AcademicTypes.NON_ACADEMIC_CREF.name,
        }

        for value in AcademicTypes:
            self.enrolment.programme.offer.academic_type = value.name
            self.enrolment.programme.offer.save()

            result = InscriptionsTranslatorService.est_en_poursuite(
                matricule_candidat=self.student.global_id,
                sigle_formation=self.training.acronym,
            )

            self.assertEqual(result, value.name in valid_values)

    def test_depends_on_status(self):
        valid_values = {
            StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
        }

        for value in StatutInscriptionProgrammAnnuel:
            self.enrolment.statut = value.name
            self.enrolment.save()

            result = InscriptionsTranslatorService.est_en_poursuite(
                matricule_candidat=self.student.global_id,
                sigle_formation=self.training.acronym,
            )

            self.assertEqual(result, value.name in valid_values)

    def test_depends_on_academic_year(self):
        for year, academic_year in self.academic_years.items():
            self.enrolment.programme.offer.academic_year = academic_year
            self.enrolment.programme.offer.save()

            result = InscriptionsTranslatorService.est_en_poursuite(
                matricule_candidat=self.student.global_id,
                sigle_formation=self.training.acronym,
            )

            self.assertTrue(result)


@freezegun.freeze_time(datetime.date(2025, 1, 1))
class IsInDirectPursuitTestCase(TestCase):
    is_in_direct_pursuit = partial(
        InscriptionsTranslatorService.est_en_poursuite_directe,
        annee_inscription_formation_translator=AnneeInscriptionFormationTranslator(),
    )

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.academic_years = {year: AcademicYearFactory(year=year) for year in [2023, 2024, 2025, 2026]}

        cls.administrative_calendar = AcademicCalendarFactory(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            start_date=datetime.date(2024, 11, 1),
            end_date=datetime.date(2025, 10, 31),
            data_year=cls.academic_years[2025],
        )

    def setUp(self):
        super().setUp()

        self.enrolment = InscriptionProgrammeAnnuelFactory(
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            programme__offer__academic_type=AcademicTypes.ACADEMIC.name,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            programme__root_group__academic_year=self.academic_years[2024],
        )

        self.student = self.enrolment.programme_cycle.etudiant.person
        self.training = self.enrolment.programme.offer

    def test_with_no_enrolment(self):
        result = self.is_in_direct_pursuit(
            matricule_candidat='UNKNOWN',
            sigle_formation=self.training.acronym,
        )

        self.assertFalse(result)

    def test_depends_on_training(self):
        result = self.is_in_direct_pursuit(
            matricule_candidat=self.student.global_id,
            sigle_formation=self.training.acronym,
        )

        self.assertTrue(result)

        result = self.is_in_direct_pursuit(matricule_candidat=self.student.global_id, sigle_formation='ABCDE')

        self.assertFalse(result)

    def test_depends_on_enrolment_state(self):
        valid_values = {
            EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            EtatInscriptionFormation.PROVISOIRE.name,
            EtatInscriptionFormation.CESSATION.name,
        }

        for value in EtatInscriptionFormation:
            self.enrolment.etat_inscription = value.name
            self.enrolment.save()

            result = self.is_in_direct_pursuit(
                matricule_candidat=self.student.global_id,
                sigle_formation=self.training.acronym,
            )

            self.assertEqual(result, value.name in valid_values)

    def test_depends_on_academic_type(self):
        valid_values = {
            AcademicTypes.ACADEMIC.name,
            AcademicTypes.NON_ACADEMIC_CREF.name,
        }

        for value in AcademicTypes:
            self.enrolment.programme.offer.academic_type = value.name
            self.enrolment.programme.offer.save()

            result = self.is_in_direct_pursuit(
                matricule_candidat=self.student.global_id,
                sigle_formation=self.training.acronym,
            )

            self.assertEqual(result, value.name in valid_values)

    def test_depends_on_status(self):
        valid_values = {
            StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
        }

        for value in StatutInscriptionProgrammAnnuel:
            self.enrolment.statut = value.name
            self.enrolment.save()

            result = self.is_in_direct_pursuit(
                matricule_candidat=self.student.global_id,
                sigle_formation=self.training.acronym,
            )

            self.assertEqual(result, value.name in valid_values)

    def test_depends_on_academic_year(self):
        valid_values = {
            2024,
        }

        for year, academic_year in self.academic_years.items():
            self.enrolment.programme.offer.academic_year = academic_year
            self.enrolment.programme.offer.save()

            result = self.is_in_direct_pursuit(
                matricule_candidat=self.student.global_id,
                sigle_formation=self.training.acronym,
            )

            self.assertEqual(result, year in valid_values)


@freezegun.freeze_time(datetime.date(2025, 1, 1))
class RetrieveValidEnrolmentsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.academic_years = {year: AcademicYearFactory(year=year) for year in [2023, 2024, 2025, 2026]}

    def setUp(self):
        super().setUp()

        self.enrolment = InscriptionProgrammeAnnuelFactory(
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            programme__offer__academic_type=AcademicTypes.ACADEMIC.name,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            programme__root_group__academic_year=self.academic_years[2024],
        )

        self.student = self.enrolment.programme_cycle.etudiant.person

    def test_with_no_enrolment(self):
        result = InscriptionsTranslatorService.recuperer(matricule_candidat='UNKNOWN')

        self.assertEqual(len(result), 0)

    def test_retrieve_valid_dto(self):
        result = InscriptionsTranslatorService.recuperer(matricule_candidat=self.student.global_id)

        self.assertEqual(len(result), 1)

        self.assertEqual(result[0].sigle, self.enrolment.programme.offer.acronym)
        self.assertEqual(result[0].annee, self.enrolment.programme.offer.academic_year.year)
        self.assertEqual(result[0].noma, self.enrolment.programme_cycle.etudiant.registration_id)
        self.assertEqual(result[0].est_premiere_annee_bachelier, self.enrolment.est_premiere_annee_bachelier)

    def test_depends_on_enrolment_state(self):
        valid_values = {
            EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            EtatInscriptionFormation.PROVISOIRE.name,
            EtatInscriptionFormation.CESSATION.name,
        }

        for value in EtatInscriptionFormation:
            self.enrolment.etat_inscription = value.name
            self.enrolment.save()

            result = InscriptionsTranslatorService.recuperer(matricule_candidat=self.student.global_id)

            self.assertEqual(len(result), int(value.name in valid_values))

    def test_depends_on_academic_type(self):
        valid_values = {
            AcademicTypes.ACADEMIC.name,
            AcademicTypes.NON_ACADEMIC_CREF.name,
        }

        for value in AcademicTypes:
            self.enrolment.programme.offer.academic_type = value.name
            self.enrolment.programme.offer.save()

            result = InscriptionsTranslatorService.recuperer(matricule_candidat=self.student.global_id)

            self.assertEqual(len(result), int(value.name in valid_values))

    def test_depends_on_status(self):
        valid_values = {
            StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
        }

        for value in StatutInscriptionProgrammAnnuel:
            self.enrolment.statut = value.name
            self.enrolment.save()

            result = InscriptionsTranslatorService.recuperer(matricule_candidat=self.student.global_id)

            self.assertEqual(len(result), int(value.name in valid_values))

    def test_depends_on_academic_year(self):
        valid_values = {
            2024,
        }

        for year, academic_year in self.academic_years.items():
            result = InscriptionsTranslatorService.recuperer(
                matricule_candidat=self.student.global_id,
                annees=[year],
            )

            self.assertEqual(len(result), int(year in valid_values))


@freezegun.freeze_time(datetime.date(2025, 1, 1))
class RetrieveLastValidEnrolmentTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.academic_years = {year: AcademicYearFactory(year=year) for year in [2023, 2024, 2025, 2026]}

    def setUp(self):
        super().setUp()

        self.enrolment = InscriptionProgrammeAnnuelFactory(
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            programme__offer__academic_type=AcademicTypes.ACADEMIC.name,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            programme__root_group__academic_year=self.academic_years[2024],
        )

        self.previous_enrolment = InscriptionProgrammeAnnuelFactory(
            programme_cycle__etudiant=self.enrolment.programme_cycle.etudiant,
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            programme__offer__academic_type=AcademicTypes.ACADEMIC.name,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            programme__root_group__academic_year=self.academic_years[2023],
        )

        self.student = self.enrolment.programme_cycle.etudiant.person

    def test_with_no_enrolment(self):
        result = InscriptionsTranslatorService.recuperer_derniere_inscription(matricule_candidat='UNKNOWN')

        self.assertIsNone(result)

    def test_retrieve_valid_dto(self):
        result = InscriptionsTranslatorService.recuperer_derniere_inscription(
            matricule_candidat=self.student.global_id,
        )

        self.assertIsNotNone(result)

        self.assertEqual(result.sigle, self.enrolment.programme.offer.acronym)
        self.assertEqual(result.annee, self.enrolment.programme.offer.academic_year.year)
        self.assertEqual(result.noma, self.enrolment.programme_cycle.etudiant.registration_id)
        self.assertEqual(result.est_premiere_annee_bachelier, self.enrolment.est_premiere_annee_bachelier)

    def test_depends_on_enrolment_state(self):
        valid_values = {
            EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            EtatInscriptionFormation.PROVISOIRE.name,
            EtatInscriptionFormation.CESSATION.name,
        }

        for value in EtatInscriptionFormation:
            self.enrolment.etat_inscription = value.name
            self.enrolment.save()

            result = InscriptionsTranslatorService.recuperer_derniere_inscription(
                matricule_candidat=self.student.global_id,
            )

            self.assertIsNotNone(result)

            if value.name in valid_values:
                self.assertEqual(result.sigle, self.enrolment.programme.offer.acronym)
                self.assertEqual(result.annee, self.enrolment.programme.offer.academic_year.year)
            else:
                self.assertEqual(result.sigle, self.previous_enrolment.programme.offer.acronym)
                self.assertEqual(result.annee, self.previous_enrolment.programme.offer.academic_year.year)

    def test_depends_on_academic_type(self):
        valid_values = {
            AcademicTypes.ACADEMIC.name,
            AcademicTypes.NON_ACADEMIC_CREF.name,
        }

        for value in AcademicTypes:
            self.enrolment.programme.offer.academic_type = value.name
            self.enrolment.programme.offer.save()

            result = InscriptionsTranslatorService.recuperer_derniere_inscription(
                matricule_candidat=self.student.global_id,
            )

            self.assertIsNotNone(result)

            if value.name in valid_values:
                self.assertEqual(result.sigle, self.enrolment.programme.offer.acronym)
                self.assertEqual(result.annee, self.enrolment.programme.offer.academic_year.year)
            else:
                self.assertEqual(result.sigle, self.previous_enrolment.programme.offer.acronym)
                self.assertEqual(result.annee, self.previous_enrolment.programme.offer.academic_year.year)

    def test_depends_on_status(self):
        valid_values = {
            StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
        }

        for value in StatutInscriptionProgrammAnnuel:
            self.enrolment.statut = value.name
            self.enrolment.save()

            result = InscriptionsTranslatorService.recuperer_derniere_inscription(
                matricule_candidat=self.student.global_id,
            )

            self.assertIsNotNone(result)

            if value.name in valid_values:
                self.assertEqual(result.sigle, self.enrolment.programme.offer.acronym)
                self.assertEqual(result.annee, self.enrolment.programme.offer.academic_year.year)
            else:
                self.assertEqual(result.sigle, self.previous_enrolment.programme.offer.acronym)
                self.assertEqual(result.annee, self.previous_enrolment.programme.offer.academic_year.year)


@freezegun.freeze_time(datetime.date(2025, 1, 1))
class RetrieveValidEnrolmentsForDeliberationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.academic_years = {year: AcademicYearFactory(year=year) for year in [2023, 2024, 2025, 2026]}

    def setUp(self):
        super().setUp()

        self.enrolment = InscriptionProgrammeAnnuelFactory(
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            programme__offer__academic_type=AcademicTypes.ACADEMIC.name,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            programme__root_group__academic_year=self.academic_years[2024],
        )

        self.student = self.enrolment.programme_cycle.etudiant.person

    def test_with_no_enrolment(self):
        result = InscriptionsTranslatorService.recuperer_inscriptions_deliberables(
            matricule_candidat='UNKNOWN',
            annee=2024,
        )

        self.assertEqual(len(result), 0)

    def test_retrieve_valid_dto(self):
        result = InscriptionsTranslatorService.recuperer_inscriptions_deliberables(
            matricule_candidat=self.student.global_id,
            annee=2024,
        )

        self.assertEqual(len(result), 1)

        self.assertEqual(result[0].sigle, self.enrolment.programme.offer.acronym)
        self.assertEqual(result[0].annee, self.enrolment.programme.offer.academic_year.year)
        self.assertEqual(result[0].noma, self.enrolment.programme_cycle.etudiant.registration_id)
        self.assertEqual(result[0].est_premiere_annee_bachelier, self.enrolment.est_premiere_annee_bachelier)

    def test_depends_on_enrolment_state(self):
        valid_values = {
            EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            EtatInscriptionFormation.PROVISOIRE.name,
        }

        for value in EtatInscriptionFormation:
            self.enrolment.etat_inscription = value.name
            self.enrolment.save()

            result = InscriptionsTranslatorService.recuperer_inscriptions_deliberables(
                matricule_candidat=self.student.global_id,
                annee=2024,
            )

            self.assertEqual(len(result), int(value.name in valid_values))

    def test_depends_on_academic_type(self):
        valid_values = {
            AcademicTypes.ACADEMIC.name,
            AcademicTypes.NON_ACADEMIC_CREF.name,
        }

        for value in AcademicTypes:
            self.enrolment.programme.offer.academic_type = value.name
            self.enrolment.programme.offer.save()

            result = InscriptionsTranslatorService.recuperer_inscriptions_deliberables(
                matricule_candidat=self.student.global_id,
                annee=2024,
            )

            self.assertEqual(len(result), int(value.name in valid_values))

    def test_depends_on_status(self):
        valid_values = {
            StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
        }

        for value in StatutInscriptionProgrammAnnuel:
            self.enrolment.statut = value.name
            self.enrolment.save()

            result = InscriptionsTranslatorService.recuperer_inscriptions_deliberables(
                matricule_candidat=self.student.global_id,
                annee=2024,
            )

            self.assertEqual(len(result), int(value.name in valid_values))

    def test_depends_on_academic_year(self):
        valid_values = {
            2024,
        }

        for year, academic_year in self.academic_years.items():
            result = InscriptionsTranslatorService.recuperer_inscriptions_deliberables(
                matricule_candidat=self.student.global_id,
                annee=year,
            )

            self.assertEqual(len(result), int(year in valid_values))


@freezegun.freeze_time(datetime.date(2025, 1, 1))
class RetrieveDirectPursuitAssimilationTestCase(TestCase):
    retrieve_direct_pursuit_assimilation = partial(
        InscriptionsTranslatorService.recuperer_assimilation_inscription_formation_annee_precedente,
        annee_inscription_formation_translator=AnneeInscriptionFormationTranslator(),
    )

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.academic_years = {year: AcademicYearFactory(year=year) for year in [2023, 2024, 2025, 2026]}

        cls.administrative_calendar = AcademicCalendarFactory(
            reference=AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name,
            start_date=datetime.date(2024, 11, 1),
            end_date=datetime.date(2025, 10, 31),
            data_year=cls.academic_years[2025],
        )

    def setUp(self):
        super().setUp()

        self.enrolment = InscriptionProgrammeAnnuelFactory(
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            programme__offer__academic_type=AcademicTypes.ACADEMIC.name,
            statut=StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            programme__root_group__academic_year=self.academic_years[2024],
            assimilation=AssimilationEnum.UNE.name,
        )

        self.student = self.enrolment.programme_cycle.etudiant.person
        self.training = self.enrolment.programme.offer

    def test_with_no_enrolment(self):
        result = self.retrieve_direct_pursuit_assimilation(
            matricule_candidat='UNKNOWN',
            sigle_formation=self.training.acronym,
        )

        self.assertIsNone(result)

    def test_depends_on_training(self):
        result = self.retrieve_direct_pursuit_assimilation(
            matricule_candidat=self.student.global_id,
            sigle_formation=self.training.acronym,
        )

        self.assertIsNotNone(result)

        result = self.retrieve_direct_pursuit_assimilation(
            matricule_candidat=self.student.global_id,
            sigle_formation='ABCDE',
        )

        self.assertIsNone(result)

    def test_depends_on_enrolment_state(self):
        valid_values = {
            EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            EtatInscriptionFormation.PROVISOIRE.name,
            EtatInscriptionFormation.CESSATION.name,
        }

        for value in EtatInscriptionFormation:
            self.enrolment.etat_inscription = value.name
            self.enrolment.save()

            result = self.retrieve_direct_pursuit_assimilation(
                matricule_candidat=self.student.global_id,
                sigle_formation=self.training.acronym,
            )

            if value.name in valid_values:
                self.assertIsNotNone(result)
            else:
                self.assertIsNone(result)

    def test_depends_on_academic_type(self):
        valid_values = {
            AcademicTypes.ACADEMIC.name,
            AcademicTypes.NON_ACADEMIC_CREF.name,
        }

        for value in AcademicTypes:
            self.enrolment.programme.offer.academic_type = value.name
            self.enrolment.programme.offer.save()

            result = self.retrieve_direct_pursuit_assimilation(
                matricule_candidat=self.student.global_id,
                sigle_formation=self.training.acronym,
            )

            if value.name in valid_values:
                self.assertIsNotNone(result)
            else:
                self.assertIsNone(result)

    def test_depends_on_status(self):
        valid_values = {
            StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
        }

        for value in StatutInscriptionProgrammAnnuel:
            self.enrolment.statut = value.name
            self.enrolment.save()

            result = self.retrieve_direct_pursuit_assimilation(
                matricule_candidat=self.student.global_id,
                sigle_formation=self.training.acronym,
            )

            if value.name in valid_values:
                self.assertIsNotNone(result)
            else:
                self.assertIsNone(result)

    def test_depends_on_academic_year(self):
        valid_values = {
            2024,
        }

        for year, academic_year in self.academic_years.items():
            self.enrolment.programme.offer.academic_year = academic_year
            self.enrolment.programme.offer.save()

            result = self.retrieve_direct_pursuit_assimilation(
                matricule_candidat=self.student.global_id,
                sigle_formation=self.training.acronym,
            )

            if year in valid_values:
                self.assertIsNotNone(result)
            else:
                self.assertIsNone(result)

    def test_retrieve_assimilation_from_enrolment(self):
        for original_value, target_value in [
            (
                AssimilationEnum.UNE.name,
                TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE,
            ),
            (
                AssimilationEnum.DEUX.name,
                TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE,
            ),
            (
                AssimilationEnum.TROIS.name,
                TypeSituationAssimilation.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT,
            ),
            (
                AssimilationEnum.QUATRE.name,
                TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS,
            ),
            (
                AssimilationEnum.CINQ.name,
                TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4,
            ),
            (
                AssimilationEnum.SIX.name,
                TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2,
            ),
            (
                AssimilationEnum.SEPT.name,
                TypeSituationAssimilation.RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE,
            ),
        ]:
            self.enrolment.assimilation = original_value
            self.enrolment.save(update_fields=['assimilation'])

            result = self.retrieve_direct_pursuit_assimilation(
                matricule_candidat=self.student.global_id,
                sigle_formation=self.training.acronym,
            )
            self.assertIsNotNone(result)
            self.assertEqual(result.type_situation_assimilation, target_value)

        self.enrolment.assimilation = AssimilationEnum.E.name
        self.enrolment.save(update_fields=['assimilation'])

        result = self.retrieve_direct_pursuit_assimilation(
            matricule_candidat=self.student.global_id,
            sigle_formation=self.training.acronym,
        )
        self.assertIsNone(result)

        self.enrolment.assimilation = ''
        self.enrolment.save(update_fields=['assimilation'])

        result = self.retrieve_direct_pursuit_assimilation(
            matricule_candidat=self.student.global_id,
            sigle_formation=self.training.acronym,
        )
        self.assertIsNone(result)

    def test_retrieve_assimilation_from_other_admission(self):
        other_admission = GeneralEducationAdmissionFactory(
            candidate=self.student,
            training__academic_year=self.academic_years[2024],
            status=ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
            training=self.enrolment.programme.offer,
        )

        other_admission.accounting.assimilation_situation = (
            TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2.name
        )
        other_admission.accounting.assimilation_1_situation_type = ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name
        other_admission.accounting.assimilation_2_situation_type = ChoixAssimilation2.DEMANDEUR_ASILE.name
        other_admission.accounting.assimilation_3_situation_type = (
            ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT.name
        )
        other_admission.accounting.relationship = LienParente.PERE.name
        other_admission.accounting.assimilation_5_situation_type = ChoixAssimilation5.A_NATIONALITE_UE.name
        other_admission.accounting.assimilation_6_situation_type = (
            ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name
        )
        other_admission.accounting.save()

        result = self.retrieve_direct_pursuit_assimilation(
            matricule_candidat=self.student.global_id,
            sigle_formation=self.training.acronym,
        )

        self.assertIsNotNone(result)

        self.assertEqual(result.type_situation_assimilation, TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2)
        self.assertEqual(result.sous_type_situation_assimilation_1, ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER)
        self.assertEqual(result.sous_type_situation_assimilation_2, ChoixAssimilation2.DEMANDEUR_ASILE)
        self.assertEqual(
            result.sous_type_situation_assimilation_3,
            ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT,
        )
        self.assertEqual(result.relation_parente, LienParente.PERE)
        self.assertEqual(result.sous_type_situation_assimilation_5, ChoixAssimilation5.A_NATIONALITE_UE)
        self.assertEqual(
            result.sous_type_situation_assimilation_6,
            ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT,
        )
        self.assertEqual(result.source, Assimilation.Source.OSIS)

        other_admission.accounting.assimilation_situation = TypeSituationAssimilation.AUCUNE_ASSIMILATION.name
        other_admission.accounting.save()

        result = self.retrieve_direct_pursuit_assimilation(
            matricule_candidat=self.student.global_id,
            sigle_formation=self.training.acronym,
        )

        self.assertIsNotNone(result)
        self.assertEqual(
            result.type_situation_assimilation,
            TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE,
        )
        self.assertEqual(result.source, Assimilation.Source.EPC)

        self.enrolment.assimilation = ''
        self.enrolment.save(update_fields=['assimilation'])

        result = self.retrieve_direct_pursuit_assimilation(
            matricule_candidat=self.student.global_id,
            sigle_formation=self.training.acronym,
        )

        self.assertIsNone(result)
