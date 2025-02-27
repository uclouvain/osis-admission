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
from unittest.mock import patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from osis_signature.enums import SignatureState
from osis_signature.models import StateHistory

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import (
    ENTITY_CDE,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixStatutPropositionDoctorale,
)
from admission.forms.admission.doctorate.supervision import (
    ACTOR_EXTERNAL,
    EXTERNAL_FIELDS,
)
from admission.models.enums.actor_type import ActorType
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.curriculum import (
    AdmissionEducationalValuatedExperiencesFactory,
    AdmissionProfessionalValuatedExperiencesFactory,
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
    ProfessionalExperienceFactory,
)
from admission.tests.factories.roles import ProgramManagerRoleFactory
from admission.tests.factories.supervision import (
    CaMemberFactory,
    ExternalPromoterFactory,
    PromoterFactory,
    _ProcessFactory,
)
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.tutor import TutorFactory
from reference.tests.factories.country import CountryFactory


@override_settings(ADMISSION_TOKEN_EXTERNAL='api-token-external')
class SupervisionTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        # Create admissions
        cls.admission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            proximity_commission=ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
            supervision_group=_ProcessFactory(),
        )

        # Users
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.admission.training.education_group
        ).person.user

        cls.promoter = PromoterFactory(process=cls.admission.supervision_group)
        cls.ca_member = CaMemberFactory(process=cls.admission.supervision_group)
        cls.external_member = ExternalPromoterFactory(process=cls.admission.supervision_group)

        cls.country = CountryFactory()

        cls.person = PersonFactory()
        TutorFactory(person=cls.person)

        # Urls
        cls.update_url = reverse('admission:doctorate:update:supervision', args=[cls.admission.uuid])
        cls.detail_url = reverse('admission:doctorate:supervision', args=[cls.admission.uuid])

    def setUp(self):
        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            return_value={"name": "myfile", "mimetype": "application/pdf", "size": 1},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.confirm_remote_upload",
            side_effect=lambda token, *args, **kwargs: token,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "osis_document.contrib.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_should_detail_supervision_member(self):
        self.client.force_login(user=self.program_manager_user)
        response = self.client.get(self.update_url)
        self.assertTemplateUsed(response, 'admission/doctorate/details/supervision.html')
        # Display the signatures
        self.assertContains(response, self.promoter.person.last_name)

    def test_should_add_supervision_member_error(self):
        self.client.force_login(user=self.program_manager_user)
        response = self.client.post(self.update_url, {'type': ActorType.CA_MEMBER.name})
        self.assertEqual(response.status_code, 200)
        self.assertIn('__all__', response.context['add_form'].errors)

    def test_should_add_ca_member_ok(self):
        self.client.force_login(user=self.program_manager_user)
        data = {
            'type': ActorType.CA_MEMBER.name,
            'internal_external': "INTERNAL",
            'person': self.person.global_id,
            'email': "test@test.fr",
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 302)

    def test_should_add_supervision_member_error_already_in(self):
        self.client.force_login(user=self.program_manager_user)
        response = self.client.post(self.update_url, {'type': ActorType.PROMOTER.name})
        self.assertEqual(response.status_code, 200)
        self.assertIn('__all__', response.context['add_form'].errors)

    def test_should_add_promoter_ok(self):
        self.client.force_login(user=self.program_manager_user)

        data = {
            'type': ActorType.PROMOTER.name,
            'internal_external': "INTERNAL",
            'person': self.person.global_id,
            'email': "test@test.fr",
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 302)

    def test_should_add_promoter_external_error(self):
        self.client.force_login(user=self.program_manager_user)
        data = {
            'type': ActorType.PROMOTER.name,
            'internal_external': ACTOR_EXTERNAL,
            'email': "test@test.fr",
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(EXTERNAL_FIELDS) - 1, len(response.context['add_form'].errors))
        self.assertIn('prenom', response.context['add_form'].errors)

    def test_should_add_promoter_external_ok(self):
        self.client.force_login(user=self.program_manager_user)
        external_data = {
            'prenom': 'John',
            'nom': 'Doe',
            'email': 'john@example.org',
            'est_docteur': True,
            'institution': 'ins',
            'ville': 'mons',
            'pays': self.country.iso_code,
            'langue': 'fr-be',
        }
        data = {
            'type': ActorType.PROMOTER.name,
            'internal_external': ACTOR_EXTERNAL,
            'person': self.person.global_id,
            **external_data,
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 302)

    def test_should_remove_promoter(self):
        self.client.force_login(user=self.program_manager_user)
        url = resolve_url(
            "admission:doctorate:update:remove-actor",
            uuid=str(self.admission.uuid),
            type=ActorType.PROMOTER.name,
            uuid_membre=str(self.promoter.uuid),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_should_remove_supervision_member_error(self):
        self.client.force_login(user=self.program_manager_user)
        url = resolve_url(
            "admission:doctorate:update:remove-actor",
            uuid=str(self.admission.uuid),
            type=ActorType.PROMOTER.name,
            uuid_membre=str(self.ca_member.uuid),
        )
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 404)

    def test_should_edit_external_supervision_member(self):
        self.client.force_login(user=self.program_manager_user)
        url = resolve_url(
            "admission:doctorate:update:edit-external-member",
            uuid=str(self.admission.uuid),
            uuid_membre=str(self.external_member.uuid),
        )
        external_data = {
            f'member-{self.external_member.uuid}-{k}': v
            for k, v in {
                'prenom': 'John',
                'nom': 'Doe',
                'email': 'john@example.org',
                'est_docteur': True,
                'institution': 'ins',
                'ville': 'mons',
                'pays': self.country.iso_code,
                'langue': 'fr-be',
            }.items()
        }
        response = self.client.post(url, external_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.detail_url, target_status_code=302)
        self.external_member.refresh_from_db()
        self.assertEqual(self.external_member.last_name, 'Doe')
        self.assertEqual(self.external_member.email, 'john@example.org')

    def test_should_not_remove_ca_member_if_not_found(self):
        self.client.force_login(user=self.program_manager_user)
        url = resolve_url(
            "admission:doctorate:update:remove-actor",
            uuid=str(self.admission.uuid),
            type=ActorType.CA_MEMBER.name,
            uuid_membre="34eab30c-27e3-40db-b92e-0b51546a2448",
        )
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, 404)

    def test_should_not_remove_promoter_if_not_found(self):
        self.client.force_login(user=self.program_manager_user)

        url = resolve_url(
            "admission:doctorate:update:remove-actor",
            uuid=str(self.admission.uuid),
            type=ActorType.PROMOTER.name,
            uuid_membre="34eab30c-27e3-40db-b92e-0b51546a2448",
        )
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, 404)

    def test_should_approval_by_pdf_redirect_without_errors(self, *args):
        self.client.force_login(user=self.program_manager_user)
        StateHistory.objects.create(
            actor=self.promoter,
            state=SignatureState.INVITED.name,
        )

        url = resolve_url("admission:doctorate:update:approve-by-pdf", uuid=str(self.admission.uuid))
        response = self.client.post(
            url,
            {
                'uuid_membre': self.promoter.uuid,
                'pdf_0': '34eab30c-27e3-40db-b92e-0b51546a2448',
            },
        )
        expected_url = resolve_url("admission:doctorate:supervision", uuid=str(self.admission.uuid))
        self.assertRedirects(response, expected_url, target_status_code=302)
        self.promoter.refresh_from_db()
        self.assertTrue(self.promoter.pdf_from_candidate)
        self.assertEqual(self.promoter.state, SignatureState.APPROVED.name)

    def test_should_approval_by_pdf_redirect_with_errors(self):
        self.client.force_login(user=self.program_manager_user)
        url = resolve_url("admission:doctorate:update:approve-by-pdf", uuid=str(self.admission.uuid))
        response = self.client.post(url, {})
        self.assertRedirects(response, self.detail_url, target_status_code=302)

    def test_should_set_reference_promoter(self):
        self.client.force_login(user=self.program_manager_user)
        url = resolve_url(
            "admission:doctorate:update:set-reference-promoter",
            uuid=str(self.admission.uuid),
            uuid_promoteur=self.promoter.uuid,
        )
        response = self.client.post(url, {})
        self.assertRedirects(response, self.detail_url, target_status_code=302)
        self.promoter.refresh_from_db()
        self.assertTrue(self.promoter.is_reference_promoter)

    def test_should_resend_invite(self):
        self.client.force_login(user=self.program_manager_user)

        StateHistory.objects.create(
            actor=self.external_member,
            state=SignatureState.INVITED.name,
        )

        url = resolve_url(
            "admission:doctorate:update:resend-invite",
            uuid=str(self.admission.uuid),
            uuid_membre=str(self.external_member.uuid),
        )
        response = self.client.post(url, {}, follow=True)
        self.assertRedirects(response, self.update_url)
        self.assertContains(response, _("An invitation has been sent again."))

    def test_back_to_candidate(self):
        # Create experiences for the candidate
        valuated_educational_experience = EducationalExperienceFactory(person=self.admission.candidate)
        EducationalExperienceYearFactory(educational_experience=valuated_educational_experience)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=self.admission,
            educationalexperience=valuated_educational_experience,
        )

        not_valuated_educational_experience = EducationalExperienceFactory(person=self.admission.candidate)
        EducationalExperienceYearFactory(educational_experience=not_valuated_educational_experience)

        professional_experience = ProfessionalExperienceFactory(person=self.admission.candidate)
        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=self.admission,
            professionalexperience=professional_experience,
        )

        not_valuated_professional_experience = ProfessionalExperienceFactory(person=self.admission.candidate)

        # Create experiences for another candidate
        other_admission = DoctorateAdmissionFactory()
        other_educational_experience = EducationalExperienceFactory(person=other_admission.candidate)
        EducationalExperienceYearFactory(educational_experience=other_educational_experience)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=other_admission,
            educationalexperience=other_educational_experience,
        )

        other_professional_experience = ProfessionalExperienceFactory(person=other_admission.candidate)
        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=other_admission,
            professionalexperience=other_professional_experience,
        )

        self.admission.status = ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name
        self.admission.save(update_fields=["status"])

        self.client.force_login(user=self.program_manager_user)
        url = resolve_url(
            "admission:doctorate:update:send-back-to-candidate",
            uuid=str(self.admission.uuid),
        )
        response = self.client.post(url, {})
        self.admission.refresh_from_db()
        self.assertEqual(self.admission.status, ChoixStatutPropositionDoctorale.EN_BROUILLON.name)

        educational_experiences = self.admission.candidate.educationalexperience_set.all().values_list(
            'uuid',
            flat=True,
        )
        professional_experiences = self.admission.candidate.professionalexperience_set.all().values_list(
            'uuid',
            flat=True,
        )

        self.assertCountEqual(
            educational_experiences,
            [valuated_educational_experience.uuid, not_valuated_educational_experience.uuid],
        )
        self.assertCountEqual(
            professional_experiences,
            [professional_experience.uuid, not_valuated_professional_experience.uuid],
        )

        self.assertFalse(self.admission.educational_valuated_experiences.exists())
        self.assertFalse(self.admission.professional_valuated_experiences.exists())

        self.assertTrue(other_admission.educational_valuated_experiences.exists())
        self.assertTrue(other_admission.professional_valuated_experiences.exists())
