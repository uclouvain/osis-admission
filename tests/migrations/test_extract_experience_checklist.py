# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.test import TestCase

from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
    ChoixStatutPropositionGenerale,
)
from admission.migrations.utils.extract_experience_checklists import (
    extract_experience_authentication_status,
    extract_experience_checklist,
    in_draft_educational_experiences_qs,
    in_draft_exams_qs,
    in_draft_professional_experiences_qs,
    in_draft_secondary_studies_qs,
    update_first_cycle_exam_statuses,
    validated_educational_experiences_qs,
    validated_exams_qs,
    validated_professional_experiences_qs,
    validated_secondary_studies_qs,
)
from admission.models import GeneralEducationAdmission
from admission.models.base import BaseAdmission
from admission.models.exam import AdmissionExam
from admission.models.valuated_epxeriences import (
    AdmissionEducationalValuatedExperiences,
    AdmissionProfessionalValuatedExperiences,
)
from admission.tests.factories.curriculum import (
    AdmissionEducationalValuatedExperiencesFactory,
    AdmissionProfessionalValuatedExperiencesFactory,
    EducationalExperienceFactory,
    ProfessionalExperienceFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.secondary_studies import BelgianHighSchoolDiplomaFactory, ForeignHighSchoolDiplomaFactory
from base.tests.factories.person import PersonFactory
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from epc.models.inscription_programme_annuel import InscriptionProgrammeAnnuel
from epc.tests.factories.inscription_programme_annuel import InscriptionProgrammeAnnuelFactory
from osis_profile.models import (
    EXAM_TYPE_PREMIER_CYCLE_LABEL_FR,
    BelgianHighSchoolDiploma,
    EducationalExperience,
    Exam,
    ForeignHighSchoolDiploma,
    ProfessionalExperience,
)
from osis_profile.models.education import HighSchoolDiploma
from osis_profile.models.enums.experience_validation import (
    ChoixStatutValidationExperience,
    EtatAuthentificationParcours,
)
from osis_profile.models.epc_injection import EPCInjection, ExperienceType
from osis_profile.models.exam import EXAM_TYPE_PREMIER_CYCLE_LABEL_EN
from osis_profile.tests.factories.exam import ExamFactory, ExamTypeFactory
from osis_profile.tests.factories.high_school_diploma import HighSchoolDiplomaFactory


class ExtractExperiencesChecklistTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admission = GeneralEducationAdmissionFactory(
            checklist={'current': {'parcours_anterieur': {'enfants': []}}},
        )

        cls.first_cycle_exam_type = ExamTypeFactory(
            label_fr=EXAM_TYPE_PREMIER_CYCLE_LABEL_FR,
            label_en=EXAM_TYPE_PREMIER_CYCLE_LABEL_EN,
        )

        cls.valid_enrolment_statues = (
            EtatInscriptionFormation.INSCRIT_AU_ROLE,
            EtatInscriptionFormation.PROVISOIRE,
            EtatInscriptionFormation.CESSATION,
        )

    def extract_experience_checklist(
        self,
    ):
        return extract_experience_checklist(
            base_admission_model=BaseAdmission,
            secondary_studies_model=HighSchoolDiploma,
            exam_model=Exam,
            educational_experience_model=EducationalExperience,
            professional_experience_model=ProfessionalExperience,
            epc_injection_model=EPCInjection,
            admission_educational_valuated_experiences_model=AdmissionEducationalValuatedExperiences,
            inscription_programme_annuel_model=InscriptionProgrammeAnnuel,
            admission_professional_valuated_experiences_model=AdmissionProfessionalValuatedExperiences,
            foreign_high_school_diploma_model=ForeignHighSchoolDiploma,
            belgian_high_school_diploma_model=BelgianHighSchoolDiploma,
            admission_exam_model=AdmissionExam,
        )

    def test_in_draft_educational_experiences_qs(self):
        qs = in_draft_educational_experiences_qs(
            educational_experience_model=EducationalExperience,
            epc_injection_model=EPCInjection,
            admission_educational_valuated_experiences_model=AdmissionEducationalValuatedExperiences,
        )

        # No experience
        self.assertEqual(qs.count(), 0)

        # Experience to return
        experience = EducationalExperienceFactory(external_id=None, person=self.admission.candidate)

        self.assertEqual(qs.count(), 1)

        # Experience with epc injection
        epc_injection = EPCInjection.objects.create(
            person=experience.person,
            type_experience=ExperienceType.ACADEMIC.name,
            experience_uuid=experience.uuid,
        )

        self.assertEqual(qs.count(), 0)

        epc_injection.delete()

        # Valuated experience
        valuation = AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=self.admission,
            educationalexperience=experience,
        )

        self.assertEqual(qs.count(), 0)

        valuation.delete()

        # External experience
        experience.external_id = 'EXTERNAL_ID'
        experience.save()

        self.assertEqual(qs.count(), 0)

    def test_in_draft_professional_experiences_qs(self):
        qs = in_draft_professional_experiences_qs(
            professional_experience_model=ProfessionalExperience,
            epc_injection_model=EPCInjection,
            admission_professional_valuated_experiences_model=AdmissionProfessionalValuatedExperiences,
        )

        # No experience
        self.assertEqual(qs.count(), 0)

        # Experience to return
        experience = ProfessionalExperienceFactory(external_id=None, person=self.admission.candidate)

        self.assertEqual(qs.count(), 1)

        # Experience with epc injection
        epc_injection = EPCInjection.objects.create(
            person=experience.person,
            type_experience=ExperienceType.PROFESSIONAL.name,
            experience_uuid=experience.uuid,
        )

        self.assertEqual(qs.count(), 0)

        epc_injection.delete()

        # Valuated experience
        valuation = AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=self.admission,
            professionalexperience=experience,
        )

        self.assertEqual(qs.count(), 0)

        valuation.delete()

        # External experience
        experience.external_id = 'EXTERNAL_ID'
        experience.save()

        self.assertEqual(qs.count(), 0)

    def test_in_draft_secondary_studies_qs(self):
        qs = in_draft_secondary_studies_qs(
            secondary_studies_model=HighSchoolDiploma,
            foreign_high_school_diploma_model=ForeignHighSchoolDiploma,
            belgian_high_school_diploma_model=BelgianHighSchoolDiploma,
            exam_model=Exam,
            epc_injection_model=EPCInjection,
            base_admission_model=BaseAdmission,
            first_cycle_exam_type_id=self.first_cycle_exam_type.id,
        )

        # No experience
        self.assertEqual(qs.count(), 0)

        # Experience to return
        experience = HighSchoolDiplomaFactory(person=self.admission.candidate)

        self.assertEqual(qs.count(), 1)

        # Experience with foreign diploma
        foreign_diploma = ForeignHighSchoolDiplomaFactory(person=experience.person)

        self.assertEqual(qs.count(), 1)

        foreign_diploma.external_id = 'EXTERNAL_ID'
        foreign_diploma.save()

        self.assertEqual(qs.count(), 0)

        foreign_diploma.delete()

        # Experience with belgian diploma
        belgian_diploma = BelgianHighSchoolDiplomaFactory(person=experience.person)

        self.assertEqual(qs.count(), 1)

        belgian_diploma.external_id = 'EXTERNAL_ID'
        belgian_diploma.save()

        self.assertEqual(qs.count(), 0)

        belgian_diploma.delete()

        # Experience with first cycle exam
        exam = ExamFactory(person=experience.person, type=self.first_cycle_exam_type)

        self.assertEqual(qs.count(), 1)

        exam.external_id = 'EXTERNAL_ID'
        exam.save()

        self.assertEqual(qs.count(), 0)

        exam.delete()

        # Experience with epc injection
        epc_injection = EPCInjection.objects.create(
            person=experience.person,
            type_experience=ExperienceType.HIGH_SCHOOL.name,
        )

        self.assertEqual(qs.count(), 0)

        epc_injection.delete()

        # Valuated experience
        GeneralEducationAdmissionFactory(
            candidate=self.admission.candidate,
            valuated_secondary_studies_person=self.admission.candidate,
        )

        self.assertEqual(qs.count(), 0)

    def test_in_draft_exams_qs(self):
        in_draft_admission_statuses = (
            ChoixStatutPropositionGenerale.EN_BROUILLON,
            ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE,
            ChoixStatutPropositionGenerale.ANNULEE,
        )

        qs = in_draft_exams_qs(
            exam_model=Exam,
            admission_exam_model=AdmissionExam,
            first_cycle_exam_type_id=self.first_cycle_exam_type.id,
        )

        # No experience
        self.assertEqual(qs.count(), 0)

        # Experience to return
        experience = ExamFactory(external_id=None, person=self.admission.candidate)
        admission_exam = AdmissionExam.objects.create(admission=self.admission, exam=experience)
        self.admission.status = in_draft_admission_statuses[0].name
        self.admission.save(update_fields=['status'])

        self.assertEqual(qs.count(), 1)

        # Check the admission status
        for status in ChoixStatutPropositionGenerale:
            self.admission.status = status.name
            self.admission.save(update_fields=['status'])

            self.assertEqual(qs.count(), 1 if status in in_draft_admission_statuses else 0)

        self.admission.status = in_draft_admission_statuses[0].name
        self.admission.save(update_fields=['status'])

        # External experience
        experience.external_id = 'EXTERNAL_ID'
        experience.save()

        self.assertEqual(qs.count(), 0)

        experience.external_id = None
        experience.save()

        # No related admission
        admission_exam.delete()
        self.assertEqual(qs.count(), 1)

    def test_validated_educational_experiences_qs(self):
        qs = validated_educational_experiences_qs(
            educational_experience_model=EducationalExperience,
            admission_educational_valuated_experiences_model=AdmissionEducationalValuatedExperiences,
            inscription_programme_annuel_model=InscriptionProgrammeAnnuel,
        )

        # No experience
        self.assertEqual(qs.count(), 0)

        # Experience to return
        experience: EducationalExperience = EducationalExperienceFactory(person=self.admission.candidate)
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=self.admission,
            educationalexperience=experience,
        )

        # External experience
        experience.external_id = 'EXTERNAL_ID'
        experience.save(update_fields=['external_id'])

        self.assertEqual(qs.count(), 1)

        # External experience but in draft
        experience.external_id = 'EXTERNAL_ID'
        experience.validation_status = ChoixStatutValidationExperience.EN_BROUILLON.name
        experience.save()

        self.assertEqual(qs.count(), 0)

        experience.external_id = None
        experience.validation_status = ChoixStatutValidationExperience.A_TRAITER.name
        experience.save()

        # Validated experience
        self.admission.checklist['current']['parcours_anterieur']['enfants'] = [
            {
                'statut': ChoixStatutChecklist.GEST_REUSSITE.name,
                'extra': {'identifiant': str(experience.uuid)},
            }
        ]
        self.admission.save(update_fields=['checklist'])

        self.assertEqual(qs.count(), 1)

        # To complete after enrolment status
        self.admission.checklist['current']['parcours_anterieur']['enfants'] = [
            {
                'statut': ChoixStatutChecklist.GEST_BLOCAGE_ULTERIEUR.name,
                'extra': {'identifiant': str(experience.uuid)},
            }
        ]
        self.admission.save(update_fields=['checklist'])

        self.assertEqual(qs.count(), 0)

        enrolment = InscriptionProgrammeAnnuelFactory(
            admission_uuid=self.admission.uuid,
        )

        for enrolment_status in EtatInscriptionFormation:
            enrolment.etat_inscription = enrolment_status.name
            enrolment.save(update_fields=['etat_inscription'])

            self.assertEqual(qs.count(), 1 if enrolment_status in self.valid_enrolment_statues else 0)

        # Other checklist status
        self.admission.checklist['current']['parcours_anterieur']['enfants'] = [
            {
                'statut': ChoixStatutChecklist.GEST_EN_COURS.name,
                'extra': {'identifiant': str(experience.uuid)},
            }
        ]
        self.admission.save(update_fields=['checklist'])

        self.assertEqual(qs.count(), 0)

    def test_validated_professional_experiences_qs(self):
        qs = validated_professional_experiences_qs(
            professional_experience_model=ProfessionalExperience,
            admission_professional_valuated_experiences_model=AdmissionProfessionalValuatedExperiences,
            inscription_programme_annuel_model=InscriptionProgrammeAnnuel,
        )

        # No experience
        self.assertEqual(qs.count(), 0)

        # Experience to return
        experience: ProfessionalExperience = ProfessionalExperienceFactory(person=self.admission.candidate)
        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=self.admission,
            professionalexperience=experience,
        )

        # External experience
        experience.external_id = 'EXTERNAL_ID'
        experience.save(update_fields=['external_id'])

        self.assertEqual(qs.count(), 1)

        # External experience but in draft
        experience.external_id = 'EXTERNAL_ID'
        experience.validation_status = ChoixStatutValidationExperience.EN_BROUILLON.name
        experience.save()

        self.assertEqual(qs.count(), 0)

        experience.external_id = None
        experience.validation_status = ChoixStatutValidationExperience.A_TRAITER.name
        experience.save()

        # Validated experience
        self.admission.checklist['current']['parcours_anterieur']['enfants'] = [
            {
                'statut': ChoixStatutChecklist.GEST_REUSSITE.name,
                'extra': {'identifiant': str(experience.uuid)},
            }
        ]
        self.admission.save(update_fields=['checklist'])

        self.assertEqual(qs.count(), 1)

        # To complete after enrolment status
        self.admission.checklist['current']['parcours_anterieur']['enfants'] = [
            {
                'statut': ChoixStatutChecklist.GEST_BLOCAGE_ULTERIEUR.name,
                'extra': {'identifiant': str(experience.uuid)},
            }
        ]
        self.admission.save(update_fields=['checklist'])

        self.assertEqual(qs.count(), 0)

        enrolment = InscriptionProgrammeAnnuelFactory(
            admission_uuid=self.admission.uuid,
        )

        for enrolment_status in EtatInscriptionFormation:
            enrolment.etat_inscription = enrolment_status.name
            enrolment.save(update_fields=['etat_inscription'])

            self.assertEqual(qs.count(), 1 if enrolment_status in self.valid_enrolment_statues else 0)

        # Other checklist status
        self.admission.checklist['current']['parcours_anterieur']['enfants'] = [
            {
                'statut': ChoixStatutChecklist.GEST_EN_COURS.name,
                'extra': {'identifiant': str(experience.uuid)},
            }
        ]
        self.admission.save(update_fields=['checklist'])

        self.assertEqual(qs.count(), 0)

    def test_validated_secondary_studies_qs(self):
        qs = validated_secondary_studies_qs(
            secondary_studies_model=HighSchoolDiploma,
            foreign_high_school_diploma_model=ForeignHighSchoolDiploma,
            belgian_high_school_diploma_model=BelgianHighSchoolDiploma,
            exam_model=Exam,
            base_admission_model=BaseAdmission,
            inscription_programme_annuel_model=InscriptionProgrammeAnnuel,
            first_cycle_exam_type_id=self.first_cycle_exam_type.id,
        )

        # No experience
        self.assertEqual(qs.count(), 0)

        # Experience to return
        experience = HighSchoolDiplomaFactory(person=self.admission.candidate)

        # Foreign diploma
        foreign_diploma = ForeignHighSchoolDiplomaFactory(person=self.admission.candidate, external_id=None)

        self.assertEqual(qs.count(), 0)

        foreign_diploma.external_id = 'EXTERNAL_ID'
        foreign_diploma.save()

        self.assertEqual(qs.count(), 1)

        # In draft experience
        experience.validation_status = ChoixStatutValidationExperience.EN_BROUILLON.name
        experience.save()

        self.assertEqual(qs.count(), 0)

        experience.validation_status = ChoixStatutValidationExperience.A_TRAITER.name
        experience.save()
        foreign_diploma.delete()

        # Belgian diploma
        belgian_diploma = BelgianHighSchoolDiplomaFactory(person=self.admission.candidate, external_id=None)

        self.assertEqual(qs.count(), 0)

        belgian_diploma.external_id = 'EXTERNAL_ID'
        belgian_diploma.save()

        self.assertEqual(qs.count(), 1)

        belgian_diploma.delete()

        # First cycle exam
        first_cycle_exam = ExamFactory(person=self.admission.candidate, type=self.first_cycle_exam_type)

        self.assertEqual(qs.count(), 0)

        first_cycle_exam.external_id = 'EXTERNAL_ID'
        first_cycle_exam.save()

        self.assertEqual(qs.count(), 1)

        first_cycle_exam.delete()

        # Another exam
        exam = ExamFactory(person=self.admission.candidate, external_id='EXTERNAL_ID')

        self.assertEqual(qs.count(), 0)

        exam.delete()

        # Validated experience
        self.admission.checklist['current']['parcours_anterieur']['enfants'] = [
            {
                'statut': ChoixStatutChecklist.GEST_REUSSITE.name,
                'extra': {'identifiant': 'ETUDES_SECONDAIRES'},
            }
        ]
        self.admission.save(update_fields=['checklist'])

        self.assertEqual(qs.count(), 1)

        # To complete after enrolment status
        self.admission.checklist['current']['parcours_anterieur']['enfants'] = [
            {
                'statut': ChoixStatutChecklist.GEST_BLOCAGE_ULTERIEUR.name,
                'extra': {'identifiant': 'ETUDES_SECONDAIRES'},
            }
        ]
        self.admission.save(update_fields=['checklist'])

        self.assertEqual(qs.count(), 0)

        enrolment = InscriptionProgrammeAnnuelFactory(
            admission_uuid=self.admission.uuid,
        )

        for enrolment_status in EtatInscriptionFormation:
            enrolment.etat_inscription = enrolment_status.name
            enrolment.save(update_fields=['etat_inscription'])

            self.assertEqual(qs.count(), 1 if enrolment_status in self.valid_enrolment_statues else 0)

        # Other checklist status
        self.admission.checklist['current']['parcours_anterieur']['enfants'] = [
            {
                'statut': ChoixStatutChecklist.GEST_EN_COURS.name,
                'extra': {'identifiant': 'ETUDES_SECONDAIRES'},
            }
        ]
        self.admission.save(update_fields=['checklist'])

        self.assertEqual(qs.count(), 0)

    def test_validated_exam_qs(self):
        qs = validated_exams_qs(
            exam_model=Exam,
            admission_exam_model=AdmissionExam,
            first_cycle_exam_type_id=self.first_cycle_exam_type.id,
        )

        # No experience
        self.assertEqual(qs.count(), 0)

        # Experience to return
        experience = ExamFactory(person=self.admission.candidate)
        admission_exam = AdmissionExam.objects.create(admission=self.admission, exam=experience)

        # External experience
        experience.external_id = 'EXTERNAL_ID'
        experience.save()

        self.assertEqual(qs.count(), 1)

        # In draft experience
        experience.validation_status = ChoixStatutValidationExperience.EN_BROUILLON.name
        experience.save()

        self.assertEqual(qs.count(), 0)

        # First cycle diploma
        experience.external_id = None
        experience.validation_status = ChoixStatutValidationExperience.A_TRAITER.name
        previous_type = experience.type
        experience.type = self.first_cycle_exam_type
        experience.save()

        self.assertEqual(qs.count(), 0)

        experience.type = previous_type
        experience.save()

        validated_admission_statuses = (ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE,)

        # Check the admission status
        for status in ChoixStatutPropositionGenerale:
            self.admission.status = status.name
            self.admission.save(update_fields=['status'])

            self.assertEqual(qs.count(), 1 if status in validated_admission_statuses else 0)

        self.admission.status = validated_admission_statuses[0].name
        self.admission.save(update_fields=['status'])

        admission_exam.delete()

        self.assertEqual(qs.count(), 0)

    def test_update_first_cycle_exam_statuses(self):
        first_first_cycle_exam = ExamFactory(
            type=self.first_cycle_exam_type,
            validation_status=ChoixStatutValidationExperience.EN_BROUILLON.name,
            authentication_status=EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name,
        )

        second_first_cycle_exam = ExamFactory(
            type=self.first_cycle_exam_type,
            validation_status=ChoixStatutValidationExperience.EN_BROUILLON.name,
            authentication_status=EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name,
        )

        other_exam = ExamFactory(
            validation_status=ChoixStatutValidationExperience.EN_BROUILLON.name,
            authentication_status=EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name,
        )

        HighSchoolDiplomaFactory(
            person=first_first_cycle_exam.person,
            validation_status=ChoixStatutValidationExperience.AUTHENTIFICATION.name,
            authentication_status=EtatAuthentificationParcours.VRAI.name,
        )

        HighSchoolDiplomaFactory(
            person=other_exam.person,
            validation_status=ChoixStatutValidationExperience.AVIS_EXPERT.name,
            authentication_status=EtatAuthentificationParcours.FAUX.name,
        )

        updates_number = update_first_cycle_exam_statuses(
            exam_model=Exam,
            secondary_studies_model=HighSchoolDiploma,
            first_cycle_exam_type_id=self.first_cycle_exam_type.id,
        )

        self.assertEqual(updates_number, 1)

        first_first_cycle_exam.refresh_from_db()
        second_first_cycle_exam.refresh_from_db()
        other_exam.refresh_from_db()

        # Updated
        self.assertEqual(
            first_first_cycle_exam.validation_status,
            ChoixStatutValidationExperience.AUTHENTIFICATION.name,
        )
        self.assertEqual(first_first_cycle_exam.authentication_status, EtatAuthentificationParcours.VRAI.name)

        # Not updated because there is no related high school diploma
        self.assertEqual(other_exam.validation_status, ChoixStatutValidationExperience.EN_BROUILLON.name)
        self.assertEqual(other_exam.authentication_status, EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name)

        # Not updated because it's not a first cycle exam
        self.assertEqual(other_exam.validation_status, ChoixStatutValidationExperience.EN_BROUILLON.name)
        self.assertEqual(other_exam.authentication_status, EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name)

    def test_extraction(self):
        person = PersonFactory()

        # Educational experiences
        in_draft_educational_experience = EducationalExperienceFactory(person=person)
        validated_educational_experience = EducationalExperienceFactory(person=person)
        to_be_processed_educational_experience = EducationalExperienceFactory(person=person)

        # Professional experiences
        in_draft_professional_experience = ProfessionalExperienceFactory(person=person)
        validated_professional_experience = ProfessionalExperienceFactory(person=person, external_id='EXTERNAL_ID')
        to_be_processed_professional_experience = ProfessionalExperienceFactory(person=person)

        # High school diploma
        high_school_diploma = HighSchoolDiplomaFactory(person=person)

        # Exam
        first_cycle_exam = ExamFactory(person=person, type=self.first_cycle_exam_type)
        in_draft_exam = ExamFactory(person=person)
        validated_exam = ExamFactory(person=person, external_id='EXTERNAL_ID')

        admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            checklist={
                'current': {
                    'parcours_anterieur': {
                        'enfants': [
                            {
                                'extra': {
                                    'identifiant': str(validated_educational_experience.uuid),
                                    'etat_authentification': EtatAuthentificationParcours.VRAI.name,
                                },
                                'statut': ChoixStatutChecklist.GEST_REUSSITE.name,
                            },
                            {
                                'extra': {
                                    'identifiant': str(to_be_processed_educational_experience.uuid),
                                    'etat_authentification': EtatAuthentificationParcours.FAUX.name,
                                },
                                'statut': ChoixStatutChecklist.GEST_EN_COURS.name,
                            },
                            {
                                'extra': {
                                    'identifiant': str(validated_professional_experience.uuid),
                                    'etat_authentification': EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name,
                                },
                                'statut': ChoixStatutChecklist.INITIAL_CANDIDAT.name,
                            },
                            {
                                'extra': {
                                    'identifiant': str(to_be_processed_professional_experience.uuid),
                                    'etat_authentification': EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name,
                                },
                                'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
                            },
                            {
                                'extra': {
                                    'identifiant': 'ETUDES_SECONDAIRES',
                                    'etat_authentification': EtatAuthentificationParcours.NON_CONCERNE.name,
                                },
                                'statut': ChoixStatutChecklist.GEST_BLOCAGE_ULTERIEUR.name,
                            },
                            {
                                'extra': {
                                    'identifiant': str(validated_exam.uuid),
                                    'etat_authentification': EtatAuthentificationParcours.VRAI.name,
                                },
                                'statut': ChoixStatutChecklist.INITIAL_CANDIDAT.name,
                            },
                        ]
                    }
                }
            },
            valuated_secondary_studies_person=person,
            candidate=person,
        )

        InscriptionProgrammeAnnuelFactory(
            admission_uuid=admission.uuid,
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
        )

        # Educational experiences
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=admission,
            educationalexperience=validated_educational_experience,
        )
        AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=admission,
            educationalexperience=to_be_processed_educational_experience,
        )

        # Professional experiences
        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=admission,
            professionalexperience=validated_professional_experience,
        )
        AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=admission,
            professionalexperience=to_be_processed_professional_experience,
        )

        # Exams
        AdmissionExam.objects.create(admission=admission, exam=validated_exam)

        self.extract_experience_checklist()

        in_draft_educational_experience.refresh_from_db()
        self.assertEqual(
            in_draft_educational_experience.validation_status,
            ChoixStatutValidationExperience.EN_BROUILLON.name,
        )
        self.assertEqual(
            in_draft_educational_experience.authentication_status,
            EtatAuthentificationParcours.NON_CONCERNE.name,
        )

        validated_educational_experience.refresh_from_db()
        self.assertEqual(
            validated_educational_experience.validation_status,
            ChoixStatutValidationExperience.VALIDEE.name,
        )
        self.assertEqual(
            validated_educational_experience.authentication_status,
            EtatAuthentificationParcours.VRAI.name,
        )

        to_be_processed_educational_experience.refresh_from_db()
        self.assertEqual(
            to_be_processed_educational_experience.validation_status,
            ChoixStatutValidationExperience.A_TRAITER.name,
        )
        self.assertEqual(
            to_be_processed_educational_experience.authentication_status,
            EtatAuthentificationParcours.FAUX.name,
        )

        in_draft_professional_experience.refresh_from_db()
        self.assertEqual(
            in_draft_professional_experience.validation_status,
            ChoixStatutValidationExperience.EN_BROUILLON.name,
        )
        self.assertEqual(
            in_draft_professional_experience.authentication_status,
            EtatAuthentificationParcours.NON_CONCERNE.name,
        )

        validated_professional_experience.refresh_from_db()
        self.assertEqual(
            validated_professional_experience.validation_status,
            ChoixStatutValidationExperience.VALIDEE.name,
        )
        self.assertEqual(
            validated_professional_experience.authentication_status,
            EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name,
        )

        to_be_processed_professional_experience.refresh_from_db()
        self.assertEqual(
            to_be_processed_professional_experience.validation_status,
            ChoixStatutValidationExperience.A_TRAITER.name,
        )
        self.assertEqual(
            to_be_processed_professional_experience.authentication_status,
            EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name,
        )

        high_school_diploma.refresh_from_db()
        self.assertEqual(
            high_school_diploma.validation_status,
            ChoixStatutValidationExperience.VALIDEE.name,
        )
        self.assertEqual(
            high_school_diploma.authentication_status,
            EtatAuthentificationParcours.NON_CONCERNE.name,
        )

        first_cycle_exam.refresh_from_db()
        self.assertEqual(
            first_cycle_exam.validation_status,
            ChoixStatutValidationExperience.VALIDEE.name,
        )
        self.assertEqual(
            first_cycle_exam.authentication_status,
            EtatAuthentificationParcours.NON_CONCERNE.name,
        )

        in_draft_exam.refresh_from_db()
        self.assertEqual(
            in_draft_exam.validation_status,
            ChoixStatutValidationExperience.EN_BROUILLON.name,
        )
        self.assertEqual(
            in_draft_exam.authentication_status,
            EtatAuthentificationParcours.NON_CONCERNE.name,
        )

        validated_exam.refresh_from_db()
        self.assertEqual(
            validated_exam.validation_status,
            ChoixStatutValidationExperience.VALIDEE.name,
        )
        self.assertEqual(
            validated_exam.authentication_status,
            EtatAuthentificationParcours.VRAI.name,
        )


class ExtractExperienceAuthenticationStatusTestCase(TestCase):
    def extract_experience_authentication_status(self):
        return extract_experience_authentication_status(
            base_admission_model=BaseAdmission,
            educational_experience_model=EducationalExperience,
            exam_model=Exam,
            professional_experience_model=ProfessionalExperience,
            secondary_studies_model=HighSchoolDiploma,
        )

    @classmethod
    def setUpTestData(cls):
        cls.experience_uuid = uuid.uuid4()

        cls.admission = GeneralEducationAdmissionFactory(
            checklist={
                'current': {
                    'parcours_anterieur': {
                        'enfants': [
                            {
                                'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
                                'extra': {
                                    'identifiant': str(cls.experience_uuid),
                                    'etat_authentification': EtatAuthentificationParcours.VRAI.name,
                                },
                            },
                            {
                                'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
                                'extra': {
                                    'identifiant': 'ETUDES_SECONDAIRES',
                                    'etat_authentification': EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name,
                                },
                            },
                        ]
                    }
                }
            },
        )

    def test_with_educational_experience(self):
        experience: EducationalExperience = EducationalExperienceFactory(
            uuid=self.experience_uuid, person=self.admission.candidate
        )

        self.extract_experience_authentication_status()

        experience.refresh_from_db()

        self.assertEqual(experience.authentication_status, EtatAuthentificationParcours.VRAI.name)

    def test_with_professional_experience(self):
        experience: ProfessionalExperience = ProfessionalExperienceFactory(
            uuid=self.experience_uuid, person=self.admission.candidate
        )

        self.extract_experience_authentication_status()

        experience.refresh_from_db()

        self.assertEqual(experience.authentication_status, EtatAuthentificationParcours.VRAI.name)

    def test_with_exam(self):
        experience: Exam = ExamFactory(uuid=self.experience_uuid, person=self.admission.candidate)

        self.extract_experience_authentication_status()

        experience.refresh_from_db()

        self.assertEqual(experience.authentication_status, EtatAuthentificationParcours.VRAI.name)

    def test_with_secondary_studies(self):
        experience: HighSchoolDiploma = HighSchoolDiplomaFactory(person=self.admission.candidate)

        self.extract_experience_authentication_status()

        experience.refresh_from_db()

        self.assertEqual(experience.authentication_status, EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name)

    def test_status_priority(self):
        experience: EducationalExperience = EducationalExperienceFactory(person=self.admission.candidate)

        high_school_diploma: HighSchoolDiploma = HighSchoolDiplomaFactory(person=self.admission.candidate)

        first_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            candidate=self.admission.candidate,
            checklist={
                'current': {
                    'parcours_anterieur': {
                        'enfants': [
                            {
                                'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
                                'extra': {
                                    'identifiant': str(experience.uuid),
                                    'etat_authentification': EtatAuthentificationParcours.NON_CONCERNE.name,
                                },
                            },
                            {
                                'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
                                'extra': {
                                    'identifiant': 'ETUDES_SECONDAIRES',
                                    'etat_authentification': EtatAuthentificationParcours.NON_CONCERNE.name,
                                },
                            },
                        ]
                    }
                }
            },
        )

        second_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            candidate=first_admission.candidate,
            checklist=first_admission.checklist,
        )

        def _test_priority(
            reference_status: EtatAuthentificationParcours, priority_statuses: list[EtatAuthentificationParcours]
        ):
            first_admission.checklist['current']['parcours_anterieur']['enfants'][0]['extra'][
                'etat_authentification'
            ] = reference_status.name
            first_admission.checklist['current']['parcours_anterieur']['enfants'][1]['extra'][
                'etat_authentification'
            ] = reference_status.name
            first_admission.save(update_fields=['checklist'])

            for status in EtatAuthentificationParcours:
                target_status = status if status in priority_statuses else reference_status

                second_admission.checklist['current']['parcours_anterieur']['enfants'][0]['extra'][
                    'etat_authentification'
                ] = status.name
                second_admission.checklist['current']['parcours_anterieur']['enfants'][1]['extra'][
                    'etat_authentification'
                ] = status.name
                second_admission.save(update_fields=['checklist'])

                self.extract_experience_authentication_status()

                experience.refresh_from_db()
                self.assertEqual(experience.authentication_status, target_status.name)

                high_school_diploma.refresh_from_db()
                self.assertEqual(high_school_diploma.authentication_status, target_status.name)

        _test_priority(
            reference_status=EtatAuthentificationParcours.VRAI,
            priority_statuses=[],
        )

        _test_priority(
            reference_status=EtatAuthentificationParcours.FAUX,
            priority_statuses=[
                EtatAuthentificationParcours.VRAI,
            ],
        )

        _test_priority(
            reference_status=EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE,
            priority_statuses=[
                EtatAuthentificationParcours.FAUX,
                EtatAuthentificationParcours.VRAI,
            ],
        )

        _test_priority(
            reference_status=EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE,
            priority_statuses=[
                EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE,
                EtatAuthentificationParcours.FAUX,
                EtatAuthentificationParcours.VRAI,
            ],
        )
