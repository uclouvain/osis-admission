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
from django.test import TestCase

from admission.ddd.projet_doctoral.preparation.domain.model._enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
)
from admission.ddd.projet_doctoral.preparation.domain.model.doctorat import (
    ENTITY_CDE,
    ENTITY_CDSS,
    SIGLE_SCIENCES,
    ENTITY_CLSM,
)
from admission.forms import EMPTY_CHOICE
from admission.forms.doctorate.cdd.filter import FilterForm
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import CddManagerFactory
from base.templatetags.pagination import PAGINATOR_SIZE_LIST
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class FilterTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        cls.first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=cls.first_doctoral_commission, acronym=ENTITY_CDE)
        cls.first_entity_admissions = [
            DoctorateAdmissionFactory(
                doctorate__management_entity=cls.first_doctoral_commission,
                doctorate__academic_year=academic_years[0],
            ),
            DoctorateAdmissionFactory(
                doctorate__management_entity=cls.first_doctoral_commission,
                doctorate__academic_year=academic_years[0],
            ),
        ]

        # Second entity
        cls.second_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=cls.second_doctoral_commission, acronym=ENTITY_CDSS)

        cls.second_entity_admissions = [
            DoctorateAdmissionFactory(
                doctorate__management_entity=cls.second_doctoral_commission,
                doctorate__academic_year=academic_years[1],
            ),
            DoctorateAdmissionFactory(
                doctorate__management_entity=cls.second_doctoral_commission,
                doctorate__academic_year=academic_years[1],
            ),
        ]

        # Third entity
        cls.third_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=cls.third_doctoral_commission)
        cls.third_entity_admissions = [
            DoctorateAdmissionFactory(
                doctorate__management_entity=cls.second_doctoral_commission,
                doctorate__academic_year=academic_years[1],
                doctorate__acronym=SIGLE_SCIENCES,
            ),
        ]

        # User with several cdds
        person_with_several_cdds = CddManagerFactory(entity=cls.first_doctoral_commission).person
        cls.user_with_several_cdds = person_with_several_cdds.user

        for entity in [cls.second_doctoral_commission, cls.third_doctoral_commission]:
            manager_factory = CddManagerFactory(entity=entity)
            manager_factory.person = person_with_several_cdds
            manager_factory.save()

        # User with one cdd
        cls.user_with_one_cdd = CddManagerFactory(entity=cls.first_doctoral_commission).person.user

        # User without cdd
        cls.user_without_cdd = PersonFactory().user

    def test_form_initialization_with_user_without_cdd(self):
        form = FilterForm(user=self.user_without_cdd)

        # Check initial values of dynamic fields
        self.assertEqual(form.fields['cdds'].choices, [])
        self.assertEqual(form.fields['cdds'].initial, [])

        self.assertEqual(form.fields['sigles_formations'].choices, [])

        self.assertEqual(form.fields['commission_proximite'].choices, [EMPTY_CHOICE[0]])

        self.assertEqual(
            form.fields['annee_academique'].choices,
            [EMPTY_CHOICE[0]]
            + [
                (2022, '2022-23'),
                (2021, '2021-22'),
            ],
        )

        # Check some fields are hidden
        hidden_fields_names = [field.name for field in form.hidden_fields()]
        self.assertIn('cdds', hidden_fields_names)

    def test_form_initialization_with_user_with_one_cdd(self):
        form = FilterForm(user=self.user_with_one_cdd)

        # Check initial values of dynamic fields
        self.assertEqual(
            form.fields['cdds'].choices,
            [
                (ENTITY_CDE, ENTITY_CDE),
            ],
        )
        self.assertEqual(form.fields['cdds'].initial, [ENTITY_CDE])

        for admission in self.first_entity_admissions:
            self.assertIn(
                (admission.doctorate.acronym, '{} - {}'.format(admission.doctorate.acronym, admission.doctorate.title)),
                form.fields['sigles_formations'].choices,
            )

        self.assertEqual(
            form.fields['commission_proximite'].choices,
            [EMPTY_CHOICE[0], ['{} / {}'.format(ENTITY_CDE, ENTITY_CLSM), ChoixCommissionProximiteCDEouCLSM.choices()]],
        )

        # Check some fields are hidden
        hidden_fields_names = [field.name for field in form.hidden_fields()]
        self.assertIn('cdds', hidden_fields_names)

    def test_form_initialization_with_user_with_several_cdds(self):
        form = FilterForm(user=self.user_with_several_cdds)

        # Check initial values of dynamic fields
        for cdd in [ENTITY_CDE, ENTITY_CDSS]:
            self.assertIn(
                (cdd, cdd),
                form.fields['cdds'].choices,
            )
            self.assertIn(
                cdd,
                form.fields['cdds'].initial,
            )

        for admission in self.first_entity_admissions + self.second_entity_admissions + self.third_entity_admissions:
            self.assertIn(
                (admission.doctorate.acronym, '{} - {}'.format(admission.doctorate.acronym, admission.doctorate.title)),
                form.fields['sigles_formations'].choices,
            )

        self.assertIn(
            ['{} / {}'.format(ENTITY_CDE, ENTITY_CLSM), ChoixCommissionProximiteCDEouCLSM.choices()],
            form.fields['commission_proximite'].choices,
        )
        self.assertIn(
            [ENTITY_CDSS, ChoixCommissionProximiteCDSS.choices()],
            form.fields['commission_proximite'].choices,
        )
        self.assertIn(
            [SIGLE_SCIENCES, ChoixSousDomaineSciences.choices()],
            form.fields['commission_proximite'].choices,
        )

        # Check no fields is hidden
        self.assertEqual(len(form.hidden_fields()), 0)

    def test_form_validation_with_no_data(self):
        form = FilterForm(user=self.user_with_one_cdd, data={})

        self.assertFalse(form.is_valid())

        # Mandatory fields
        self.assertIn('cdds', form.errors)
        self.assertIn('page_size', form.errors)

    def test_form_validation_with_valid_data(self):
        form = FilterForm(
            user=self.user_with_one_cdd,
            data={
                'page_size': PAGINATOR_SIZE_LIST[0],
                'cdds': [ENTITY_CDE],
                'numero': '20-300000',
            },
        )
        self.assertTrue(form.is_valid())

    def test_form_validation_with_invalid_data(self):
        # Check form
        default_params = {
            'page_size': PAGINATOR_SIZE_LIST[0],
            'cdds': [ENTITY_CDE],
        }
        form = FilterForm(
            user=self.user_with_one_cdd,
            data={
                'numero': '320-300000',
                **default_params,
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn('numero', form.errors)
