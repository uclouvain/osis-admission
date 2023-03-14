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
from typing import List

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.urls import reverse

from admission.contrib.models import DoctorateAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import ENTITY_CDE, ENTITY_CDSS
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    BourseRecherche,
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixStatutCDD, ChoixStatutSIC
from admission.ddd.admission.doctorat.validation.dtos import DemandeRechercheDTO
from admission.tests import QueriesAssertionsMixin
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import CandidateFactory, CddManagerFactory, DoctorateReaderRoleFactory
from admission.tests.factories.supervision import PromoterFactory
from base.models.enums.entity_type import EntityType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from reference.tests.factories.country import CountryFactory


class CddDoctorateAdmissionListTestCase(QueriesAssertionsMixin, TestCase):
    admissions = []
    NB_MAX_QUERIES = 22

    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.user = User.objects.create_user(
            username='john_doe',
            password='top_secret',
        )

        cls.doctorate_reader_user = DoctorateReaderRoleFactory().person.user

        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(
            entity=first_doctoral_commission,
            acronym=ENTITY_CDE,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
        )

        second_doctoral_commission = EntityFactory()
        EntityVersionFactory(
            entity=second_doctoral_commission,
            acronym=ENTITY_CDSS,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
        )

        candidate = CandidateFactory(
            person__country_of_citizenship=CountryFactory(
                iso_code='be',
                name='Belgique',
                name_en='Belgium',
            )
        )
        promoter = PromoterFactory()
        cls.promoter = promoter.person

        # Create admissions
        cls.admissions: List[DoctorateAdmission] = [
            DoctorateAdmissionFactory(
                training__management_entity=first_doctoral_commission,
                training__academic_year=academic_years[0],
                training__enrollment_campus__name='Mons',
                cotutelle=False,
                supervision_group=promoter.process,
                financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
                financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
                type=ChoixTypeAdmission.PRE_ADMISSION.name,
                pre_admission_submission_date=datetime.datetime.now(),
            ),
            DoctorateAdmissionFactory(
                cotutelle=None,
                training__management_entity=first_doctoral_commission,
                training__academic_year=academic_years[0],
                training__enrollment_campus__name='Mons',
                status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
                candidate=candidate.person,
                financing_type=ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
                other_international_scholarship=BourseRecherche.ARC.name,
                financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
                type=ChoixTypeAdmission.ADMISSION.name,
                submitted_at=datetime.datetime.now(),
                status_cdd=ChoixStatutCDD.TO_BE_VERIFIED.name,
                status_sic=ChoixStatutSIC.VALID.name,
                submitted_profile={
                    "coordinates": {
                        "city": "Louvain-La-Neuves",
                        "email": "user@uclouvain.be",
                        "place": "",
                        "street": "Place de l'Université",
                        "country": "BE",
                        "postal_box": "",
                        "postal_code": "1348",
                        "street_number": "2",
                    },
                    "identification": {
                        "gender": "M",
                        "last_name": "Doe",
                        "first_name": "John",
                        "country_of_citizenship": "BE",
                    },
                },
            ),
            DoctorateAdmissionFactory(
                cotutelle=None,
                training__management_entity=second_doctoral_commission,
                training__academic_year=academic_years[0],
                training__enrollment_campus__name='Mons',
                other_international_scholarship='Custom grant',
                financing_work_contract='Custom working contract',
            ),
        ]
        cls.admission_references = [
            f'M-{ENTITY_CDE}21-{str(cls.admissions[0])}',
            f'M-{ENTITY_CDE}21-{str(cls.admissions[1])}',
            f'M-{ENTITY_CDSS}21-{str(cls.admissions[2])}',
        ]

        cls.results = [
            DemandeRechercheDTO(
                uuid=cls.admissions[0].uuid,
                numero_demande=cls.admission_references[0],
                statut_demande=cls.admissions[0].status,
                nom_candidat='{}, {}'.format(
                    cls.admissions[0].candidate.last_name, cls.admissions[0].candidate.first_name
                ),
                formation='{} - {}'.format(cls.admissions[0].doctorate.acronym, cls.admissions[0].doctorate.title),
                nationalite=cls.admissions[0].candidate.country_of_citizenship.name
                if cls.admissions[0].candidate.country_of_citizenship
                else None,
                derniere_modification=cls.admissions[0].modified_at,
                code_bourse=cls.admissions[0].other_international_scholarship,
                statut_cdd=None,
                statut_sic=None,
                date_confirmation=None,
            ),
            DemandeRechercheDTO(
                uuid=cls.admissions[1].uuid,
                numero_demande=cls.admission_references[1],
                statut_cdd=cls.admissions[1].status_cdd,
                statut_sic=cls.admissions[1].status_sic,
                statut_demande=cls.admissions[1].status,
                nom_candidat='{}, {}'.format(
                    cls.admissions[1].candidate.last_name, cls.admissions[1].candidate.first_name
                ),
                formation='{} - {}'.format(cls.admissions[1].doctorate.acronym, cls.admissions[1].doctorate.title),
                nationalite=cls.admissions[1].candidate.country_of_citizenship.name
                if cls.admissions[1].candidate.country_of_citizenship
                else None,
                derniere_modification=cls.admissions[1].modified_at,
                date_confirmation=cls.admissions[1].submitted_at,
                code_bourse=cls.admissions[1].other_international_scholarship,
            ),
            DemandeRechercheDTO(
                uuid=cls.admissions[2].uuid,
                numero_demande=cls.admission_references[2],
                statut_demande=cls.admissions[2].status,
                nom_candidat='{}, {}'.format(
                    cls.admissions[2].candidate.last_name, cls.admissions[2].candidate.first_name
                ),
                formation='{} - {}'.format(cls.admissions[2].doctorate.acronym, cls.admissions[2].doctorate.title),
                nationalite=cls.admissions[2].candidate.country_of_citizenship.name
                if cls.admissions[2].candidate.country_of_citizenship
                else None,
                derniere_modification=cls.admissions[2].modified_at,
                code_bourse=cls.admissions[2].other_international_scholarship,
                statut_cdd=None,
                statut_sic=None,
                date_confirmation=None,
            ),
        ]

        # User with one cdd
        cdd_person_user = CddManagerFactory(entity=first_doctoral_commission).person
        cls.one_cdd_user = cdd_person_user.user

        # User with several cdds
        several_cdd_person_user = CddManagerFactory(entity=first_doctoral_commission).person
        cdd_manager = CddManagerFactory(entity=second_doctoral_commission)
        cdd_manager.person = several_cdd_person_user
        cdd_manager.save()
        cls.several_cdds_user = several_cdd_person_user.user

        # Targeted url
        cls.url = reverse('admission:doctorate:cdd:list')

    def setUp(self) -> None:
        cache.clear()

    def test_list_user_without_person(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_list_candidate_user(self):
        self.client.force_login(user=self.admissions[0].candidate.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_list_cdd_user_without_any_query_param(self):
        self.client.force_login(user=self.one_cdd_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object_list'], [])

    def test_list_cdd_user_with_needed_query_params(self):
        self.client.force_login(user=self.one_cdd_user)

        data = {
            'cdds': [ENTITY_CDE],
            'taille_page': 10,
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES, verbose=True):
            response = self.client.get(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)

        self.assertIn(self.results[0], response.context['object_list'])
        self.assertIn(self.results[1], response.context['object_list'])

    def test_list_cdd_user_with_sorting(self):
        self.client.force_login(user=self.one_cdd_user)

        # Sorting
        data = {
            'cdds': [ENTITY_CDE],
            'taille_page': 10,
            'o': 'numero_demande',
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES):
            response = self.client.get(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)
        self.assertEqual(response.context['object_list'][0].numero_demande, self.results[0].numero_demande)
        self.assertEqual(response.context['object_list'][1].numero_demande, self.results[1].numero_demande)

        # Revert sorting
        data['o'] = '-' + data['o']

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES):
            response = self.client.get(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)
        self.assertEqual(response.context['object_list'][0].numero_demande, self.results[1].numero_demande)
        self.assertEqual(response.context['object_list'][1].numero_demande, self.results[0].numero_demande)

    def test_list_cdd_user_with_all_query_params(self):
        self.client.force_login(user=self.one_cdd_user)

        data = {
            'cdds': [ENTITY_CDE],
            'taille_page': 10,
            'numero': str(self.admissions[1]),
            'etat_cdd': self.admissions[1].status_cdd,
            'etat_sic': self.admissions[1].status_sic,
            'matricule_candidat': self.admissions[1].candidate.global_id,
            'nationalite': self.admissions[1].candidate.country_of_citizenship.iso_code,
            'type': self.admissions[1].type,
            'commission_proximite': self.admissions[1].proximity_commission,
            'annee_academique': self.admissions[1].doctorate.academic_year.year,
            'sigles_formations': [self.admissions[1].doctorate.acronym],
            'type_financement': self.admissions[1].financing_type,
            'type_contrat_travail': self.admissions[1].financing_work_contract,
            'autre_bourse_recherche': self.admissions[1].other_international_scholarship,
        }

        response = self.client.get(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0], self.results[1])

    def test_list_cdd_user_with_other_params(self):
        self.client.force_login(user=self.several_cdds_user)

        data = {
            'cdds': [ENTITY_CDSS],
            'type_contrat_travail': ChoixTypeContratTravail.OTHER.name,
            'bourse_recherche': BourseRecherche.OTHER.name,
        }

        response = self.client.get(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0], self.results[2])

    def test_list_cdd_user_with_cotutelle_query_param(self):
        self.client.force_login(user=self.one_cdd_user)

        data = {
            'cdds': [ENTITY_CDE],
            'taille_page': 10,
            'cotutelle': False,
        }

        response = self.client.get(
            self.url,
            data,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0], self.results[0])

    def test_list_cdd_user_with_promoter_query_param(self):
        self.client.force_login(user=self.one_cdd_user)

        data = {
            'cdds': [ENTITY_CDE],
            'taille_page': 10,
            'matricule_promoteur': self.promoter.global_id,
        }

        response = self.client.get(
            self.url,
            data,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0], self.results[0])

    def test_list_cdd_user_with_several_cdds(self):
        self.client.force_login(user=self.several_cdds_user)

        data = {
            'cdds': [ENTITY_CDE, ENTITY_CDSS],
            'taille_page': 10,
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES):
            response = self.client.get(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 3)
        self.assertCountEqual(self.results, response.context['object_list'])

    def test_htmx_form_errors(self):
        self.client.force_login(user=self.one_cdd_user)

        data = {
            'nationalite': 'FR',
            'cdds': 'unknown_cdd',
        }

        response = self.client.get(
            self.url,
            data,
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'CDDs - Sélectionnez un choix valide. unknown_cdd n’en fait pas partie.',
            [m.message for m in response.context['messages']],
        )

    def test_list_doctorate_reader_user_without_any_query_param(self):
        self.client.force_login(user=self.doctorate_reader_user)

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES):
            response = self.client.get(self.url, data={'taille_page': 10})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 3)

        self.assertIn(self.results[0], response.context['object_list'])
        self.assertIn(self.results[1], response.context['object_list'])
        self.assertIn(self.results[2], response.context['object_list'])
