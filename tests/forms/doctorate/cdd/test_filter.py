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

from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import (
    ENTITY_CDE,
    ENTITY_CDSS,
    ENTITY_CLSM,
    SIGLE_SCIENCES,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
)
from admission.forms import EMPTY_CHOICE
from admission.forms.doctorate.cdd.filter import DoctorateListFilterForm
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import CentralManagerRoleFactory
from base.models.enums.entity_type import EntityType
from base.templatetags.pagination import PAGINATOR_SIZE_LIST
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from reference.tests.factories.country import CountryFactory


class FilterTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(
            entity=first_doctoral_commission,
            acronym=ENTITY_CDE,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
        )
        cls.first_entity_admissions = [
            DoctorateAdmissionFactory(
                training__management_entity=first_doctoral_commission,
                training__academic_year=academic_years[0],
            ),
            DoctorateAdmissionFactory(
                training__management_entity=first_doctoral_commission,
                training__academic_year=academic_years[0],
            ),
        ]

        # Second entity
        second_doctoral_commission = EntityFactory()
        EntityVersionFactory(
            entity=second_doctoral_commission,
            acronym=ENTITY_CDSS,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
        )

        cls.second_entity_admissions = [
            DoctorateAdmissionFactory(
                training__management_entity=second_doctoral_commission,
                training__academic_year=academic_years[1],
            ),
            DoctorateAdmissionFactory(
                training__management_entity=second_doctoral_commission,
                training__academic_year=academic_years[1],
            ),
        ]

        # Third entity
        third_doctoral_commission = EntityFactory()
        EntityVersionFactory(
            entity=third_doctoral_commission,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='ABC',
        )
        cls.third_entity_admissions = [
            DoctorateAdmissionFactory(
                training__management_entity=second_doctoral_commission,
                training__academic_year=academic_years[1],
                training__acronym=SIGLE_SCIENCES,
            ),
        ]

        cls.all_admissions = cls.first_entity_admissions + cls.second_entity_admissions + cls.third_entity_admissions
        cls.all_commissions = [
            EMPTY_CHOICE[0],
            ['{} / {}'.format(ENTITY_CDE, ENTITY_CLSM), ChoixCommissionProximiteCDEouCLSM.choices()],
            [ENTITY_CDSS, ChoixCommissionProximiteCDSS.choices()],
            [SIGLE_SCIENCES, ChoixSousDomaineSciences.choices()],
        ]

        # Other entity
        EntityVersionFactory(
            entity=EntityFactory(),
            acronym='DEF',
            entity_type=EntityType.LOGISTICS_ENTITY.name,
        )

        # Countries
        cls.country = CountryFactory()

        # User with several cdds
        person_with_several_cdds = CentralManagerRoleFactory(entity=first_doctoral_commission).person
        cls.user_with_several_cdds = person_with_several_cdds.user

        for entity in [second_doctoral_commission, third_doctoral_commission]:
            manager_factory = CentralManagerRoleFactory(entity=entity)
            manager_factory.person = person_with_several_cdds
            manager_factory.save()

        # User with one cdd
        cls.user_with_one_cdd = CentralManagerRoleFactory(entity=first_doctoral_commission).person.user

        # User without cdd
        cls.user_without_cdd = PersonFactory().user

        # Other users
        cls.candidate = PersonFactory()
        cls.promoter = PersonFactory()

    def test_form_initialization_with_user_without_cdd(self):
        form = DoctorateListFilterForm(user=self.user_without_cdd)

        # Check initial values of dynamic fields
        self.assertCountEqual(
            form.fields['cdds'].choices,
            [
                (ENTITY_CDE, ENTITY_CDE),
                (ENTITY_CDSS, ENTITY_CDSS),
                ('ABC', 'ABC'),
            ],
        )
        for admission in self.all_admissions:
            self.assertIn(
                (admission.doctorate.acronym, '{} - {}'.format(admission.doctorate.acronym, admission.doctorate.title)),
                form.fields['sigles_formations'].choices,
            )

        self.assertEqual(form.fields['commission_proximite'].choices, self.all_commissions)

        self.assertEqual(
            form.fields['annee_academique'].choices,
            [EMPTY_CHOICE[0]]
            + [
                (2022, '2022-23'),
                (2021, '2021-22'),
            ],
        )

    def test_form_initialization_with_user_with_one_cdd(self):
        form = DoctorateListFilterForm(user=self.user_with_one_cdd)

        # Check initial values of dynamic fields
        self.assertEqual(
            form.fields['cdds'].choices,
            [
                (ENTITY_CDE, ENTITY_CDE),
            ],
        )

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
        form = DoctorateListFilterForm(user=self.user_with_several_cdds)

        # Check initial values of dynamic fields
        for cdd in [ENTITY_CDE, ENTITY_CDSS]:
            self.assertIn(
                (cdd, cdd),
                form.fields['cdds'].choices,
            )

        for admission in self.all_admissions:
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
        form = DoctorateListFilterForm(user=self.user_with_one_cdd, data={})

        self.assertTrue(form.is_valid())

    def test_form_validation_with_valid_data(self):
        form = DoctorateListFilterForm(
            user=self.user_with_one_cdd,
            data={
                'taille_page': PAGINATOR_SIZE_LIST[0],
                'cdds': [ENTITY_CDE],
                'numero': '0000.0000',
            },
        )
        self.assertTrue(form.is_valid())

    def test_form_validation_with_invalid_data(self):
        # Check form
        default_params = {
            'taille_page': PAGINATOR_SIZE_LIST[0],
            'cdds': [ENTITY_CDE],
        }
        form = DoctorateListFilterForm(
            user=self.user_with_one_cdd,
            data={
                'numero': '320-300000',
                **default_params,
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn('numero', form.errors)

    def test_form_validation_with_valid_cached_data(self):
        form = DoctorateListFilterForm(
            user=self.user_with_one_cdd,
            data={
                'taille_page': PAGINATOR_SIZE_LIST[0],
                'cdds': [ENTITY_CDE],
                'numero': '0000.0000',
                'nationalite': self.country.iso_code,
                'matricule_candidat': self.candidate.global_id,
                'matricule_promoteur': self.promoter.global_id,
            },
            load_labels=True,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['nationalite'].widget.choices, ((self.country.iso_code, self.country.name),))
        self.assertEqual(
            form.fields['matricule_candidat'].widget.choices,
            ((self.candidate.global_id, '{}, {}'.format(self.candidate.last_name, self.candidate.first_name)),),
        )
        self.assertEqual(
            form.fields['matricule_promoteur'].widget.choices,
            ((self.promoter.global_id, '{}, {}'.format(self.promoter.last_name, self.promoter.first_name)),),
        )

    def test_form_validation_with_invalid_cached_data(self):
        form = DoctorateListFilterForm(
            user=self.user_with_one_cdd,
            data={
                'taille_page': PAGINATOR_SIZE_LIST[0],
                'cdds': [ENTITY_CDE],
                'numero': '0000.0000',
                'nationalite': 'FR',
                'matricule_candidat': '123456',
                'matricule_promoteur': '654321',
            },
            load_labels=True,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['nationalite'].widget.choices, [])
        self.assertEqual(form.fields['matricule_candidat'].widget.choices, [])
        self.assertEqual(form.fields['matricule_promoteur'].widget.choices, [])

    def test_form_validation_with_no_autocomplete_cached_data(self):
        form = DoctorateListFilterForm(
            user=self.user_with_one_cdd,
            data={
                'taille_page': PAGINATOR_SIZE_LIST[0],
                'cdds': [ENTITY_CDE],
                'numero': '0000.0001',
            },
            load_labels=True,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.fields['nationalite'].widget.choices, [])
        self.assertEqual(form.fields['matricule_candidat'].widget.choices, [])
        self.assertEqual(form.fields['matricule_promoteur'].widget.choices, [])
