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
from unittest import TestCase

import freezegun
import mock

from admission.ddd import BE_ISO_CODE, FR_ISO_CODE
from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.commands import VerifierPropositionQuery
from admission.ddd.admission.enums import ChoixTypeCompteBancaire
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixEtatSignature,
    ChoixStatutSignatureGroupeDeSupervision,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AbsenceDeDetteNonCompleteeException,
    AdresseCorrespondanceNonCompleteeException,
    AdresseDomicileLegalNonCompleteeException,
    AnneesCurriculumNonSpecifieesException,
    CandidatNonTrouveException,
    CarteBancaireRemboursementAutreFormatNonCompleteException,
    CarteBancaireRemboursementIbanNonCompleteException,
    CarteIdentiteeNonSpecifieeException,
    DateOuAnneeNaissanceNonSpecifieeException,
    DetailsPasseportNonSpecifiesException,
    FichierCurriculumNonRenseigneException,
    IdentificationNonCompleteeException,
    LanguesConnuesNonSpecifieesException,
    NomEtPrenomNonSpecifiesException,
    NumeroIdentiteBelgeNonSpecifieException,
    NumeroIdentiteNonSpecifieException,
    ProcedureDemandeSignatureNonLanceeException,
    PropositionNonApprouveeParMembresCAException,
    PropositionNonApprouveeParPromoteurException,
    SpecifierNOMASiDejaInscritException,
    ExperiencesAcademiquesNonCompleteesException,
)
from admission.ddd.admission.doctorat.preparation.test.factory.groupe_de_supervision import (
    _SignatureMembreCAFactory,
    _SignaturePromoteurFactory,
)
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    _ComptabiliteFactory,
)
from admission.ddd.admission.domain.validator.exceptions import (
    QuestionsSpecifiquesCurriculumNonCompleteesException,
    QuestionsSpecifiquesEtudesSecondairesNonCompleteesException,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import (
    DiplomeEtudeSecondaire,
    ExperienceNonAcademique,
    ProfilCandidatInMemoryTranslator,
    ExperienceAcademique,
    AnneeExperienceAcademique,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository
from osis_profile.models.enums.curriculum import Result, TranscriptType


class TestVerifierPropositionServiceCommun(TestCase):
    def setUp(self) -> None:
        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.proposition_repository = PropositionInMemoryRepository()
        self.groupe_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.proposition = PropositionInMemoryRepository().get(
            entity_id=PropositionIdentityBuilder.build_from_uuid(uuid='uuid-SC3DP-promoteurs-membres-deja-approuves')
        )
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
        patcher = freezegun.freeze_time('2020-11-01')
        patcher.start()
        self.addCleanup(patcher.stop)

        self.cmd = VerifierPropositionQuery(uuid_proposition=self.proposition.entity_id.uuid)


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
        with mock.patch.object(self.proposition, 'curriculum', []):
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

    def _test_should_retourner_erreur_si_comptabilite_incomplete(self, comptabilite, exception):
        with mock.patch.object(self.proposition, 'comptabilite', comptabilite):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertTrue(any(member for member in context.exception.exceptions if isinstance(member, exception)))

    def _test_should_retourner_erreur_si_assimilation_incomplete(self, comptabilite, exception):
        with mock.patch.object(self.candidat, 'pays_nationalite', 'CA'):
            self._test_should_retourner_erreur_si_comptabilite_incomplete(
                comptabilite=comptabilite,
                exception=exception,
            )

    def test_should_retourner_erreur_si_questions_specifiques_pas_completees_pour_curriculum(self):
        with mock.patch.multiple(
            self.proposition,
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
        with mock.patch.multiple(
            self.proposition,
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

    def test_should_retourner_erreur_si_absence_dettes_incomplet(self):
        self._test_should_retourner_erreur_si_comptabilite_incomplete(
            comptabilite=_ComptabiliteFactory(attestation_absence_dette_etablissement=[]),
            exception=AbsenceDeDetteNonCompleteeException,
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


class TestVerifierPropositionServiceCurriculumYears(TestVerifierPropositionServiceCommun):
    def setUp(self) -> None:
        super().setUp()
        for experience in (
            self.candidat_translator.experiences_academiques + self.candidat_translator.experiences_non_academiques
        ):
            experience.personne = 'other'

        self.experience_academiques_complete = ExperienceAcademique(
            personne=self.candidat.matricule,
            communaute_fr=True,
            pays=BE_ISO_CODE,
            annees=[
                AnneeExperienceAcademique(
                    annee=2016,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                ),
                AnneeExperienceAcademique(
                    annee=2017,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                ),
                AnneeExperienceAcademique(
                    annee=2018,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                ),
                AnneeExperienceAcademique(
                    annee=2019,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                ),
                AnneeExperienceAcademique(
                    annee=2020,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
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
        )

    def assertHasInstance(self, container, cls, msg=None):
        if not any(isinstance(obj, cls) for obj in container):
            self.fail(msg or f"No instance of '{cls}' has been found")

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
                'De Septembre 2016 à Janvier 2017',
                'De Septembre 2017 à Janvier 2018',
                'De Septembre 2018 à Janvier 2019',
                'De Septembre 2019 à Janvier 2020',
                'De Septembre 2020 à Octobre 2020',
            ],
        )

    def test_should_retourner_erreur_si_dernieres_annees_curriculum_non_saisies_avec_diplome_secondaire_belge(self):
        self.candidat_translator.diplomes_etudes_secondaires_belges.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2018)
        )

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2019 à Janvier 2020',
                'De Septembre 2020 à Octobre 2020',
            ],
        )

    def test_should_retourner_erreur_si_dernieres_annees_curriculum_non_saisies_avec_diplome_secondaire_etranger(self):
        self.candidat_translator.diplomes_etudes_secondaires_etrangers.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2017)
        )

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2018 à Janvier 2019',
                'De Septembre 2019 à Janvier 2020',
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

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2019 à Janvier 2020',
                'De Septembre 2020 à Octobre 2020',
            ],
        )

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

    def test_should_verification_etre_ok_si_une_des_experiences_professionnelles_couvre_davantage(self):
        self.candidat_translator.diplomes_etudes_secondaires_belges.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2017)
        )
        self.candidat_translator.experiences_non_academiques.extend(
            [
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 8, 1),
                    date_fin=datetime.date(2021, 7, 31),
                ),
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2017, 8, 1),
                    date_fin=datetime.date(2018, 7, 31),
                ),
            ],
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

        self.assertAnneesCurriculum(context.exception.exceptions, ['Septembre 2018'])

    def test_should_verification_renvoyer_exception_si_une_experiences_professionnelles_couvre_pas_fin(self):
        self.candidat_translator.diplomes_etudes_secondaires_belges.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2017)
        )
        self.candidat_translator.experiences_non_academiques.append(
            ExperienceNonAcademique(
                personne=self.candidat.matricule,
                date_debut=datetime.date(2018, 9, 1),
                date_fin=datetime.date(2020, 9, 30),
            )
        )

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(context.exception.exceptions, ['Octobre 2020'])

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

    def test_should_renvoyer_exception_si_experiences_professionnelles_trop_anciennes(self):
        self.candidat_translator.diplomes_etudes_secondaires_belges.append(
            DiplomeEtudeSecondaire(personne=self.candidat.matricule, annee=2017)
        )
        self.candidat_translator.experiences_non_academiques.extend(
            [
                ExperienceNonAcademique(
                    personne=self.candidat.matricule,
                    date_debut=datetime.date(2018, 10, 1),
                    date_fin=datetime.date(2018, 12, 31),
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

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2019 à Janvier 2020',
                'De Septembre 2020 à Octobre 2020',
            ],
        )

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

        self.assertAnneesCurriculum(context.exception.exceptions, ['Septembre 2019'])

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

    def test_should_verification_etre_ok_si_experience_complete(self):
        self.candidat_translator.experiences_academiques.append(self.experience_academiques_complete)
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.proposition.entity_id.uuid)

    def test_should_verification_renvoyer_erreur_si_releve_notes_global_non_renseigne(self):
        self.experience_academiques_complete.releve_notes = []
        self.candidat_translator.experiences_academiques.append(self.experience_academiques_complete)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'Cette expérience académique est incomplète.',
                'De Septembre 2016 à Janvier 2017',
                'De Septembre 2017 à Janvier 2018',
                'De Septembre 2018 à Janvier 2019',
                'De Septembre 2019 à Janvier 2020',
                'De Septembre 2020 à Octobre 2020',
            ],
        )

    def test_should_verification_renvoyer_erreur_si_traduction_releve_notes_global_non_renseignee(self):
        self.experience_academiques_complete.traduction_releve_notes = []
        self.experience_academiques_complete.pays = FR_ISO_CODE
        self.experience_academiques_complete.regime_linguistique = 'BR'
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
        self.experience_academiques_complete.regime_linguistique = 'BR'
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

    def test_should_verification_renvoyer_erreur_si_rang_diplome_non_renseigne(self):
        self.experience_academiques_complete.a_obtenu_diplome = True
        self.experience_academiques_complete.rang_diplome = ''
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

    def test_should_verification_renvoyer_erreur_si_titre_memoire_non_renseigne(self):
        self.experience_academiques_complete.a_obtenu_diplome = True
        self.experience_academiques_complete.titre_memoire = ''
        self.candidat_translator.experiences_academiques.append(self.experience_academiques_complete)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_note_memoire_non_renseigne(self):
        self.experience_academiques_complete.a_obtenu_diplome = True
        self.experience_academiques_complete.note_memoire = ''
        self.candidat_translator.experiences_academiques.append(self.experience_academiques_complete)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)

    def test_should_verification_renvoyer_erreur_si_resume_memoire_non_renseigne(self):
        self.experience_academiques_complete.a_obtenu_diplome = True
        self.experience_academiques_complete.resume_memoire = []
        self.candidat_translator.experiences_academiques.append(self.experience_academiques_complete)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertHasInstance(context.exception.exceptions, ExperiencesAcademiquesNonCompleteesException)
