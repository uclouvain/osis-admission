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

import mock
from django.test import SimpleTestCase

from admission.ddd.projet_doctoral.preparation.commands import VerifierPropositionCommand
from admission.ddd.projet_doctoral.preparation.domain.model._enums import ChoixStatutSignatureGroupeDeSupervision
from admission.ddd.projet_doctoral.preparation.domain.model._signature_promoteur import ChoixEtatSignature
from admission.ddd.projet_doctoral.preparation.domain.validator.exceptions import (
    AdresseCorrespondanceNonCompleteeException,
    AdresseDomicileLegalNonCompleteeException,
    AnneesCurriculumNonSpecifieesException,
    CandidatNonTrouveException,
    CarteIdentiteeNonSpecifieeException,
    DateOuAnneeNaissanceNonSpecifieeException,
    DetailsPasseportNonSpecifiesException,
    FichierCurriculumNonRenseigneException,
    IdentificationNonCompleteeException,
    LanguesConnuesNonSpecifieesException,
    NumeroIdentiteBelgeNonSpecifieException,
    NumeroIdentiteNonSpecifieException,
    ProcedureDemandeSignatureNonLanceeException,
    PropositionNonApprouveeParMembresCAException,
    PropositionNonApprouveeParPromoteurException,
    NomEtPrenomNonSpecifiesException,
    SpecifierNOMASiDejaInscritException,
)
from admission.ddd.projet_doctoral.preparation.test.factory.groupe_de_supervision import (
    _SignatureMembreCAFactory,
    _SignaturePromoteurFactory,
)
from admission.ddd.projet_doctoral.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.projet_doctoral.preparation.domain.service.in_memory.profil_candidat import (
    DiplomeEtudeSecondaire,
    ProfilCandidatInMemoryTranslator,
    ExperienceNonAcademique,
)
from admission.infrastructure.projet_doctoral.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.projet_doctoral.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository


class TestVerifierPropositionServiceCommun(SimpleTestCase):
    def setUp(self) -> None:
        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.proposition_repository = PropositionInMemoryRepository()
        self.groupe_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.proposition = PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory()
        self.groupe_supervision = self.groupe_supervision_repository.get_by_proposition_id(self.proposition.entity_id)
        self.candidat = self.candidat_translator.profil_candidats[0]
        self.adresse_domicile_legal = self.candidat_translator.adresses_candidats[0]
        self.adresse_correspondance = self.candidat_translator.adresses_candidats[1]
        self.experiences_non_academiques = self.candidat_translator.experiences_non_academiques
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance
        self.academic_year_repository = AcademicYearInMemoryRepository()

        for annee in range(2016, 2021):
            self.academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )

        # Mock datetime to return the 2020 year as the current year
        patcher = mock.patch(
            'admission.ddd.projet_doctoral.preparation.use_case.read.verifier_proposition_service.datetime'
        )
        self.addCleanup(patcher.stop)
        self.mock_foo = patcher.start()
        self.mock_foo.date.today.return_value = datetime.date(2020, 11, 1)

        self.cmd = VerifierPropositionCommand(uuid_proposition=self.proposition.entity_id.uuid)


class TestVerifierPropositionService(TestVerifierPropositionServiceCommun):
    def test_should_verifier_etre_ok_si_complet(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.proposition.entity_id.uuid)

    def test_should_retourner_erreur_si_candidat_non_trouve(self):
        with mock.patch.multiple(self.candidat, matricule='unknown_user_id'):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), CandidatNonTrouveException)

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

    def test_should_retourner_erreur_si_noma_non_renseigne_si_precedente_inscription(self):
        with mock.patch.multiple(
            self.candidat,
            annee_derniere_inscription_ucl=2020,
            noma_derniere_inscription_ucl='',
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), SpecifierNOMASiDejaInscritException)

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
            date_expiration_passeport=None,
            passeport=[],
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

    def test_should_retourner_erreur_si_adresse_domicile_legal_non_renseignee(self):
        with mock.patch.object(self.adresse_domicile_legal, 'personne', 'unknown_user_id'):
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
            self.assertEqual(proposition_id.uuid, self.proposition.entity_id.uuid)

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
        with mock.patch.object(self.candidat, 'curriculum', None):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), FichierCurriculumNonRenseigneException)

    def test_should_retourner_erreur_si_demande_signature_pas_en_cours(self):
        with mock.patch.object(
            self.groupe_supervision,
            'statut_signature',
            ChoixStatutSignatureGroupeDeSupervision.IN_PROGRESS,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), ProcedureDemandeSignatureNonLanceeException)

    def test_should_retourner_erreur_si_tous_promoteurs_n_ont_pas_approuve(self):
        self.groupe_supervision.signatures_promoteurs.append(
            _SignaturePromoteurFactory(promoteur_id__matricule='promoteur-SC3DP', etat=ChoixEtatSignature.DECLINED),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)
        self.assertIsInstance(context.exception.exceptions.pop(), PropositionNonApprouveeParPromoteurException)

        self.groupe_supervision.signatures_promoteurs.pop()

    def test_should_retourner_erreur_si_tous_membres_ca_n_ont_pas_approuve(self):
        self.groupe_supervision.signatures_membres_CA.append(
            _SignatureMembreCAFactory(membre_CA_id__matricule='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED),
        )

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)
        self.assertIsInstance(context.exception.exceptions.pop(), PropositionNonApprouveeParMembresCAException)

        self.groupe_supervision.signatures_membres_CA.pop()


class TestVerifierPropositionServiceCurriculumYears(TestVerifierPropositionServiceCommun):
    def setUp(self) -> None:
        super().setUp()
        for experience in (
            self.candidat_translator.experiences_academiques + self.candidat_translator.experiences_non_academiques
        ):
            experience.personne = 'other'

    def test_should_retourner_erreur_si_5_dernieres_annees_curriculum_non_saisies(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        exception = context.exception.exceptions.pop()
        self.assertIsInstance(exception, AnneesCurriculumNonSpecifieesException)
        self.assertIn('2020', exception.message)
        self.assertIn('2019', exception.message)
        self.assertIn('2018', exception.message)
        self.assertIn('2017', exception.message)
        self.assertIn('2016', exception.message)

    def test_should_retourner_erreur_si_dernieres_annees_curriculum_non_saisies_avec_diplome_secondaire_belge(self):
        self.candidat_translator.diplomes_etudes_secondaires_belges.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2018)
        )

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        exception = context.exception.exceptions.pop()
        self.assertIsInstance(exception, AnneesCurriculumNonSpecifieesException)
        self.assertIn('2020', exception.message)
        self.assertIn('2019', exception.message)

    def test_should_retourner_erreur_si_dernieres_annees_curriculum_non_saisies_avec_diplome_secondaire_etranger(self):
        self.candidat_translator.diplomes_etudes_secondaires_etrangers.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2017)
        )

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        exception = context.exception.exceptions.pop()
        self.assertIsInstance(exception, AnneesCurriculumNonSpecifieesException)
        self.assertIn('2020', exception.message)
        self.assertIn('2019', exception.message)
        self.assertIn('2018', exception.message)

    def test_should_retourner_erreur_si_dernieres_annees_curriculum_non_saisies_avec_ancienne_inscription_ucl(self):
        with mock.patch.multiple(
            self.candidat,
            annee_derniere_inscription_ucl=2019,
            noma_derniere_inscription_ucl='01234567',
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)

        exception = context.exception.exceptions.pop()
        self.assertIsInstance(exception, AnneesCurriculumNonSpecifieesException)
        self.assertIn('2020', exception.message)

    def test_should_retourner_erreur_si_annees_curriculum_non_saisies_avec_diplome_et_ancienne_inscription(self):
        self.candidat_translator.diplomes_etudes_secondaires_belges.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2017)
        )

        with mock.patch.multiple(
            self.candidat,
            annee_derniere_inscription_ucl=2018,
            noma_derniere_inscription_ucl='01234567',
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)

        exception = context.exception.exceptions.pop()
        self.assertIsInstance(exception, AnneesCurriculumNonSpecifieesException)
        self.assertIn('2020', exception.message)
        self.assertIn('2019', exception.message)

    def test_should_verification_etre_ok_si_une_experiences_professionnelles_couvre_exactement(self):
        self.candidat_translator.diplomes_etudes_secondaires_belges.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2017)
        )
        self.candidat_translator.experiences_non_academiques.append(
            ExperienceNonAcademique(
                personne=self.candidat.matricule,
                date_debut=datetime.date(2018, 9, 1),
                date_fin=datetime.date(2021, 6, 30),
            ),
        )
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.proposition.entity_id.uuid)
        self.candidat_translator.experiences_non_academiques.pop()

    def test_should_verification_etre_ok_si_une_experiences_professionnelles_couvre_davantage(self):
        self.candidat_translator.diplomes_etudes_secondaires_belges.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2017)
        )
        self.candidat_translator.experiences_non_academiques.append(
            ExperienceNonAcademique(
                personne=self.candidat.matricule,
                date_debut=datetime.date(2018, 8, 1),
                date_fin=datetime.date(2021, 7, 31),
            )
        )
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.proposition.entity_id.uuid)

    def test_should_verification_renvoyer_exception_si_une_experiences_professionnelles_couvre_pas_debut(self):
        self.candidat_translator.diplomes_etudes_secondaires_belges.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2017)
        )
        self.candidat_translator.experiences_non_academiques.append(
            ExperienceNonAcademique(
                personne=self.candidat.matricule,
                date_debut=datetime.date(2018, 10, 1),
                date_fin=datetime.date(2021, 6, 30),
            )
        )

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        exception = context.exception.exceptions.pop()
        self.assertIsInstance(exception, AnneesCurriculumNonSpecifieesException)
        self.assertIn('2018', exception.message)

    def test_should_verification_renvoyer_exception_si_une_experiences_professionnelles_couvre_pas_fin(self):
        self.candidat_translator.diplomes_etudes_secondaires_belges.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2017)
        )
        self.candidat_translator.experiences_non_academiques.append(
            ExperienceNonAcademique(
                personne=self.candidat.matricule,
                date_debut=datetime.date(2018, 9, 1),
                date_fin=datetime.date(2021, 5, 31),
            )
        )

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        exception = context.exception.exceptions.pop()
        self.assertIsInstance(exception, AnneesCurriculumNonSpecifieesException)
        self.assertIn('2020', exception.message)

    def test_should_verification_etre_ok_si_experiences_professionnelles_couvrent_en_se_suivant_ou_chevauchant(self):
        self.candidat_translator.diplomes_etudes_secondaires_belges.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2017)
        )
        self.candidat_translator.experiences_non_academiques.extend(
            [
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2020, 1, 1),
                    date_fin=datetime.date(2021, 8, 31),
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 11, 1),
                    date_fin=datetime.date(2020, 3, 31),
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 7, 1),
                    date_fin=datetime.date(2019, 10, 31),
                ),
            ]
        )
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.proposition.entity_id.uuid)

    def test_should_verification_etre_ok_si_experiences_professionnelles_couvrent_en_ne_se_chevauchant_pas(self):
        self.candidat_translator.diplomes_etudes_secondaires_belges.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2017)
        )
        self.candidat_translator.experiences_non_academiques.extend(
            [
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 10, 1),
                    date_fin=datetime.date(2021, 8, 31),
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 10, 1),
                    date_fin=datetime.date(2020, 5, 31),
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 9, 1),
                    date_fin=datetime.date(2019, 9, 30),
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 9, 1),
                    date_fin=datetime.date(2019, 6, 30),
                ),
            ]
        )
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.proposition.entity_id.uuid)

    def test_should_renvoyer_exception_si_experiences_professionnelles_ne_couvrent_pas_et_ne_se_chevauchent_pas(self):
        self.candidat_translator.diplomes_etudes_secondaires_belges.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2017)
        )
        self.candidat_translator.experiences_non_academiques.extend(
            [
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 10, 1),
                    date_fin=datetime.date(2021, 8, 31),
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 10, 1),
                    date_fin=datetime.date(2020, 5, 31),
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 9, 1),
                    date_fin=datetime.date(2019, 6, 30),
                ),
            ]
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        exception = context.exception.exceptions.pop()
        self.assertIsInstance(exception, AnneesCurriculumNonSpecifieesException)
        self.assertIn('2019', exception.message)

    def test_should_renvoyer_exception_si_experiences_professionnelles_ne_couvrent_pas_et_ne_se_chevauchent_pas_v2(
        self,
    ):
        self.candidat_translator.diplomes_etudes_secondaires_belges.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2017)
        )
        self.candidat_translator.experiences_non_academiques.extend(
            [
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 10, 1),
                    date_fin=datetime.date(2021, 8, 31),
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 10, 1),
                    date_fin=datetime.date(2020, 5, 31),
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 2, 1),
                    date_fin=datetime.date(2019, 6, 30),
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 9, 1),
                    date_fin=datetime.date(2019, 1, 31),
                ),
            ]
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        exception = context.exception.exceptions.pop()
        self.assertIsInstance(exception, AnneesCurriculumNonSpecifieesException)
        self.assertIn('2019', exception.message)

    def test_should_etre_ok_si_periode_couverte_avec_une_experience_professionnelle_continue_apres_future_experience(
        self,
    ):
        self.candidat_translator.diplomes_etudes_secondaires_belges.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2017)
        )
        self.candidat_translator.experiences_non_academiques.extend(
            [
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 10, 1),
                    date_fin=datetime.date(2021, 8, 31),
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2019, 9, 1),
                    date_fin=datetime.date(2020, 5, 31),
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 9, 1),
                    date_fin=datetime.date(2019, 1, 31),
                ),
                # L'expérience suivante commence avant la précédente mais se termine après
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 2, 1),
                    date_fin=datetime.date(2019, 6, 30),
                ),
            ]
        )
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.proposition.entity_id.uuid)

    def test_should_verification_etre_ok_si_aucune_annee_curriculum_a_saisir(self):
        with mock.patch.multiple(
            self.candidat,
            annee_derniere_inscription_ucl=2020,
            noma_derniere_inscription_ucl='01234567',
        ):
            proposition_id = self.message_bus.invoke(self.cmd)
            self.assertEqual(proposition_id.uuid, self.proposition.entity_id.uuid)
