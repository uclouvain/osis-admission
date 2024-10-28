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
import random

from django.db.models import QuerySet
from django.shortcuts import resolve_url
from django.test import TestCase, Client

from admission.contrib.models import AdmissionFormItem, AdmissionFormItemInstantiation
from admission.ddd.admission.enums import (
    CritereItemFormulaireNationaliteCandidat,
    CritereItemFormulaireNationaliteDiplome,
    CritereItemFormulaireLangueEtudes,
    CritereItemFormulaireVIP,
)
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from admission.management.commands.initialize_specific_questions import SpecificQuestionToInit
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, Master120TrainingFactory
from base.tests.factories.user import SuperUserFactory, UserFactory


class InitializeSpecificQuestionsFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_year = AcademicYearFactory(year=2023)

        acronyms = {
            'EDPH2M',
            'KINE2M1',
            'MOTR2M',
            'GEHM2M',
            'GEHM2M1',
            'GEHC2M',
            'GEHC2M1',
            'FEHC2M',
            'COMU2M1',
            'CORP2M',
            'EJL2M',
            'STIC2M',
            'OPES2M',
            'ENVI2MC',
            'ENVI2MC',
            'COMM2M',
            'PRIM2M',
            'ADPM2M',
            'COMM2M1',
            'SPOM2M1',
            'COHM2M',
            'COAM2M',
            'APHM2M',
            'SPHM2M',
            'SPHM2M1',
            'ARCB2M',
            'ARCT2M',
            'ARCH2M',
            'SINF2M',
            'NRGY2M',
            'MAP2M',
            'MECA2M',
            'GCE2M',
            'INFO2M',
            'GBIO2M',
            'ELME2M',
            'DATI2M',
            'DATE2M',
            'SINF2M1',
            'ECON2M1',
            'ECON2M',
            'ETRI2M',
            'GESA2M',
            'GESM2M',
            'GEST2M',
            'GEST2M1',
            'INGE2M',
            'INGM2M',
            'GESA2M',
            'GESM2M',
            'GEST2M',
            'INGE2M',
            'INGM2M',
            'EBEP2MC',
            'EDUC2MC',
            'GERM2M',
            'MD1BA',
            'DENT1BA',
            'MD2M',
            'DENT2M',
            'DEGE2MC',
            'ORTD2MC',
            'PARO2MC',
            'SBIM2M',
            'SBIM2M',
            'FARM2M',
            'FARM2M',
            'FSA1BA',
            'ARCH1BA',
            'KINE1BA',
            'LOGO1BA',
            'VETE1BA',
        }

        for group_type in AnneeInscriptionFormationTranslator.ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE.keys():
            EducationGroupTypeFactory(name=group_type)

        cls.education_groups = {}

        masters_in_programs = [
            TrainingType.MASTER_MA_120.name,
            TrainingType.MASTER_MD_120.name,
            TrainingType.MASTER_MS_120.name,
            TrainingType.MASTER_MS_180_240.name,
        ]

        for acronym in acronyms:
            program_acronym = acronym.endswith('2M')
            final_acronym = f'{acronym}D' if program_acronym else acronym
            cls.education_groups[final_acronym] = (
                Master120TrainingFactory(
                    academic_year=academic_year,
                    acronym=final_acronym,
                    education_group_type__name=masters_in_programs[random.randint(0, 3)],
                    enrollment_enabled=True,
                )
                if program_acronym
                else EducationGroupYearFactory(
                    academic_year=academic_year,
                    acronym=final_acronym,
                    education_group_type__name=TrainingType.MASTER_M1.name,
                    enrollment_enabled=True,
                )
            ).education_group

        AdmissionFormItemInstantiation.objects.all().delete()
        AdmissionFormItem.objects.all().delete()

        main_client = Client()
        cls.super_user = SuperUserFactory()

        main_client.force_login(user=cls.super_user)
        cls.url = resolve_url('admission:admin:initialize-specific-questions')
        cls.response = main_client.post(
            cls.url,
            data={
                'academic_year': academic_year.pk,
            },
        )

    def test_get_page_is_forbidden_if_no_permission(self):
        self.client.force_login(user=UserFactory())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_post_form_is_invalid_if_no_data(self):
        self.client.force_login(user=self.super_user)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('academic_year', []))

    def test_motivation_letter(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.MOTIVATION_LETTER.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        education_group_types = [
            TrainingType.MASTER_MC.name,
            TrainingType.MASTER_MA_120.name,
            TrainingType.MASTER_MD_120.name,
            TrainingType.MASTER_MS_120.name,
            TrainingType.MASTER_MS_180_240.name,
            TrainingType.MASTER_M1.name,
            TrainingType.FORMATION_PHD.name,
            TrainingType.CAPAES.name,
            TrainingType.CERTIFICATE.name,
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group_type')

        self.assertEqual(len(form_item_instantiations), len(education_group_types))

        for education_group_type in education_group_types:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group_type.name == education_group_type), None
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 0)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.TOUS.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.TOUS.name)

    def test_language_proficiency_exam(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.FRENCH_LANGUAGE_PROFICIENCY_EXAM.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        education_group_types = [
            TrainingType.MASTER_MD_120.name,
            TrainingType.AGGREGATION.name,
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group_type')

        self.assertEqual(len(form_item_instantiations), len(education_group_types))

        for education_group_type in education_group_types:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group_type.name == education_group_type), None
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 0)
            self.assertFalse(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.NON_BELGE.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.TOUS.name)

    def test_b2_french_level(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.B2_FRENCH_LEVEL.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'EDPH2MD',
            'KINE2M1',
            'MOTR2MD',
            'GEHM2MD',
            'GEHM2M1',
            'GEHC2MD',
            'GEHC2M1',
            'FEHC2MD',
            'FARM2MD',
            'SBIM2MD',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in [
            'EDPH2MD',
            'KINE2M1',
            'MOTR2MD',
        ]:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.NON_UE.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.TOUS.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.TOUS.name)

        for acronym in [
            'GEHM2MD',
            'GEHM2M1',
            'GEHC2MD',
            'GEHC2M1',
            'FEHC2MD',
        ]:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.NON_UE.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.TOUS.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_FR.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.NON_VIP.name)

        for acronym in [
            'FARM2MD',
            'SBIM2MD',
        ]:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.NON_BELGE.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_FR.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.NON_VIP.name)

    def test_b1_french_level(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.B1_FRENCH_LEVEL.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'COMM2MD',
            'PRIM2MD',
            'ADPM2MD',
            'COMM2M1',
            'SPOM2M1',
            'COHM2MD',
            'COAM2MD',
            'APHM2MD',
            'SPHM2MD',
            'SPHM2M1',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in acronyms:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.NON_UE.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.TOUS.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_FR.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.NON_VIP.name)

    def test_c1_french_level(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.C1_FRENCH_LEVEL.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'COMU2M1',
            'CORP2MD',
            'EJL2MD',
            'STIC2MD',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in acronyms:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.NON_UE.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.TOUS.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.NON_VIP.name)

    def test_lsm_english_level(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.LSM_ENGLISH_LEVEL.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'GESA2MD',
            'GESM2MD',
            'GEST2MD',
            'GEST2M1',
            'INGE2MD',
            'INGM2MD',
            'EBEP2MC',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in [
            'GESA2MD',
            'GESM2MD',
            'GEST2MD',
            'GEST2M1',
            'INGE2MD',
            'INGM2MD',
        ]:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.NON_BELGE.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.NON_VIP.name)

        for acronym in [
            'EBEP2MC',
        ]:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.NON_BELGE.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_EN.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.NON_VIP.name)

    def test_econ_english_level(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.ECON_ENGLISH_LEVEL.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'ECON2M1',
            'ECON2MD',
            'ETRI2MD',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in acronyms:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.NON_BELGE.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_EN.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.NON_VIP.name)

    def test_epl_english_level(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.EPL_ENGLISH_LEVEL.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'SINF2MD',
            'NRGY2MD',
            'MAP2MD',
            'MECA2MD',
            'GCE2MD',
            'INFO2MD',
            'GBIO2MD',
            'ELME2MD',
            'DATI2MD',
            'DATE2MD',
            'SINF2M1',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in acronyms:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.NON_BELGE.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.NON_VIP.name)

    def test_b2_english_level(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.B2_ENGLISH_LEVEL.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'SBIM2MD',
            'FARM2MD',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in acronyms:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 2)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.NON_BELGE.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_EN.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.NON_VIP.name)

    def test_belgian_resident_message(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.BELGIAN_RESIDENT_MESSAGE.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'OPES2MD',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in acronyms:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.TOUS.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.TOUS.name)

    def test_dissertation_summary(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.DISSERTATION_SUMMARY.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'ENVI2MC',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in acronyms:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.TOUS.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.NON_VIP.name)

    def test_dissertation_date(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.DISSERTATION_DATE.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'ENVI2MC',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in acronyms:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 2)
            self.assertFalse(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.TOUS.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.NON_VIP.name)

    def test_portfolio(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.PORTFOLIO.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'ARCB2MD',
            'ARCT2MD',
            'ARCH2MD',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in acronyms:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.TOUS.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.TOUS.name)

    def test_gmat(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.GMAT.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'GESA2MD',
            'GESM2MD',
            'GEST2MD',
            'INGE2MD',
            'INGM2MD',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in acronyms:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 2)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.NON_BELGE.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.NON_VIP.name)

    def test_school_commitment(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.SCHOOL_COMMITMENT.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'EDUC2MC',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in acronyms:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertFalse(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.TOUS.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.TOUS.name)

    def test_germanic_language_choice(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.GERMANIC_LANGUAGE_CHOICE.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'GERM2MD',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in acronyms:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.TOUS.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.TOUS.name)

    def test_medical_entrance_proof(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.MEDICAL_ENTRANCE_PROOF.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'MD1BA',
            'DENT1BA',
            'MD2MD',
            'DENT2MD',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in [
            'MD1BA',
            'DENT1BA',
        ]:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertFalse(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.TOUS.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.TOUS.name)

        for acronym in [
            'MD2MD',
            'DENT2MD',
        ]:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertFalse(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.NON_BELGE.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.TOUS.name)

    def test_dentristry_specialization_proof(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.DENTISTRY_SPECIALIZATION_PROOF.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'DEGE2MC',
            'ORTD2MC',
            'PARO2MC',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in acronyms:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.TOUS.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.TOUS.name)

    def test_engineering_entrance_proof(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.ENGINEERING_ENTRANCE_EXAM_PROOF.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'FSA1BA',
            'ARCH1BA',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in acronyms:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.TOUS.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.TOUS.name)

    def test_resident_student_form(self):
        # Check that the question has been created
        form_item: AdmissionFormItem = AdmissionFormItem.objects.filter(
            internal_label=SpecificQuestionToInit.RESIDENT_STUDENT_FORM.value,
        ).first()

        self.assertIsNotNone(form_item)

        # Check that the question has been instantiated
        acronyms = [
            'KINE1BA',
            'LOGO1BA',
            'VETE1BA',
        ]

        form_item_instantiations: QuerySet[
            AdmissionFormItemInstantiation
        ] = AdmissionFormItemInstantiation.objects.filter(form_item=form_item).select_related('education_group')

        self.assertEqual(len(form_item_instantiations), len(acronyms))

        for acronym in acronyms:
            instantiation = next(
                (i for i in form_item_instantiations if i.education_group == self.education_groups[acronym]),
                None,
            )
            self.assertIsNotNone(instantiation)
            self.assertEqual(instantiation.weight, 1)
            self.assertTrue(instantiation.required)
            self.assertEqual(instantiation.candidate_nationality, CritereItemFormulaireNationaliteCandidat.TOUS.name)
            self.assertEqual(instantiation.diploma_nationality, CritereItemFormulaireNationaliteDiplome.TOUS.name)
            self.assertEqual(instantiation.study_language, CritereItemFormulaireLangueEtudes.TOUS.name)
            self.assertEqual(instantiation.vip_candidate, CritereItemFormulaireVIP.TOUS.name)
