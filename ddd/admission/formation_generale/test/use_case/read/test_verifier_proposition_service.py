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
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    ReductionDesDroitsInscriptionNonCompleteeException,
    AbsenceDeDetteNonCompleteeException,
    AssimilationNonCompleteeException,
    CarteBancaireRemboursementIbanNonCompleteException,
    CarteBancaireRemboursementAutreFormatNonCompleteException,
    AffiliationsNonCompleteesException,
)
from admission.ddd.admission.domain.validator.exceptions import (
    ConditionsAccessNonRempliesException,
    QuestionsSpecifiquesChoixFormationNonCompleteesException,
    QuestionsSpecifiquesCurriculumNonCompleteesException,
    QuestionsSpecifiquesEtudesSecondairesNonCompleteesException,
    QuestionsSpecifiquesInformationsComplementairesNonCompleteesException,
)
from admission.ddd.admission.formation_generale.commands import VerifierPropositionQuery
from admission.ddd.admission.enums import (
    TypeSituationAssimilation,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    LienParente,
    ChoixAssimilation5,
    ChoixAssimilation6,
    ChoixTypeCompteBancaire,
)
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    AttestationContinuationBachelierNonRenseigneeException,
    ContinuationBachelierNonRenseigneeException,
    EquivalenceNonRenseigneeException,
    FichierCurriculumNonRenseigneException,
)
from admission.ddd.admission.formation_generale.test.factory.proposition import _ComptabiliteFactory
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import (
    AnneeExperienceAcademique,
    ExperienceAcademique,
    ProfilCandidatInMemoryTranslator,
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
        self.candidat = self.candidat_translator.profil_candidats[1]

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
        self.cmd = lambda uuid: VerifierPropositionQuery(uuid_proposition=uuid)

    def _test_should_retourner_erreur_si_comptabilite_incomplete(self, comptabilite, exception):
        with mock.patch.object(self.master_proposition, 'comptabilite', comptabilite):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(uuid='uuid-MASTER-SCI'))
            self.assertTrue(any(member for member in context.exception.exceptions if isinstance(member, exception)))

    def _test_should_retourner_erreur_si_assimilation_incomplete(self, comptabilite, exception):
        with mock.patch.object(self.candidat, 'pays_nationalite', 'CA'):
            self._test_should_retourner_erreur_si_comptabilite_incomplete(
                comptabilite=comptabilite,
                exception=exception,
            )

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

    def _test_should_retourner_erreur_si_assimilation_incomplete(self, comptabilite, exception):
        with mock.patch.object(self.candidat, 'pays_nationalite', 'CA'):
            self._test_should_retourner_erreur_si_comptabilite_incomplete(
                comptabilite=comptabilite,
                exception=exception,
            )

    def test_should_retourner_erreur_si_comptabilite_incomplete_pour_document_enfant_personnel(self):
        self._test_should_retourner_erreur_si_comptabilite_incomplete(
            comptabilite=_ComptabiliteFactory(enfant_personnel=True, attestation_enfant_personnel=[]),
            exception=ReductionDesDroitsInscriptionNonCompleteeException,
        )

    def test_should_retourner_erreur_si_absence_dettes_incomplet(self):
        self._test_should_retourner_erreur_si_comptabilite_incomplete(
            comptabilite=_ComptabiliteFactory(attestation_absence_dette_etablissement=[]),
            exception=AbsenceDeDetteNonCompleteeException,
        )

    def test_should_retourner_erreur_si_comptabilite_incomplete_pour_indication_enfant_personnel(self):
        self._test_should_retourner_erreur_si_comptabilite_incomplete(
            comptabilite=_ComptabiliteFactory(enfant_personnel=None),
            exception=ReductionDesDroitsInscriptionNonCompleteeException,
        )

    def test_should_retourner_erreur_si_comptabilite_incomplete_pour_indication_demande_allocation_fr_be(self):
        self._test_should_retourner_erreur_si_comptabilite_incomplete(
            comptabilite=_ComptabiliteFactory(demande_allocation_d_etudes_communaute_francaise_belgique=None),
            exception=ReductionDesDroitsInscriptionNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_incomplete_pour_type_situation(self):
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=_ComptabiliteFactory(type_situation_assimilation=None),
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_incomplete_pour_type_assimilation_1(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE,
            sous_type_situation_assimilation_1='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_1_incomplete_pour_carte_resident_longue_duree(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE,
            sous_type_situation_assimilation_1=ChoixAssimilation1.TITULAIRE_CARTE_RESIDENT_LONGUE_DUREE,
            carte_resident_longue_duree=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_1_incomplete_pour_carte_etranger(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE,
            sous_type_situation_assimilation_1=ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER,
            carte_cire_sejour_illimite_etranger=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_1_incomplete_pour_carte_sejour_membre_famille_ue(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE,
            sous_type_situation_assimilation_1=ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_MEMBRE_UE,
            carte_sejour_membre_ue=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_1_incomplete_pour_carte_sejour_permanent_membre_famille_ue(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE,
            sous_type_situation_assimilation_1=ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_PERMANENT_MEMBRE_UE,
            carte_sejour_permanent_membre_ue=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_incomplete_pour_type_assimilation_2(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_2_incomplete_pour_refugie(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2=ChoixAssimilation2.REFUGIE,
            carte_a_b_refugie=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_2_incomplete_pour_demandeur_asile_annexe(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2=ChoixAssimilation2.DEMANDEUR_ASILE,
            annexe_25_26_refugies_apatrides=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_2_incomplete_pour_demandeur_asile_attestation(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2=ChoixAssimilation2.DEMANDEUR_ASILE,
            attestation_immatriculation=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_2_incomplete_pour_protection_subsidiaire_carte_a_b(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2=ChoixAssimilation2.PROTECTION_SUBSIDIAIRE,
            carte_a_b=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_2_incomplete_pour_protection_subsidiaire_decision(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2=ChoixAssimilation2.PROTECTION_SUBSIDIAIRE,
            decision_protection_subsidiaire=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_2_incomplete_pour_protection_temporaire(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2=ChoixAssimilation2.PROTECTION_TEMPORAIRE,
            decision_protection_temporaire=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_incomplete_pour_type_assimilation_3(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT'
            ],
            sous_type_situation_assimilation_3='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_3_incomplete_pour_revenus_professionnels_titre_sejour(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT'
            ],
            sous_type_situation_assimilation_3=ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS,
            titre_sejour_3_mois_professionel=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_3_incomplete_pour_revenus_professionnels_fiche_remuneration(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT'
            ],
            sous_type_situation_assimilation_3=ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS,
            fiches_remuneration=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_3_incomplete_pour_revenus_remplacemente_titre_sejour(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT'
            ],
            sous_type_situation_assimilation_3=ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT,
            titre_sejour_3_mois_remplacement=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_3_incomplete_pour_revenus_remplacemente_preuve_allocations(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT'
            ],
            sous_type_situation_assimilation_3=ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT,
            preuve_allocations_chomage_pension_indemnite=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_4_incomplete(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS,
            attestation_cpas=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_incomplete_pour_type_assimilation_5(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            relation_parente=LienParente.COHABITANT_LEGAL,
            sous_type_situation_assimilation_5='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_incomplete_pour_lien_parente_assimilation_5(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE,
            relation_parente='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_avec_pere_composition_menage_acte_naissance(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE,
            relation_parente=LienParente.PERE,
            composition_menage_acte_naissance=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_avec_mere_composition_menage_acte_naissance(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE,
            relation_parente=LienParente.MERE,
            composition_menage_acte_naissance=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_avec_tuteur_acte_tutelle(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE,
            relation_parente=LienParente.TUTEUR_LEGAL,
            acte_tutelle=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_avec_conjoint_acte_tutelle(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE,
            relation_parente=LienParente.CONJOINT,
            composition_menage_acte_mariage=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_avec_cohabitant_legal_attestation(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE,
            relation_parente=LienParente.COHABITANT_LEGAL,
            attestation_cohabitation_legale=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_carte_identite(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE,
            relation_parente=LienParente.PERE,
            carte_identite_parent=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_titre_sejour_longue_duree(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.TITULAIRE_TITRE_SEJOUR_LONGUE_DUREE,
            relation_parente=LienParente.PERE,
            titre_sejour_longue_duree_parent=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_refugie_apatride(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5[
                'CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE'
            ],
            relation_parente=LienParente.PERE,
            annexe_25_26_refugies_apatrides_decision_protection_parent=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_titre_sejour(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5[
                'AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT'
            ],
            relation_parente=LienParente.PERE,
            titre_sejour_3_mois_parent=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_revenus(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5[
                'AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT'
            ],
            relation_parente=LienParente.PERE,
            fiches_remuneration_parent=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_attestation_cpas(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.PRIS_EN_CHARGE_OU_DESIGNE_CPAS,
            relation_parente=LienParente.PERE,
            attestation_cpas_parent=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_incomplete_pour_type_assimilation_6(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2,
            sous_type_situation_assimilation_6='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_6_incomplete_bourse_communaute_francaise(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2,
            sous_type_situation_assimilation_6=ChoixAssimilation6.A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE,
            decision_bourse_cfwb=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_6_incomplete_bourse_cooperation_developpement(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2,
            sous_type_situation_assimilation_6=ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT,
            attestation_boursier=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_7_incomplete_titre_identite_sejour_longue_duree_ue(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE,
            titre_identite_sejour_longue_duree_ue=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_assimilation_7_incomplete_titre_sejour_belgique(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE,
            type_numero_compte=ChoixTypeCompteBancaire.AUTRE_FORMAT,
            titre_sejour_belgique=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeException,
        )

    def test_should_retourner_erreur_si_compte_bancaire_iban_incomplet(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=ChoixTypeCompteBancaire.IBAN,
            numero_compte_iban='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=CarteBancaireRemboursementIbanNonCompleteException,
        )

    def test_should_retourner_erreur_prenom_titulaire_compte_bancaire_iban_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=ChoixTypeCompteBancaire.IBAN,
            prenom_titulaire_compte='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=CarteBancaireRemboursementIbanNonCompleteException,
        )

    def test_should_retourner_erreur_nom_titulaire_compte_bancaire_iban_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=ChoixTypeCompteBancaire.IBAN,
            nom_titulaire_compte='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=CarteBancaireRemboursementIbanNonCompleteException,
        )

    def test_should_retourner_erreur_si_numero_compte_bancaire_autre_format_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=ChoixTypeCompteBancaire.AUTRE_FORMAT,
            numero_compte_autre_format='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=CarteBancaireRemboursementAutreFormatNonCompleteException,
        )

    def test_should_retourner_erreur_si_code_bic_compte_bancaire_autre_format_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=ChoixTypeCompteBancaire.AUTRE_FORMAT,
            code_bic_swift_banque='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=CarteBancaireRemboursementAutreFormatNonCompleteException,
        )

    def test_should_retourner_erreur_prenom_titulaire_compte_bancaire_autre_format_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=ChoixTypeCompteBancaire.AUTRE_FORMAT,
            prenom_titulaire_compte='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=CarteBancaireRemboursementAutreFormatNonCompleteException,
        )

    def test_should_retourner_erreur_nom_titulaire_compte_bancaire_autre_format_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=ChoixTypeCompteBancaire.AUTRE_FORMAT,
            nom_titulaire_compte='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=CarteBancaireRemboursementAutreFormatNonCompleteException,
        )

    def test_should_retourner_erreur_si_affiliation_sport_non_renseignee(self):
        comptabilite = _ComptabiliteFactory(
            affiliation_sport='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AffiliationsNonCompleteesException,
        )

    def test_should_retourner_erreur_si_etudiant_solidaire_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            etudiant_solidaire=None,
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AffiliationsNonCompleteesException,
        )
