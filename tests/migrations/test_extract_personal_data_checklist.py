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

from django.test import TestCase

from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT,
)
from admission.migrations.utils.extract_personal_data_checklist import extract_personal_data_checklist
from admission.models import GeneralEducationAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from base.models.enums.personal_data import ChoixStatutValidationDonneesPersonnelles
from base.models.person import Person
from base.tests.factories.person import PersonFactory


class ExtractPersonalDataChecklistTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.personal_data_statuses = ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT['donnees_personnelles']
        cls.to_be_processed_status = cls.personal_data_statuses[ChoixStatutValidationDonneesPersonnelles.A_TRAITER.name]
        cls.cleaned_status = cls.personal_data_statuses[ChoixStatutValidationDonneesPersonnelles.TOILETTEES.name]
        cls.to_be_completed_status = cls.personal_data_statuses[
            ChoixStatutValidationDonneesPersonnelles.A_COMPLETER.name
        ]
        cls.expert_opinion_status = cls.personal_data_statuses[
            ChoixStatutValidationDonneesPersonnelles.AVIS_EXPERT.name
        ]
        cls.fraudster_status = cls.personal_data_statuses[ChoixStatutValidationDonneesPersonnelles.FRAUDEUR.name]
        cls.validated_status = cls.personal_data_statuses[ChoixStatutValidationDonneesPersonnelles.VALIDEES.name]

    def test_do_not_update_if_the_person_has_no_admission(self):
        person: Person = PersonFactory()

        extract_personal_data_checklist(person_model_class=Person)

        person.refresh_from_db()

        self.assertEqual(
            person.personal_data_validation_status,
            ChoixStatutValidationDonneesPersonnelles.A_TRAITER.name,
        )

    def test_do_not_update_if_the_person_has_no_checklist_in_his_admissions(self):
        person: Person = PersonFactory()

        GeneralEducationAdmissionFactory(
            candidate=person,
            checklist={},
        )

        extract_personal_data_checklist(person_model_class=Person)

        person.refresh_from_db()

        self.assertEqual(
            person.personal_data_validation_status,
            ChoixStatutValidationDonneesPersonnelles.A_TRAITER.name,
        )

    def test_update_if_the_person_has_a_checklist_in_his_single_admission(self):
        person: Person = PersonFactory()

        admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            candidate=person,
            checklist={
                'current': {
                    'donnees_personnelles': {},
                }
            },
        )

        for status in ChoixStatutValidationDonneesPersonnelles:
            admission.checklist['current']['donnees_personnelles'] = self.personal_data_statuses[status.name].to_dict()
            admission.save()

            extract_personal_data_checklist(person_model_class=Person)

            person.refresh_from_db()

            self.assertEqual(person.personal_data_validation_status, status.name)

    def test_update_if_the_person_has_a_checklist_in_several_admissions(self):
        person: Person = PersonFactory()

        GeneralEducationAdmissionFactory(
            candidate=person,
            checklist={
                'current': {
                    'donnees_personnelles': self.to_be_completed_status.to_dict(),
                }
            },
        )

        second_general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            candidate=person,
            checklist={
                'current': {
                    'donnees_personnelles': self.to_be_processed_status.to_dict(),
                }
            },
        )

        extract_personal_data_checklist(person_model_class=Person)

        person.refresh_from_db()

        self.assertEqual(person.personal_data_validation_status, self.to_be_completed_status.identifiant)

        ContinuingEducationAdmissionFactory(
            candidate=person,
            checklist={
                'current': {'donnees_personnelles': self.cleaned_status.to_dict()},
            },
        )

        extract_personal_data_checklist(person_model_class=Person)

        person.refresh_from_db()

        self.assertEqual(person.personal_data_validation_status, self.to_be_completed_status.identifiant)

        DoctorateAdmissionFactory(
            candidate=person,
            checklist={
                'current': {'donnees_personnelles': self.validated_status.to_dict()},
            },
        )

        extract_personal_data_checklist(person_model_class=Person)

        person.refresh_from_db()

        self.assertEqual(person.personal_data_validation_status, self.validated_status.identifiant)

        second_general_admission.checklist['current']['donnees_personnelles'] = self.fraudster_status.to_dict()
        second_general_admission.save()

        extract_personal_data_checklist(person_model_class=Person)

        person.refresh_from_db()

        self.assertEqual(person.personal_data_validation_status, self.fraudster_status.identifiant)

    def test_priority_when_updating_if_the_person_has_a_checklist_in_several_admissions(self):
        person: Person = PersonFactory()

        first_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            candidate=person,
            checklist={'current': {}},
        )

        second_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            candidate=person,
            checklist={'current': {}},
        )

        extract_personal_data_checklist(person_model_class=Person)

        person.refresh_from_db()

        self.assertEqual(person.personal_data_validation_status, self.to_be_processed_status.identifiant)

        def _test_priority(current_status, priority_statuses):
            first_admission.checklist['current']['donnees_personnelles'] = self.personal_data_statuses[
                current_status
            ].to_dict()
            first_admission.save(update_fields=['checklist'])

            for priority_status in priority_statuses:
                second_admission.checklist['current']['donnees_personnelles'] = self.personal_data_statuses[
                    priority_status
                ].to_dict()
                second_admission.save(update_fields=['checklist'])

                extract_personal_data_checklist(person_model_class=Person)
                person.refresh_from_db()

                self.assertEqual(person.personal_data_validation_status, priority_status)

            for non_priority_status in ChoixStatutValidationDonneesPersonnelles.get_names_except(
                current_status, *priority_statuses
            ):
                second_admission.checklist['current']['donnees_personnelles'] = self.personal_data_statuses[
                    non_priority_status
                ].to_dict()
                second_admission.save(update_fields=['checklist'])

                extract_personal_data_checklist(person_model_class=Person)
                person.refresh_from_db()

                self.assertEqual(person.personal_data_validation_status, current_status)

        _test_priority(
            ChoixStatutValidationDonneesPersonnelles.A_TRAITER.name,
            priority_statuses=[
                ChoixStatutValidationDonneesPersonnelles.TOILETTEES.name,
                ChoixStatutValidationDonneesPersonnelles.A_COMPLETER.name,
                ChoixStatutValidationDonneesPersonnelles.AVIS_EXPERT.name,
                ChoixStatutValidationDonneesPersonnelles.FRAUDEUR.name,
                ChoixStatutValidationDonneesPersonnelles.VALIDEES.name,
            ],
        )
        _test_priority(
            ChoixStatutValidationDonneesPersonnelles.TOILETTEES.name,
            priority_statuses=[
                ChoixStatutValidationDonneesPersonnelles.A_COMPLETER.name,
                ChoixStatutValidationDonneesPersonnelles.AVIS_EXPERT.name,
                ChoixStatutValidationDonneesPersonnelles.FRAUDEUR.name,
                ChoixStatutValidationDonneesPersonnelles.VALIDEES.name,
            ],
        )
        _test_priority(
            ChoixStatutValidationDonneesPersonnelles.A_COMPLETER.name,
            priority_statuses=[
                ChoixStatutValidationDonneesPersonnelles.AVIS_EXPERT.name,
                ChoixStatutValidationDonneesPersonnelles.FRAUDEUR.name,
                ChoixStatutValidationDonneesPersonnelles.VALIDEES.name,
            ],
        )
        _test_priority(
            ChoixStatutValidationDonneesPersonnelles.AVIS_EXPERT.name,
            priority_statuses=[
                ChoixStatutValidationDonneesPersonnelles.FRAUDEUR.name,
                ChoixStatutValidationDonneesPersonnelles.VALIDEES.name,
            ],
        )
        _test_priority(
            ChoixStatutValidationDonneesPersonnelles.FRAUDEUR.name,
            priority_statuses=[],
        )
        _test_priority(
            ChoixStatutValidationDonneesPersonnelles.VALIDEES.name,
            priority_statuses=[
                ChoixStatutValidationDonneesPersonnelles.FRAUDEUR.name,
            ],
        )
