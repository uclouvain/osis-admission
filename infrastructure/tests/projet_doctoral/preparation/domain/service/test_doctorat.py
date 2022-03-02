# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
import mock
from django.test import SimpleTestCase

from base.models.enums.education_group_types import TrainingType
from ddd.logic.formation_catalogue.dtos import TrainingDto
from admission.infrastructure.projet_doctoral.preparation.domain.service.doctorat import DoctoratTranslator
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance as message_bus_instance


class TestDoctoratTranslator(SimpleTestCase):
    def setUp(self) -> None:
        self._mock_message_bus()
        self.doctorat_translator = DoctoratTranslator()
        self.sigle_secteur_entite_gestion = 'SST'
        self.annee = 2020

    def _mock_message_bus(self):
        message_bus_patcher = mock.patch.multiple(
            'admission.infrastructure.message_bus',
            DoctoratTranslator=lambda: self.doctorat_translator,
        )
        message_bus_patcher.start()
        self.addCleanup(message_bus_patcher.stop)
        self.message_bus = message_bus_instance

    @mock.patch("infrastructure.messages_bus.search_formations")
    def test_should_renvoyer_aucun_resultat(self, mock_search_formations):
        mock_search_formations.return_value = []
        result = self.doctorat_translator.search(self.sigle_secteur_entite_gestion, self.annee)
        self.assertEqual(list(), result)

    @mock.patch("infrastructure.messages_bus.search_formations")
    def test_should_renvoyer_detail_doctorat(self, mock_search_formations):
        mock_search_formations.return_value = [_get_training_dto('SST', 'AGRO3DP', self.annee)]
        result = self.doctorat_translator.search(self.sigle_secteur_entite_gestion, self.annee)
        dto = result[0]
        self.assertEqual(dto.sigle, 'AGRO3DP')
        self.assertEqual(dto.annee, self.annee)
        self.assertEqual(dto.sigle_entite_gestion, 'SST')
        self.assertEqual(dto.intitule_fr, 'Intitule du doctorat (Mons)')
        self.assertEqual(dto.intitule_en, 'Title of PHD (Mons)')

    @mock.patch("infrastructure.messages_bus.search_formations")
    def test_should_filtre_doctorat_uniquement(self, mock_search_formations):
        mock_search_formations.return_value = [_get_training_dto('SST', 'AGRO3DP', self.annee)]
        self.doctorat_translator.search(self.sigle_secteur_entite_gestion, self.annee)
        search_formation_cmd = mock_search_formations.call_args[0][0]
        self.assertEqual(search_formation_cmd.type, TrainingType.PHD.name)


def _get_training_dto(sigle_gestion, sigle, annee):
    return TrainingDto(
        acronym=sigle,
        year=annee,
        code='',
        uuid='',
        type=TrainingType.PHD.name,
        credits='',
        schedule_type='',
        duration='',
        start_year='',
        title_fr='Intitule du doctorat',
        partial_title_fr='',
        title_en='Title of PHD',
        partial_title_en='',
        status='',
        keywords='',
        internship_presence='',
        is_enrollment_enabled='',
        has_online_re_registration='',
        has_partial_deliberation='',
        has_admission_exam='',
        has_dissertation='',
        produce_university_certificate='',
        decree_category='',
        rate_code='',
        main_language_name='',
        english_activities='',
        other_language_activities='',
        internal_comment='',
        main_domain_decree_name='',
        main_domain_code='',
        main_domain_name='',
        secondary_domains='',
        isced_domain_code='',
        isced_domain_title_fr='',
        isced_domain_title_en='',
        management_entity_acronym=sigle_gestion,
        administration_entity_acronym='',
        end_year='',
        enrollment_campus_name='Mons',
        enrollment_campus_university_name='',
        other_campus_activities='',
        funding_can_be_funded='',
        funding_orientation='',
        funding_can_be_international_funded='',
        funding_international_funding_orientation='',
        ares_code='',
        ares_graca='',
        ares_authorization='',
        co_graduation_code_inter_cfb='',
        co_graduation_coefficient='',
        co_organizations='',
        academic_type='',
        duration_unit='',
        diploma_leads_to_diploma='',
        diploma_printing_title='',
        diploma_professional_title='',
        diploma_aims='',
    )
