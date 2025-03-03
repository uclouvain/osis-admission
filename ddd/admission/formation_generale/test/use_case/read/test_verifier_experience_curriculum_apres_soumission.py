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
from typing import Optional
from unittest import TestCase, mock

from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    ExperiencesAcademiquesNonCompleteesException,
)
from admission.ddd.admission.formation_generale.commands import (
    VerifierExperienceCurriculumApresSoumissionQuery,
)
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import (
    AnneeExperienceAcademique,
    ExperienceAcademique,
    ProfilCandidatInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.enums.community import CommunityEnum
from ddd.logic.shared_kernel.profil.domain.enums import TypeExperience
from osis_profile import BE_ISO_CODE
from osis_profile.models.enums.curriculum import (
    EvaluationSystem,
    Grade,
    Result,
    TranscriptType,
)
from reference.models.enums.cycle import Cycle


class TestVerifierExperienceCVApresSoumissionService(TestCase):
    experience_academiques_complete: Optional[ExperienceAcademique] = None

    def assertHasInstance(self, container, cls, msg=None):
        if not any(isinstance(obj, cls) for obj in container):
            self.fail(msg or f"No instance of '{cls}' has been found")

    def assertHasNoInstance(self, container, cls, msg=None):
        if any(isinstance(obj, cls) for obj in container):
            self.fail(msg or f"Instance of '{cls}' has been found")

    @classmethod
    def setUpClass(cls) -> None:
        cls.experience_academiques_complete = ExperienceAcademique(
            personne='0000000001',
            communaute_fr=True,
            pays=BE_ISO_CODE,
            annees=[
                AnneeExperienceAcademique(
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2011,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_inscrits=10,
                    credits_acquis=10,
                ),
                AnneeExperienceAcademique(
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2013,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_inscrits=10,
                    credits_acquis=10,
                ),
                AnneeExperienceAcademique(
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2014,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_inscrits=10,
                    credits_acquis=10,
                ),
            ],
            traduction_releve_notes=['traduction_releve_notes.pdf'],
            releve_notes=['releve.pdf'],
            type_releve_notes=TranscriptType.ONE_FOR_ALL_YEARS.name,
            a_obtenu_diplome=False,
            diplome=['diplome.pdf'],
            traduction_diplome=['traduction_diplome.pdf'],
            regime_linguistique='',
            note_memoire='17',
            rang_diplome='10',
            resume_memoire=['resume_memoire.pdf'],
            titre_memoire='Titre',
            date_prevue_delivrance_diplome=datetime.date(2019, 1, 1),
            uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee6',
            nom_formation='Formation AA',
            grade_obtenu=Grade.GREAT_DISTINCTION.name,
            systeme_evaluation=EvaluationSystem.ECTS_CREDITS.name,
            adresse_institut='',
            code_institut='',
            communaute_institut='',
            nom_institut='',
            nom_pays='',
            nom_regime_linguistique='',
            type_enseignement='',
            type_institut='',
            nom_formation_equivalente_communaute_fr='',
            cycle_formation='',
        )

    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

        self.proposition_in_memory = PropositionInMemoryRepository()

        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.experiences_academiques = self.candidat_translator.experiences_academiques

        self.proposition = self.proposition_in_memory.get(
            entity_id=PropositionIdentityBuilder.build_from_uuid(uuid='uuid-MASTER-SCI'),
        )

        self.cmd = VerifierExperienceCurriculumApresSoumissionQuery(
            uuid_proposition=self.proposition.entity_id.uuid,
            uuid_experience=self.experience_academiques_complete.uuid,
            type_experience=TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name,
        )

    def tearDown(self):
        mock.patch.stopall()

    def test_should_lever_exception_si_experience_incomplete(self):
        self.experiences_academiques.append(self.experience_academiques_complete)

        with mock.patch.multiple(
            self.experience_academiques_complete,
            a_obtenu_diplome=True,
            diplome=[],
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)

            self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

        with mock.patch.multiple(
            self.experience_academiques_complete,
            a_obtenu_diplome=True,
            diplome=['uuid-diplome'],
            grade_obtenu=Grade.DISTINCTION.name,
        ):
            proposition_id = self.message_bus.invoke(self.cmd)
            self.assertEqual(proposition_id, self.proposition.entity_id)

    def test_should_lever_exception_si_experience_pour_bachelier_fwb_incomplete(self):
        self.experiences_academiques.append(self.experience_academiques_complete)

        with mock.patch.multiple(
            self.experience_academiques_complete,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.FIRST_CYCLE.name,
            credits_acquis_bloc_1=None,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)

            self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

        with mock.patch.multiple(
            self.experience_academiques_complete,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.FIRST_CYCLE.name,
            credits_acquis_bloc_1=10,
        ):
            proposition_id = self.message_bus.invoke(self.cmd)
            self.assertEqual(proposition_id, self.proposition.entity_id)

    def test_should_lever_exception_si_experience_pour_master_fwb_incomplete(self):
        self.experiences_academiques.append(self.experience_academiques_complete)

        with mock.patch.multiple(
            self.experience_academiques_complete,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.SECOND_CYCLE.name,
            avec_complements=None,
            credits_inscrits_complements=None,
            credits_acquis_complements=None,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)

            self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

        with mock.patch.multiple(
            self.experience_academiques_complete,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.SECOND_CYCLE.name,
            avec_complements=True,
            credits_inscrits_complements=10,
            credits_acquis_complements=None,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)

            self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

        with mock.patch.multiple(
            self.experience_academiques_complete,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.SECOND_CYCLE.name,
            avec_complements=True,
            credits_inscrits_complements=None,
            credits_acquis_complements=10,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)

            self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

        with mock.patch.multiple(
            self.experience_academiques_complete,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.SECOND_CYCLE.name,
            avec_complements=True,
            credits_inscrits_complements=20,
            credits_acquis_complements=15,
        ):
            proposition_id = self.message_bus.invoke(self.cmd)
            self.assertEqual(proposition_id, self.proposition.entity_id)

        with mock.patch.multiple(
            self.experience_academiques_complete,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.SECOND_CYCLE.name,
            avec_complements=False,
            credits_inscrits_complements=None,
            credits_acquis_complements=None,
        ):
            proposition_id = self.message_bus.invoke(self.cmd)
            self.assertEqual(proposition_id, self.proposition.entity_id)
