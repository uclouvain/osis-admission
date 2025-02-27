# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid

import attr
import freezegun
from django.test import TestCase
from mock import mock

from admission.ddd import FR_ISO_CODE
from admission.ddd.admission.doctorat.preparation.commands import VerifierProjetQuery
from admission.ddd.admission.doctorat.preparation.domain.model._cotutelle import (
    Cotutelle,
)
from admission.ddd.admission.doctorat.preparation.domain.model._detail_projet import (
    DetailProjet,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AdresseCorrespondanceNonCompleteeException,
    AdresseDomicileLegalNonCompleteeException,
    AnneesCurriculumNonSpecifieesException,
    CarteIdentiteeNonSpecifieeException,
    CotutelleDoitAvoirAuMoinsUnPromoteurExterneException,
    CotutelleNonCompleteException,
    DateOuAnneeNaissanceNonSpecifieeException,
    DetailProjetNonCompleteException,
    DetailsPasseportNonSpecifiesException,
    ExperiencesAcademiquesNonCompleteesException,
    FichierCurriculumNonRenseigneException,
    GroupeDeSupervisionNonTrouveException,
    IdentificationNonCompleteeException,
    LanguesConnuesNonSpecifieesException,
    MembreCAManquantException,
    NomEtPrenomNonSpecifiesException,
    NumeroIdentiteBelgeNonSpecifieException,
    NumeroIdentiteNonSpecifieException,
    PromoteurDeReferenceManquantException,
    PromoteurManquantException,
    PropositionNonTrouveeException,
)
from admission.ddd.admission.doctorat.preparation.test.factory.groupe_de_supervision import (
    GroupeDeSupervisionSC3DPPreAdmissionFactory,
    _SignaturePromoteurFactory,
)
from admission.ddd.admission.doctorat.preparation.test.factory.person import (
    PersonneConnueUclDTOFactory,
)
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionPreAdmissionSC3DPMinimaleFactory,
)
from admission.ddd.admission.domain.validator.exceptions import (
    QuestionsSpecifiquesChoixFormationNonCompleteesException,
    QuestionsSpecifiquesCurriculumNonCompleteesException,
    QuestionsSpecifiquesEtudesSecondairesNonCompleteesException,
)
from admission.ddd.admission.test.mixins import AdmissionTestMixin
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import (
    AnneeExperienceAcademique,
    ExperienceAcademique,
    ExperienceNonAcademique,
    ProfilCandidatInMemoryTranslator,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.enums.establishment_type import EstablishmentTypeEnum
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import (
    AcademicYear,
    AcademicYearIdentity,
)
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import (
    AcademicYearInMemoryRepository,
)
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import (
    PersonneConnueUclInMemoryTranslator,
)
from osis_profile import BE_ISO_CODE
from osis_profile.models.enums.curriculum import (
    ActivitySector,
    ActivityType,
    EvaluationSystem,
    Grade,
    Result,
    TranscriptType,
)
from reference.models.enums.cycle import Cycle


@freezegun.freeze_time('2020-11-01')
class TestVerifierPropositionService(AdmissionTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year_repository = AcademicYearInMemoryRepository()

        for annee in range(2016, 2025):
            cls.academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )

    def setUp(self) -> None:
        self.uuid_proposition = 'uuid-SC3DP-promoteur-membre'
        self.uuid_proposition_pre_admission = 'uuid-SC3DP-pre-admission'

        PersonneConnueUclInMemoryTranslator.personnes_connues_ucl = {
            PersonneConnueUclDTOFactory(matricule='promoteur-SC3DP-unique'),
            PersonneConnueUclDTOFactory(matricule='0123456789'),
        }

        self.proposition_repository = PropositionInMemoryRepository()
        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.addCleanup(self.groupe_de_supervision_repository.reset)
        self.addCleanup(self.proposition_repository.reset)

        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.proposition_repository = PropositionInMemoryRepository()
        self.candidat = self.candidat_translator.profil_candidats[0]
        self.adresse_domicile_legal = self.candidat_translator.adresses_candidats[0]
        self.adresse_correspondance = self.candidat_translator.adresses_candidats[1]

        self.message_bus = message_bus_in_memory_instance
        self.cmd = VerifierProjetQuery(uuid_proposition=self.uuid_proposition)
        self.cmd_pre_admission = attr.evolve(self.cmd, uuid_proposition=self.uuid_proposition_pre_admission)

    def test_should_verifier_etre_ok(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)

    def test_should_retourner_erreur_si_identification_non_completee(self):
        with mock.patch.multiple(self.candidat, pays_naissance=''):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), IdentificationNonCompleteeException)

    def test_should_retourner_erreur_si_numero_identite_non_renseigne_candidat_etranger(self):
        with mock.patch.multiple(
            self.candidat,
            numero_registre_national_belge='',
            numero_carte_identite='',
            numero_passeport='',
            pays_nationalite='FR',
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), NumeroIdentiteNonSpecifieException)

    def test_should_retourner_erreur_si_numero_identite_belge_non_renseigne_candidat_belge(self):
        with mock.patch.multiple(
            self.candidat,
            numero_registre_national_belge='',
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), NumeroIdentiteBelgeNonSpecifieException)

    def test_should_retourner_erreur_si_nom_et_prenom_non_renseignes(self):
        with mock.patch.multiple(
            self.candidat,
            nom='',
            prenom='',
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), NomEtPrenomNonSpecifiesException)

    def test_should_retourner_erreur_si_date_annee_naissance_non_renseignees(self):
        with mock.patch.multiple(
            self.candidat,
            date_naissance=None,
            annee_naissance=None,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), DateOuAnneeNaissanceNonSpecifieeException)

    def test_should_retourner_erreur_si_details_passeport_non_renseignes(self):
        with mock.patch.multiple(
            self.candidat,
            passeport=[],
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), DetailsPasseportNonSpecifiesException)

    def test_should_retourner_erreur_si_date_expiration_passeport_non_renseignee(self):
        with mock.patch.multiple(
            self.candidat,
            date_expiration_passeport=None,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), DetailsPasseportNonSpecifiesException)

    def test_should_retourner_erreur_si_carte_identite_non_renseignee(self):
        with mock.patch.multiple(
            self.candidat,
            carte_identite=[],
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), CarteIdentiteeNonSpecifieeException)

    def test_should_retourner_erreur_si_date_expiration_carte_identite_non_renseignee(self):
        with mock.patch.multiple(
            self.candidat,
            date_expiration_carte_identite=None,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), CarteIdentiteeNonSpecifieeException)

    def test_should_retourner_erreur_si_adresse_domicile_legal_non_renseignee(self):
        with mock.patch.object(self.candidat_translator.coordonnees_candidats[0], 'domicile_legal', None):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), AdresseDomicileLegalNonCompleteeException)

    def test_should_retourner_erreur_si_adresse_domicile_legal_incomplete(self):
        with mock.patch.object(self.adresse_domicile_legal, 'pays', None):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), AdresseDomicileLegalNonCompleteeException)

    def test_should_verifier_etre_ok_si_adresse_correspondance_non_renseignee(self):
        with mock.patch.object(self.adresse_correspondance, 'personne', 'unknown_user_id'):
            proposition_id = self.message_bus.invoke(self.cmd)
            self.assertEqual(proposition_id.uuid, self.uuid_proposition)

    def test_should_retourner_erreur_si_adresse_correspondance_incomplete(self):
        with mock.patch.object(self.adresse_correspondance, 'pays', None):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), AdresseCorrespondanceNonCompleteeException)

    def test_should_retourner_erreur_si_pas_toutes_les_langues_requises_connues(self):
        with mock.patch.object(
            self.candidat_translator.connaissances_langues[0],
            'langue',
            self.candidat_translator.langues[3],
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), LanguesConnuesNonSpecifieesException)

    def test_should_retourner_erreur_si_fichier_curriculum_non_renseigne(self):
        proposition = self.proposition_repository.get(PropositionIdentity(uuid=self.uuid_proposition))
        with mock.patch.object(proposition, 'curriculum', []):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), FichierCurriculumNonRenseigneException)

    def test_should_retourner_erreur_si_questions_specifiques_pas_completees_pour_curriculum(self):
        proposition = self.proposition_repository.get(PropositionIdentity(uuid=self.uuid_proposition))
        with mock.patch.multiple(
            proposition,
            reponses_questions_specifiques={
                '06de0c3d-3c06-4c93-8eb4-c8648f04f140': 'My response 1',
                '06de0c3d-3c06-4c93-8eb4-c8648f04f143': 'My response 3',
            },
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(
                context.exception.exceptions.pop(),
                QuestionsSpecifiquesCurriculumNonCompleteesException,
            )

    def test_should_retourner_erreur_si_questions_specifiques_pas_completees_pour_etudes_secondaires(self):
        proposition = self.proposition_repository.get(PropositionIdentity(uuid=self.uuid_proposition))
        with mock.patch.multiple(
            proposition,
            reponses_questions_specifiques={
                '06de0c3d-3c06-4c93-8eb4-c8648f04f140': 'My response 1',
                '06de0c3d-3c06-4c93-8eb4-c8648f04f142': 'My response 2',
            },
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(
                context.exception.exceptions.pop(),
                QuestionsSpecifiquesEtudesSecondairesNonCompleteesException,
            )

    def test_should_retourner_erreur_si_detail_projet_pas_complete(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP-no-project')
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(context.exception.exceptions.pop(), DetailProjetNonCompleteException)

    def test_should_retourner_erreur_si_financement_pas_complete(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP-no-financement')
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(context.exception.exceptions.pop(), DetailProjetNonCompleteException)

    def test_should_retourner_erreur_si_preadmission_et_aucun_membre_supervision(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP-pre-admission')
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(cmd)
        self.assertTrue(any(isinstance(exc, PromoteurManquantException) for exc in context.exception.exceptions))
        self.assertTrue(
            any(isinstance(exc, PromoteurDeReferenceManquantException) for exc in context.exception.exceptions)
        )
        self.assertEqual(len(context.exception.exceptions), 2)

    def test_should_retourner_erreur_si_cotutelle_pas_complete(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP-cotutelle-indefinie')
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(cmd)
        self.assertTrue(any(isinstance(exc, CotutelleNonCompleteException) for exc in context.exception.exceptions))

    def test_should_retourner_erreur_si_groupe_supervision_non_trouve(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-ECGE3DP')
        with self.assertRaises(GroupeDeSupervisionNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_retourner_erreur_si_proposition_non_trouvee(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='propositioninconnue')
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_retourner_erreur_si_cotutelle_sans_promoteur_externe(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP-cotutelle-sans-promoteur-externe')
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(context.exception.exceptions.pop(), CotutelleDoitAvoirAuMoinsUnPromoteurExterneException)

    def test_should_verifier_etre_ok_si_cotutelle_avec_promoteur_externe(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP-cotutelle-avec-promoteur-externe')
        proposition_id = self.message_bus.invoke(cmd)
        self.assertEqual(proposition_id.uuid, 'uuid-SC3DP-cotutelle-avec-promoteur-externe')

    def test_should_retourner_erreur_si_groupe_de_supervision_a_pas_promoteur(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP-sans-promoteur')
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(cmd)
        self.assertTrue(any(isinstance(exc, PromoteurManquantException) for exc in context.exception.exceptions))
        self.assertTrue(
            any(isinstance(exc, PromoteurDeReferenceManquantException) for exc in context.exception.exceptions)
        )
        self.assertEqual(len(context.exception.exceptions), 2)

    def test_should_retourner_erreur_si_groupe_de_supervision_a_pas_membre_CA(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='uuid-SC3DP-sans-membre_CA')
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(context.exception.exceptions.pop(), MembreCAManquantException)

    def test_should_retourner_erreur_si_questions_specifiques_pas_completees(self):
        proposition = next(
            (p for p in PropositionInMemoryRepository.entities if p.entity_id.uuid == self.uuid_proposition),
            None,
        )
        with mock.patch.multiple(proposition, reponses_questions_specifiques={}):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertHasInstance(
                context.exception.exceptions, QuestionsSpecifiquesChoixFormationNonCompleteesException
            )

    def test_should_demander_signatures_pour_pre_admission(self):
        proposition = PropositionPreAdmissionSC3DPMinimaleFactory(
            projet=DetailProjet(),
            matricule_candidat='0123456789',
        )
        self.proposition_repository.save(proposition)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd_pre_admission)

        self.assertHasInstance(context.exception.exceptions, PromoteurManquantException)
        self.assertHasInstance(context.exception.exceptions, PromoteurDeReferenceManquantException)
        self.assertHasNoInstance(context.exception.exceptions, MembreCAManquantException)
        self.assertHasNoInstance(context.exception.exceptions, CotutelleNonCompleteException)
        self.assertHasNoInstance(context.exception.exceptions, CotutelleDoitAvoirAuMoinsUnPromoteurExterneException)

        proposition = PropositionPreAdmissionSC3DPMinimaleFactory(
            projet=DetailProjet(titre='titre'),
            matricule_candidat='0123456789',
        )
        self.proposition_repository.save(proposition)

        ancien_groupe_supervision = self.groupe_de_supervision_repository.get_by_proposition_id(proposition.entity_id)
        self.groupe_de_supervision_repository.delete(ancien_groupe_supervision.entity_id)

        groupe_supervision = GroupeDeSupervisionSC3DPPreAdmissionFactory(
            proposition_id__uuid=self.uuid_proposition_pre_admission,
            signatures_promoteurs=[_SignaturePromoteurFactory(promoteur_id__uuid='promoteur-SC3DP')],
            cotutelle=Cotutelle(motivation='motivation'),
        )
        self.groupe_de_supervision_repository.save(groupe_supervision)

        resultat = self.message_bus.invoke(self.cmd_pre_admission)

        self.assertEqual(resultat.uuid, self.uuid_proposition_pre_admission)


class TestVerifierPropositionServicePourAnneesCurriculum(AdmissionTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year_repository = AcademicYearInMemoryRepository()

        for annee in range(2016, 2025):
            cls.academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )

        cls.params_default_experience_non_academique = {
            'uuid': str(uuid.uuid4()),
            'employeur': 'UCL',
            'type': ActivityType.WORK.name,
            'certificat': [],
            'fonction': 'Bibliothécaire',
            'secteur': ActivitySector.PUBLIC.name,
            'autre_activite': '',
        }

    def setUp(self) -> None:
        self.uuid_proposition = 'uuid-SC3DP-promoteur-membre'

        PersonneConnueUclInMemoryTranslator.personnes_connues_ucl = {
            PersonneConnueUclDTOFactory(matricule='promoteur-SC3DP-unique'),
            PersonneConnueUclDTOFactory(matricule='0123456789'),
        }

        self.proposition_repository = PropositionInMemoryRepository()
        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.addCleanup(self.groupe_de_supervision_repository.reset)
        self.addCleanup(self.proposition_repository.reset)

        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.proposition_repository = PropositionInMemoryRepository()
        self.candidat = self.candidat_translator.profil_candidats[0]

        self.message_bus = message_bus_in_memory_instance
        self.cmd = VerifierProjetQuery(uuid_proposition=self.uuid_proposition)

        self.experiences_non_academiques = self.candidat_translator.experiences_non_academiques
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance

        self.academic_year_repository = AcademicYearInMemoryRepository()
        self.etudes_secondaires = self.candidat_translator.etudes_secondaires.get(self.candidat.matricule)
        if self.etudes_secondaires:
            self.etudes_secondaires.annee_diplome_etudes_secondaires = None

        for annee in range(2016, 2021):
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

        self.cmd = VerifierProjetQuery(uuid_proposition=self.uuid_proposition)

        for experience_acad in self.candidat_translator.experiences_academiques:
            experience_acad.personne = 'other'

        for experience_non_acad in self.candidat_translator.experiences_non_academiques:
            experience_non_acad.personne = 'other'

        self.experience_academiques_complete = ExperienceAcademique(
            personne=self.candidat.matricule,
            communaute_fr=True,
            pays=BE_ISO_CODE,
            annees=[
                AnneeExperienceAcademique(
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2016,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_acquis=10,
                    credits_inscrits=10,
                ),
                AnneeExperienceAcademique(
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2017,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_acquis=10,
                    credits_inscrits=10,
                ),
                AnneeExperienceAcademique(
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2018,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_acquis=10,
                    credits_inscrits=10,
                ),
                AnneeExperienceAcademique(
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2019,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_acquis=10,
                    credits_inscrits=10,
                ),
                AnneeExperienceAcademique(
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2020,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_acquis=10,
                    credits_inscrits=10,
                ),
            ],
            traduction_releve_notes=['traduction_releve_notes.pdf'],
            releve_notes=['releve.pdf'],
            type_releve_notes=TranscriptType.ONE_FOR_ALL_YEARS.name,
            a_obtenu_diplome=False,
            diplome=['diplome.pdf'],
            traduction_diplome=['traduction_diplome.pdf'],
            regime_linguistique='',
            note_memoire='10',
            rang_diplome='10',
            resume_memoire=['resume.pdf'],
            titre_memoire='Titre',
            date_prevue_delivrance_diplome=datetime.date(2020, 9, 1),
            uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee6',
            grade_obtenu=Grade.GREAT_DISTINCTION.name,
            systeme_evaluation=EvaluationSystem.ECTS_CREDITS.name,
            nom_formation='Formation AA',
            nom_pays='Belgique',
            code_institut='',
            type_enseignement='',
            nom_institut='',
            adresse_institut='',
            communaute_institut='',
            nom_regime_linguistique='',
            type_institut=EstablishmentTypeEnum.UNIVERSITY.name,
            cycle_formation=Cycle.FIRST_CYCLE.name,
            nom_formation_equivalente_communaute_fr='Formation B',
        )

    def assertAnneesCurriculum(self, exceptions, messages):
        messages_renvoyes = []
        for exception in exceptions:
            self.assertIsInstance(
                exception, (AnneesCurriculumNonSpecifieesException, ExperiencesAcademiquesNonCompleteesException)
            )
            messages_renvoyes.append(exception.message)

        self.assertCountEqual(messages, messages_renvoyes)

    def test_should_retourner_erreur_si_5_dernieres_annees_curriculum_non_saisies(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2016 à Février 2017',
                'De Septembre 2017 à Février 2018',
                'De Septembre 2018 à Février 2019',
                'De Septembre 2019 à Février 2020',
                'De Septembre 2020 à Octobre 2020',
            ],
        )

    def test_should_retourner_erreur_si_dernieres_annees_curriculum_non_saisies_avec_demande_signature_soumise(self):
        proposition = self.proposition_repository.get(entity_id=PropositionIdentity(uuid=self.uuid_proposition))
        proposition.derniere_demande_signature_avant_soumission_le = datetime.datetime(2020, 10, 1)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2016 à Février 2017',
                'De Septembre 2017 à Février 2018',
                'De Septembre 2018 à Février 2019',
                'De Septembre 2019 à Février 2020',
                'De Septembre 2020 à Octobre 2020',
            ],
        )

    def test_should_retourner_erreur_si_dernieres_annees_curriculum_non_saisies_avec_diplome_secondaire_belge(self):
        self.etudes_secondaires.annee_diplome_etudes_secondaires = 2018

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2019 à Février 2020',
                'De Septembre 2020 à Octobre 2020',
            ],
        )

    def test_should_retourner_erreur_si_dernieres_annees_curriculum_non_saisies_avec_diplome_secondaire_etranger(self):
        self.etudes_secondaires.annee_diplome_etudes_secondaires = 2017

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2018 à Février 2019',
                'De Septembre 2019 à Février 2020',
                'De Septembre 2020 à Octobre 2020',
            ],
        )

    def test_should_retourner_erreur_si_dernieres_annees_curriculum_non_saisies_avec_ancienne_inscription_ucl(self):
        with mock.patch.multiple(
            self.candidat,
            annee_derniere_inscription_ucl=2019,
            noma_derniere_inscription_ucl='01234567',
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(context.exception.exceptions, ['De Septembre 2020 à Octobre 2020'])

    def test_should_retourner_erreur_si_annees_curriculum_non_saisies_avec_diplome_et_ancienne_inscription(self):
        self.etudes_secondaires.annee_diplome_etudes_secondaires = 2017

        with mock.patch.multiple(
            self.candidat,
            annee_derniere_inscription_ucl=2018,
            noma_derniere_inscription_ucl='01234567',
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2019 à Février 2020',
                'De Septembre 2020 à Octobre 2020',
            ],
        )

    def test_should_verification_etre_ok_si_une_experiences_professionnelles_couvre_exactement(self):
        self.etudes_secondaires.annee_diplome_etudes_secondaires = 2017
        self.candidat_translator.experiences_non_academiques.append(
            ExperienceNonAcademique(
                personne=self.candidat.matricule,
                date_debut=datetime.date(2018, 9, 1),
                date_fin=datetime.date(2021, 6, 30),
                **self.params_default_experience_non_academique,
            ),
        )
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)
        self.candidat_translator.experiences_non_academiques.pop()

    def test_should_verification_etre_ok_si_une_experiences_professionnelles_couvre_davantage(self):
        self.etudes_secondaires.annee_diplome_etudes_secondaires = 2017
        self.candidat_translator.experiences_non_academiques.append(
            ExperienceNonAcademique(
                personne=self.candidat.matricule,
                date_debut=datetime.date(2018, 8, 1),
                date_fin=datetime.date(2021, 7, 31),
                **self.params_default_experience_non_academique,
            )
        )
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)

    def test_should_verification_etre_ok_si_une_des_experiences_professionnelles_couvre_davantage(self):
        self.etudes_secondaires.annee_diplome_etudes_secondaires = 2017
        self.candidat_translator.experiences_non_academiques.extend(
            [
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 8, 1),
                    date_fin=datetime.date(2021, 7, 31),
                    **self.params_default_experience_non_academique,
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2017, 8, 1),
                    date_fin=datetime.date(2018, 7, 31),
                    **self.params_default_experience_non_academique,
                ),
            ],
        )
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)

    def test_should_verification_renvoyer_exception_si_une_experiences_professionnelles_couvre_pas_debut(self):
        self.etudes_secondaires.annee_diplome_etudes_secondaires = 2017
        self.candidat_translator.experiences_non_academiques.append(
            ExperienceNonAcademique(
                personne=self.candidat.matricule,
                date_debut=datetime.date(2018, 10, 1),
                date_fin=datetime.date(2021, 6, 30),
                **self.params_default_experience_non_academique,
            )
        )

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(context.exception.exceptions, ['Septembre 2018'])

    def test_should_verification_renvoyer_exception_si_une_experiences_professionnelles_couvre_pas_fin(self):
        self.etudes_secondaires.annee_diplome_etudes_secondaires = 2017
        self.candidat_translator.experiences_non_academiques.append(
            ExperienceNonAcademique(
                personne=self.candidat.matricule,
                date_debut=datetime.date(2018, 9, 1),
                date_fin=datetime.date(2020, 9, 30),
                **self.params_default_experience_non_academique,
            )
        )

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(context.exception.exceptions, ['Octobre 2020'])

    def test_should_verification_etre_ok_si_experiences_professionnelles_couvrent_en_se_suivant_ou_chevauchant(self):
        self.etudes_secondaires.annee_diplome_etudes_secondaires = 2017
        self.candidat_translator.experiences_non_academiques.extend(
            [
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2020, 1, 1),
                    date_fin=datetime.date(2021, 8, 31),
                    **self.params_default_experience_non_academique,
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 11, 1),
                    date_fin=datetime.date(2020, 3, 31),
                    **self.params_default_experience_non_academique,
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 7, 1),
                    date_fin=datetime.date(2019, 10, 31),
                    **self.params_default_experience_non_academique,
                ),
            ]
        )
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)

    def test_should_verification_etre_ok_si_experiences_professionnelles_couvrent_en_ne_se_chevauchant_pas(self):
        self.etudes_secondaires.annee_diplome_etudes_secondaires = 2017
        self.candidat_translator.experiences_non_academiques.extend(
            [
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 10, 1),
                    date_fin=datetime.date(2021, 8, 31),
                    **self.params_default_experience_non_academique,
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 10, 1),
                    date_fin=datetime.date(2020, 5, 31),
                    **self.params_default_experience_non_academique,
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 9, 1),
                    date_fin=datetime.date(2019, 9, 30),
                    **self.params_default_experience_non_academique,
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 9, 1),
                    date_fin=datetime.date(2019, 6, 30),
                    **self.params_default_experience_non_academique,
                ),
            ]
        )
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)

    def test_should_renvoyer_exception_si_experiences_professionnelles_trop_anciennes(self):
        self.etudes_secondaires.annee_diplome_etudes_secondaires = 2017
        self.candidat_translator.experiences_non_academiques.extend(
            [
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 10, 1),
                    date_fin=datetime.date(2018, 12, 31),
                    **self.params_default_experience_non_academique,
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 9, 1),
                    date_fin=datetime.date(2019, 6, 30),
                    **self.params_default_experience_non_academique,
                ),
            ]
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2019 à Février 2020',
                'De Septembre 2020 à Octobre 2020',
            ],
        )

    def test_should_renvoyer_exception_si_experiences_professionnelles_ne_couvrent_pas_et_ne_se_chevauchent_pas_v2(
        self,
    ):
        self.etudes_secondaires.annee_diplome_etudes_secondaires = 2017
        self.candidat_translator.experiences_non_academiques.extend(
            [
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 10, 1),
                    date_fin=datetime.date(2021, 8, 31),
                    **self.params_default_experience_non_academique,
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 10, 1),
                    date_fin=datetime.date(2020, 5, 31),
                    **self.params_default_experience_non_academique,
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 2, 1),
                    date_fin=datetime.date(2019, 6, 30),
                    **self.params_default_experience_non_academique,
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 9, 1),
                    date_fin=datetime.date(2019, 1, 31),
                    **self.params_default_experience_non_academique,
                ),
            ]
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(context.exception.exceptions, ['Septembre 2019'])

    def test_should_etre_ok_si_periode_couverte_avec_une_experience_professionnelle_continue_apres_future_experience(
        self,
    ):
        self.etudes_secondaires.annee_diplome_etudes_secondaires = 2017
        self.candidat_translator.experiences_non_academiques.extend(
            [
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 10, 1),
                    date_fin=datetime.date(2021, 8, 31),
                    **self.params_default_experience_non_academique,
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 9, 1),
                    date_fin=datetime.date(2020, 5, 31),
                    **self.params_default_experience_non_academique,
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 9, 1),
                    date_fin=datetime.date(2019, 1, 31),
                    **self.params_default_experience_non_academique,
                ),
                # L'expérience suivante commence avant la précédente mais se termine après
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 2, 1),
                    date_fin=datetime.date(2019, 6, 30),
                    **self.params_default_experience_non_academique,
                ),
            ]
        )
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)

    def test_should_verification_etre_ok_si_aucune_annee_curriculum_a_saisir(self):
        with mock.patch.multiple(
            self.candidat,
            annee_derniere_inscription_ucl=2020,
            noma_derniere_inscription_ucl='01234567',
        ):
            proposition_id = self.message_bus.invoke(self.cmd)
            self.assertEqual(proposition_id.uuid, self.uuid_proposition)

    def test_should_verification_etre_ok_si_experience_complete(self):
        self.candidat_translator.experiences_academiques.append(self.experience_academiques_complete)
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.uuid_proposition)

    def test_should_verification_renvoyer_erreur_si_releve_notes_global_non_renseigne(self):
        self.experience_academiques_complete.releve_notes = []
        self.candidat_translator.experiences_academiques.append(self.experience_academiques_complete)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                "L'expérience académique 'Formation AA' est incomplète.",
                'De Septembre 2016 à Février 2017',
                'De Septembre 2017 à Février 2018',
                'De Septembre 2018 à Février 2019',
                'De Septembre 2019 à Février 2020',
                'De Septembre 2020 à Octobre 2020',
            ],
        )

    def test_should_verification_renvoyer_erreur_si_traduction_releve_notes_global_non_renseignee(self):
        self.experience_academiques_complete.traduction_releve_notes = []
        self.experience_academiques_complete.pays = FR_ISO_CODE
        self.experience_academiques_complete.regime_linguistique = 'SV'
        self.candidat_translator.experiences_academiques.append(self.experience_academiques_complete)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)
        self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_releve_notes_annuel_non_renseigne(self):
        self.experience_academiques_complete.type_releve_notes = TranscriptType.ONE_A_YEAR.name
        self.experience_academiques_complete.annees[0].releve_notes = []
        self.candidat_translator.experiences_academiques.append(self.experience_academiques_complete)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_traduction_releve_notes_annuel_non_renseignee(self):
        self.experience_academiques_complete.annees[0].traduction_releve_notes = []
        self.experience_academiques_complete.type_releve_notes = TranscriptType.ONE_A_YEAR.name
        self.experience_academiques_complete.pays = FR_ISO_CODE
        self.experience_academiques_complete.regime_linguistique = 'SV'
        self.candidat_translator.experiences_academiques.append(self.experience_academiques_complete)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_diplome_non_renseigne(self):
        self.experience_academiques_complete.a_obtenu_diplome = True
        self.experience_academiques_complete.diplome = []
        self.candidat_translator.experiences_academiques.append(self.experience_academiques_complete)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_date_prevue_delivrance_diplome_non_renseigne(self):
        self.experience_academiques_complete.a_obtenu_diplome = True
        self.experience_academiques_complete.date_prevue_delivrance_diplome = None
        self.candidat_translator.experiences_academiques.append(self.experience_academiques_complete)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)
