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
import uuid

import freezegun
from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import resolve, reverse
from rest_framework import status

from admission.ddd.admission.dtos import EtudesSecondairesAdmissionDTO
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
    ContinuingEducationTrainingFactory,
)
from admission.tests.factories.roles import SicManagementRoleFactory, ProgramManagerRoleFactory
from admission.tests.factories.secondary_studies import (
    BelgianHighSchoolDiplomaFactory,
    ForeignHighSchoolDiplomaFactory,
    HighSchoolDiplomaAlternativeFactory,
)
from base.models.enums.community import CommunityEnum
from base.models.enums.establishment_type import EstablishmentTypeEnum
from base.models.enums.got_diploma import GotDiploma
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.entity_version_address import EntityVersionAddressFactory
from base.tests.factories.organization import OrganizationFactory
from ddd.logic.shared_kernel.profil.dtos.etudes_secondaires import (
    ValorisationEtudesSecondairesDTO,
    DiplomeBelgeEtudesSecondairesDTO,
    DiplomeEtrangerEtudesSecondairesDTO,
    AlternativeSecondairesDTO,
)
from osis_profile import BE_ISO_CODE
from osis_profile.models import BelgianHighSchoolDiploma, HighSchoolDiplomaAlternative, ForeignHighSchoolDiploma
from osis_profile.models.enums.education import ForeignDiplomaTypes, Equivalence
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time('2022-01-01')
class AdmissionEducationDetailViewForContinuingEducationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]

        cls.training = ContinuingEducationTrainingFactory(
            academic_year=cls.academic_years[1],
            management_entity=EntityVersionFactory().entity,
        )

        cls.sic_manager_user = SicManagementRoleFactory(
            entity=cls.training.management_entity,
        ).person.user

        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.training.education_group,
        ).person.user

        cls.first_institute = OrganizationFactory(
            name='UCL',
            community=CommunityEnum.FRENCH_SPEAKING.name,
            establishment_type=EstablishmentTypeEnum.UNIVERSITY.name,
        )

        cls.be_country = CountryFactory(iso_code=BE_ISO_CODE)

        cls.first_institute_address = EntityVersionAddressFactory(
            entity_version__entity__organization=cls.first_institute,
            city='Louvain-la-Neuve',
            street='Place de la République',
            street_number='1',
            postal_code='1348',
            country=cls.be_country,
            entity_version__parent=None,
        )

    def setUp(self):
        self.continuing_admission = ContinuingEducationAdmissionFactory(
            training=self.training,
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
            candidate__graduated_from_high_school='',
            candidate__graduated_from_high_school_year=None,
        )

        self.url = resolve_url('admission:continuing-education:education', uuid=self.continuing_admission.uuid)

    def test_get_with_sic_manager_user_is_allowed(self):
        self.client.force_login(self.sic_manager_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_with_program_manager_user_is_allowed(self):
        self.client.force_login(self.program_manager_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_secondary_studies_with_no_specified_data(self):
        self.client.force_login(self.program_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        secondary_studies: EtudesSecondairesAdmissionDTO = response.context['etudes_secondaires']

        self.assertEqual(secondary_studies.diplome_belge, None)
        self.assertEqual(secondary_studies.diplome_etranger, None)
        self.assertEqual(secondary_studies.alternative_secondaires, None)
        self.assertEqual(secondary_studies.diplome_etudes_secondaires, '')
        self.assertEqual(secondary_studies.annee_diplome_etudes_secondaires, None)
        self.assertEqual(secondary_studies.injectee, False)
        self.assertEqual(secondary_studies.identifiant_externe, None)
        self.assertEqual(
            secondary_studies.valorisation,
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[],
            ),
        )

    def test_get_secondary_studies_with_belgian_diploma(self):
        diploma: BelgianHighSchoolDiploma = BelgianHighSchoolDiplomaFactory(
            person=self.continuing_admission.candidate,
        )

        self.continuing_admission.candidate.graduated_from_high_school = GotDiploma.YES.name
        self.continuing_admission.candidate.graduated_from_high_school_year = self.academic_years[2]
        self.continuing_admission.candidate.save()

        self.client.force_login(self.program_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        secondary_studies: EtudesSecondairesAdmissionDTO = response.context['etudes_secondaires']

        self.assertEqual(
            secondary_studies.diplome_belge,
            DiplomeBelgeEtudesSecondairesDTO(
                uuid=diploma.uuid,
                diplome=diploma.high_school_diploma,
                type_enseignement=diploma.educational_type,
                autre_type_enseignement=diploma.educational_other,
                nom_institut=diploma.other_institute_name,
                adresse_institut=diploma.other_institute_address,
                communaute=diploma.community,
            ),
        )
        self.assertEqual(secondary_studies.diplome_etranger, None)
        self.assertEqual(secondary_studies.alternative_secondaires, None)
        self.assertEqual(secondary_studies.diplome_etudes_secondaires, GotDiploma.YES.name)
        self.assertEqual(secondary_studies.annee_diplome_etudes_secondaires, self.academic_years[2].year)
        self.assertEqual(secondary_studies.injectee, False)
        self.assertEqual(secondary_studies.identifiant_externe, None)
        self.assertEqual(
            secondary_studies.valorisation,
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[],
            ),
        )

        # With institute
        diploma.institute = self.first_institute
        diploma.other_institute_name = ''
        diploma.other_institute_address = ''
        diploma.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        secondary_studies: EtudesSecondairesAdmissionDTO = response.context['etudes_secondaires']

        self.assertEqual(
            secondary_studies.diplome_belge,
            DiplomeBelgeEtudesSecondairesDTO(
                uuid=diploma.uuid,
                diplome=diploma.high_school_diploma,
                type_enseignement=diploma.educational_type,
                autre_type_enseignement=diploma.educational_other,
                nom_institut=diploma.institute.name,
                adresse_institut='{street} {street_number}, {postal_code} {city}'.format(
                    street=self.first_institute_address.street,
                    street_number=self.first_institute_address.street_number,
                    postal_code=self.first_institute_address.postal_code,
                    city=self.first_institute_address.city,
                ),
                communaute=diploma.community,
            ),
        )

    def test_get_secondary_studies_with_foreign_diploma(self):
        diploma: ForeignHighSchoolDiploma = ForeignHighSchoolDiplomaFactory(
            person=self.continuing_admission.candidate,
            foreign_diploma_type=ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
            other_linguistic_regime='Unknown language',
            high_school_transcript=[uuid.uuid4()],
            high_school_transcript_translation=[uuid.uuid4()],
            high_school_diploma_translation=[uuid.uuid4()],
            equivalence=Equivalence.YES.name,
            final_equivalence_decision_ue=[uuid.uuid4()],
            final_equivalence_decision_not_ue=[uuid.uuid4()],
            equivalence_decision_proof=[uuid.uuid4()],
            restrictive_equivalence_daes=[uuid.uuid4()],
            restrictive_equivalence_admission_test=[uuid.uuid4()],
        )

        self.continuing_admission.candidate.graduated_from_high_school = GotDiploma.THIS_YEAR.name
        self.continuing_admission.candidate.graduated_from_high_school_year = self.academic_years[2]
        self.continuing_admission.candidate.save()

        self.client.force_login(self.program_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        secondary_studies: EtudesSecondairesAdmissionDTO = response.context['etudes_secondaires']

        self.assertEqual(secondary_studies.diplome_belge, None)
        self.assertEqual(
            secondary_studies.diplome_etranger,
            DiplomeEtrangerEtudesSecondairesDTO(
                uuid=diploma.uuid,
                type_diplome=diploma.foreign_diploma_type,
                regime_linguistique=diploma.linguistic_regime.code,
                pays_regime_linguistique=diploma.linguistic_regime.name,
                pays_membre_ue=diploma.country.european_union,
                pays_iso_code=diploma.country.iso_code,
                pays_nom=diploma.country.name,
                releve_notes=diploma.high_school_transcript,
                traduction_releve_notes=diploma.high_school_transcript_translation,
                diplome=diploma.high_school_diploma,
                traduction_diplome=diploma.high_school_diploma_translation,
                equivalence=diploma.equivalence,
                decision_final_equivalence_ue=diploma.final_equivalence_decision_ue,
                decision_final_equivalence_hors_ue=diploma.final_equivalence_decision_not_ue,
                preuve_decision_equivalence=diploma.equivalence_decision_proof,
            ),
        )
        self.assertEqual(secondary_studies.alternative_secondaires, None)
        self.assertEqual(secondary_studies.diplome_etudes_secondaires, GotDiploma.THIS_YEAR.name)
        self.assertEqual(secondary_studies.annee_diplome_etudes_secondaires, self.academic_years[2].year)
        self.assertEqual(secondary_studies.injectee, False)
        self.assertEqual(secondary_studies.identifiant_externe, None)
        self.assertEqual(
            secondary_studies.valorisation,
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[],
            ),
        )

    def test_get_secondary_studies_with_diploma_alternative(self):
        diploma: HighSchoolDiplomaAlternative = HighSchoolDiplomaAlternativeFactory(
            person=self.continuing_admission.candidate,
            first_cycle_admission_exam=[uuid.uuid4()],
        )

        self.continuing_admission.candidate.graduated_from_high_school = GotDiploma.NO.name
        self.continuing_admission.candidate.save()

        self.client.force_login(self.program_manager_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        secondary_studies: EtudesSecondairesAdmissionDTO = response.context['etudes_secondaires']

        self.assertEqual(secondary_studies.diplome_belge, None)
        self.assertEqual(secondary_studies.diplome_etranger, None)
        self.assertEqual(
            secondary_studies.alternative_secondaires,
            AlternativeSecondairesDTO(
                uuid=diploma.uuid, examen_admission_premier_cycle=diploma.first_cycle_admission_exam
            ),
        )
        self.assertEqual(secondary_studies.diplome_etudes_secondaires, GotDiploma.NO.name)
        self.assertEqual(secondary_studies.annee_diplome_etudes_secondaires, None)
        self.assertEqual(secondary_studies.injectee, False)
        self.assertEqual(secondary_studies.identifiant_externe, None)
        self.assertEqual(
            secondary_studies.valorisation,
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[],
            ),
        )
