# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
from unittest import TestCase, mock

import freezegun

from admission.ddd import BE_ISO_CODE
from admission.ddd.admission.domain.validator.exceptions import (
    ConditionsAccessNonRempliesException,
    QuestionsSpecifiquesCurriculumNonCompleteesException,
    QuestionsSpecifiquesEtudesSecondairesNonCompleteesException,
    QuestionsSpecifiquesInformationsComplementairesNonCompleteesException,
    QuestionsSpecifiquesChoixFormationNonCompleteesException,
)
from admission.ddd.admission.formation_generale.commands import VerifierPropositionCommand
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    FichierCurriculumNonRenseigneException,
    EquivalenceNonRenseigneeException,
    ContinuationBachelierNonRenseigneeException,
    AttestationContinuationBachelierNonRenseigneeException,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import (
    ProfilCandidatInMemoryTranslator,
    ExperienceAcademique,
    AnneeExperienceAcademique,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository
from osis_profile.models.enums.curriculum import Result


class TestVerifierPropositionService(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

        self.academic_year_repository = AcademicYearInMemoryRepository()
        self.proposition_in_memory = PropositionInMemoryRepository()

        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.experiences_academiques = self.candidat_translator.experiences_academiques

        self.master_proposition = self.proposition_in_memory.get(
            entity_id=PropositionIdentityBuilder.build_from_uuid(uuid='uuid-MASTER-SCI'),
        )
        self.bachelier_proposition = self.proposition_in_memory.get(
            entity_id=PropositionIdentityBuilder.build_from_uuid(uuid='uuid-BACHELIER-ECO1'),
        )
        self.bachelier_veto_proposition = self.proposition_in_memory.get(
            entity_id=PropositionIdentityBuilder.build_from_uuid(uuid='uuid-BACHELIER-VET'),
        )
        self.aggregation_proposition = self.proposition_in_memory.get(
            entity_id=PropositionIdentityBuilder.build_from_uuid(uuid='uuid-AGGREGATION-ECO'),
        )
        self.capaes_proposition = self.proposition_in_memory.get(
            entity_id=PropositionIdentityBuilder.build_from_uuid(uuid='uuid-CAPAES-ECO'),
        )

        for annee in range(2016, 2023):
            self.academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )
        # Mock datetime to return the 2020 year as the current year
        patcher = freezegun.freeze_time('2020-11-01')
        patcher.start()
        self.addCleanup(patcher.stop)
        self.cmd = lambda uuid: VerifierPropositionCommand(uuid_proposition=uuid)

    def test_should_verifier_etre_ok_si_complet_pour_master(self):
        proposition_id = self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
        self.assertEqual(proposition_id.uuid, self.master_proposition.entity_id.uuid)

    def test_should_verifier_etre_ok_si_complet_pour_bachelier(self):
        proposition_id = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertEqual(proposition_id.uuid, self.bachelier_proposition.entity_id.uuid)

    def test_should_verifier_etre_ok_si_complet_pour_bachelier_veto(self):
        proposition_id = self.message_bus.invoke(self.cmd(self.bachelier_veto_proposition.entity_id.uuid))
        self.assertEqual(proposition_id.uuid, self.bachelier_veto_proposition.entity_id.uuid)

    def test_should_verifier_etre_ok_si_complet_pour_aggregation(self):
        proposition_id = self.message_bus.invoke(self.cmd(self.aggregation_proposition.entity_id.uuid))
        self.assertEqual(proposition_id.uuid, self.aggregation_proposition.entity_id.uuid)

    def test_should_verifier_etre_ok_si_complet_pour_capaes(self):
        proposition_id = self.message_bus.invoke(self.cmd(self.capaes_proposition.entity_id.uuid))
        self.assertEqual(proposition_id.uuid, self.capaes_proposition.entity_id.uuid)

    def test_should_retourner_erreur_si_conditions_acces_non_remplies(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd('uuid-BACHELIER-ECO2'))
        self.assertEqual(len(context.exception.exceptions), 1)
        self.assertIsInstance(context.exception.exceptions.pop(), ConditionsAccessNonRempliesException)

    def test_should_retourner_erreur_si_fichier_pdf_cv_non_fourni_master(self):
        with mock.patch.multiple(self.master_proposition, curriculum=[]):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
            self.assertEqual(len(context.exception.exceptions), 1)
            self.assertIsInstance(context.exception.exceptions.pop(), FichierCurriculumNonRenseigneException)

    def test_should_retourner_erreur_si_equivalence_non_fournie_aggregation(self):
        with mock.patch.multiple(self.aggregation_proposition, equivalence_diplome=[]):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.aggregation_proposition.entity_id.uuid))
            self.assertEqual(len(context.exception.exceptions), 1)
            self.assertIsInstance(context.exception.exceptions.pop(), EquivalenceNonRenseigneeException)

    def test_should_retourner_erreur_si_equivalence_non_fournie_capaes(self):
        with mock.patch.multiple(self.capaes_proposition, equivalence_diplome=[]):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.capaes_proposition.entity_id.uuid))
            self.assertEqual(len(context.exception.exceptions), 1)
            self.assertIsInstance(context.exception.exceptions.pop(), EquivalenceNonRenseigneeException)

    def test_should_verifier_etre_ok_si_equivalence_non_fournie_avec_experience_belge_aggregation(self):
        self.experiences_academiques.append(
            ExperienceAcademique(
                personne='0000000002',
                communaute_fr=True,
                pays=BE_ISO_CODE,
                annees=[
                    AnneeExperienceAcademique(annee=2015, resultat=Result.SUCCESS.name),
                ],
            ),
        )
        with mock.patch.multiple(self.aggregation_proposition, equivalence_diplome=[]):
            proposition_id = self.message_bus.invoke(self.cmd(self.aggregation_proposition.entity_id.uuid))
            self.assertEqual(proposition_id.uuid, self.aggregation_proposition.entity_id.uuid)

    def test_should_retourner_erreur_si_continuation_cycle_bachelier_non_remplie_avec_succes(self):
        with mock.patch.multiple(self.bachelier_proposition, continuation_cycle_bachelier=None):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
            self.assertEqual(len(context.exception.exceptions), 1)
            self.assertIsInstance(context.exception.exceptions.pop(), ContinuationBachelierNonRenseigneeException)

    def test_should_verifier_etre_ok_si_continuation_cycle_bachelier_non_remplie_sans_succes(self):
        with mock.patch.multiple(self.bachelier_proposition, continuation_cycle_bachelier=None):
            for exp in self.experiences_academiques:
                if exp.personne == self.bachelier_proposition.matricule_candidat:
                    for a in exp.annees:
                        a.resultat = Result.SUCCESS_WITH_RESIDUAL_CREDITS.name
            proposition_id = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
            self.assertEqual(proposition_id.uuid, self.bachelier_proposition.entity_id.uuid)

    def test_should_verifier_etre_ok_si_continuation_cycle_bachelier_est_faux(self):
        with mock.patch.multiple(self.bachelier_proposition, continuation_cycle_bachelier=False):
            proposition_id = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
            self.assertEqual(proposition_id.uuid, self.bachelier_proposition.entity_id.uuid)

    def test_should_retourner_erreur_si_attestation_continuation_cycle_bachelier_non_remplie_si_continuation_veto(self):
        with mock.patch.multiple(
            self.bachelier_veto_proposition,
            continuation_cycle_bachelier=True,
            attestation_continuation_cycle_bachelier=[],
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.bachelier_veto_proposition.entity_id.uuid))
            self.assertEqual(len(context.exception.exceptions), 1)
            self.assertIsInstance(
                context.exception.exceptions.pop(),
                AttestationContinuationBachelierNonRenseigneeException,
            )

    def test_should_verifier_etre_ok_si_continuation_cycle_bachelier_est_faux_et_pas_attestation_veto(self):
        with mock.patch.multiple(
            self.bachelier_veto_proposition,
            continuation_cycle_bachelier=False,
            attestation_continuation_cycle_bachelier=[],
        ):
            proposition_id = self.message_bus.invoke(self.cmd(self.bachelier_veto_proposition.entity_id.uuid))
            self.assertEqual(proposition_id.uuid, self.bachelier_veto_proposition.entity_id.uuid)

    def test_should_retourner_erreur_si_questions_specifiques_pas_completees_pour_curriculum(self):
        with mock.patch.multiple(
            self.master_proposition,
            reponses_questions_specifiques={
                **self.master_proposition.reponses_questions_specifiques,
                '16de0c3d-3c06-4c93-8eb4-c8648f04f142': '',
            },
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
            self.assertIsInstance(
                context.exception.exceptions.pop(),
                QuestionsSpecifiquesCurriculumNonCompleteesException,
            )

    def test_should_retourner_erreur_si_questions_specifiques_pas_completees_pour_etudes_secondaires(self):
        with mock.patch.multiple(
            self.master_proposition,
            reponses_questions_specifiques={
                **self.master_proposition.reponses_questions_specifiques,
                '16de0c3d-3c06-4c93-8eb4-c8648f04f143': '',
            },
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
            self.assertIsInstance(
                context.exception.exceptions.pop(),
                QuestionsSpecifiquesEtudesSecondairesNonCompleteesException,
            )

    def test_should_retourner_erreur_si_questions_specifiques_pas_completees_pour_informations_additionnelles(self):
        with mock.patch.multiple(
            self.master_proposition,
            reponses_questions_specifiques={
                **self.master_proposition.reponses_questions_specifiques,
                '16de0c3d-3c06-4c93-8eb4-c8648f04f144': '',
            },
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
            self.assertIsInstance(
                context.exception.exceptions.pop(),
                QuestionsSpecifiquesInformationsComplementairesNonCompleteesException,
            )

    def test_should_retourner_erreur_si_questions_specifiques_pas_completees_pour_choix_formation(self):
        with mock.patch.multiple(
            self.master_proposition,
            reponses_questions_specifiques={
                **self.master_proposition.reponses_questions_specifiques,
                '16de0c3d-3c06-4c93-8eb4-c8648f04f140': '',
            },
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
            self.assertIsInstance(
                context.exception.exceptions.pop(),
                QuestionsSpecifiquesChoixFormationNonCompleteesException,
            )
