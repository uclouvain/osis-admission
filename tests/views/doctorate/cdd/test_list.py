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
from typing import List

import freezegun
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import NON_FIELD_ERRORS
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext

from admission.contrib.models import DoctorateAdmission
from admission.ddd import FR_ISO_CODE
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import (
    ENTITY_CDE,
    ENTITY_CDSS,
    SIGLE_SCIENCES,
    ENTITY_CLSM,
    ENTITY_SCIENCES,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    BourseRecherche,
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixStatutCDD, ChoixStatutSIC
from admission.ddd.admission.doctorat.validation.dtos import DemandeRechercheDTO
from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.forms import ALL_EMPTY_CHOICE, ALL_FEMININE_EMPTY_CHOICE
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import (
    CandidateFactory,
    DoctorateReaderRoleFactory,
    ProgramManagerRoleFactory,
    SicManagementRoleFactory,
)
from admission.tests.factories.scholarship import (
    DoctorateScholarshipFactory,
    InternationalScholarshipFactory,
    DoubleDegreeScholarshipFactory,
    ErasmusMundusScholarshipFactory,
)
from admission.tests.factories.supervision import PromoterFactory
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.entity_type import EntityType
from base.tests import QueriesAssertionsMixin
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from osis_profile import BE_ISO_CODE
from reference.tests.factories.country import CountryFactory


@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
@freezegun.freeze_time('2022-01-01')
class DoctorateAdmissionListTestCase(QueriesAssertionsMixin, TestCase):
    admissions = []
    NB_MAX_QUERIES_WITHOUT_SEARCH = 25
    NB_MAX_QUERIES_WITH_SEARCH = 28

    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.doctorate_reader_user = DoctorateReaderRoleFactory().person.user

        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # Academic calendars
        academic_calendar = AcademicCalendarFactory(
            data_year=academic_years[0],
            start_date=datetime.date(year=2021, month=9, day=15),
            end_date=datetime.date(year=2022, month=9, day=14),
            reference=AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT.name,
        )

        # Scholarships
        cls.scholarships = [
            DoctorateScholarshipFactory(short_name='AAA'),
            InternationalScholarshipFactory(),
            DoubleDegreeScholarshipFactory(),
            ErasmusMundusScholarshipFactory(),
        ]

        # Countries
        cls.country = CountryFactory()

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

        third_doctoral_commission = EntityFactory()
        EntityVersionFactory(
            entity=third_doctoral_commission,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='ABC',
        )

        # Countries
        cls.belgium_country = CountryFactory(iso_code=BE_ISO_CODE, name='Belgique', name_en='Belgium')
        cls.france_country = CountryFactory(iso_code=FR_ISO_CODE, name='France', name_en='France')
        cls.greece_country = CountryFactory(iso_code='GR', name='Grèce', name_en='Greece')

        candidate = CandidateFactory(
            person__country_of_citizenship=cls.greece_country,
            person__first_name='Jim',
            person__last_name='Doe',
        )
        promoter = PromoterFactory(
            actor_ptr__person__first_name='Jane',
            actor_ptr__person__last_name='Collins',
        )
        cls.promoter = promoter.person

        # Create admissions
        admission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            training__enrollment_campus__name='Mons',
            training__acronym='EFG3',
            cotutelle=False,
            supervision_group=promoter.process,
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            status=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            proximity_commission=ChoixCommissionProximiteCDSS.BCM.name,
            candidate__country_of_citizenship=cls.belgium_country,
            submitted_at=datetime.datetime(2021, 1, 1),
            candidate__first_name='John',
            candidate__last_name='Doe',
            last_update_author__first_name='Joe',
            last_update_author__last_name='Cole',
        )
        cls.admissions: List[DoctorateAdmission] = [
            admission,
            DoctorateAdmissionFactory(
                cotutelle=None,
                training__management_entity=first_doctoral_commission,
                training__academic_year=academic_years[0],
                training__enrollment_campus__name='Mons',
                training__acronym='BCD2',
                status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
                candidate=candidate.person,
                financing_type=ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
                other_international_scholarship=BourseRecherche.ARC.name,
                financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
                type=ChoixTypeAdmission.ADMISSION.name,
                submitted_at=datetime.datetime(2021, 1, 2),
                status_cdd=ChoixStatutCDD.TO_BE_VERIFIED.name,
                status_sic=ChoixStatutSIC.VALID.name,
                proximity_commission=ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
                last_update_author=cls.promoter,
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
                cotutelle=True,
                training__management_entity=second_doctoral_commission,
                training__academic_year=academic_years[0],
                training__enrollment_campus__name='Mons',
                training__acronym='ABC1',
                status=ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC.name,
                financing_type=ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
                international_scholarship=cls.scholarships[0],
                type=ChoixTypeAdmission.ADMISSION.name,
                submitted_at=datetime.datetime(2021, 1, 3),
                proximity_commission=ChoixSousDomaineSciences.BIOLOGY.name,
                other_international_scholarship='Custom grant',
                financing_work_contract='Custom working contract',
                candidate__country_of_citizenship=cls.france_country,
                candidate__first_name='John',
                candidate__last_name='Foe',
                modified_at=datetime.datetime(2021, 1, 2),
                last_update_author=None,
            ),
            DoctorateAdmissionFactory(
                training__management_entity=third_doctoral_commission,
                training__academic_year=academic_years[1],
                training__enrollment_campus__name='Mons',
                training__acronym=SIGLE_SCIENCES,
                status=ChoixStatutPropositionDoctorale.INSCRIPTION_REFUSEE.name,
                proximity_commission=ChoixCommissionProximiteCDEouCLSM.MANAGEMENT.name,
                type=ChoixTypeAdmission.ADMISSION.name,
                determined_academic_year=academic_years[1],
                candidate__country_of_citizenship=None,
                last_update_author=None,
            ),
        ]

        with freezegun.freeze_time('2021-01-03'):
            cls.admissions[0].modified_at = datetime.datetime(2021, 1, 3)
            cls.admissions[0].save(update_fields=['modified_at'])

        with freezegun.freeze_time('2021-01-01'):
            cls.admissions[1].modified_at = datetime.datetime(2021, 1, 1)
            cls.admissions[1].save(update_fields=['modified_at'])

        with freezegun.freeze_time('2021-01-02'):
            cls.admissions[2].modified_at = datetime.datetime(2021, 1, 2)
            cls.admissions[2].save(update_fields=['modified_at'])

        cls.admission_references = [
            f'M-{ENTITY_CDE}21-{str(cls.admissions[0])}',
            f'M-{ENTITY_CDE}21-{str(cls.admissions[1])}',
            f'M-{ENTITY_CDSS}21-{str(cls.admissions[2])}',
            f'M-ABC22-{str(cls.admissions[3])}',
        ]

        cls.sic_user = SicManagementRoleFactory(entity=first_doctoral_commission).person.user
        program_manager_person = ProgramManagerRoleFactory(
            education_group=cls.admissions[0].training.education_group,
        ).person
        program_manager_person.language = settings.LANGUAGE_CODE_EN
        program_manager_person.save(update_fields=['language'])
        ProgramManagerRoleFactory(
            education_group=cls.admissions[2].training.education_group,
            person=program_manager_person,
        )
        cls.program_manager_user = program_manager_person.user

        # User with several cdds
        person_with_several_cdds = SicManagementRoleFactory(entity=first_doctoral_commission).person
        cls.user_with_several_cdds = person_with_several_cdds.user

        for entity in [second_doctoral_commission, third_doctoral_commission]:
            manager_factory = SicManagementRoleFactory(entity=entity)
            manager_factory.person = person_with_several_cdds
            manager_factory.save()

        # Targeted url
        cls.url = reverse('admission:doctorate:cdd:list')

    def setUp(self) -> None:
        cache.clear()

    def test_list_user_without_person(self):
        self.client.force_login(user=UserFactory())

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_list_manager_without_any_query_param(self):
        self.client.force_login(user=self.program_manager_user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object_list'], [])

    def test_form_initialization_for_a_program_manager(self):
        self.client.force_login(user=self.program_manager_user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(form['annee_academique'].value(), 2022)
        self.assertEqual(
            form.fields['annee_academique'].choices,
            [
                (2022, '2022-23'),
                (2021, '2021-22'),
            ],
        )

        self.assertEqual(form['numero'].value(), None)

        self.assertEqual(form['matricule_candidat'].value(), None)

        self.assertCountEqual(form.fields['etats'].choices, ChoixStatutPropositionDoctorale.choices())
        self.assertEqual(form['etats'].value(), ChoixStatutPropositionDoctorale.get_names())

        self.assertEqual(form['taille_page'].value(), 500)

        self.assertEqual(form['page'].value(), 1)

        self.assertEqual(form['nationalite'].value(), None)

        self.assertEqual(form['type'].value(), None)
        self.assertCountEqual(form.fields['type'].choices, ALL_EMPTY_CHOICE + ChoixTypeAdmission.choices())

        self.assertEqual(form['cotutelle'].value(), None)
        self.assertCountEqual(
            form.fields['cotutelle'].widget.choices,
            ALL_EMPTY_CHOICE + ((True, 'Yes'), (False, 'No')),
        )

        self.assertEqual(form['date_soumission_debut'].value(), None)

        self.assertEqual(form['date_soumission_fin'].value(), None)

        self.assertEqual(form['commission_proximite'].value(), None)
        self.assertCountEqual(
            form.fields['commission_proximite'].choices,
            [
                ALL_FEMININE_EMPTY_CHOICE[0],
                ['{} / {}'.format(ENTITY_CDE, ENTITY_CLSM), ChoixCommissionProximiteCDEouCLSM.choices()],
                [ENTITY_CDSS, ChoixCommissionProximiteCDSS.choices()],
            ],
        )

        self.assertEqual(form.fields['cdds'].choices, [(ENTITY_CDE, ENTITY_CDE), (ENTITY_CDSS, ENTITY_CDSS)])

        self.assertEqual(form['matricule_promoteur'].value(), None)

        self.assertEqual(form['sigles_formations'].value(), None)
        self.assertCountEqual(
            form.fields['sigles_formations'].choices,
            [
                (training.acronym, f'{training.acronym} - {training.title_english}')
                for training in [
                    self.admissions[0].training,
                    self.admissions[2].training,
                ]
            ],
        )

        self.assertEqual(form['type_financement'].value(), None)
        self.assertCountEqual(
            form.fields['type_financement'].choices, ALL_EMPTY_CHOICE + ChoixTypeFinancement.choices()
        )

        self.assertEqual(form['bourse_recherche'].value(), None)
        self.assertCountEqual(
            form.fields['bourse_recherche'].choices,
            [
                ALL_FEMININE_EMPTY_CHOICE[0],
                (self.scholarships[0].uuid, self.scholarships[0].short_name),
                (BourseRecherche.OTHER.name, BourseRecherche.OTHER.value),
            ],
        )

        self.assertEqual(form['mode_filtres_etats_checklist'].value(), ModeFiltrageChecklist.INCLUSION.name)

        self.assertEqual(form['filtres_etats_checklist'].value(), None)

        self.assertEqual(form['liste_travail'].value(), None)

    def test_form_initialization_for_a_central_manager_having_one_cdd(self):
        self.client.force_login(user=self.sic_user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(form.fields['cdds'].choices, [(ENTITY_CDE, ENTITY_CDE)])

        self.assertCountEqual(
            form.fields['commission_proximite'].choices,
            [
                ALL_FEMININE_EMPTY_CHOICE[0],
                ['{} / {}'.format(ENTITY_CDE, ENTITY_CLSM), ChoixCommissionProximiteCDEouCLSM.choices()],
            ],
        )

        # Check that some fields are hidden
        hidden_fields_names = [field.name for field in form.hidden_fields()]
        self.assertIn('cdds', hidden_fields_names)

    def test_form_initialization_for_a_central_manager_having_several_cdds(self):
        self.client.force_login(user=self.user_with_several_cdds)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertCountEqual(
            form.fields['cdds'].choices,
            [
                (ENTITY_CDE, ENTITY_CDE),
                (ENTITY_CDSS, ENTITY_CDSS),
                ('ABC', 'ABC'),
            ],
        )

        self.assertCountEqual(
            form.fields['commission_proximite'].choices,
            [
                ALL_FEMININE_EMPTY_CHOICE[0],
                ['{} / {}'.format(ENTITY_CDE, ENTITY_CLSM), ChoixCommissionProximiteCDEouCLSM.choices()],
                [ENTITY_CDSS, ChoixCommissionProximiteCDSS.choices()],
                [ENTITY_SCIENCES, ChoixSousDomaineSciences.choices()],
            ],
        )

        # Check that no field is hidden
        hidden_fields_names = [field.name for field in form.hidden_fields()]
        self.assertNotIn('cdds', hidden_fields_names)
        self.assertNotIn('commission_proximite', hidden_fields_names)

    def test_load_of_dynamic_choices(self):
        self.client.force_login(user=self.sic_user)

        data = {
            'nationalite': self.country.iso_code,
            'matricule_candidat': self.admissions[0].candidate.global_id,
            'matricule_promoteur': self.promoter.global_id,
        }
        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITHOUT_SEARCH):
            response = self.client.get(self.url, data)

            self.assertEqual(response.status_code, 200)

            form = response.context['form']

            self.assertEqual(form.fields['nationalite'].widget.choices, ((self.country.iso_code, self.country.name),))
            self.assertEqual(
                form.fields['matricule_candidat'].widget.choices,
                (
                    (
                        self.admissions[0].candidate.global_id,
                        '{}, {}'.format(
                            self.admissions[0].candidate.last_name, self.admissions[0].candidate.first_name
                        ),
                    ),
                ),
            )
            self.assertEqual(
                form.fields['matricule_promoteur'].widget.choices,
                ((self.promoter.global_id, '{}, {}'.format(self.promoter.last_name, self.promoter.first_name)),),
            )

        data = {
            'nationalite': 'UNKOWN',
            'matricule_candidat': '123456',
            'matricule_promoteur': '654321',
        }
        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITHOUT_SEARCH):
            response = self.client.get(self.url, data)

            self.assertEqual(response.status_code, 200)

            form = response.context['form']
            self.assertEqual(form.fields['nationalite'].widget.choices, [])
            self.assertEqual(form.fields['matricule_candidat'].widget.choices, [])
            self.assertEqual(form.fields['matricule_promoteur'].widget.choices, [])

    def test_get_with_invalid_dates(self):
        self.client.force_login(user=self.sic_user)

        error_message = gettext('The start date must be earlier than or the same as the end date.')

        # One date is specified
        response = self.client.get(
            self.url,
            {
                'date_soumission_debut': '2020-01-01',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            error_message,
            response.context['form'].errors.get(NON_FIELD_ERRORS, []),
        )

        # Two dates are specified and are valid
        response = self.client.get(
            self.url,
            {
                'date_soumission_debut': '2020-01-01',
                'date_soumission_fin': '2020-01-02',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            error_message,
            response.context['form'].errors.get(NON_FIELD_ERRORS, []),
        )

        # Two dates are specified and are invalid
        response = self.client.get(
            self.url,
            {
                'date_soumission_debut': '2020-01-02',
                'date_soumission_fin': '2020-01-01',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            error_message,
            response.context['form'].errors.get(NON_FIELD_ERRORS, []),
        )

    def assertPropositionList(self, response, propositions_references, ordered=False):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), len(propositions_references))
        {True: self.assertListEqual, False: self.assertCountEqual}[ordered](
            [proposition.numero_demande for proposition in response.context['object_list']],
            propositions_references,
        )

    def test_filter_by_academic_year(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[0],
                    self.admission_references[1],
                    self.admission_references[2],
                ],
            )

    def test_filter_by_reference(self):
        self.client.force_login(user=self.user_with_several_cdds)

        # Short reference
        data = {
            'annee_academique': '2021',
            'numero': str(self.admissions[0]),
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[0],
                ],
            )

        # Long reference
        data = {
            'annee_academique': '2021',
            'numero': self.admission_references[1],
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[1],
                ],
            )

    def test_filter_by_candidate(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'matricule_candidat': self.admissions[1].candidate.global_id,
        }

        # Known candidate
        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH + 1):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[1],
                ],
            )

        # Unknown candidate
        response = self.client.get(self.url, {'annee_academique': '2021', 'matricule_candidat': '0123456789'})
        self.assertPropositionList(response, [])

    def test_filter_by_country_of_citizenship(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'nationalite': BE_ISO_CODE,
        }

        # Known candidate
        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH + 1):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[0],
                ],
            )

        # Unknown country
        response = self.client.get(self.url, {'annee_academique': '2021', 'nationalite': 'WZ0'})
        self.assertPropositionList(response, [])

    def test_filter_by_status(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'etats': [
                ChoixStatutPropositionDoctorale.CONFIRMEE.name,
                ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
            ],
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[0],
                    self.admission_references[1],
                ],
            )

    def test_filter_by_type(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'type': ChoixTypeAdmission.PRE_ADMISSION.name,
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[0],
                ],
            )

    def test_filter_by_cdd(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'cdds': [ENTITY_CDE],
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH + 1):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[0],
                    self.admission_references[1],
                ],
            )

    def test_filter_by_proximity_commission(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'commission_proximite': ChoixSousDomaineSciences.BIOLOGY.name,
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[2],
                ],
            )

    def test_filter_by_training_acronym(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'sigles_formations': [
                self.admissions[2].training.acronym,
            ],
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[2],
                ],
            )

    def test_filter_by_promoter(self):
        self.client.force_login(user=self.program_manager_user)

        data = {
            'annee_academique': '2021',
            'matricule_promoteur': self.promoter.global_id,
        }

        response = self.client.get(self.url, data)

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH + 1):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[0],
                ],
            )

    def test_filter_by_financing_type(self):
        self.client.force_login(user=self.program_manager_user)

        data = {
            'annee_academique': '2021',
            'type_financement': ChoixTypeFinancement.WORK_CONTRACT.name,
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH + 1):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[0],
                ],
            )

    def test_filter_by_scholarship(self):
        self.client.force_login(user=self.user_with_several_cdds)

        # Known scholarship
        data = {
            'annee_academique': '2021',
            'bourse_recherche': self.scholarships[0].uuid,
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH + 1):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[2],
                ],
            )

        # Unknown scholarship
        data = {
            'annee_academique': '2021',
            'bourse_recherche': uuid.uuid4(),
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH + 1):
            response = self.client.get(self.url, data)

            self.assertPropositionList(response, [])

        # Other scholarship
        data = {
            'annee_academique': '2021',
            'bourse_recherche': BourseRecherche.OTHER.name,
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[1],
                    self.admission_references[2],
                ],
            )

    def test_filter_by_cotutelle(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'cotutelle': True,
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[2],
                ],
            )

        data = {
            'annee_academique': '2021',
            'cotutelle': False,
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[0],
                ],
            )

    def test_filter_by_submission_date(self):
        self.client.force_login(user=self.user_with_several_cdds)

        # With a start date
        data = {
            'annee_academique': '2021',
            'date_soumission_debut': '2021-01-02',
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[1],
                    self.admission_references[2],
                ],
            )

        # With an end date
        data = {
            'annee_academique': '2021',
            'date_soumission_fin': '2021-01-02',
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[0],
                    self.admission_references[1],
                ],
            )

        # With both dates
        data = {
            'annee_academique': '2021',
            'date_soumission_debut': '2021-01-02',
            'date_soumission_fin': '2021-01-02',
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertPropositionList(
                response,
                [
                    self.admission_references[1],
                ],
            )

    def test_returned_dto_in_french(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'numero': self.admission_references[1],
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertEqual(response.status_code, 200)

            results = response.context['object_list']

            self.assertEqual(len(results), 1)

            proposition = results[0]

            self.assertEqual(proposition.uuid, self.admissions[1].uuid)
            self.assertEqual(proposition.numero_demande, self.admission_references[1])
            self.assertEqual(proposition.etat_demande, self.admissions[1].status)
            self.assertEqual(proposition.nom_candidat, self.admissions[1].candidate.last_name)
            self.assertEqual(proposition.prenom_candidat, self.admissions[1].candidate.first_name)
            self.assertEqual(proposition.sigle_formation, self.admissions[1].training.acronym)
            self.assertEqual(proposition.code_formation, self.admissions[1].training.partial_acronym)
            self.assertEqual(proposition.intitule_formation, self.admissions[1].training.title)
            self.assertEqual(proposition.decision_fac, 'TODO')
            self.assertEqual(proposition.decision_sic, 'TODO')
            self.assertEqual(proposition.date_confirmation, self.admissions[1].submitted_at)
            self.assertEqual(proposition.derniere_modification_le, self.admissions[1].modified_at)
            self.assertEqual(proposition.type_admission, self.admissions[1].type)
            self.assertEqual(proposition.cotutelle, self.admissions[1].cotutelle)
            self.assertEqual(proposition.code_bourse, self.admissions[1].other_international_scholarship)
            self.assertEqual(
                proposition.code_pays_nationalite_candidat,
                self.admissions[1].candidate.country_of_citizenship.iso_code,
            )
            self.assertEqual(
                proposition.nom_pays_nationalite_candidat,
                self.admissions[1].candidate.country_of_citizenship.name,
            )
            self.assertEqual(proposition.prenom_auteur_derniere_modification, self.promoter.first_name)
            self.assertEqual(proposition.nom_auteur_derniere_modification, self.promoter.last_name)

    def test_returned_dto_in_english_with_existing_scholarship(self):
        self.client.force_login(user=self.program_manager_user)

        data = {
            'annee_academique': '2021',
            'numero': self.admission_references[2],
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertEqual(response.status_code, 200)

            results = response.context['object_list']

            self.assertEqual(len(results), 1)

            proposition = results[0]

            # English properties
            self.assertEqual(proposition.intitule_formation, self.admissions[2].training.title_english)
            self.assertEqual(
                proposition.nom_pays_nationalite_candidat,
                self.admissions[2].candidate.country_of_citizenship.name_en,
            )

            # Existing scholarship
            self.assertEqual(proposition.code_bourse, self.admissions[2].international_scholarship.short_name)

    def test_returned_dto_with_missing_data(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2022',
            'numero': self.admission_references[3],
        }

        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES_WITH_SEARCH):
            response = self.client.get(self.url, data)

            self.assertEqual(response.status_code, 200)

            results = response.context['object_list']

            self.assertEqual(len(results), 1)

            proposition = results[0]

            self.assertEqual(proposition.prenom_auteur_derniere_modification, '')
            self.assertEqual(proposition.nom_auteur_derniere_modification, '')
            self.assertEqual(proposition.code_pays_nationalite_candidat, '')
            self.assertEqual(proposition.nom_pays_nationalite_candidat, '')

    def test_htmx_form_errors(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'nationalite': 'FR',
            'cdds': 'unknown_cdd',
        }
        response = self.client.get(self.url, data, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Commissions doctorales - Sélectionnez un choix valide. unknown_cdd n’en fait pas partie.',
            [m.message for m in response.context['messages']],
        )

    def test_sort_results_by_reference(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'o': 'numero_demande',
        }

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[0],
                self.admission_references[1],
                self.admission_references[2],
            ],
            ordered=True,
        )

        data['o'] = '-' + data['o']

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[2],
                self.admission_references[1],
                self.admission_references[0],
            ],
            ordered=True,
        )

    def test_sort_results_by_candidate_name(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'o': 'nom_candidat',
        }

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[1],
                self.admission_references[0],
                self.admission_references[2],
            ],
            ordered=True,
        )

        data['o'] = '-' + data['o']

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[2],
                self.admission_references[0],
                self.admission_references[1],
            ],
            ordered=True,
        )

    def test_sort_results_by_country_of_citizenship(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'o': 'nationalite',
        }

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[0],
                self.admission_references[2],
                self.admission_references[1],
            ],
            ordered=True,
        )

        data['o'] = '-' + data['o']

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[1],
                self.admission_references[2],
                self.admission_references[0],
            ],
            ordered=True,
        )

    def test_sort_results_by_scholarship_code(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'o': 'code_bourse',
        }

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[0],
                self.admission_references[2],
                self.admission_references[1],
            ],
            ordered=True,
        )

        data['o'] = '-' + data['o']

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[1],
                self.admission_references[2],
                self.admission_references[0],
            ],
            ordered=True,
        )

    def test_sort_results_by_training(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'o': 'formation',
        }

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[2],
                self.admission_references[1],
                self.admission_references[0],
            ],
            ordered=True,
        )

        data['o'] = '-' + data['o']

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[0],
                self.admission_references[1],
                self.admission_references[2],
            ],
            ordered=True,
        )

    def test_sort_results_by_admission_status(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'o': 'etat_demande',
        }

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[1],
                self.admission_references[0],
                self.admission_references[2],
            ],
            ordered=True,
        )

        data['o'] = '-' + data['o']

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[2],
                self.admission_references[0],
                self.admission_references[1],
            ],
            ordered=True,
        )

    def test_sort_results_by_submission_date(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'o': 'date_confirmation',
        }

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[0],
                self.admission_references[1],
                self.admission_references[2],
            ],
            ordered=True,
        )

        data['o'] = '-' + data['o']

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[2],
                self.admission_references[1],
                self.admission_references[0],
            ],
            ordered=True,
        )

    def test_sort_results_by_last_modification_date(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'o': 'derniere_modification',
        }

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[1],
                self.admission_references[2],
                self.admission_references[0],
            ],
            ordered=True,
        )

        data['o'] = '-' + data['o']

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[0],
                self.admission_references[2],
                self.admission_references[1],
            ],
            ordered=True,
        )

    def test_sort_results_by_last_modification_author(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'o': 'derniere_modification_par',
        }

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[0],
                self.admission_references[1],
                self.admission_references[2],
            ],
            ordered=True,
        )

        data['o'] = '-' + data['o']

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[2],
                self.admission_references[1],
                self.admission_references[0],
            ],
            ordered=True,
        )

    def test_sort_results_by_admission_type(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'o': 'pre_admission',
        }

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[0],
                self.admission_references[1],
                self.admission_references[2],
            ],
        )

        self.assertEqual(self.admission_references[0], response.context['object_list'][2].numero_demande)

        data['o'] = '-' + data['o']

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[2],
                self.admission_references[1],
                self.admission_references[0],
            ],
        )

        self.assertEqual(self.admission_references[0], response.context['object_list'][0].numero_demande)

    def test_sort_results_by_cotutelle(self):
        self.client.force_login(user=self.user_with_several_cdds)

        data = {
            'annee_academique': '2021',
            'o': 'cotutelle',
        }

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[0],
                self.admission_references[2],
                self.admission_references[1],
            ],
            ordered=True,
        )

        data['o'] = '-' + data['o']

        response = self.client.get(self.url, data)

        self.assertPropositionList(
            response,
            [
                self.admission_references[1],
                self.admission_references[2],
                self.admission_references[0],
            ],
            ordered=True,
        )
