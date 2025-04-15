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
from typing import List

from django.test import TestCase

from admission.ddd.admission.shared_kernel.email_destinataire.dtos.destinataire import (
    InformationsDestinataireDTO,
)
from admission.ddd.admission.shared_kernel.email_destinataire.queries import (
    RecupererInformationsDestinataireQuery,
    RecupererInformationsDestinatairesQuery,
)
from base.tests.factories.education_group_year import (
    EducationGroupYearCommonBachelorFactory,
    EducationGroupYearFactory,
)
from epc.models.email_fonction_programme import EmailFonctionProgramme
from epc.models.enums.type_email_fonction_programme import TypeEmailFonctionProgramme
from epc.tests.factories.email_fonction_programme import EmailFonctionProgrammeFactory
from infrastructure.messages_bus import message_bus_instance


class SearchRecipientsInformationTestCase(TestCase):
    def test_search_known_results(self):
        year_program = EducationGroupYearFactory()
        other_year_program = EducationGroupYearFactory()
        first_email: EmailFonctionProgramme = EmailFonctionProgrammeFactory(
            programme=year_program.education_group,
            premiere_annee=False,
            type=TypeEmailFonctionProgramme.DESTINATAIRE_ADMISSION.name,
        )
        second_email: EmailFonctionProgramme = EmailFonctionProgrammeFactory(
            programme=year_program.education_group,
            premiere_annee=False,
            type=TypeEmailFonctionProgramme.DESTINATAIRE_ADMISSION.name,
        )
        third_email: EmailFonctionProgramme = EmailFonctionProgrammeFactory(
            programme=year_program.education_group,
            premiere_annee=True,
            type=TypeEmailFonctionProgramme.DESTINATAIRE_ADMISSION.name,
        )
        other_email: EmailFonctionProgramme = EmailFonctionProgrammeFactory(
            programme=other_year_program.education_group,
            premiere_annee=False,
            type=TypeEmailFonctionProgramme.DESTINATAIRE_ADMISSION.name,
        )

        results: List[InformationsDestinataireDTO] = message_bus_instance.invoke(
            RecupererInformationsDestinatairesQuery(
                sigle_formation=year_program.acronym,
                annee=year_program.academic_year.year,
                est_premiere_annee=False,
            )
        )

        self.assertEqual(len(results), 2)

        self.assertCountEqual(
            results,
            [
                InformationsDestinataireDTO(
                    en_tete=first_email.en_tete,
                    email=first_email.email,
                    sigle_formation=year_program.acronym,
                    annee=year_program.academic_year.year,
                    pour_premiere_annee=first_email.premiere_annee,
                ),
                InformationsDestinataireDTO(
                    en_tete=second_email.en_tete,
                    email=second_email.email,
                    sigle_formation=year_program.acronym,
                    annee=year_program.academic_year.year,
                    pour_premiere_annee=second_email.premiere_annee,
                ),
            ],
        )

        results: List[InformationsDestinataireDTO] = message_bus_instance.invoke(
            RecupererInformationsDestinatairesQuery(
                sigle_formation=year_program.acronym + '-1',
                annee=year_program.academic_year.year,
                est_premiere_annee=True,
            )
        )

        self.assertEqual(len(results), 1)

        self.assertCountEqual(
            results,
            [
                InformationsDestinataireDTO(
                    en_tete=third_email.en_tete,
                    email=third_email.email,
                    sigle_formation=year_program.acronym,
                    annee=year_program.academic_year.year,
                    pour_premiere_annee=third_email.premiere_annee,
                ),
            ],
        )

    def test_search_unknown_results(self):
        year_program = EducationGroupYearFactory()
        first_email: EmailFonctionProgramme = EmailFonctionProgrammeFactory(
            programme=year_program.education_group,
            premiere_annee=False,
            type=TypeEmailFonctionProgramme.DESTINATAIRE_ADMISSION.name,
        )

        results: List[InformationsDestinataireDTO] = message_bus_instance.invoke(
            RecupererInformationsDestinatairesQuery(
                sigle_formation=f'{year_program.acronym}B',
                annee=year_program.academic_year.year,
                est_premiere_annee=False,
            )
        )

        self.assertEqual(len(results), 0)
