# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest.mock import ANY, patch

import freezegun
from django.test import TestCase, override_settings
from osis_history.models import HistoryEntry

from admission.contrib.models import DoctorateAdmission
from admission.ddd.admission.doctorat.preparation.commands import RecupererPropositionGestionnaireQuery
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.doctorat.preparation.dtos import DoctoratDTO
from admission.ddd.admission.doctorat.preparation.dtos.proposition import PropositionGestionnaireDTO
from admission.ddd.admission.dtos.bourse import BourseDTO
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.scholarship import DoctorateScholarshipFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.student import StudentFactory
from infrastructure.messages_bus import message_bus_instance
from reference.tests.factories.country import CountryFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
@freezegun.freeze_time('2023-01-01')
class GetPropositionDTOForGestionnaireTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.country = CountryFactory()
        cls.france_country = CountryFactory(iso_code='FR')

    def setUp(self) -> None:
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        school = EntityFactory()
        EntityVersionFactory(entity=school, acronym='SCH', parent=first_doctoral_commission)

        self.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            training__management_entity=school,
            international_scholarship=None,
            candidate__private_email='john.doe@example.com',
            candidate__country_of_citizenship=self.country,
        )

        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("osis_document.api.utils.get_remote_metadata", return_value={"name": "myfile", "size": 1})
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("osis_document.api.utils.confirm_remote_upload", return_value=str(uuid.uuid4()))
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            'osis_document.contrib.fields.FileField._confirm_multiple_upload',
            side_effect=lambda _, value, __: [str(uuid.uuid4())] if value else [],
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _get_command_result(self, uuid_proposition=None) -> PropositionGestionnaireDTO:
        return message_bus_instance.invoke(
            RecupererPropositionGestionnaireQuery(uuid_proposition=uuid_proposition or self.admission.uuid),
        )

    def test_get_proposition_with_base_data(self):
        result = self._get_command_result()

        self.assertEqual(result.uuid, self.admission.uuid)
        self.assertEqual(
            result.doctorat,
            DoctoratDTO(
                sigle=self.admission.training.acronym,
                code=self.admission.training.partial_acronym,
                annee=self.admission.training.academic_year.year,
                intitule=self.admission.training.title,
                campus=ANY,
                type=self.admission.training.education_group_type.name,
                campus_inscription=ANY,
                sigle_entite_gestion='SCH',
            ),
        )
        self.assertEqual(result.reference, f'M-SCH22-{self.admission}')
        self.assertEqual(result.creee_le, self.admission.created_at)
        self.assertEqual(result.modifiee_le, self.admission.modified_at)
        self.assertEqual(result.soumise_le, self.admission.submitted_at)
        self.assertEqual(result.statut, self.admission.status)
        self.assertEqual(result.matricule_candidat, self.admission.candidate.global_id)
        self.assertEqual(result.prenom_candidat, self.admission.candidate.first_name)
        self.assertEqual(result.nom_candidat, self.admission.candidate.last_name)
        self.assertEqual(result.curriculum, self.admission.curriculum)
        self.assertEqual(result.pdf_recapitulatif, self.admission.pdf_recap)
        self.assertEqual(result.type_demande, self.admission.type_demande)
        self.assertEqual(result.date_changement_statut, None)
        self.assertEqual(result.genre_candidat, self.admission.candidate.gender)
        self.assertEqual(result.noma_candidat, '')
        self.assertEqual(result.adresse_email_candidat, self.admission.candidate.private_email)
        self.assertEqual(result.langue_contact_candidat, self.admission.candidate.language)
        self.assertEqual(result.nationalite_candidat, self.admission.candidate.country_of_citizenship.name)
        self.assertEqual(result.nationalite_candidat_fr, self.admission.candidate.country_of_citizenship.name)
        self.assertEqual(result.nationalite_candidat_en, self.admission.candidate.country_of_citizenship.name_en)
        self.assertEqual(result.nationalite_ue_candidat, self.admission.candidate.country_of_citizenship.european_union)
        self.assertEqual(result.nationalite_candidat_code_iso, self.admission.candidate.country_of_citizenship.iso_code)
        self.assertEqual(result.photo_identite_candidat, self.admission.candidate.id_card)
        self.assertEqual(result.candidat_a_plusieurs_demandes, False)
        self.assertEqual(result.cotutelle, None)
        self.assertEqual(result.profil_soumis_candidat, None)
        self.assertEqual(result.bourse_recherche, None)

    def test_get_proposition_with_country_of_citizenship(self):
        self.admission.candidate.country_of_citizenship = CountryFactory()
        self.admission.candidate.save()

        result = self._get_command_result()

        self.assertEqual(result.nationalite_candidat, self.admission.candidate.country_of_citizenship.name)
        self.assertEqual(result.nationalite_candidat_fr, self.admission.candidate.country_of_citizenship.name)
        self.assertEqual(result.nationalite_candidat_en, self.admission.candidate.country_of_citizenship.name_en)
        self.assertEqual(result.nationalite_ue_candidat, self.admission.candidate.country_of_citizenship.european_union)

    def test_get_proposition_with_scholarship(self):
        self.admission.international_scholarship = DoctorateScholarshipFactory()
        self.admission.save()

        result = self._get_command_result()

        self.assertEqual(
            result.bourse_recherche,
            BourseDTO(
                uuid=str(self.admission.international_scholarship.uuid),
                nom_court=self.admission.international_scholarship.short_name,
                nom_long=self.admission.international_scholarship.long_name,
                type=self.admission.international_scholarship.type,
            ),
        )

    def test_get_proposition_with_update_status_history_entry(self):
        self.history_entry = HistoryEntry.objects.create(
            object_uuid=self.admission.uuid,
            tags=['proposition', 'status-changed'],
        )

        result = self._get_command_result()

        self.assertEqual(result.date_changement_statut, self.history_entry.created)

    def test_get_proposition_with_noma(self):
        student = StudentFactory(person=self.admission.candidate)

        result = self._get_command_result()

        self.assertEqual(result.noma_candidat, student.registration_id)

    def test_get_proposition_with_several_enrolments(self):
        second_admission = DoctorateAdmissionFactory(
            candidate=self.admission.candidate,
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
        )

        result = self._get_command_result()
        self.assertEqual(result.candidat_a_plusieurs_demandes, True)

        second_admission.status = ChoixStatutPropositionDoctorale.ANNULEE.name
        second_admission.save()

        result = self._get_command_result()
        self.assertEqual(result.candidat_a_plusieurs_demandes, False)

        second_admission.status = ChoixStatutPropositionDoctorale.EN_BROUILLON.name
        second_admission.save()

        result = self._get_command_result()
        self.assertEqual(result.candidat_a_plusieurs_demandes, False)

        second_admission.status = ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name
        second_admission.save()

        result = self._get_command_result()
        self.assertEqual(result.candidat_a_plusieurs_demandes, False)

    def test_get_unknown_proposition_triggers_exception(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self._get_command_result(uuid_proposition=uuid.uuid4())

    def test_get_proposition_with_cotutelle(self):
        self.admission.cotutelle = True
        self.admission.cotutelle_motivation = 'My motivation'
        self.admission.cotutelle_institution_fwb = True
        self.admission.cotutelle_institution = 'Institute'
        self.admission.cotutelle_opening_request = [uuid.uuid4()]
        self.admission.cotutelle_convention = [uuid.uuid4()]
        self.admission.cotutelle_other_documents = [uuid.uuid4()]

        self.admission.save()

        result = self._get_command_result()

        self.assertIsNotNone(result.cotutelle)

        self.assertEqual(result.cotutelle.cotutelle, True)
        self.assertEqual(result.cotutelle.motivation, 'My motivation')
        self.assertEqual(result.cotutelle.institution_fwb, True)
        self.assertEqual(result.cotutelle.institution, 'Institute')
        self.assertEqual([str(result.cotutelle.demande_ouverture[0])], self.admission.cotutelle_opening_request)
        self.assertEqual([str(result.cotutelle.convention[0])], self.admission.cotutelle_convention)
        self.assertEqual([str(result.cotutelle.autres_documents[0])], self.admission.cotutelle_other_documents)

    def test_get_proposition_with_submitted_profile(self):
        self.admission.submitted_profile = {
            'identification': {
                'last_name': 'Joe',
                'first_name': 'Doe',
                'gender': 'M',
                'country_of_citizenship': 'FR',
                'birth_date': '1990-01-01',
            },
            'coordinates': {
                'country': 'FR',
                'city': 'Paris',
                'street': 'Rue de la Paix',
                'postal_code': '75000',
                'street_number': '1',
                'postal_box': 'A',
            },
        }

        self.admission.save()

        result = self._get_command_result()

        self.assertIsNotNone(result.profil_soumis_candidat)
        self.assertEqual(result.profil_soumis_candidat.nom, 'Joe')
        self.assertEqual(result.profil_soumis_candidat.prenom, 'Doe')
        self.assertEqual(result.profil_soumis_candidat.genre, 'M')
        self.assertEqual(result.profil_soumis_candidat.nationalite, 'FR')
        self.assertEqual(result.profil_soumis_candidat.nom_pays_nationalite, self.france_country.name)
        self.assertEqual(result.profil_soumis_candidat.date_naissance, datetime.date(1990, 1, 1))
        self.assertEqual(result.profil_soumis_candidat.pays, 'FR')
        self.assertEqual(result.profil_soumis_candidat.nom_pays, self.france_country.name)
        self.assertEqual(result.profil_soumis_candidat.code_postal, '75000')
        self.assertEqual(result.profil_soumis_candidat.ville, 'Paris')
        self.assertEqual(result.profil_soumis_candidat.rue, 'Rue de la Paix')
        self.assertEqual(result.profil_soumis_candidat.numero_rue, '1')
        self.assertEqual(result.profil_soumis_candidat.boite_postale, 'A')
