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

from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase

from admission.constants import ORDERED_CAMPUSES_UUIDS
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import (
    ENTITY_CDE,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    DispenseOuDroitsMajores,
    DroitsInscriptionMontant,
)
from admission.ddd.admission.enums.emplacement_document import (
    DocumentsCurriculum,
    DocumentsIdentification,
    StatutReclamationEmplacementDocument,
)
from admission.models import DoctorateAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.curriculum import (
    AdmissionEducationalValuatedExperiencesFactory,
    AdmissionProfessionalValuatedExperiencesFactory,
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
    ProfessionalExperienceFactory,
)
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.faculty_decision import DoctorateRefusalReasonFactory
from admission.tests.factories.person import CompletePersonFactory
from admission.tests.factories.roles import (
    ProgramManagerRoleFactory,
    SicManagementRoleFactory,
)
from admission.tests.views.doctorate.checklist.sic_decision.base import SicPatchMixin
from base.models.enums.organization_type import MAIN
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from osis_profile.models.enums.curriculum import (
    CURRICULUM_ACTIVITY_LABEL,
    ActivityType,
    TranscriptType,
)
from reference.tests.factories.language import LanguageFactory


class SicDecisionPdfPreviewViewTestCase(SicPatchMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.first_doctoral_commission = EntityWithVersionFactory(version__acronym=ENTITY_CDE)
        EntityVersionFactory(entity=cls.first_doctoral_commission)

        cls.training = DoctorateFactory(
            management_entity=cls.first_doctoral_commission,
            academic_year=cls.academic_years[0],
            enrollment_campus__uuid=ORDERED_CAMPUSES_UUIDS['LOUVAIN_LA_NEUVE_UUID'],
            enrollment_campus__organization__type=MAIN,
        )

        cls.sic_manager_user = SicManagementRoleFactory(entity=cls.first_doctoral_commission).person.user
        cls.fac_manager_user = ProgramManagerRoleFactory(education_group=cls.training.education_group).person.user
        cls.default_headers = {'HTTP_HX-Request': 'true'}
        cls.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training=cls.training,
            submitted=True,
            candidate=CompletePersonFactory(language=settings.LANGUAGE_CODE_FR),
            status=ChoixStatutPropositionDoctorale.ATTENTE_VALIDATION_DIRECTION.name,
            with_prerequisite_courses=False,
            annual_program_contact_person_name='foo',
            annual_program_contact_person_email='bar@example.org',
            tuition_fees_amount=DroitsInscriptionMontant.INSCRIPTION_REGULIERE.name,
            tuition_fees_dispensation=DispenseOuDroitsMajores.NON_CONCERNE.name,
            must_report_to_sic=False,
            communication_to_the_candidate='',
        )
        cls.admission.refusal_reasons.add(DoctorateRefusalReasonFactory())
        document_params = {
            'automatically_required': False,
            'last_action_at': '2023-01-01T00:00:00',
            'last_actor': '0123456',
            'reason': 'My reason',
            'requested_at': '',
            'status': 'A_RECLAMER',
            'type': 'NON_LIBRE',
            'request_status': StatutReclamationEmplacementDocument.ULTERIEUREMENT_NON_BLOQUANT.name,
        }

        new_educational_experience = EducationalExperienceFactory(
            person=cls.admission.candidate,
            transcript_type=TranscriptType.ONE_A_YEAR.name,
            obtained_diploma=True,
            linguistic_regime=LanguageFactory(code='GK', name='Greek'),
        )

        new_educational_experience_year = EducationalExperienceYearFactory(
            educational_experience=new_educational_experience,
            academic_year__year=2023,
        )

        new_professional_experience = ProfessionalExperienceFactory(
            person=cls.admission.candidate,
            start_date=datetime.date(2023, 1, 1),
            end_date=datetime.date(2023, 3, 31),
        )

        new_custom_professional_experience = ProfessionalExperienceFactory(
            person=cls.admission.candidate,
            start_date=datetime.date(2024, 1, 1),
            end_date=datetime.date(2024, 1, 31),
            type=ActivityType.OTHER.name,
            activity='My custom activity',
        )

        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=cls.admission,
            educationalexperience=new_educational_experience,
        )

        for experience in [new_professional_experience, new_custom_professional_experience]:
            AdmissionProfessionalValuatedExperiencesFactory(
                baseadmission=cls.admission,
                professionalexperience=experience,
            )

        cls.admission.requested_documents = {
            'CURRICULUM.CURRICULUM': document_params,
            'IDENTIFICATION.CARTE_IDENTITE': document_params,
            f'CURRICULUM.{new_educational_experience.uuid}.{new_educational_experience_year.academic_year.year}.'
            f'RELEVE_NOTES_ANNUEL': document_params,
            f'CURRICULUM.{new_educational_experience.uuid}.{new_educational_experience_year.academic_year.year}.'
            f'TRADUCTION_RELEVE_NOTES_ANNUEL': document_params,
            f'CURRICULUM.{new_educational_experience.uuid}.DIPLOME': document_params,
            f'CURRICULUM.{new_professional_experience.uuid}.CERTIFICAT_EXPERIENCE': document_params,
            f'CURRICULUM.{new_custom_professional_experience.uuid}.CERTIFICAT_EXPERIENCE': document_params,
        }

        cls.admission.save(update_fields=['requested_documents'])

        cls.url = resolve_url(
            'admission:doctorate:sic-decision-pdf-preview',
            uuid=cls.admission.uuid,
            pdf='accord',
        )

        cls.refusal_url = resolve_url(
            'admission:doctorate:sic-decision-pdf-preview',
            uuid=cls.admission.uuid,
            pdf='refus',
        )

    def test_pdf_preview_is_forbidden_with_fac_user(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 403)

    def test_refusal_pdf_preview(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.refusal_url, **self.default_headers)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'http://dummyurlfile/a-token')

        self.get_pdf_from_template_patcher.assert_called_once()

        # Check the documents names
        call_args = self.get_pdf_from_template_patcher.call_args_list[0]
        self.assertEqual(call_args[0][0], 'admission/exports/sic_refusal_certificate.html')

    def test_pdf_preview(self):
        self.client.force_login(user=self.sic_manager_user)

        response = self.client.get(self.url, **self.default_headers)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'http://dummyurlfile/a-token')

        self.get_pdf_from_template_patcher.assert_called_once()

        # Check the documents names
        call_args = self.get_pdf_from_template_patcher.call_args_list[0]
        self.assertIn('documents_names', call_args[0][2])

        documents_names = call_args[0][2]['documents_names']

        # By default, we only display the documents names
        self.assertIn(f"{DocumentsCurriculum['CURRICULUM']}. My reason", documents_names)
        self.assertIn(f"{DocumentsIdentification['CARTE_IDENTITE']}. My reason", documents_names)

        # For the curriculum experiences, we display the names of the experiences before the documents names
        self.assertIn(
            f"{CURRICULUM_ACTIVITY_LABEL[ActivityType.WORK.name]} : 01/2023-03/2023. My reason",
            documents_names,
        )

        self.assertIn(
            f"{CURRICULUM_ACTIVITY_LABEL[ActivityType.OTHER.name]} : My custom activity 01/2024. My reason",
            documents_names,
        )

        self.assertIn(
            f"{DocumentsCurriculum['RELEVE_NOTES_ANNUEL']} 2023-2024 : Computer science. My reason",
            documents_names,
        )

        self.assertIn(
            f"{DocumentsCurriculum['TRADUCTION_RELEVE_NOTES_ANNUEL']} 2023-2024 : Computer science. My reason",
            documents_names,
        )

        self.assertIn(
            f"{DocumentsCurriculum['DIPLOME']} : Computer science. My reason",
            documents_names,
        )
