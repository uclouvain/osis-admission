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
from unittest.mock import patch

from django.test import TestCase, override_settings

from admission.tests.factories.curriculum import (
    ProfessionalExperienceFactory,
    AdmissionProfessionalValuatedExperiencesFactory,
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
    AdmissionEducationalValuatedExperiencesFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.utils import get_missing_curriculum_periods
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.enums.got_diploma import GotDiploma
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.student import StudentFactory
from epc.models.enums.decision_resultat_cycle import DecisionResultatCycle
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from epc.models.enums.type_duree import TypeDuree
from epc.tests.factories.inscription_programme_annuel import InscriptionProgrammeAnnuelFactory
from epc.tests.factories.inscription_programme_cycle import InscriptionProgrammeCycleFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class GetMissingCurriculumPeriodsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = {
            year.year: year for year in AcademicYearFactory.produce(base_year=2015, number_past=5, number_future=5)
        }

    def setUp(self):
        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            return_value={
                "name": "myfile",
                "explicit_name": "My file",
                "author": "0123456",
                "mimetype": PDF_MIME_TYPE,
                "size": 1,
            },
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
            side_effect=lambda _, tokens, __: tokens,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.admission = GeneralEducationAdmissionFactory(
            submitted_at=datetime.datetime(2015, 1, 15),
        )

    def test_no_cv_experience(self):
        result = get_missing_curriculum_periods(proposition_uuid=self.admission.uuid)

        self.assertCountEqual(
            result,
            [
                'De Septembre 2010 à Février 2011',
                'De Septembre 2011 à Février 2012',
                'De Septembre 2012 à Février 2013',
                'De Septembre 2013 à Février 2014',
                'De Septembre 2014 à Décembre 2014',
            ],
        )

    def test_with_secondary_studies(self):
        self.admission.candidate.graduated_from_high_school = GotDiploma.YES.name
        self.admission.candidate.graduated_from_high_school_year = self.academic_years[2012]
        self.admission.candidate.save()

        result = get_missing_curriculum_periods(proposition_uuid=self.admission.uuid)

        self.assertCountEqual(
            result,
            [
                'De Septembre 2013 à Février 2014',
                'De Septembre 2014 à Décembre 2014',
            ],
        )

    def test_with_non_academic_experiences(self):
        non_academic_experience = ProfessionalExperienceFactory(
            person=self.admission.candidate,
            start_date=datetime.date(2011, 10, 1),
            end_date=datetime.date(2014, 1, 31),
        )

        result = get_missing_curriculum_periods(proposition_uuid=self.admission.uuid)

        # No changes as the experience has not been valuated
        self.assertCountEqual(
            result,
            [
                'De Septembre 2010 à Février 2011',
                'De Septembre 2011 à Février 2012',
                'De Septembre 2012 à Février 2013',
                'De Septembre 2013 à Février 2014',
                'De Septembre 2014 à Décembre 2014',
            ],
        )

        # Valuation of the non-academic experience
        valuation = AdmissionProfessionalValuatedExperiencesFactory(
            baseadmission=self.admission,
            professionalexperience=non_academic_experience,
        )

        result = get_missing_curriculum_periods(proposition_uuid=self.admission.uuid)

        self.assertCountEqual(
            result,
            [
                'De Septembre 2010 à Février 2011',
                'Septembre 2011',
                'Février 2014',
                'De Septembre 2014 à Décembre 2014',
            ],
        )

    def test_with_academic_experiences(self):
        academic_experience = EducationalExperienceFactory(
            person=self.admission.candidate,
        )

        academic_experience_years = [
            EducationalExperienceYearFactory(
                educational_experience=academic_experience,
                academic_year=self.academic_years[year],
            )
            for year in [2011, 2013, 2014]
        ]

        result = get_missing_curriculum_periods(proposition_uuid=self.admission.uuid)

        # No changes as the experience has not been valuated
        self.assertCountEqual(
            result,
            [
                'De Septembre 2010 à Février 2011',
                'De Septembre 2011 à Février 2012',
                'De Septembre 2012 à Février 2013',
                'De Septembre 2013 à Février 2014',
                'De Septembre 2014 à Décembre 2014',
            ],
        )

        # Valuation of the non-academic experience
        valuation = AdmissionEducationalValuatedExperiencesFactory(
            baseadmission=self.admission,
            educationalexperience=academic_experience,
        )

        result = get_missing_curriculum_periods(proposition_uuid=self.admission.uuid)

        self.assertCountEqual(
            result,
            [
                'De Septembre 2010 à Février 2011',
                'De Septembre 2012 à Février 2013',
            ],
        )

        academic_experience.transcript = []
        academic_experience.save()

        # No changes as the experience is incomplete
        result = get_missing_curriculum_periods(proposition_uuid=self.admission.uuid)

        self.assertCountEqual(
            result,
            [
                'De Septembre 2010 à Février 2011',
                'De Septembre 2011 à Février 2012',
                'De Septembre 2012 à Février 2013',
                'De Septembre 2013 à Février 2014',
                'De Septembre 2014 à Décembre 2014',
            ],
        )

    def test_with_internal_experience(self):
        student = StudentFactory(person=self.admission.candidate)

        pce_a = InscriptionProgrammeCycleFactory(
            etudiant=student,
            decision=DecisionResultatCycle.DISTINCTION.name,
            sigle_formation="SF1",
        )
        pce_a_pae_a = InscriptionProgrammeAnnuelFactory(
            programme_cycle=pce_a,
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            programme__offer__academic_year=self.academic_years[2010],
            programme__root_group__academic_year=self.academic_years[2010],
            type_duree=TypeDuree.NORMAL.name,
        )
        pce_a_pae_b = InscriptionProgrammeAnnuelFactory(
            programme_cycle=pce_a,
            etat_inscription=EtatInscriptionFormation.ERREUR.name,
            programme__offer__academic_year=self.academic_years[2012],
            programme__root_group__academic_year=self.academic_years[2012],
            type_duree=TypeDuree.NORMAL.name,
        )
        pce_a_pae_c = InscriptionProgrammeAnnuelFactory(
            programme_cycle=pce_a,
            etat_inscription=EtatInscriptionFormation.FIN_DE_CYCLE.name,
            programme__offer__academic_year=self.academic_years[2013],
            programme__root_group__academic_year=self.academic_years[2013],
            type_duree=TypeDuree.NORMAL.name,
        )
        pce_b = InscriptionProgrammeCycleFactory(
            etudiant=student,
            decision=DecisionResultatCycle.DISTINCTION.name,
            sigle_formation="SF2",
        )
        pce_b_pae_a = InscriptionProgrammeAnnuelFactory(
            programme_cycle=pce_b,
            etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            programme__offer__academic_year=self.academic_years[2014],
            programme__root_group__academic_year=self.academic_years[2014],
            type_duree=TypeDuree.NORMAL.name,
        )

        result = get_missing_curriculum_periods(proposition_uuid=self.admission.uuid)

        self.assertCountEqual(
            result,
            [
                'De Septembre 2011 à Février 2012',
                'De Septembre 2012 à Février 2013',
            ],
        )
