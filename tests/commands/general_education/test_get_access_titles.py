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
from typing import List, Dict
from unittest.mock import patch

import freezegun
from django.test import TestCase

from admission.contrib.models import GeneralEducationAdmission
from admission.contrib.models.base import (
    AdmissionEducationalValuatedExperiences,
    AdmissionProfessionalValuatedExperiences,
)
from admission.ddd.admission.domain.model.enums.condition_acces import (
    TypeTitreAccesSelectionnable,
)
from admission.ddd.admission.dtos.titre_acces_selectionnable import TitreAccesSelectionnableDTO
from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from admission.ddd.admission.formation_generale.commands import RecupererTitresAccesSelectionnablesPropositionQuery
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.tests.factories.curriculum import (
    ProfessionalExperienceFactory,
    EducationalExperienceFactory,
    EducationalExperienceYearFactory,
)
from admission.tests.factories.general_education import (
    GeneralEducationTrainingFactory,
    GeneralEducationAdmissionFactory,
)
from admission.tests.factories.secondary_studies import (
    BelgianHighSchoolDiplomaFactory,
    ForeignHighSchoolDiplomaFactory,
    HighSchoolDiplomaAlternativeFactory,
)
from base.models.enums.education_group_types import TrainingType
from base.models.enums.got_diploma import GotDiploma
from base.tests.factories.academic_year import AcademicYearFactory
from infrastructure.messages_bus import message_bus_instance
from osis_profile.models import BelgianHighSchoolDiploma, ForeignHighSchoolDiploma, HighSchoolDiplomaAlternative
from osis_profile.models.enums.curriculum import Result


@freezegun.freeze_time('2023-01-01')
class GetAccessTitlesViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.training = GeneralEducationTrainingFactory(
            academic_year=cls.academic_years[0],
            education_group_type__name=TrainingType.BACHELOR.name,
        )

    def test_get_access_titles_with_no_experience(self):
        general_admission = GeneralEducationAdmissionFactory(
            training=self.training,
        )

        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
            )
        )

        self.assertEqual(len(access_titles), 0)

    def test_get_access_title_with_cv_academic_experience(self):
        access_titles: List[TitreAccesSelectionnableDTO]

        general_admission = GeneralEducationAdmissionFactory(
            training=self.training,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Add an educational experience
        educational_experience = EducationalExperienceFactory(person=general_admission.candidate, obtained_diploma=True)

        educational_experience_uuid = educational_experience.uuid

        for year in self.academic_years:
            EducationalExperienceYearFactory(
                educational_experience=educational_experience,
                result=Result.SUCCESS.name,
                academic_year=year,
            )

        # The experience has not been valuated so we don't retrieve the experience
        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
            )
        )

        self.assertEqual(len(access_titles), 0)

        # The experience has been valuated so we retrieve it
        AdmissionEducationalValuatedExperiences.objects.create(
            baseadmission=general_admission,
            educationalexperience=educational_experience,
        )

        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
            )
        )

        self.assertEqual(len(access_titles), 1)
        self.assertIn(educational_experience_uuid, access_titles)

        self.assertEqual(access_titles[educational_experience_uuid].uuid_experience, educational_experience.uuid)
        self.assertEqual(
            access_titles[educational_experience_uuid].type_titre,
            TypeTitreAccesSelectionnable.EXPERIENCE_ACADEMIQUE.name,
        )
        self.assertEqual(access_titles[educational_experience_uuid].annee, self.academic_years[1].year)
        self.assertEqual(access_titles[educational_experience_uuid].selectionne, False)

        # Only retrieve selected access titles if specified
        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
                seulement_selectionnes=True,
            )
        )

        self.assertEqual(len(access_titles), 0)

        # The diploma has not been obtained
        educational_experience.obtained_diploma = False
        educational_experience.save()

        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
            )
        )

        self.assertEqual(len(access_titles), 0)

        # The diploma has not been obtained but the results of one year are in progress
        educational_experience.educationalexperienceyear_set.filter(academic_year=self.academic_years[-1]).update(
            result=Result.WAITING_RESULT.name,
        )

        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
            )
        )

        self.assertEqual(len(access_titles), 1)
        self.assertIn(educational_experience_uuid, access_titles)

    def test_get_access_title_with_cv_non_academic_experience(self):
        access_titles: List[TitreAccesSelectionnableDTO]

        general_admission = GeneralEducationAdmissionFactory(
            training=self.training,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Add an educational experience
        non_educational_experience = ProfessionalExperienceFactory(
            person=general_admission.candidate,
            end_date=datetime.date(2022, 1, 1),
        )

        non_educational_experience_uuid = non_educational_experience.uuid

        # The experience has not been valuated so we don't retrieve the experience
        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
            )
        )

        self.assertEqual(len(access_titles), 0)

        # The experience has been valuated so we retrieve it
        AdmissionProfessionalValuatedExperiences.objects.create(
            baseadmission=general_admission,
            professionalexperience=non_educational_experience,
            is_access_title=True,
        )

        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
            )
        )

        self.assertEqual(len(access_titles), 1)
        self.assertIn(non_educational_experience_uuid, access_titles)

        self.assertEqual(
            access_titles[non_educational_experience_uuid].uuid_experience, non_educational_experience.uuid
        )
        self.assertEqual(
            access_titles[non_educational_experience_uuid].type_titre,
            TypeTitreAccesSelectionnable.EXPERIENCE_NON_ACADEMIQUE.name,
        )
        self.assertEqual(access_titles[non_educational_experience_uuid].annee, 2021)
        self.assertEqual(access_titles[non_educational_experience_uuid].selectionne, True)

        # Change related year
        non_educational_experience.end_date = datetime.date(2022, 9, 15)
        non_educational_experience.save()

        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
            )
        )

        self.assertEqual(len(access_titles), 1)
        self.assertIn(non_educational_experience_uuid, access_titles)
        self.assertEqual(access_titles[non_educational_experience_uuid].annee, 2022)

    @patch("osis_document.contrib.fields.FileField._confirm_multiple_upload")
    def test_get_access_title_with_high_school_diploma(self, confirm_multiple_upload):
        confirm_multiple_upload.side_effect = (
            lambda _, value, __: ["550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92"] if value else []
        )

        access_titles: Dict[str, TitreAccesSelectionnableDTO]

        general_admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training=self.training,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
        )

        # Belgian high school diploma
        belgian_high_school_diploma = BelgianHighSchoolDiplomaFactory(
            person=general_admission.candidate,
            academic_graduation_year=self.academic_years[1],
        )

        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
            )
        )

        self.assertEqual(len(access_titles), 1)
        self.assertIn(belgian_high_school_diploma.uuid, access_titles)

        self.assertEqual(
            access_titles[belgian_high_school_diploma.uuid].uuid_experience, belgian_high_school_diploma.uuid
        )
        self.assertEqual(
            access_titles[belgian_high_school_diploma.uuid].type_titre,
            TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES.name,
        )
        self.assertEqual(access_titles[belgian_high_school_diploma.uuid].annee, 2022)
        self.assertEqual(access_titles[belgian_high_school_diploma.uuid].selectionne, False)

        # Only retrieve selected access titles if specified
        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
                seulement_selectionnes=True,
            )
        )

        self.assertEqual(len(access_titles), 0)

        # The diploma has been selected as access title
        general_admission.are_secondary_studies_access_title = True
        general_admission.save()

        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
                seulement_selectionnes=True,
            )
        )

        self.assertEqual(len(access_titles), 1)
        self.assertIn(belgian_high_school_diploma.uuid, access_titles)
        self.assertEqual(access_titles[belgian_high_school_diploma.uuid].selectionne, True)

        # Foreign high school diploma
        belgian_high_school_diploma.delete()

        foreign_high_school_diploma = ForeignHighSchoolDiplomaFactory(
            person=general_admission.candidate,
            academic_graduation_year=self.academic_years[0],
        )

        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
            ),
        )

        self.assertEqual(len(access_titles), 1)
        self.assertIn(foreign_high_school_diploma.uuid, access_titles)

        self.assertEqual(
            access_titles[foreign_high_school_diploma.uuid].uuid_experience, foreign_high_school_diploma.uuid
        )
        self.assertEqual(
            access_titles[foreign_high_school_diploma.uuid].type_titre,
            TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES.name,
        )
        self.assertEqual(access_titles[foreign_high_school_diploma.uuid].annee, 2021)
        self.assertEqual(access_titles[foreign_high_school_diploma.uuid].selectionne, True)

        # High school diploma alternative
        foreign_high_school_diploma.delete()

        high_school_diploma_alternative = HighSchoolDiplomaAlternativeFactory(
            person=general_admission.candidate,
        )

        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
            )
        )

        self.assertEqual(len(access_titles), 0)

        high_school_diploma_alternative.first_cycle_admission_exam = ['file.pdf']
        high_school_diploma_alternative.save()

        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
            )
        )

        self.assertEqual(len(access_titles), 1)
        self.assertIn(high_school_diploma_alternative.uuid, access_titles)

        self.assertEqual(
            access_titles[high_school_diploma_alternative.uuid].uuid_experience,
            high_school_diploma_alternative.uuid,
        )
        self.assertEqual(
            access_titles[high_school_diploma_alternative.uuid].type_titre,
            TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES.name,
        )
        self.assertEqual(access_titles[high_school_diploma_alternative.uuid].annee, None)
        self.assertEqual(access_titles[high_school_diploma_alternative.uuid].selectionne, True)

        high_school_diploma_alternative.delete()

        # The candidate specified that he has a secondary education but without more information
        general_admission.candidate.graduated_from_high_school = GotDiploma.YES.name
        general_admission.candidate.graduated_from_high_school_year = general_admission.training.academic_year
        general_admission.candidate.save()

        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
            )
        )

        self.assertEqual(len(access_titles), 1)

        self.assertIn(OngletsDemande.ETUDES_SECONDAIRES.name, access_titles)

        current_access_title = access_titles[OngletsDemande.ETUDES_SECONDAIRES.name]

        self.assertEqual(current_access_title.type_titre, TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES.name)
        self.assertEqual(current_access_title.annee, general_admission.candidate.graduated_from_high_school_year.year)
        self.assertEqual(current_access_title.selectionne, True)

        general_admission.candidate.graduated_from_high_school = GotDiploma.THIS_YEAR.name
        general_admission.candidate.save()

        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
            )
        )

        self.assertEqual(len(access_titles), 1)

        self.assertIn(OngletsDemande.ETUDES_SECONDAIRES.name, access_titles)

        current_access_title = access_titles[OngletsDemande.ETUDES_SECONDAIRES.name]

        self.assertEqual(current_access_title.type_titre, TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES.name)
        self.assertEqual(current_access_title.annee, general_admission.candidate.graduated_from_high_school_year.year)
        self.assertEqual(current_access_title.selectionne, True)

        # The candidate specified that he had no secondary education
        general_admission.candidate.graduated_from_high_school = GotDiploma.NO.name
        general_admission.candidate.graduated_from_high_school_year = None
        general_admission.candidate.save()

        access_titles = message_bus_instance.invoke(
            RecupererTitresAccesSelectionnablesPropositionQuery(
                uuid_proposition=general_admission.uuid,
            )
        )

        self.assertEqual(len(access_titles), 0)
