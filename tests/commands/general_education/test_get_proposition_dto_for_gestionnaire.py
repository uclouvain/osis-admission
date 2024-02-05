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
from unittest.mock import ANY, patch

import freezegun
from django.test import TestCase, override_settings
from django.utils.translation import gettext, pgettext
from osis_history.models import HistoryEntry

from admission.contrib.models import GeneralEducationAdmission
from admission.ddd.admission.dtos.bourse import BourseDTO
from admission.ddd.admission.dtos.campus import CampusDTO
from admission.ddd.admission.dtos.formation import FormationDTO, BaseFormationDTO
from admission.ddd.admission.enums import TypeSituationAssimilation
from admission.ddd.admission.formation_continue.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.formation_generale.commands import RecupererPropositionGestionnaireQuery
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.formation_generale.dtos.proposition import PropositionGestionnaireDTO
from admission.tests.factories.faculty_decision import RefusalReasonFactory, AdditionalApprovalConditionFactory
from admission.tests.factories.general_education import (
    GeneralEducationAdmissionFactory,
    GeneralEducationTrainingFactory,
)
from admission.tests.factories.scholarship import ErasmusMundusScholarshipFactory
from base.models.enums.organization_type import MAIN
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.student import StudentFactory
from ddd.logic.learning_unit.dtos import LearningUnitPartimDTO
from infrastructure.messages_bus import message_bus_instance
from program_management.models.education_group_version import EducationGroupVersion
from reference.tests.factories.country import CountryFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
@freezegun.freeze_time('2023-01-01')
class GetPropositionDTOForGestionnaireTestCase(TestCase):
    def setUp(self) -> None:
        school = EntityFactory()
        EntityVersionFactory(entity=school, acronym='SCH')

        self.admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            training__management_entity=school,
            erasmus_mundus_scholarship=None,
            double_degree_scholarship=None,
            international_scholarship=None,
            candidate__private_email='john.doe@example.com',
        )

        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("osis_document.api.utils.get_remote_metadata", return_value={"name": "myfile"})
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

    def test_get_proposition_dto_with_base_data(self):
        result = self._get_command_result()

        self.assertEqual(result.uuid, self.admission.uuid)
        self.assertEqual(
            result.formation,
            FormationDTO(
                sigle=self.admission.training.acronym,
                code=self.admission.training.partial_acronym,
                annee=self.admission.training.academic_year.year,
                date_debut=self.admission.training.academic_year.start_date,
                intitule=self.admission.training.title,
                intitule_fr=self.admission.training.title,
                intitule_en=self.admission.training.title_english,
                campus=ANY,
                type=self.admission.training.education_group_type.name,
                code_domaine=self.admission.training.main_domain.code,
                campus_inscription=CampusDTO(
                    nom='Mons',
                    code_postal='',
                    ville='',
                    pays_iso_code='',
                    nom_pays='',
                    rue='',
                    numero_rue='',
                    boite_postale='',
                    localisation='',
                    email='',
                ),
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
        self.assertEqual(result.bourse_double_diplome, None)
        self.assertEqual(result.bourse_internationale, None)
        self.assertEqual(result.bourse_erasmus_mundus, None)
        self.assertEqual(result.curriculum, self.admission.curriculum)
        self.assertEqual(result.equivalence_diplome, self.admission.diploma_equivalence)
        self.assertEqual(result.est_bachelier_belge, self.admission.is_belgian_bachelor)
        self.assertEqual(result.est_reorientation_inscription_externe, self.admission.is_external_reorientation)
        self.assertEqual(result.attestation_inscription_reguliere, self.admission.regular_registration_proof)
        self.assertEqual(result.est_modification_inscription_externe, self.admission.is_external_modification)
        self.assertEqual(result.formulaire_modification_inscription, self.admission.registration_change_form)
        self.assertEqual(result.est_non_resident_au_sens_decret, self.admission.is_non_resident)
        self.assertEqual(result.pdf_recapitulatif, self.admission.pdf_recap)
        self.assertEqual(result.type, self.admission.type_demande)
        self.assertEqual(result.date_changement_statut, None)
        self.assertEqual(result.genre_candidat, self.admission.candidate.gender)
        self.assertEqual(result.noma_candidat, '')
        self.assertEqual(result.adresse_email_candidat, self.admission.candidate.private_email)
        self.assertEqual(result.langue_contact_candidat, self.admission.candidate.language)
        self.assertEqual(result.nationalite_candidat, '')
        self.assertEqual(result.nationalite_candidat_fr, '')
        self.assertEqual(result.nationalite_candidat_en, '')
        self.assertEqual(result.nationalite_ue_candidat, None)
        self.assertEqual(result.photo_identite_candidat, self.admission.candidate.id_card)
        self.assertEqual(result.candidat_a_plusieurs_demandes, False)
        self.assertEqual(result.titre_acces, '')
        self.assertEqual(result.fraudeur_ares, False)
        self.assertEqual(result.non_financable, False)
        self.assertEqual(result.est_inscription_tardive, None)
        self.assertEqual(result.candidat_vip, False)
        self.assertEqual(result.candidat_assimile, False)

    def test_get_proposition_with_country_of_citizenship(self):
        self.admission.candidate.country_of_citizenship = CountryFactory()
        self.admission.candidate.save()

        result = self._get_command_result()

        self.assertEqual(result.nationalite_candidat, self.admission.candidate.country_of_citizenship.name)
        self.assertEqual(result.nationalite_candidat_fr, self.admission.candidate.country_of_citizenship.name)
        self.assertEqual(result.nationalite_candidat_en, self.admission.candidate.country_of_citizenship.name_en)
        self.assertEqual(result.nationalite_ue_candidat, self.admission.candidate.country_of_citizenship.european_union)

    def test_get_proposition_with_scholarship(self):
        self.admission.erasmus_mundus_scholarship = ErasmusMundusScholarshipFactory()
        self.admission.save()

        result = self._get_command_result()

        self.assertEqual(
            result.bourse_erasmus_mundus,
            BourseDTO(
                uuid=str(self.admission.erasmus_mundus_scholarship.uuid),
                nom_court=self.admission.erasmus_mundus_scholarship.short_name,
                nom_long=self.admission.erasmus_mundus_scholarship.long_name,
                type=self.admission.erasmus_mundus_scholarship.type,
            ),
        )
        self.assertEqual(result.candidat_vip, True)

    def test_get_proposition_with_update_status_history_entry(self):
        self.history_entry = HistoryEntry.objects.create(
            object_uuid=self.admission.uuid, tags=['proposition', 'status-changed']
        )

        result = self._get_command_result()

        self.assertEqual(result.date_changement_statut, self.history_entry.created)

    def test_get_proposition_with_noma(self):
        student = StudentFactory(person=self.admission.candidate)

        result = self._get_command_result()

        self.assertEqual(result.noma_candidat, student.registration_id)

    def test_get_proposition_with_late_enrolment(self):
        self.admission.late_enrollment = True
        self.admission.save()

        result = self._get_command_result()

        self.assertEqual(result.est_inscription_tardive, True)

    def test_get_proposition_with_several_enrolments(self):
        second_admission = GeneralEducationAdmissionFactory(
            candidate=self.admission.candidate,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        result = self._get_command_result()
        self.assertEqual(result.candidat_a_plusieurs_demandes, True)

        second_admission.status = ChoixStatutPropositionGenerale.ANNULEE.name
        second_admission.save()

        result = self._get_command_result()
        self.assertEqual(result.candidat_a_plusieurs_demandes, False)

        second_admission.status = ChoixStatutPropositionGenerale.EN_BROUILLON.name
        second_admission.save()

        result = self._get_command_result()
        self.assertEqual(result.candidat_a_plusieurs_demandes, False)

    def test_get_proposition_with_assimilation(self):
        self.admission.accounting.assimilation_situation = TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name
        self.admission.accounting.save()

        result = self._get_command_result()
        self.assertEqual(result.candidat_assimile, True)

    def test_get_unknown_proposition_triggers_exception(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self._get_command_result(uuid_proposition=uuid.uuid4())

    def test_get_proposition_with_faculty_refusal_reason(self):
        self.admission.fac_refusal_certificate = ['uuid-fac-refusal-certificate']

        # Choose an existing reason
        chosen_reason = RefusalReasonFactory()
        self.admission.refusal_reasons.add(chosen_reason)
        self.admission.other_refusal_reasons = []
        self.admission.save()

        result = self._get_command_result()
        self.assertEqual([str(result.certificat_refus_fac[0])], self.admission.fac_refusal_certificate)
        self.assertEqual(len(result.motifs_refus), 1)
        self.assertEqual(result.motifs_refus[0].motif, chosen_reason.name)
        self.assertEqual(result.motifs_refus[0].categorie, chosen_reason.category.name)

        # Choose a free reason
        self.admission.refusal_reasons.all().delete()
        self.admission.other_refusal_reasons = ['other reason']
        self.admission.save()

        result = self._get_command_result()
        self.assertEqual(len(result.motifs_refus), 1)
        self.assertEqual(result.motifs_refus[0].motif, 'other reason')
        self.assertEqual(result.motifs_refus[0].categorie, pgettext('admission', 'Other reasons'))

    def test_get_proposition_with_faculty_approval_reason(self):
        # Approval data
        self.admission.fac_approval_certificate = ['uuid-fac-approval-certificate']
        self.admission.with_additional_approval_conditions = True
        self.admission.additional_approval_conditions.set(
            [
                AdditionalApprovalConditionFactory(),
                AdditionalApprovalConditionFactory(),
            ]
        )
        self.admission.free_additional_approval_conditions = [
            'first free condition',
            'second free condition',
        ]
        self.admission.other_training_accepted_by_fac = GeneralEducationTrainingFactory(
            academic_year__current=True,
            enrollment_campus__name='Mons',
            enrollment_campus__organization__type=MAIN,
        )

        self.admission.with_prerequisite_courses = True
        self.admission.prerequisite_courses.set(
            [
                LearningUnitYearFactory(),
                LearningUnitYearFactory(),
            ]
        )
        self.admission.prerequisite_courses_fac_comment = 'My comment about the additional trainings'
        self.admission.program_planned_years_number = 3
        self.admission.annual_program_contact_person_name = 'John Doe'
        self.admission.annual_program_contact_person_email = 'john.doe@example.com'
        self.admission.join_program_fac_comment = 'My comment about the join program'

        self.admission.save()

        result = self._get_command_result()
        self.assertEqual([str(result.certificat_approbation_fac[0])], self.admission.fac_approval_certificate)

        self.assertIsNotNone(result.autre_formation_choisie_fac)
        self.assertEqual(
            result.autre_formation_choisie_fac,
            BaseFormationDTO(
                sigle=self.admission.other_training_accepted_by_fac.acronym,
                annee=self.admission.other_training_accepted_by_fac.academic_year.year,
                intitule=self.admission.other_training_accepted_by_fac.title,
                uuid=self.admission.other_training_accepted_by_fac.uuid,
                lieu_enseignement=(
                    EducationGroupVersion.objects.filter(offer=self.admission.other_training_accepted_by_fac)
                    .first()
                    .root_group.main_teaching_campus.name
                ),
            ),
        )

        self.assertEqual(result.avec_conditions_complementaires, self.admission.with_additional_approval_conditions)

        self.assertCountEqual(
            result.conditions_complementaires,
            self.admission.free_additional_approval_conditions
            + [condition.name_fr for condition in self.admission.additional_approval_conditions.all()],
        )

        prerequisite_courses = self.admission.prerequisite_courses.all()
        self.assertEqual(result.avec_complements_formation, self.admission.with_prerequisite_courses)
        self.assertCountEqual(
            result.complements_formation,
            [
                LearningUnitPartimDTO(
                    code=prerequisite_courses[0].acronym,
                    full_title=prerequisite_courses[0].complete_title_i18n,
                ),
                LearningUnitPartimDTO(
                    code=prerequisite_courses[1].acronym,
                    full_title=prerequisite_courses[1].complete_title_i18n,
                ),
            ],
        )
        self.assertEqual(result.commentaire_complements_formation, self.admission.prerequisite_courses_fac_comment)
        self.assertEqual(result.nombre_annees_prevoir_programme, self.admission.program_planned_years_number)
        self.assertEqual(
            result.nom_personne_contact_programme_annuel_annuel,
            self.admission.annual_program_contact_person_name,
        )
        self.assertEqual(
            result.email_personne_contact_programme_annuel_annuel,
            self.admission.annual_program_contact_person_email,
        )
        self.assertEqual(result.commentaire_programme_conjoint, self.admission.join_program_fac_comment)
