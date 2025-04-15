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
from django.test import TestCase

from admission.ddd.admission.shared_kernel.email_destinataire.dtos.destinataire import (
    InformationsDestinataireDTO,
)
from admission.ddd.admission.shared_kernel.email_destinataire.queries import (
    RecupererInformationsDestinataireQuery,
)
from base.tests.factories.education_group_year import (
    EducationGroupYearCommonBachelorFactory,
    EducationGroupYearFactory,
)
from epc.models.email_fonction_programme import EmailFonctionProgramme
from epc.models.enums.type_email_fonction_programme import TypeEmailFonctionProgramme
from epc.tests.factories.email_fonction_programme import EmailFonctionProgrammeFactory
from infrastructure.messages_bus import message_bus_instance


class GetRecipientInformationTestCase(TestCase):
    def test_get_known_result(self):
        year_program = EducationGroupYearFactory()
        first_email: EmailFonctionProgramme = EmailFonctionProgrammeFactory(
            programme=year_program.education_group,
            premiere_annee=False,
            type=TypeEmailFonctionProgramme.DESTINATAIRE_ADMISSION.name,
        )

        result: InformationsDestinataireDTO = message_bus_instance.invoke(
            RecupererInformationsDestinataireQuery(
                sigle_formation=year_program.acronym,
                annee=year_program.academic_year.year,
                est_premiere_annee=False,
            )
        )

        self.assertEqual(result.en_tete, first_email.en_tete)
        self.assertEqual(result.email, first_email.email)
        self.assertEqual(result.sigle_formation, year_program.acronym)
        self.assertEqual(result.annee, year_program.academic_year.year)
        self.assertEqual(result.pour_premiere_annee, first_email.premiere_annee)

    def test_get_known_result_for_first_year(self):
        year_program = EducationGroupYearFactory()
        first_email: EmailFonctionProgramme = EmailFonctionProgrammeFactory(
            programme=year_program.education_group,
            premiere_annee=True,
            type=TypeEmailFonctionProgramme.DESTINATAIRE_ADMISSION.name,
        )

        result: InformationsDestinataireDTO = message_bus_instance.invoke(
            RecupererInformationsDestinataireQuery(
                sigle_formation=f'{year_program.acronym}-1',
                annee=year_program.academic_year.year,
                est_premiere_annee=True,
            )
        )

        self.assertEqual(result.en_tete, first_email.en_tete)
        self.assertEqual(result.email, first_email.email)
        self.assertEqual(result.sigle_formation, year_program.acronym)
        self.assertEqual(result.annee, year_program.academic_year.year)
        self.assertEqual(result.pour_premiere_annee, first_email.premiere_annee)
