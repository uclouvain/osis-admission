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
import uuid
from typing import Optional
from unittest import TestCase, mock

import freezegun

from admission.ddd import BE_ISO_CODE, FR_ISO_CODE
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    ReductionDesDroitsInscriptionNonCompleteeException,
    AbsenceDeDetteNonCompleteeException,
    AssimilationNonCompleteeException,
    CarteBancaireRemboursementIbanNonCompleteException,
    CarteBancaireRemboursementAutreFormatNonCompleteException,
    AffiliationsNonCompleteesException,
    ExperiencesAcademiquesNonCompleteesException,
    TypeCompteBancaireRemboursementNonCompleteException,
)
from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.domain.validator.exceptions import (
    ConditionsAccessNonRempliesException,
    QuestionsSpecifiquesChoixFormationNonCompleteesException,
    QuestionsSpecifiquesCurriculumNonCompleteesException,
    QuestionsSpecifiquesEtudesSecondairesNonCompleteesException,
    QuestionsSpecifiquesInformationsComplementairesNonCompleteesException,
    NombrePropositionsSoumisesDepasseException,
)
from admission.ddd.admission.dtos import EtudesSecondairesDTO
from admission.ddd.admission.dtos.etudes_secondaires import (
    DiplomeBelgeEtudesSecondairesDTO,
    AlternativeSecondairesDTO,
    DiplomeEtrangerEtudesSecondairesDTO,
)
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
from admission.ddd.admission.formation_generale.commands import VerifierPropositionQuery
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    EquivalenceNonRenseigneeException,
    FichierCurriculumNonRenseigneException,
    EtudesSecondairesNonCompleteesException,
    EtudesSecondairesNonCompleteesPourDiplomeBelgeException,
    EtudesSecondairesNonCompleteesPourAlternativeException,
    EtudesSecondairesNonCompleteesPourDiplomeEtrangerException,
    InformationsVisaNonCompleteesException,
)
from admission.ddd.admission.formation_generale.test.factory.proposition import _ComptabiliteFactory
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import (
    AnneeExperienceAcademique,
    ExperienceAcademique,
    ProfilCandidatInMemoryTranslator,
    ExperienceNonAcademique,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.enums.got_diploma import GotDiploma
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository
from osis_profile.models.enums.curriculum import (
    Result,
    TranscriptType,
    Grade,
    EvaluationSystem,
    ActivityType,
    ActivitySector,
)
from osis_profile.models.enums.education import ForeignDiplomaTypes, Equivalence


class TestVerifierPropositionService(TestCase):
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
                    annee=2016,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_inscrits=10,
                    credits_acquis=10,
                ),
                AnneeExperienceAcademique(
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2017,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_inscrits=10,
                    credits_acquis=10,
                ),
                AnneeExperienceAcademique(
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2018,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_inscrits=10,
                    credits_acquis=10,
                ),
                AnneeExperienceAcademique(
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2019,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_inscrits=10,
                    credits_acquis=10,
                ),
                AnneeExperienceAcademique(
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2020,
                    resultat=Result.WAITING_RESULT.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_inscrits=None,
                    credits_acquis=None,
                ),
            ],
            traduction_releve_notes=['traduction_releve_notes.pdf'],
            releve_notes=['releve.pdf'],
            type_releve_notes=TranscriptType.ONE_FOR_ALL_YEARS.name,
            a_obtenu_diplome=False,
            diplome=['diplome.pdf'],
            traduction_diplome=['traduction_diplome.pdf'],
            regime_linguistique='',
            note_memoire='',
            rang_diplome='',
            resume_memoire=[],
            titre_memoire='',
            date_prevue_delivrance_diplome=None,
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

        cls.params_defaut_experience_non_academique = {
            'uuid': str(uuid.uuid4()),
            'employeur': 'UCL',
            'type': ActivityType.WORK.name,
            'certificat': [],
            'fonction': 'Bibliothécaire',
            'secteur': ActivitySector.PUBLIC.name,
            'autre_activite': '',
        }

    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

        self.academic_year_repository = AcademicYearInMemoryRepository()
        self.proposition_in_memory = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_in_memory.reset)

        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.experiences_academiques = self.candidat_translator.experiences_academiques

        self.candidat = self.candidat_translator.profil_candidats[1]
        self.experiences_non_academiques = self.candidat_translator.experiences_non_academiques

        self.adresse_residentielle = next(
            adresse
            for adresse in self.candidat_translator.adresses_candidats
            if adresse.personne == self.candidat.matricule
        )

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

        self.etudes_secondaires = self.candidat_translator.etudes_secondaires

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

    def tearDown(self):
        mock.patch.stopall()

    def _test_should_retourner_erreur_si_assimilation_incomplete(self, comptabilite, exception):
        with mock.patch.object(self.candidat, 'pays_nationalite', 'CA'):
            self._test_should_retourner_erreur_si_comptabilite_incomplete(
                comptabilite=comptabilite,
                exception=exception,
            )

    def _test_should_retourner_erreur_si_comptabilite_incomplete(self, comptabilite, exception):
        with mock.patch.object(self.master_proposition, 'comptabilite', comptabilite):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(uuid='uuid-MASTER-SCI'))
            self.assertTrue(any(member for member in context.exception.exceptions if isinstance(member, exception)))

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
        self.assertHasInstance(context.exception.exceptions, ConditionsAccessNonRempliesException)

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
                    AnneeExperienceAcademique(
                        uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                        annee=2015,
                        resultat=Result.SUCCESS.name,
                        releve_notes=[],
                        traduction_releve_notes=[],
                        credits_acquis=10,
                        credits_inscrits=10,
                    ),
                ],
                traduction_releve_notes=[],
                releve_notes=['releve.pdf'],
                type_releve_notes=TranscriptType.ONE_FOR_ALL_YEARS.name,
                a_obtenu_diplome=True,
                diplome=['diplome.pdf'],
                traduction_diplome=[],
                regime_linguistique='',
                note_memoire='10',
                rang_diplome='10',
                resume_memoire=['resume.pdf'],
                titre_memoire='Titre',
                date_prevue_delivrance_diplome=datetime.date(2020, 9, 1),
                uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee6',
                nom_formation='Formation AA',
                systeme_evaluation=EvaluationSystem.ECTS_CREDITS.name,
                grade_obtenu=Grade.GREAT_DISTINCTION.name,
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
            ),
        )
        with mock.patch.multiple(self.aggregation_proposition, equivalence_diplome=[]):
            proposition_id = self.message_bus.invoke(self.cmd(self.aggregation_proposition.entity_id.uuid))
            self.assertEqual(proposition_id.uuid, self.aggregation_proposition.entity_id.uuid)

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

    def test_should_retourner_erreur_si_comptabilite_incomplete_pour_enfant_personnel(self):
        self._test_should_retourner_erreur_si_comptabilite_incomplete(
            comptabilite=_ComptabiliteFactory(enfant_personnel=None),
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

    def test_should_retourner_erreur_si_assimilation_2_incomplete_pour_apatride_preuve_statut_apatride(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2=ChoixAssimilation2.APATRIDE,
            preuve_statut_apatride=[],
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

    def test_should_retourner_erreur_si_assimilation_2_incomplete_pour_protection_temporaire_pour_decision(self):
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

    def test_should_retourner_erreur_si_assimilation_2_incomplete_pour_protection_temporaire_pour_carte_a(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2=ChoixAssimilation2.PROTECTION_TEMPORAIRE,
            carte_a=[],
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

    def test_should_retourner_erreur_si_type_compte_bancaire_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=None,
        )
        self._test_should_retourner_erreur_si_comptabilite_incomplete(
            comptabilite=comptabilite,
            exception=TypeCompteBancaireRemboursementNonCompleteException,
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

        # No exception as the training campus is not concerned by the sport affiliation
        with mock.patch.multiple(
            self.master_proposition,
            formation_id=FormationIdentity(sigle='MASTER-SCI-UNKNOWN-CAMPUS', annee=2021),
        ):
            comptabilite = _ComptabiliteFactory(
                affiliation_sport='',
            )
            with mock.patch.object(self.master_proposition, 'comptabilite', comptabilite):
                self.message_bus.invoke(self.cmd(uuid='uuid-MASTER-SCI'))

    def test_should_retourner_erreur_si_etudiant_solidaire_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            etudiant_solidaire=None,
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AffiliationsNonCompleteesException,
        )

    def test_should_retourner_erreur_si_indication_a_diplome_etudes_secondaires_non_specifiee_pour_master(self):
        self.etudes_secondaires[self.master_proposition.matricule_candidat] = EtudesSecondairesDTO(
            annee_diplome_etudes_secondaires=2020,
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesException)

    def test_should_retourner_erreur_si_indication_annee_diplome_etudes_secondaires_non_specifiee_pour_master(self):
        self.etudes_secondaires[self.master_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesException)

    def test_should_etre_ok_si_indication_et_annee_diplome_etudes_secondaires_specifiees_pour_master(self):
        self.etudes_secondaires[self.master_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
        )
        id_proposition = self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
        self.assertEqual(id_proposition, self.master_proposition.entity_id)

    def test_should_retourner_erreur_si_indication_a_diplome_etudes_secondaires_non_specifiee_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            annee_diplome_etudes_secondaires=2020,
            diplome_belge=DiplomeBelgeEtudesSecondairesDTO(diplome=['diplome.pdf']),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesException)

    def test_should_retourner_erreur_si_indication_annee_diplome_etudes_secondaires_non_specifiee_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            diplome_belge=DiplomeBelgeEtudesSecondairesDTO(diplome=['diplome.pdf']),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesException)

    def test_should_retourner_erreur_si_etudes_secondaires_et_diplome_non_specifie_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesException)

    def test_should_etre_ok_si_etudes_secondaires_et_diplome_non_specifie_pour_bachelier_avec_valorisation(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            valorisees=True,
        )

        id_proposition = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertEqual(id_proposition, self.bachelier_proposition.entity_id)

    def test_should_retourner_erreur_si_etudes_secondaires_en_cours_et_diplome_non_specifie_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.THIS_YEAR.name,
            annee_diplome_etudes_secondaires=2020,
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesException)

    def test_should_retourner_erreur_si_pas_etudes_secondaires_et_alternative_non_specifiee_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.NO.name,
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesException)

    def test_should_etre_ok_si_pas_etudes_secondaires_et_alternative_non_specifiee_pour_bachelier_vae(self):
        self.experiences_non_academiques.append(
            ExperienceNonAcademique(
                personne=self.bachelier_proposition.matricule_candidat,
                date_debut=datetime.date(2015, 1, 1),
                date_fin=datetime.date(2018, 1, 1),
                **self.params_defaut_experience_non_academique,
            )
        )
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.NO.name,
        )
        id_proposition = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertEqual(id_proposition, self.bachelier_proposition.entity_id)

    def test_should_retourner_erreur_si_diplome_belge_etudes_secondaires_incomplet_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_belge=DiplomeBelgeEtudesSecondairesDTO(diplome=[]),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesPourDiplomeBelgeException)

    def test_should_retourner_erreur_si_diplome_belge_etudes_secondaires_en_cours_incomplet_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_belge=DiplomeBelgeEtudesSecondairesDTO(),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesPourDiplomeBelgeException)

    def test_should_etre_ok_si_diplome_belge_etudes_secondaires_en_cours_avec_diplome_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.THIS_YEAR.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_belge=DiplomeBelgeEtudesSecondairesDTO(diplome=['diplome.pdf']),
        )
        id_proposition = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertEqual(id_proposition, self.bachelier_proposition.entity_id)

    def test_should_retourner_erreur_si_alternative_etudes_secondaires_incomplet_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.NO.name,
            alternative_secondaires=AlternativeSecondairesDTO(),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesPourAlternativeException)

    def test_should_etre_ok_si_alternative_etudes_secondaires_complet_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.NO.name,
            alternative_secondaires=AlternativeSecondairesDTO(examen_admission_premier_cycle=['examen.pdf']),
        )
        id_proposition = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertEqual(id_proposition, self.bachelier_proposition.entity_id)

    def test_should_etre_ok_si_pas_etudes_secondaires_et_alternative_incomplet_pour_bachelier_vae(self):
        self.experiences_non_academiques.append(
            ExperienceNonAcademique(
                personne=self.bachelier_proposition.matricule_candidat,
                date_debut=datetime.date(2015, 1, 1),
                date_fin=datetime.date(2018, 1, 1),
                **self.params_defaut_experience_non_academique,
            )
        )
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.NO.name, alternative_secondaires=AlternativeSecondairesDTO()
        )
        id_proposition = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertEqual(id_proposition, self.bachelier_proposition.entity_id)

    def test_should_etre_ok_si_diplome_etranger_ue_europeen_complet_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
                pays_membre_ue=True,
                pays_iso_code=FR_ISO_CODE,
                diplome=['diplome.pdf'],
                releve_notes=['releve.pdf'],
            ),
        )
        id_proposition = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertEqual(id_proposition, self.bachelier_proposition.entity_id)

    def test_should_retourner_erreur_si_diplome_etranger_etudes_secondaires_incomplet_releve_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
                pays_membre_ue=True,
                pays_iso_code=FR_ISO_CODE,
                diplome=['diplome.pdf'],
            ),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesPourDiplomeEtrangerException)

    def test_should_retourner_erreur_si_diplome_etranger_etudes_secondaires_incomplet_diplome_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
                pays_membre_ue=True,
                pays_iso_code=FR_ISO_CODE,
                releve_notes=['releve.pdf'],
            ),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesPourDiplomeEtrangerException)

    def test_should_etre_ok_si_diplome_etranger_etudes_secondaires_en_cours_avec_diplome_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.THIS_YEAR.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
                pays_membre_ue=True,
                pays_iso_code=FR_ISO_CODE,
                releve_notes=['releve.pdf'],
                diplome=['diplome.pdf'],
            ),
        )
        id_proposition = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertEqual(id_proposition, self.bachelier_proposition.entity_id)

    def test_should_retourner_erreur_si_diplome_etranger_en_cours_incomplet_diplome_certif_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.THIS_YEAR.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
                pays_membre_ue=True,
                pays_iso_code=FR_ISO_CODE,
                releve_notes=['releve.pdf'],
            ),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesPourDiplomeEtrangerException)

    def test_should_etre_ok_si_diplome_etranger_complet_equivalence_si_possedee_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                pays_membre_ue=True,
                pays_iso_code=FR_ISO_CODE,
                diplome=['diplome.pdf'],
                releve_notes=['releve.pdf'],
                equivalence=Equivalence.YES.name,
                decision_final_equivalence_ue=['decision_final_equivalence_ue.pdf'],
            ),
        )
        proposition_id = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertEqual(proposition_id, self.bachelier_proposition.entity_id)

    def test_should_retourner_erreur_si_diplome_etranger_incomplet_equivalence_si_possedee_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                pays_membre_ue=True,
                pays_iso_code=FR_ISO_CODE,
                diplome=['diplome.pdf'],
                releve_notes=['releve.pdf'],
                equivalence=Equivalence.YES.name,
            ),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesPourDiplomeEtrangerException)

    def test_should_etre_ok_si_diplome_etranger_complet_equivalence_si_demandee_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                pays_membre_ue=True,
                pays_iso_code=FR_ISO_CODE,
                diplome=['diplome.pdf'],
                releve_notes=['releve.pdf'],
                equivalence=Equivalence.PENDING.name,
                preuve_decision_equivalence=['preuve_decision_equivalence.pdf'],
            ),
        )
        proposition_id = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertEqual(proposition_id, self.bachelier_proposition.entity_id)

    def test_should_retourner_erreur_si_diplome_etranger_incomplet_equivalence_inconnue_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                pays_membre_ue=True,
                pays_iso_code=FR_ISO_CODE,
                diplome=['diplome.pdf'],
                releve_notes=['releve.pdf'],
                equivalence='',
            ),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesPourDiplomeEtrangerException)

    def test_should_retourner_erreur_si_diplome_etranger_incomplet_equivalence_si_demandee_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                pays_membre_ue=True,
                pays_iso_code=FR_ISO_CODE,
                diplome=['diplome.pdf'],
                releve_notes=['releve.pdf'],
                equivalence=Equivalence.PENDING.name,
            ),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesPourDiplomeEtrangerException)

    def test_should_retourner_erreur_si_diplome_etranger_non_ue_incomplet_equivalence_si_demandee_pour_bachelier_med(
        self,
    ):
        self.etudes_secondaires[self.bachelier_veto_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                pays_membre_ue=False,
                pays_iso_code='CA',
                diplome=['diplome.pdf'],
                releve_notes=['releve.pdf'],
                equivalence=Equivalence.PENDING.name,
            ),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_veto_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesPourDiplomeEtrangerException)

    def test_should_etre_ok_si_diplome_etranger_complet_equivalence_si_pas_demandee_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                pays_membre_ue=True,
                pays_iso_code=FR_ISO_CODE,
                diplome=['diplome.pdf'],
                releve_notes=['releve.pdf'],
                equivalence=Equivalence.NO.name,
            ),
        )
        proposition_id = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertEqual(proposition_id, self.bachelier_proposition.entity_id)

    def test_should_retourner_erreur_si_diplome_etranger_non_ue_incomplet_equivalence_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                pays_membre_ue=False,
                pays_iso_code='CA',
                diplome=['diplome.pdf'],
                releve_notes=['releve.pdf'],
            ),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesPourDiplomeEtrangerException)

    def test_should_etre_ok_si_diplome_etranger_non_ue_complet_equivalence_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                pays_membre_ue=False,
                pays_iso_code='CA',
                diplome=['diplome.pdf'],
                releve_notes=['releve.pdf'],
                decision_final_equivalence_hors_ue=['decision_final_equivalence_hors_ue.pdf'],
            ),
        )
        id_proposition = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertEqual(id_proposition, self.bachelier_proposition.entity_id)

    def test_should_etre_ok_si_diplome_etranger_non_ue_complet_sans_equivalence_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
                pays_membre_ue=False,
                pays_iso_code='CA',
                diplome=['diplome.pdf'],
                releve_notes=['releve.pdf'],
            ),
        )
        id_proposition = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertEqual(id_proposition, self.bachelier_proposition.entity_id)

    def test_should_retourner_erreur_si_diplome_etranger_non_ue_incomplet_diplome_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique=FR_ISO_CODE,
                type_diplome=ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
                pays_membre_ue=False,
                pays_iso_code='CA',
                releve_notes=['releve.pdf'],
            ),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesPourDiplomeEtrangerException)

    def test_should_retourner_erreur_si_diplome_etranger_incomplet_traduction_diplome_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique='SV',
                type_diplome=ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
                pays_membre_ue=True,
                pays_iso_code=FR_ISO_CODE,
                releve_notes=['releve.pdf'],
                traduction_releve_notes=['traduction_releve_notes.pdf'],
                diplome=['diplome.pdf'],
            ),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesPourDiplomeEtrangerException)

    def test_should_retourner_erreur_si_diplome_etranger_incomplet_traduction_releve_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.YES.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique='SV',
                type_diplome=ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
                pays_membre_ue=True,
                pays_iso_code=FR_ISO_CODE,
                releve_notes=['releve.pdf'],
                diplome=['diplome.pdf'],
                traduction_diplome=['traduction_diplome.pdf'],
            ),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesPourDiplomeEtrangerException)

    def test_should_etre_ok_si_diplome_etranger_complet_avec_traductions_pour_bachelier(self):
        self.etudes_secondaires[self.bachelier_proposition.matricule_candidat] = EtudesSecondairesDTO(
            diplome_etudes_secondaires=GotDiploma.THIS_YEAR.name,
            annee_diplome_etudes_secondaires=2020,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                regime_linguistique='SV',
                type_diplome=ForeignDiplomaTypes.EUROPEAN_BACHELOR.name,
                pays_membre_ue=True,
                pays_iso_code=FR_ISO_CODE,
                releve_notes=['releve.pdf'],
                traduction_releve_notes=['traduction_releve_notes.pdf'],
                diplome=['diplome.pdf'],
                traduction_diplome=['traduction_diplome.pdf'],
            ),
        )
        id_proposition = self.message_bus.invoke(self.cmd(self.bachelier_proposition.entity_id.uuid))
        self.assertEqual(id_proposition, self.bachelier_proposition.entity_id)

    def test_should_etre_ok_si_proposition_complete(self):
        proposition_id = self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
        self.assertEqual(proposition_id, self.master_proposition.entity_id)

    def test_should_etre_ok_avec_experience_academique_complete(self):
        self.experiences_academiques.append(self.experience_academiques_complete)
        proposition_id = self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
        self.assertEqual(proposition_id, self.master_proposition.entity_id)

    def test_should_verification_etre_ok_avec_experience_academique_epc_incomplete(self):
        with mock.patch.multiple(self.experience_academiques_complete, identifiant_externe=[]):
            proposition_id = self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
            self.assertEqual(proposition_id, self.master_proposition.entity_id)

    def test_should_verification_renvoyer_erreur_si_releve_notes_global_non_renseigne(self):
        with mock.patch.multiple(self.experience_academiques_complete, releve_notes=[]):
            self.experiences_academiques.append(self.experience_academiques_complete)

            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))

            self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_regime_linguistique_non_renseigne_experience_etranger(self):
        with mock.patch.multiple(self.experience_academiques_complete, regime_linguistique='', pays=FR_ISO_CODE):
            self.experiences_academiques.append(self.experience_academiques_complete)

            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))

            self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_systeme_evaluation_non_renseigne(self):
        with mock.patch.multiple(self.experience_academiques_complete, systeme_evaluation=''):
            self.experiences_academiques.append(self.experience_academiques_complete)

            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))

            self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_type_releve_notes_non_renseigne(self):
        with mock.patch.multiple(self.experience_academiques_complete, type_releve_notes=''):
            self.experiences_academiques.append(self.experience_academiques_complete)

            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))

            self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_traduction_releve_notes_global_non_renseignee(self):
        with mock.patch.multiple(
            self.experience_academiques_complete,
            releve_notes=[],
            pays=FR_ISO_CODE,
            regime_linguistique='SV',
        ):
            self.experiences_academiques.append(self.experience_academiques_complete)

            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))

            self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_releve_notes_annuel_non_renseigne(self):
        with mock.patch.multiple(
            self.experience_academiques_complete,
            type_releve_notes=TranscriptType.ONE_A_YEAR.name,
        ):
            with mock.patch.multiple(self.experience_academiques_complete.annees[0], releve_notes=[]):
                self.experiences_academiques.append(self.experience_academiques_complete)

                with self.assertRaises(MultipleBusinessExceptions) as context:
                    self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))

                self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_traduction_releve_notes_annuel_non_renseignee(self):
        with mock.patch.multiple(
            self.experience_academiques_complete,
            type_releve_notes=TranscriptType.ONE_A_YEAR.name,
            pays=FR_ISO_CODE,
            regime_linguistique='SV',
        ):
            with mock.patch.multiple(self.experience_academiques_complete.annees[0], traduction_releve_notes=[]):
                self.experiences_academiques.append(self.experience_academiques_complete)

                with self.assertRaises(MultipleBusinessExceptions) as context:
                    self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))

                self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_resultat_annuel_non_renseigne(self):
        with mock.patch.multiple(self.experience_academiques_complete.annees[0], resultat=''):
            self.experiences_academiques.append(self.experience_academiques_complete)

            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))

            self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_credits_inscrits_non_renseignes_etranger(self):
        with mock.patch.multiple(
            self.experience_academiques_complete,
            pays=FR_ISO_CODE,
            systeme_evaluation=EvaluationSystem.ECTS_CREDITS.name,
        ):
            with mock.patch.multiple(self.experience_academiques_complete.annees[0], credits_inscrits=None):
                self.experiences_academiques.append(self.experience_academiques_complete)

                with self.assertRaises(MultipleBusinessExceptions) as context:
                    self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))

                self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_credits_acquis_non_renseignes_etranger(self):
        with mock.patch.multiple(
            self.experience_academiques_complete,
            pays=FR_ISO_CODE,
            systeme_evaluation=EvaluationSystem.NON_EUROPEAN_CREDITS.name,
        ):
            with mock.patch.multiple(self.experience_academiques_complete.annees[0], credits_acquis=None):
                self.experiences_academiques.append(self.experience_academiques_complete)

                with self.assertRaises(MultipleBusinessExceptions) as context:
                    self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))

                self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_credits_acquis_non_renseignes_belgique_apres_2004(self):
        with mock.patch.multiple(
            self.experience_academiques_complete,
            pays=BE_ISO_CODE,
        ):
            with mock.patch.multiple(self.experience_academiques_complete.annees[0], annee=2004, credits_acquis=None):
                self.experiences_academiques.append(self.experience_academiques_complete)

                with self.assertRaises(MultipleBusinessExceptions) as context:
                    self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))

                self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

            with mock.patch.multiple(self.experience_academiques_complete.annees[0], annee=2003, credits_acquis=None):
                self.experiences_academiques.append(self.experience_academiques_complete)

                proposition_id = self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
                self.assertEqual(proposition_id, self.master_proposition.entity_id)

    def test_should_verification_renvoyer_erreur_si_diplome_non_renseigne(self):
        with mock.patch.multiple(self.experience_academiques_complete, a_obtenu_diplome=True, diplome=[]):

            self.experiences_academiques.append(self.experience_academiques_complete)

            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))

            self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_trop_de_demandes_envoyees(self):
        propositions = self.proposition_in_memory.search(matricule_candidat='0000000001')
        for proposition in propositions:
            proposition.statut = ChoixStatutPropositionGenerale.EN_BROUILLON

        for proposition_index in range(2):
            propositions[proposition_index].statut = ChoixStatutPropositionGenerale.CONFIRMEE

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(VerifierPropositionQuery(uuid_proposition=propositions[2].entity_id.uuid))

        self.assertHasInstance(context.exception.exceptions, NombrePropositionsSoumisesDepasseException)

    def test_should_verification_renvoyer_erreur_si_visa_necessaire_et_non_renseigne(self):
        mock.patch.multiple(self.candidat, pays_nationalite='CA', pays_nationalite_europeen=False).start()
        mock.patch.multiple(self.adresse_residentielle, pays='FR').start()
        mock.patch.multiple(self.master_proposition, poste_diplomatique=None).start()

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
        self.assertHasInstance(context.exception.exceptions, InformationsVisaNonCompleteesException)

    def test_should_verification_etre_ok_si_visa_non_renseigne_et_non_necessaire(self):
        # Visa non renseigné
        mock.patch.multiple(self.master_proposition, poste_diplomatique=None).start()

        mock.patch.multiple(self.adresse_residentielle, pays='FR').start()

        # Adresse résidentielle à l'étranger + Nationalité non spécifiée
        mock.patch.multiple(self.candidat, pays_nationalite='', pays_nationalite_europeen=None).start()

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
        self.assertHasNoInstance(context.exception.exceptions, InformationsVisaNonCompleteesException)

        # Adresse résidentielle à l'étranger + Nationalité dans UE
        self.candidat.pays_nationalite = 'FR'
        self.candidat.pays_nationalite_europeen = True
        self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))

        # Adresse résidentielle à l'étranger + Nationalité dans UE+5
        self.candidat.pays_nationalite = 'CH'
        self.candidat.pays_nationalite_europeen = False
        self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))

        self.candidat.pays_nationalite = 'CA'
        self.candidat.pays_nationalite_europeen = False

        # Pas d'adresse de résidence + Nationalité hors UE+5
        self.adresse_residentielle.pays = ''
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
        self.assertHasNoInstance(context.exception.exceptions, InformationsVisaNonCompleteesException)

        # Adresse de résidence en belgique + Nationalité hors UE+5
        self.adresse_residentielle.pays = 'BE'
        self.message_bus.invoke(self.cmd(self.master_proposition.entity_id.uuid))
