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
import uuid
from typing import Dict, List
from unittest.mock import patch

import freezegun
from django.apps import apps
from django.db import connection
from django.db.models import QuerySet
from django.shortcuts import resolve_url
from django.test import override_settings
from django.utils.translation import gettext
from osis_history.models import HistoryEntry
from rest_framework import status
from rest_framework.test import APITestCase

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDSS,
    ChoixDoctoratDejaRealise,
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.preparation.domain.validator import (
    exceptions as doctorate_education_exceptions,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    DoctoratNonTrouveException,
    MaximumPropositionsDoctoralesAtteintException,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixMoyensDecouverteFormation,
    ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_continue.domain.validator import (
    exceptions as continuing_education_exceptions,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.validator import (
    exceptions as general_education_exceptions,
)
from admission.ddd.admission.shared_kernel.enums import (
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    ChoixTypeCompteBancaire,
    LienParente,
    TypeSituationAssimilation,
)
from admission.models import (
    ContinuingEducationAdmission,
    DoctorateAdmission,
    GeneralEducationAdmission,
    SupervisionActor,
)
from admission.models.base import REFERENCE_SEQ_NAME
from admission.models.enums.actor_type import ActorType
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.calendar import (
    AdmissionAcademicCalendarFactory,
    AdmissionMedDentEnrollmentAcademicCalendarFactory,
)
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
    ContinuingEducationTrainingFactory,
)
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.form_item import (
    AdmissionFormItemInstantiationFactory,
    DocumentAdmissionFormItemFactory,
    TextAdmissionFormItemFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CandidateFactory
from admission.tests.factories.supervision import CaMemberFactory, PromoterFactory
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.enums.entity_type import EntityType
from base.tests import QueriesAssertionsMixin
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import Master120TrainingFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from ddd.logic.reference.domain.validator.exceptions import BourseNonTrouveeException
from reference.tests.factories.language import LanguageFactory
from reference.tests.factories.scholarship import (
    DoubleDegreeScholarshipFactory,
    ErasmusMundusScholarshipFactory,
    InternationalScholarshipFactory,
)


def create_default_propositions_in_progress(candidate):
    DoctorateAdmissionFactory(candidate=candidate, status=ChoixStatutPropositionDoctorale.EN_BROUILLON.name)
    DoctorateAdmissionFactory(candidate=candidate, status=ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name)
    GeneralEducationAdmissionFactory(candidate=candidate, status=ChoixStatutPropositionGenerale.EN_BROUILLON.name)
    GeneralEducationAdmissionFactory(candidate=candidate, status=ChoixStatutPropositionGenerale.EN_BROUILLON.name)
    ContinuingEducationAdmissionFactory(candidate=candidate, status=ChoixStatutPropositionContinue.EN_BROUILLON.name)


class DoctorateAdmissionTrainingChoiceInitializationApiTestCase(APITestCase):
    @classmethod
    @freezegun.freeze_time('2023-01-01')
    def setUpTestData(cls):
        cls.candidate = PersonFactory()
        root = EntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        ).entity
        cls.commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDSS',
        ).entity
        cls.doctorate = DoctorateFactory(
            management_entity=cls.commission,
            enrollment_campus__name='Mons',
        )
        cls.scholarship = ErasmusMundusScholarshipFactory()
        cls.language = LanguageFactory(code='EN')
        AdmissionAcademicCalendarFactory.produce_all_required()

        cls.create_data = {
            "type_admission": ChoixTypeAdmission.PRE_ADMISSION.name,
            "justification": "Some justification",
            "sigle_formation": cls.doctorate.acronym,
            "annee_formation": cls.doctorate.academic_year.year,
            "matricule_candidat": cls.candidate.global_id,
            "commission_proximite": ChoixCommissionProximiteCDSS.ECLI.name,
        }
        cls.url = resolve_url("admission_api_v1:doctorate_training_choice")
        cls.list_url = resolve_url("admission_api_v1:propositions")

        cls.documents_names = [
            'scholarship_proof',
            'project_document',
            'gantt_graph',
            'program_proposition',
            'additional_training_project',
            'recommendation_letters',
            'curriculum',
            'institute_absence_debts_certificate',
            'long_term_resident_card',
            'cire_unlimited_stay_foreigner_card',
            'ue_family_member_residence_card',
            'ue_family_member_permanent_residence_card',
            'stateless_person_proof',
            'refugee_a_b_card',
            'refugees_stateless_annex_25_26',
            'registration_certificate',
            'a_b_card',
            'subsidiary_protection_decision',
            'a_card',
            'temporary_protection_decision',
            'professional_3_month_residence_permit',
            'salary_slips',
            'replacement_3_month_residence_permit',
            'unemployment_benefit_pension_compensation_proof',
            'cpas_certificate',
            'household_composition_or_birth_certificate',
            'tutorship_act',
            'household_composition_or_marriage_certificate',
            'legal_cohabitation_certificate',
            'parent_identity_card',
            'parent_long_term_residence_permit',
            'parent_refugees_stateless_annex_25_26_or_protection_decision',
            'parent_3_month_residence_permit',
            'parent_salary_slips',
            'parent_cpas_certificate',
            'cfwb_scholarship_decision',
            'scholarship_certificate',
            'ue_long_term_stay_identity_document',
            'belgium_residence_permit',
        ]

        cls.documents_tokens: Dict[str, List[uuid.UUID]] = {}
        cls.duplicated_documents_tokens: Dict[str, List[uuid.UUID]] = {}
        cls.duplicated_documents_tokens_by_uuid: Dict[str, str] = {}

        for document_name in cls.documents_names:
            cls.documents_tokens[document_name] = [uuid.uuid4()]
            cls.duplicated_documents_tokens[document_name] = [uuid.uuid4()]
            cls.duplicated_documents_tokens_by_uuid[str(cls.documents_tokens[document_name][0])] = str(
                cls.duplicated_documents_tokens[document_name][0],
            )

    def setUp(self):
        # Mock documents
        patcher = patch('osis_document_components.services.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {uuid: f'token-{index}' for index, uuid in enumerate(uuids)}
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document_components.services.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {
            token: {
                'name': 'myfile',
                'mimetype': PDF_MIME_TYPE,
                'size': 1,
            }
            for token in tokens
        }
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document_components.services.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document_components.services.get_remote_metadata", return_value={"name": "myfile", "size": 1})
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document_components.services.confirm_remote_upload",
            side_effect=lambda token, *args, **kwargs: token,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document_components.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.documents_remote_duplicate_patcher = patch('osis_document_components.services.documents_remote_duplicate')
        self.documents_remote_duplicate_patched = self.documents_remote_duplicate_patcher.start()
        self.documents_remote_duplicate_patched.return_value = self.duplicated_documents_tokens_by_uuid
        self.addCleanup(self.documents_remote_duplicate_patcher.stop)

        DoctorateAdmission.objects.all().delete()

    @freezegun.freeze_time('2023-01-01')
    def test_admission_doctorate_creation_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)
        with connection.cursor() as cursor:
            cursor.execute("SELECT last_value FROM %(sequence)s" % {'sequence': REFERENCE_SEQ_NAME})
            seq_value = cursor.fetchone()[0]
        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        admissions = DoctorateAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)
        first_admission = admissions[0]
        first_admission.status = ChoixStatutPropositionDoctorale.ANNULEE.name
        first_admission.save()
        admission = admissions.get(uuid=response.data["uuid"])
        self.assertEqual(admission.type, self.create_data["type_admission"])
        self.assertEqual(admission.comment, self.create_data["justification"])
        self.assertEqual(admission.last_update_author, self.candidate)

        response = self.client.get(self.list_url, format="json")
        self.assertEqual(response.json()['doctorate_propositions'][0]["doctorat"]['sigle'], self.doctorate.acronym)
        self.assertEqual(
            admission.reference,
            seq_value + 1,
        )
        self.assertEqual(response.json()['doctorate_propositions'][0]["reference"], f'M-CDSS22-{str(admission)}')

    @freezegun.freeze_time('2023-01-01')
    def test_admission_doctorate_creation_based_on_pre_admission(self):
        if not apps.is_installed('parcours_doctoral'):
            return

        from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
        from parcours_doctoral.models import ParcoursDoctoral
        from parcours_doctoral.tests.factories.parcours_doctoral import (
            ParcoursDoctoralFactory,
        )
        from parcours_doctoral.tests.factories.supervision import (
            CaMemberFactory as DoctorateCaMemberFactory,
        )
        from parcours_doctoral.tests.factories.supervision import (
            ExternalPromoterFactory as DoctorateExternalPromoterFactory,
        )
        from parcours_doctoral.tests.factories.supervision import (
            PromoterFactory as DoctoratePromoterFactory,
        )

        self.client.force_authenticate(user=self.candidate.user)

        existing_promoter = DoctoratePromoterFactory(
            is_reference_promoter=True,
            internal_comment='Internal comment 1',
            comment='Comment 1',
            pdf_from_candidate=[uuid.uuid4()],
        )
        external_promoter = DoctorateExternalPromoterFactory(
            process=existing_promoter.process,
            internal_comment='Internal comment 2',
            comment='Comment 2',
            pdf_from_candidate=[uuid.uuid4()],
        )
        existing_ca_member = DoctorateCaMemberFactory(
            process=existing_promoter.process,
            internal_comment='Internal comment 3',
            comment='Comment 3',
            pdf_from_candidate=[uuid.uuid4()],
        )

        pre_admission = DoctorateAdmissionFactory(
            candidate=self.candidate,
            training=self.doctorate,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            status=ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
            curriculum=self.documents_tokens['curriculum'],
        )

        # Accounting
        # Absence debts
        pre_admission.accounting.institute_absence_debts_certificate = self.documents_tokens[
            'institute_absence_debts_certificate'
        ]

        # Assimilation
        pre_admission.accounting.assimilation_situation = (
            TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2.name
        )

        pre_admission.accounting.assimilation_1_situation_type = ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name
        pre_admission.accounting.long_term_resident_card = self.documents_tokens['long_term_resident_card']
        pre_admission.accounting.cire_unlimited_stay_foreigner_card = self.documents_tokens[
            'cire_unlimited_stay_foreigner_card'
        ]
        pre_admission.accounting.ue_family_member_residence_card = self.documents_tokens[
            'ue_family_member_residence_card'
        ]
        pre_admission.accounting.ue_family_member_permanent_residence_card = self.documents_tokens[
            'ue_family_member_permanent_residence_card'
        ]

        pre_admission.accounting.assimilation_2_situation_type = ChoixAssimilation2.DEMANDEUR_ASILE.name
        pre_admission.accounting.stateless_person_proof = self.documents_tokens['stateless_person_proof']
        pre_admission.accounting.refugee_a_b_card = self.documents_tokens['refugee_a_b_card']
        pre_admission.accounting.refugees_stateless_annex_25_26 = self.documents_tokens[
            'refugees_stateless_annex_25_26'
        ]
        pre_admission.accounting.registration_certificate = self.documents_tokens['registration_certificate']
        pre_admission.accounting.a_b_card = self.documents_tokens['a_b_card']
        pre_admission.accounting.subsidiary_protection_decision = self.documents_tokens[
            'subsidiary_protection_decision'
        ]
        pre_admission.accounting.a_card = self.documents_tokens['a_card']
        pre_admission.accounting.temporary_protection_decision = self.documents_tokens['temporary_protection_decision']

        pre_admission.accounting.assimilation_3_situation_type = (
            ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT.name
        )
        pre_admission.accounting.professional_3_month_residence_permit = self.documents_tokens[
            'professional_3_month_residence_permit'
        ]
        pre_admission.accounting.salary_slips = self.documents_tokens['salary_slips']
        pre_admission.accounting.replacement_3_month_residence_permit = self.documents_tokens[
            'replacement_3_month_residence_permit'
        ]
        pre_admission.accounting.unemployment_benefit_pension_compensation_proof = self.documents_tokens[
            'unemployment_benefit_pension_compensation_proof'
        ]

        pre_admission.accounting.cpas_certificate = self.documents_tokens['cpas_certificate']

        pre_admission.accounting.relationship = LienParente.CONJOINT.name
        pre_admission.accounting.assimilation_5_situation_type = ChoixAssimilation5.A_NATIONALITE_UE.name
        pre_admission.accounting.household_composition_or_birth_certificate = self.documents_tokens[
            'household_composition_or_birth_certificate'
        ]
        pre_admission.accounting.tutorship_act = self.documents_tokens['tutorship_act']
        pre_admission.accounting.household_composition_or_marriage_certificate = self.documents_tokens[
            'household_composition_or_marriage_certificate'
        ]
        pre_admission.accounting.legal_cohabitation_certificate = self.documents_tokens[
            'legal_cohabitation_certificate'
        ]
        pre_admission.accounting.parent_identity_card = self.documents_tokens['parent_identity_card']
        pre_admission.accounting.parent_long_term_residence_permit = self.documents_tokens[
            'parent_long_term_residence_permit'
        ]
        pre_admission.accounting.parent_refugees_stateless_annex_25_26_or_protection_decision = self.documents_tokens[
            'parent_refugees_stateless_annex_25_26_or_protection_decision'
        ]
        pre_admission.accounting.parent_3_month_residence_permit = self.documents_tokens[
            'parent_3_month_residence_permit'
        ]
        pre_admission.accounting.parent_salary_slips = self.documents_tokens['parent_salary_slips']
        pre_admission.accounting.parent_cpas_certificate = self.documents_tokens['parent_cpas_certificate']

        pre_admission.accounting.assimilation_6_situation_type = (
            ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name
        )
        pre_admission.accounting.cfwb_scholarship_decision = self.documents_tokens['cfwb_scholarship_decision']
        pre_admission.accounting.scholarship_certificate = self.documents_tokens['scholarship_certificate']

        pre_admission.accounting.ue_long_term_stay_identity_document = self.documents_tokens[
            'ue_long_term_stay_identity_document'
        ]
        pre_admission.accounting.belgium_residence_permit = self.documents_tokens['belgium_residence_permit']

        # Affiliations
        pre_admission.accounting.solidarity_student = True

        # Bank account number
        pre_admission.accounting.account_number_type = ChoixTypeCompteBancaire.IBAN.name
        pre_admission.accounting.iban_account_number = '43210'
        pre_admission.accounting.valid_iban = True
        pre_admission.accounting.other_format_account_number = '910'
        pre_admission.accounting.bic_swift_code = '14S'
        pre_admission.accounting.account_holder_first_name = 'John'
        pre_admission.accounting.account_holder_last_name = 'Doe'

        pre_admission.accounting.save()

        doctorate: ParcoursDoctoral = ParcoursDoctoralFactory(
            admission=pre_admission,
            supervision_group=existing_promoter.process,
            student=self.candidate,
            training=self.doctorate,
            status=ChoixStatutParcoursDoctoral.ADMIS.name,
            justification='Comment',
            proximity_commission=ChoixCommissionProximiteCDSS.ECLI.name,
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
            financing_eft=10,
            international_scholarship_id=self.scholarship.pk,
            other_international_scholarship='Other scholarship',
            scholarship_start_date=datetime.date(2020, 1, 1),
            scholarship_end_date=datetime.date(2021, 1, 1),
            scholarship_proof=self.documents_tokens['scholarship_proof'],
            planned_duration=10,
            dedicated_time=12,
            is_fnrs_fria_fresh_csc_linked=True,
            financing_comment='Financing comment',
            project_title='Project title',
            project_abstract='Project abstract',
            thesis_language=self.language,
            thesis_institute=EntityVersionFactory(),
            thesis_location='Thesis location',
            phd_alread_started=True,
            phd_alread_started_institute='PHD already started institute',
            work_start_date=datetime.date(2022, 1, 1),
            project_document=self.documents_tokens['project_document'],
            gantt_graph=self.documents_tokens['gantt_graph'],
            program_proposition=self.documents_tokens['program_proposition'],
            additional_training_project=self.documents_tokens['additional_training_project'],
            recommendation_letters=self.documents_tokens['recommendation_letters'],
            phd_already_done=ChoixDoctoratDejaRealise.YES.name,
            phd_already_done_institution='PhD already done institution',
            phd_already_done_thesis_domain='PhD already done thesis domain',
            phd_already_done_defense_date=datetime.date(2023, 1, 1),
            phd_already_done_no_defense_reason='No defense reason',
        )

        response = self.client.post(
            self.url,
            data={
                'type_admission': ChoixTypeAdmission.ADMISSION.name,
                'justification': 'Some new justification',
                'sigle_formation': '',
                'annee_formation': None,
                'matricule_candidat': self.candidate.global_id,
                'commission_proximite': '',
                'pre_admission_associee': pre_admission.uuid,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        admissions = DoctorateAdmission.objects.filter(type=ChoixTypeAdmission.ADMISSION.name)

        self.assertEqual(admissions.count(), 1)

        new_admission = admissions[0]
        self.assertEqual(new_admission.candidate, pre_admission.candidate)
        self.assertEqual(new_admission.training, pre_admission.training)
        self.assertEqual(new_admission.type, ChoixTypeAdmission.ADMISSION.name)
        self.assertEqual(new_admission.status, ChoixStatutPropositionDoctorale.EN_BROUILLON.name)
        self.assertEqual(new_admission.related_pre_admission, pre_admission)

        self.assertEqual(new_admission.comment, doctorate.justification)
        self.assertEqual(new_admission.proximity_commission, doctorate.proximity_commission)
        self.assertEqual(new_admission.financing_type, doctorate.financing_type)
        self.assertEqual(new_admission.financing_work_contract, doctorate.financing_work_contract)
        self.assertEqual(new_admission.financing_eft, doctorate.financing_eft)
        self.assertEqual(new_admission.international_scholarship_id, doctorate.international_scholarship_id)
        self.assertEqual(new_admission.other_international_scholarship, doctorate.other_international_scholarship)
        self.assertEqual(new_admission.scholarship_start_date, doctorate.scholarship_start_date)
        self.assertEqual(new_admission.scholarship_end_date, doctorate.scholarship_end_date)
        self.assertEqual(new_admission.scholarship_proof, self.duplicated_documents_tokens['scholarship_proof'])
        self.assertEqual(new_admission.planned_duration, doctorate.planned_duration)
        self.assertEqual(new_admission.dedicated_time, doctorate.dedicated_time)
        self.assertEqual(new_admission.is_fnrs_fria_fresh_csc_linked, doctorate.is_fnrs_fria_fresh_csc_linked)
        self.assertEqual(new_admission.financing_comment, doctorate.financing_comment)
        self.assertEqual(new_admission.project_title, doctorate.project_title)
        self.assertEqual(new_admission.project_abstract, doctorate.project_abstract)
        self.assertEqual(new_admission.thesis_language, doctorate.thesis_language)
        self.assertEqual(new_admission.thesis_institute, doctorate.thesis_institute)
        self.assertEqual(new_admission.thesis_location, doctorate.thesis_location)
        self.assertEqual(new_admission.phd_alread_started, doctorate.phd_alread_started)
        self.assertEqual(new_admission.phd_alread_started_institute, doctorate.phd_alread_started_institute)
        self.assertEqual(new_admission.work_start_date, doctorate.work_start_date)
        self.assertEqual(new_admission.project_document, self.duplicated_documents_tokens['project_document'])
        self.assertEqual(new_admission.gantt_graph, self.duplicated_documents_tokens['gantt_graph'])
        self.assertEqual(new_admission.program_proposition, self.duplicated_documents_tokens['program_proposition'])
        self.assertEqual(
            new_admission.additional_training_project,
            self.duplicated_documents_tokens['additional_training_project'],
        )
        self.assertEqual(
            new_admission.recommendation_letters,
            self.duplicated_documents_tokens['recommendation_letters'],
        )
        self.assertEqual(new_admission.phd_already_done, doctorate.phd_already_done)
        self.assertEqual(new_admission.phd_already_done_institution, doctorate.phd_already_done_institution)
        self.assertEqual(new_admission.phd_already_done_thesis_domain, doctorate.phd_already_done_thesis_domain)
        self.assertEqual(new_admission.phd_already_done_defense_date, doctorate.phd_already_done_defense_date)
        self.assertEqual(
            new_admission.phd_already_done_no_defense_reason,
            doctorate.phd_already_done_no_defense_reason,
        )
        self.assertEqual(new_admission.curriculum, self.duplicated_documents_tokens['curriculum'])

        # Accounting
        self.assertEqual(
            new_admission.accounting.institute_absence_debts_certificate,
            self.duplicated_documents_tokens['institute_absence_debts_certificate'],
        )

        self.assertEqual(
            new_admission.accounting.assimilation_situation, pre_admission.accounting.assimilation_situation
        )

        self.assertEqual(
            new_admission.accounting.assimilation_1_situation_type,
            pre_admission.accounting.assimilation_1_situation_type,
        )
        self.assertEqual(
            new_admission.accounting.long_term_resident_card,
            self.duplicated_documents_tokens['long_term_resident_card'],
        )
        self.assertEqual(
            new_admission.accounting.cire_unlimited_stay_foreigner_card,
            self.duplicated_documents_tokens['cire_unlimited_stay_foreigner_card'],
        )
        self.assertEqual(
            new_admission.accounting.ue_family_member_residence_card,
            self.duplicated_documents_tokens['ue_family_member_residence_card'],
        )
        self.assertEqual(
            new_admission.accounting.ue_family_member_permanent_residence_card,
            self.duplicated_documents_tokens['ue_family_member_permanent_residence_card'],
        )

        self.assertEqual(
            new_admission.accounting.assimilation_2_situation_type,
            pre_admission.accounting.assimilation_2_situation_type,
        )
        self.assertEqual(
            new_admission.accounting.stateless_person_proof,
            self.duplicated_documents_tokens['stateless_person_proof'],
        )
        self.assertEqual(
            new_admission.accounting.refugee_a_b_card,
            self.duplicated_documents_tokens['refugee_a_b_card'],
        )
        self.assertEqual(
            new_admission.accounting.refugees_stateless_annex_25_26,
            self.duplicated_documents_tokens['refugees_stateless_annex_25_26'],
        )
        self.assertEqual(
            new_admission.accounting.registration_certificate,
            self.duplicated_documents_tokens['registration_certificate'],
        )
        self.assertEqual(
            new_admission.accounting.a_b_card,
            self.duplicated_documents_tokens['a_b_card'],
        )
        self.assertEqual(
            new_admission.accounting.subsidiary_protection_decision,
            self.duplicated_documents_tokens['subsidiary_protection_decision'],
        )
        self.assertEqual(
            new_admission.accounting.a_card,
            self.duplicated_documents_tokens['a_card'],
        )

        self.assertEqual(
            new_admission.accounting.assimilation_3_situation_type,
            pre_admission.accounting.assimilation_3_situation_type,
        )
        self.assertEqual(
            new_admission.accounting.temporary_protection_decision,
            self.duplicated_documents_tokens['temporary_protection_decision'],
        )
        self.assertEqual(
            new_admission.accounting.professional_3_month_residence_permit,
            self.duplicated_documents_tokens['professional_3_month_residence_permit'],
        )
        self.assertEqual(
            new_admission.accounting.salary_slips,
            self.duplicated_documents_tokens['salary_slips'],
        )
        self.assertEqual(
            new_admission.accounting.replacement_3_month_residence_permit,
            self.duplicated_documents_tokens['replacement_3_month_residence_permit'],
        )
        self.assertEqual(
            new_admission.accounting.unemployment_benefit_pension_compensation_proof,
            self.duplicated_documents_tokens['unemployment_benefit_pension_compensation_proof'],
        )

        self.assertEqual(
            new_admission.accounting.cpas_certificate,
            self.duplicated_documents_tokens['cpas_certificate'],
        )

        self.assertEqual(new_admission.accounting.relationship, pre_admission.accounting.relationship)
        self.assertEqual(
            new_admission.accounting.assimilation_5_situation_type,
            pre_admission.accounting.assimilation_5_situation_type,
        )
        self.assertEqual(
            new_admission.accounting.household_composition_or_birth_certificate,
            self.duplicated_documents_tokens['household_composition_or_birth_certificate'],
        )
        self.assertEqual(
            new_admission.accounting.tutorship_act,
            self.duplicated_documents_tokens['tutorship_act'],
        )
        self.assertEqual(
            new_admission.accounting.household_composition_or_marriage_certificate,
            self.duplicated_documents_tokens['household_composition_or_marriage_certificate'],
        )
        self.assertEqual(
            new_admission.accounting.legal_cohabitation_certificate,
            self.duplicated_documents_tokens['legal_cohabitation_certificate'],
        )
        self.assertEqual(
            new_admission.accounting.parent_identity_card,
            self.duplicated_documents_tokens['parent_identity_card'],
        )
        self.assertEqual(
            new_admission.accounting.parent_long_term_residence_permit,
            self.duplicated_documents_tokens['parent_long_term_residence_permit'],
        )
        self.assertEqual(
            new_admission.accounting.parent_refugees_stateless_annex_25_26_or_protection_decision,
            self.duplicated_documents_tokens['parent_refugees_stateless_annex_25_26_or_protection_decision'],
        )
        self.assertEqual(
            new_admission.accounting.parent_3_month_residence_permit,
            self.duplicated_documents_tokens['parent_3_month_residence_permit'],
        )
        self.assertEqual(
            new_admission.accounting.parent_salary_slips,
            self.duplicated_documents_tokens['parent_salary_slips'],
        )
        self.assertEqual(
            new_admission.accounting.parent_cpas_certificate,
            self.duplicated_documents_tokens['parent_cpas_certificate'],
        )

        self.assertEqual(
            new_admission.accounting.assimilation_6_situation_type,
            pre_admission.accounting.assimilation_6_situation_type,
        )
        self.assertEqual(
            new_admission.accounting.cfwb_scholarship_decision,
            self.duplicated_documents_tokens['cfwb_scholarship_decision'],
        )
        self.assertEqual(
            new_admission.accounting.scholarship_certificate,
            self.duplicated_documents_tokens['scholarship_certificate'],
        )

        self.assertEqual(
            new_admission.accounting.ue_long_term_stay_identity_document,
            self.duplicated_documents_tokens['ue_long_term_stay_identity_document'],
        )
        self.assertEqual(
            new_admission.accounting.belgium_residence_permit,
            self.duplicated_documents_tokens['belgium_residence_permit'],
        )

        self.assertEqual(new_admission.accounting.solidarity_student, pre_admission.accounting.solidarity_student)

        self.assertEqual(new_admission.accounting.account_number_type, pre_admission.accounting.account_number_type)
        self.assertEqual(new_admission.accounting.iban_account_number, pre_admission.accounting.iban_account_number)
        self.assertEqual(new_admission.accounting.valid_iban, pre_admission.accounting.valid_iban)
        self.assertEqual(
            new_admission.accounting.other_format_account_number, pre_admission.accounting.other_format_account_number
        )
        self.assertEqual(new_admission.accounting.bic_swift_code, pre_admission.accounting.bic_swift_code)
        self.assertEqual(
            new_admission.accounting.account_holder_first_name, pre_admission.accounting.account_holder_first_name
        )
        self.assertEqual(
            new_admission.accounting.account_holder_last_name, pre_admission.accounting.account_holder_last_name
        )

        # Check the duplication of the supervision group
        self.assertIsNotNone(new_admission.supervision_group)

        actors = SupervisionActor.objects.filter(process=new_admission.supervision_group)

        self.assertEqual(len(actors), 3)

        duplicated_external_promoter = actors.filter(type=ActorType.PROMOTER.name, person__isnull=True).first()
        duplicated_existing_promoter = actors.filter(type=ActorType.PROMOTER.name, person__isnull=False).first()
        duplicated_existing_ca_member = actors.filter(type=ActorType.CA_MEMBER.name).first()

        self.assertEqual(duplicated_external_promoter.type, external_promoter.type)
        self.assertEqual(duplicated_external_promoter.is_doctor, external_promoter.is_doctor)
        self.assertEqual(duplicated_external_promoter.internal_comment, '')
        self.assertEqual(duplicated_external_promoter.rejection_reason, '')
        self.assertEqual(duplicated_external_promoter.pdf_from_candidate, [])
        self.assertEqual(duplicated_external_promoter.is_reference_promoter, False)
        self.assertEqual(duplicated_external_promoter.person, external_promoter.person)
        self.assertEqual(duplicated_external_promoter.first_name, external_promoter.first_name)
        self.assertEqual(duplicated_external_promoter.last_name, external_promoter.last_name)
        self.assertEqual(duplicated_external_promoter.email, external_promoter.email)
        self.assertEqual(duplicated_external_promoter.institute, external_promoter.institute)
        self.assertEqual(duplicated_external_promoter.city, external_promoter.city)
        self.assertEqual(duplicated_external_promoter.country, external_promoter.country)
        self.assertEqual(duplicated_external_promoter.language, external_promoter.language)
        self.assertEqual(duplicated_external_promoter.comment, '')

        self.assertEqual(duplicated_existing_promoter.type, existing_promoter.type)
        self.assertEqual(duplicated_existing_promoter.is_doctor, existing_promoter.is_doctor)
        self.assertEqual(duplicated_existing_promoter.internal_comment, '')
        self.assertEqual(duplicated_existing_promoter.rejection_reason, '')
        self.assertEqual(duplicated_existing_promoter.pdf_from_candidate, [])
        self.assertEqual(duplicated_existing_promoter.is_reference_promoter, True)
        self.assertEqual(duplicated_existing_promoter.person, existing_promoter.person)
        self.assertEqual(duplicated_existing_promoter.first_name, existing_promoter.first_name)
        self.assertEqual(duplicated_existing_promoter.last_name, existing_promoter.last_name)
        self.assertEqual(duplicated_existing_promoter.email, existing_promoter.email)
        self.assertEqual(duplicated_existing_promoter.institute, existing_promoter.institute)
        self.assertEqual(duplicated_existing_promoter.city, existing_promoter.city)
        self.assertEqual(duplicated_existing_promoter.country, existing_promoter.country)
        self.assertEqual(duplicated_existing_promoter.language, existing_promoter.language)
        self.assertEqual(duplicated_existing_promoter.comment, '')

        self.assertEqual(duplicated_existing_ca_member.type, existing_ca_member.type)
        self.assertEqual(duplicated_existing_ca_member.is_doctor, existing_ca_member.is_doctor)
        self.assertEqual(duplicated_existing_ca_member.internal_comment, '')
        self.assertEqual(duplicated_existing_ca_member.rejection_reason, '')
        self.assertEqual(duplicated_existing_ca_member.pdf_from_candidate, [])
        self.assertEqual(duplicated_existing_ca_member.is_reference_promoter, False)
        self.assertEqual(duplicated_existing_ca_member.person, existing_ca_member.person)
        self.assertEqual(duplicated_existing_ca_member.first_name, existing_ca_member.first_name)
        self.assertEqual(duplicated_existing_ca_member.last_name, existing_ca_member.last_name)
        self.assertEqual(duplicated_existing_ca_member.email, existing_ca_member.email)
        self.assertEqual(duplicated_existing_ca_member.institute, existing_ca_member.institute)
        self.assertEqual(duplicated_existing_ca_member.city, existing_ca_member.city)
        self.assertEqual(duplicated_existing_ca_member.country, existing_ca_member.country)
        self.assertEqual(duplicated_existing_ca_member.language, existing_ca_member.language)
        self.assertEqual(duplicated_existing_ca_member.comment, '')

    def test_admission_doctorate_creation_using_api_with_wrong_doctorate(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.create_data, "sigle_formation": "UNKONWN"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], DoctoratNonTrouveException.status_code)

    def test_admission_doctorate_creation_using_api_with_too_much_propositions_in_parallel(self):
        self.client.force_authenticate(user=self.candidate.user)
        create_default_propositions_in_progress(candidate=self.candidate)
        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admission_doctorate_creation_using_api_with_too_much_doctorate_propositions_in_parallel(self):
        self.client.force_authenticate(user=self.candidate.user)
        other_admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            candidate=self.candidate,
        )
        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            MaximumPropositionsDoctoralesAtteintException.status_code,
        )

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GeneralEducationAdmissionTrainingChoiceInitializationApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.candidate = PersonFactory()
        cls.training = Master120TrainingFactory()
        cls.erasmus_mundus_scholarship = ErasmusMundusScholarshipFactory()
        cls.international_scholarship = InternationalScholarshipFactory()
        cls.double_degree_scholarship = DoubleDegreeScholarshipFactory()
        AdmissionAcademicCalendarFactory.produce_all_required()

        cls.create_data = {
            'sigle_formation': cls.training.acronym,
            'annee_formation': cls.training.academic_year.year,
            'matricule_candidat': cls.candidate.global_id,
            'avec_bourse_erasmus_mundus': True,
            'avec_bourse_internationale': True,
            'avec_bourse_double_diplome': True,
            'bourse_erasmus_mundus': str(cls.erasmus_mundus_scholarship.uuid),
            'bourse_internationale': str(cls.international_scholarship.uuid),
            'bourse_double_diplome': str(cls.double_degree_scholarship.uuid),
        }

        cls.url = resolve_url('admission_api_v1:general_training_choice')

    def test_training_choice_initialization_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        admissions: QuerySet[GeneralEducationAdmission] = GeneralEducationAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)

        admission = admissions.get(uuid=response.data['uuid'])
        self.assertEqual(admission.training_id, self.training.pk)
        self.assertEqual(admission.candidate_id, self.candidate.pk)
        self.assertEqual(admission.international_scholarship_id, self.international_scholarship.pk)
        self.assertEqual(admission.erasmus_mundus_scholarship_id, self.erasmus_mundus_scholarship.pk)
        self.assertEqual(admission.double_degree_scholarship_id, self.double_degree_scholarship.pk)
        self.assertTrue(admission.has_international_scholarship)
        self.assertTrue(admission.has_erasmus_mundus_scholarship)
        self.assertTrue(admission.has_double_degree_scholarship)
        self.assertEqual(admission.status, ChoixStatutPropositionGenerale.EN_BROUILLON.name)

        history_entry: HistoryEntry = HistoryEntry.objects.filter(
            object_uuid=admission.uuid,
            tags__contains=['proposition', 'status-changed'],
        ).last()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.message_fr, 'La proposition a été initiée.')

    def test_training_choice_initialization_using_api_candidate_with_wrong_training(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.create_data, 'sigle_formation': 'UNKNOWN'}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            general_education_exceptions.FormationNonTrouveeException.status_code,
        )

    def test_training_choice_initialization_using_api_candidate_with_wrong_scholarship(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.create_data, 'bourse_erasmus_mundus': str(uuid.uuid4())}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], BourseNonTrouveeException.status_code)

    def test_training_choice_initialization_using_api_candidate_with_too_much_propositions_in_parallel(self):
        self.client.force_authenticate(user=self.candidate.user)
        create_default_propositions_in_progress(candidate=self.candidate)
        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@freezegun.freeze_time('2023-01-01')
class ContinuingEducationAdmissionTrainingChoiceInitializationApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.candidate = PersonFactory()
        cls.training = ContinuingEducationTrainingFactory()
        cls.create_data = {
            'sigle_formation': cls.training.acronym,
            'annee_formation': cls.training.academic_year.year,
            'matricule_candidat': cls.candidate.global_id,
            'motivations': 'Motivation',
            'moyens_decouverte_formation': [
                ChoixMoyensDecouverteFormation.FACEBOOK.name,
                ChoixMoyensDecouverteFormation.LINKEDIN.name,
            ],
            'marque_d_interet': True,
            'autre_moyen_decouverte_formation': 'Other way',
        }

        cls.url = resolve_url('admission_api_v1:continuing_training_choice')
        AdmissionAcademicCalendarFactory.produce_all_required()

    def test_training_choice_initialization_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        admissions: QuerySet[ContinuingEducationAdmission] = ContinuingEducationAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)

        admission = admissions.get(uuid=response.data['uuid'])
        self.assertEqual(admission.training_id, self.training.pk)
        self.assertEqual(admission.candidate_id, self.candidate.pk)
        self.assertEqual(admission.status, ChoixStatutPropositionContinue.EN_BROUILLON.name)
        self.assertEqual(admission.motivations, 'Motivation')
        self.assertEqual(
            admission.ways_to_find_out_about_the_course,
            [
                ChoixMoyensDecouverteFormation.FACEBOOK.name,
                ChoixMoyensDecouverteFormation.LINKEDIN.name,
            ],
        )
        self.assertEqual(admission.interested_mark, True)
        self.assertEqual(admission.other_way_to_find_out_about_the_course, 'Other way')

        history_entry: HistoryEntry = HistoryEntry.objects.filter(
            object_uuid=admission.uuid,
            tags__contains=['proposition', 'status-changed'],
        ).last()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.message_fr, 'La proposition a été initiée.')

    def test_training_choice_initialization_using_api_candidate_with_wrong_training(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.create_data, 'sigle_formation': 'UNKNOWN'}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            continuing_education_exceptions.FormationNonTrouveeException.status_code,
        )

    def test_training_choice_initialization_using_api_candidate_with_too_much_propositions_in_parallel(self):
        self.client.force_authenticate(user=self.candidate.user)
        create_default_propositions_in_progress(candidate=self.candidate)
        response = self.client.post(self.url, data=self.create_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
@freezegun.freeze_time('2023-01-01')
class GeneralEducationAdmissionTrainingChoiceUpdateApiTestCase(APITestCase):
    file_uuid = str(uuid.uuid4())

    @classmethod
    def setUpTestData(cls):
        cls.admission = GeneralEducationAdmissionFactory()
        cls.candidate = cls.admission.candidate
        cls.training = Master120TrainingFactory()
        cls.erasmus_mundus_scholarship = ErasmusMundusScholarshipFactory()
        cls.international_scholarship = InternationalScholarshipFactory()
        cls.double_degree_scholarship = DoubleDegreeScholarshipFactory()

        cls.update_data = {
            'sigle_formation': cls.training.acronym,
            'annee_formation': cls.training.academic_year.year,
            'uuid_proposition': cls.admission.uuid,
            'avec_bourse_erasmus_mundus': True,
            'avec_bourse_internationale': True,
            'avec_bourse_double_diplome': True,
            'bourse_erasmus_mundus': str(cls.erasmus_mundus_scholarship.uuid),
            'bourse_internationale': str(cls.international_scholarship.uuid),
            'bourse_double_diplome': str(cls.double_degree_scholarship.uuid),
            'reponses_questions_specifiques': {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
                'fe254203-17c7-47d6-95e4-3c5c532da552': [cls.file_uuid, 'token:abcdef'],
            },
        }
        AdmissionAcademicCalendarFactory.produce_all_required()

        AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
                internal_label='text_item',
            ),
            academic_year=cls.training.academic_year,
        )
        AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da552'),
                internal_label='document_item_1',
            ),
            academic_year=cls.training.academic_year,
        )
        AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da553'),
                active=False,
                internal_label='document_item_2',
            ),
            academic_year=cls.training.academic_year,
        )

        cls.url = resolve_url('admission_api_v1:general_training_choice', uuid=str(cls.admission.uuid))

    def setUp(self) -> None:
        patcher = patch('osis_document_components.services.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document_components.services.get_remote_metadata', return_value={'name': 'myfile', 'size': 1})
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document_components.services.confirm_remote_upload')
        patched = patcher.start()
        patched.return_value = '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document_components.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: ['550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'] if value else []
        self.addCleanup(patcher.stop)

    def test_training_choice_update_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.put(self.url, data=self.update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        admissions: QuerySet[GeneralEducationAdmission] = GeneralEducationAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)

        admission = admissions.get(uuid=response.data['uuid'])
        self.assertEqual(admission.training_id, self.training.pk)
        self.assertEqual(admission.candidate_id, self.candidate.pk)
        self.assertEqual(admission.international_scholarship_id, self.international_scholarship.pk)
        self.assertEqual(admission.erasmus_mundus_scholarship_id, self.erasmus_mundus_scholarship.pk)
        self.assertEqual(admission.double_degree_scholarship_id, self.double_degree_scholarship.pk)
        self.assertTrue(admission.has_international_scholarship)
        self.assertTrue(admission.has_erasmus_mundus_scholarship)
        self.assertTrue(admission.has_double_degree_scholarship)
        self.assertEqual(admission.status, ChoixStatutPropositionGenerale.EN_BROUILLON.name)
        expected = {
            'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
            'fe254203-17c7-47d6-95e4-3c5c532da552': [self.file_uuid, '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'],
        }
        self.assertEqual(admission.specific_question_answers, expected)
        self.assertEqual(admission.modified_at, datetime.datetime.now())
        self.assertEqual(admission.last_update_author, self.candidate.user.person)

    def test_training_choice_update_using_api_candidate_with_wrong_proposition(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.update_data, 'uuid_proposition': str(uuid.uuid4())}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            general_education_exceptions.PropositionNonTrouveeException.status_code,
        )

    def test_training_choice_update_using_api_candidate_with_wrong_training(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.update_data, 'sigle_formation': 'UNKNOWN'}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            general_education_exceptions.FormationNonTrouveeException.status_code,
        )

    def test_training_choice_update_using_api_candidate_with_wrong_scholarship(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.update_data, 'bourse_erasmus_mundus': str(uuid.uuid4())}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['non_field_errors'][0]['status_code'], BourseNonTrouveeException.status_code)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
@freezegun.freeze_time('2023-01-01')
class ContinuingEducationAdmissionTrainingChoiceUpdateApiTestCase(APITestCase):
    file_uuid = str(uuid.uuid4())

    @classmethod
    def setUpTestData(cls):
        AdmissionAcademicCalendarFactory.produce_all_required()
        cls.admission = ContinuingEducationAdmissionFactory()
        cls.candidate = cls.admission.candidate
        cls.training = ContinuingEducationTrainingFactory()

        cls.update_data = {
            'sigle_formation': cls.training.acronym,
            'annee_formation': cls.training.academic_year.year,
            'uuid_proposition': cls.admission.uuid,
            'reponses_questions_specifiques': {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
                'fe254203-17c7-47d6-95e4-3c5c532da552': [cls.file_uuid, 'token:abcdef'],
            },
            'motivations': 'Motivation',
            'moyens_decouverte_formation': [
                ChoixMoyensDecouverteFormation.FACEBOOK.name,
                ChoixMoyensDecouverteFormation.COURRIER_PERSONNALISE.name,
            ],
            'marque_d_interet': True,
            'autre_moyen_decouverte_formation': 'Other way',
        }

        AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
                internal_label='text_item',
            ),
            academic_year=cls.training.academic_year,
        )
        AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da552'),
                internal_label='document_item_1',
            ),
            academic_year=cls.training.academic_year,
        )
        AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da553'),
                active=False,
                internal_label='document_item_2',
            ),
            academic_year=cls.training.academic_year,
        )

        cls.url = resolve_url('admission_api_v1:continuing_training_choice', uuid=str(cls.admission.uuid))

    def setUp(self) -> None:
        patcher = patch('osis_document_components.services.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document_components.services.get_remote_metadata', return_value={'name': 'myfile', 'size': 1})
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document_components.services.confirm_remote_upload')
        patched = patcher.start()
        patched.return_value = '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document_components.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: ['550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'] if value else []
        self.addCleanup(patcher.stop)

    def test_training_choice_update_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.put(self.url, data=self.update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        admissions: QuerySet[ContinuingEducationAdmission] = ContinuingEducationAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)

        admission = admissions.get(uuid=response.data['uuid'])
        self.assertEqual(admission.training_id, self.training.pk)
        self.assertEqual(admission.candidate_id, self.candidate.pk)
        self.assertEqual(admission.status, ChoixStatutPropositionContinue.EN_BROUILLON.name)
        expected = {
            'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
            'fe254203-17c7-47d6-95e4-3c5c532da552': [self.file_uuid, '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'],
        }
        self.assertEqual(admission.specific_question_answers, expected)
        self.assertEqual(admission.motivations, 'Motivation')
        self.assertEqual(
            admission.ways_to_find_out_about_the_course,
            [
                ChoixMoyensDecouverteFormation.FACEBOOK.name,
                ChoixMoyensDecouverteFormation.COURRIER_PERSONNALISE.name,
            ],
        )
        self.assertEqual(admission.other_way_to_find_out_about_the_course, 'Other way')
        self.assertEqual(admission.interested_mark, True)

    def test_training_choice_update_using_api_candidate_with_wrong_proposition(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.update_data, 'uuid_proposition': str(uuid.uuid4())}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            continuing_education_exceptions.PropositionNonTrouveeException.status_code,
        )

    def test_training_choice_update_using_api_candidate_with_wrong_training(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.update_data, 'sigle_formation': 'UNKNOWN'}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            continuing_education_exceptions.FormationNonTrouveeException.status_code,
        )

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/', WAFFLE_CREATE_MISSING_SWITCHES=False)
class DoctorateEducationAdmissionTypeUpdateApiTestCase(QueriesAssertionsMixin, APITestCase):
    file_uuid = str(uuid.uuid4())

    @classmethod
    def setUpTestData(cls):
        # Create supervision group members
        promoter = PromoterFactory()
        committee_member = CaMemberFactory(process=promoter.process)

        # Create doctorate management entity
        root = EntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        ).entity
        cls.commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.admission = DoctorateAdmissionFactory(
            training__management_entity=cls.commission,
            supervision_group=promoter.process,
            with_answers_to_specific_questions=True,
        )
        AdmissionAcademicCalendarFactory.produce_all_required()

        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate_user = CandidateFactory().person.user
        cls.no_role_user = PersonFactory().user
        cls.promoter_user = promoter.person.user
        cls.other_promoter_user = PromoterFactory().person.user
        cls.committee_member_user = committee_member.person.user
        cls.other_committee_member_user = CaMemberFactory().person.user

        cls.update_data = {
            'uuid_proposition': cls.admission.uuid,
            "sigle_formation": cls.admission.training.acronym,
            "annee_formation": cls.admission.training.academic_year.year,
            'type_admission': ChoixTypeAdmission.PRE_ADMISSION.name,
            'justification': 'Justification',
            'reponses_questions_specifiques': {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
                'fe254203-17c7-47d6-95e4-3c5c532da552': [cls.file_uuid, 'token:abcdef'],
            },
        }

        AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
                internal_label='text_item',
            ),
            academic_year=cls.admission.training.academic_year,
        )
        AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da552'),
                internal_label='document_item_1',
            ),
            academic_year=cls.admission.training.academic_year,
        )
        AdmissionFormItemInstantiationFactory(
            form_item=DocumentAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da553'),
                active=False,
                internal_label='document_item_2',
            ),
            academic_year=cls.admission.training.academic_year,
        )

        cls.url = resolve_url('admission_api_v1:doctorate_admission_type_update', uuid=str(cls.admission.uuid))

    def setUp(self) -> None:
        patcher = patch('osis_document_components.services.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document_components.services.get_remote_metadata', return_value={'name': 'myfile', 'size': 1})
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document_components.services.confirm_remote_upload')
        patched = patcher.start()
        patched.return_value = '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document_components.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: ['550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'] if value else []
        self.addCleanup(patcher.stop)

    def test_admission_type_update_using_api_candidate(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.put(self.url, data=self.update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        admissions = DoctorateAdmission.objects.all()
        self.assertEqual(admissions.count(), 1)
        admission: DoctorateAdmission = admissions.get(uuid=response.data['uuid'])

        self.assertEqual(admission.candidate_id, self.candidate.pk)
        self.assertEqual(admission.status, ChoixStatutPropositionDoctorale.EN_BROUILLON.name)
        self.assertEqual(admission.type, ChoixTypeAdmission.PRE_ADMISSION.name)
        self.assertEqual(admission.comment, 'Justification')
        expected = {
            'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
            'fe254203-17c7-47d6-95e4-3c5c532da552': [self.file_uuid, '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'],
        }
        self.assertEqual(admission.specific_question_answers, expected)

    def test_admission_type_update_with_admission_based_on_pre_admission(self):
        self.client.force_authenticate(user=self.candidate.user)

        pre_admission = DoctorateAdmissionFactory(
            candidate=self.candidate,
            training=self.admission.training,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            status=ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
        )

        admission = DoctorateAdmissionFactory(
            candidate=self.candidate,
            training=self.admission.training,
            type=ChoixTypeAdmission.ADMISSION.name,
            related_pre_admission=pre_admission,
        )

        url = resolve_url('admission_api_v1:doctorate_admission_type_update', uuid=str(admission.uuid))

        response = self.client.put(url, data={}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.json()['detail'],
            gettext('The admission must not follow a pre-admission'),
        )

    def test_admission_type_update_using_api_candidate_with_wrong_proposition(self):
        self.client.force_authenticate(user=self.candidate.user)
        data = {**self.update_data, 'uuid_proposition': str(uuid.uuid4())}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            doctorate_education_exceptions.PropositionNonTrouveeException.status_code,
        )

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SpecificEnrolmentPeriodsApiViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.candidate = CandidateFactory().person.user
        cls.academic_year_2023 = AcademicYearFactory(year=2023)
        cls.academic_year_2024 = AcademicYearFactory(year=2024)

        cls.url = resolve_url('admission_api_v1:specific_enrolment_periods')

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_none_if_there_is_no_period(self):
        self.client.force_authenticate(user=self.candidate)

        response = self.client.get(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('medicine_dentistry_bachelor'), None)

    def test_get_current_period_if_the_today_date_is_inside_it(self):
        self.client.force_authenticate(user=self.candidate)

        academic_calendar = AdmissionMedDentEnrollmentAcademicCalendarFactory(data_year=self.academic_year_2023)

        with freezegun.freeze_time('2023-09-06'):
            response = self.client.get(self.url, format='json')

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertEqual(
                response.json().get('medicine_dentistry_bachelor'),
                {
                    'date_debut': academic_calendar.start_date.isoformat(),
                    'date_fin': academic_calendar.end_date.isoformat(),
                },
            )

        with freezegun.freeze_time('2024-02-15'):
            response = self.client.get(self.url, format='json')

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertEqual(
                response.json().get('medicine_dentistry_bachelor'),
                {
                    'date_debut': academic_calendar.start_date.isoformat(),
                    'date_fin': academic_calendar.end_date.isoformat(),
                },
            )

    def test_get_next_period_if_the_today_date_is_not_inside_an_existing_one(self):
        self.client.force_authenticate(user=self.candidate)

        academic_calendar_2023 = AdmissionMedDentEnrollmentAcademicCalendarFactory(data_year=self.academic_year_2023)
        academic_calendar_2024 = AdmissionMedDentEnrollmentAcademicCalendarFactory(data_year=self.academic_year_2024)

        with freezegun.freeze_time('2023-09-05'):
            response = self.client.get(self.url, format='json')

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertEqual(
                response.json().get('medicine_dentistry_bachelor'),
                {
                    'date_debut': academic_calendar_2023.start_date.isoformat(),
                    'date_fin': academic_calendar_2023.end_date.isoformat(),
                },
            )

        with freezegun.freeze_time('2024-02-16'):
            response = self.client.get(self.url, format='json')

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertEqual(
                response.json().get('medicine_dentistry_bachelor'),
                {
                    'date_debut': academic_calendar_2024.start_date.isoformat(),
                    'date_fin': academic_calendar_2024.end_date.isoformat(),
                },
            )
