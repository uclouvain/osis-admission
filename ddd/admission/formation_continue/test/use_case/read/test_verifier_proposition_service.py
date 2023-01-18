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
from unittest import TestCase, mock

from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    CarteBancaireRemboursementIbanNonCompleteException,
    CarteBancaireRemboursementAutreFormatNonCompleteException,
    AffiliationsNonCompleteesException,
    TypeCompteBancaireRemboursementNonCompleteException,
)
from admission.ddd.admission.domain.validator.exceptions import (
    ConditionsAccessNonRempliesException,
    NombrePropositionsSoumisesDepasseException,
    QuestionsSpecifiquesCurriculumNonCompleteesException,
    QuestionsSpecifiquesEtudesSecondairesNonCompleteesException,
    QuestionsSpecifiquesInformationsComplementairesNonCompleteesException,
    QuestionsSpecifiquesChoixFormationNonCompleteesException,
)
from admission.ddd.admission.dtos import EtudesSecondairesDTO
from admission.ddd.admission.enums import ChoixTypeCompteBancaire
from admission.ddd.admission.formation_continue.commands import VerifierPropositionQuery
from admission.ddd.admission.formation_continue.domain.model._comptabilite import Comptabilite
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutProposition
from admission.ddd.admission.formation_continue.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    EtudesSecondairesNonCompleteesException,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.enums.got_diploma import GotDiploma


class TestVerifierPropositionService(TestCase):
    def assertHasInstance(self, container, cls, msg=None):
        if not any(isinstance(obj, cls) for obj in container):
            self.fail(msg or f"No instance of '{cls}' has been found")

    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance
        self.proposition_repository = PropositionInMemoryRepository
        self.addCleanup(self.proposition_repository.reset)
        self.complete_proposition = self.proposition_repository.get(entity_id=PropositionIdentity(uuid='uuid-USCC1'))
        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.etudes_secondaires = self.candidat_translator.etudes_secondaires
        self.verifier_commande = VerifierPropositionQuery(uuid_proposition=self.complete_proposition.entity_id.uuid)
        self.comptabilite_complete = {
            'etudiant_solidaire': True,
            'type_numero_compte': ChoixTypeCompteBancaire.IBAN,
            'numero_compte_iban': '0123456',
            'iban_valide': True,
            'numero_compte_autre_format': '0123456',
            'code_bic_swift_banque': 'ABC',
            'prenom_titulaire_compte': 'John',
            'nom_titulaire_compte': 'Doe',
        }

    def test_should_verifier_etre_ok_si_complet(self):
        proposition_id = self.message_bus.invoke(self.verifier_commande)
        self.assertEqual(proposition_id, self.complete_proposition.entity_id)

    def test_should_retourner_erreur_si_conditions_acces_non_remplies(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(VerifierPropositionQuery(uuid_proposition='uuid-USCC4'))
        self.assertHasInstance(context.exception.exceptions, ConditionsAccessNonRempliesException)

    def test_should_verification_renvoyer_erreur_si_trop_de_demandes_envoyees(self):
        propositions = self.proposition_repository.search(matricule_candidat='0123456789')
        for proposition in propositions:
            proposition.statut = ChoixStatutProposition.IN_PROGRESS

        for proposition_index in range(2):
            propositions[proposition_index].statut = ChoixStatutProposition.SUBMITTED

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(VerifierPropositionQuery(uuid_proposition=propositions[2].entity_id.uuid))

        self.assertHasInstance(context.exception.exceptions, NombrePropositionsSoumisesDepasseException)

    def test_should_retourner_erreur_si_indication_a_diplome_etudes_secondaires_non_specifiee(self):
        with mock.patch.dict(
            self.etudes_secondaires, {'0000000001': EtudesSecondairesDTO(annee_diplome_etudes_secondaires=2020)}
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.verifier_commande)
            self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesException)

    def test_should_retourner_erreur_si_annee_diplome_etudes_secondaires_non_specifiee(self):
        with mock.patch.dict(
            self.etudes_secondaires,
            {'0000000001': EtudesSecondairesDTO(diplome_etudes_secondaires=GotDiploma.YES.name)},
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.verifier_commande)
            self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesException)

        with mock.patch.dict(
            self.etudes_secondaires,
            {'0000000001': EtudesSecondairesDTO(diplome_etudes_secondaires=GotDiploma.THIS_YEAR.name)},
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.verifier_commande)
            self.assertHasInstance(context.exception.exceptions, EtudesSecondairesNonCompleteesException)

    def test_should_etre_ok_si_indication_et_annee_diplome_etudes_secondaires_specifiees(self):
        with mock.patch.dict(
            self.etudes_secondaires,
            {
                '0000000001': EtudesSecondairesDTO(
                    diplome_etudes_secondaires=GotDiploma.YES.name,
                    annee_diplome_etudes_secondaires=2020,
                )
            },
        ):
            id_proposition = self.message_bus.invoke(self.verifier_commande)
            self.assertEqual(id_proposition, self.complete_proposition.entity_id)

    def test_should_etre_ok_si_indication_pas_etudes_secondaires(self):
        with mock.patch.dict(
            self.etudes_secondaires,
            {
                '0000000001': EtudesSecondairesDTO(
                    diplome_etudes_secondaires=GotDiploma.NO.name,
                )
            },
        ):
            id_proposition = self.message_bus.invoke(self.verifier_commande)
            self.assertEqual(id_proposition, self.complete_proposition.entity_id)

    def test_should_retourner_erreur_si_compte_bancaire_iban_incomplet(self):
        self.comptabilite_complete.update(
            {
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN,
                'numero_compte_iban': '',
            }
        )
        self.complete_proposition.comptabilite = Comptabilite(**self.comptabilite_complete)
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.verifier_commande)
        self.assertHasInstance(context.exception.exceptions, CarteBancaireRemboursementIbanNonCompleteException)

    def test_should_retourner_erreur_prenom_titulaire_compte_bancaire_iban_non_renseigne(self):
        self.comptabilite_complete.update(
            {
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN,
                'prenom_titulaire_compte': '',
            }
        )
        self.complete_proposition.comptabilite = Comptabilite(**self.comptabilite_complete)
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.verifier_commande)
        self.assertHasInstance(context.exception.exceptions, CarteBancaireRemboursementIbanNonCompleteException)

    def test_should_retourner_erreur_nom_titulaire_compte_bancaire_iban_non_renseigne(self):
        self.comptabilite_complete.update(
            {
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN,
                'nom_titulaire_compte': '',
            }
        )
        self.complete_proposition.comptabilite = Comptabilite(**self.comptabilite_complete)
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.verifier_commande)
        self.assertHasInstance(context.exception.exceptions, CarteBancaireRemboursementIbanNonCompleteException)

    def test_should_retourner_erreur_si_numero_compte_bancaire_autre_format_non_renseigne(self):
        self.comptabilite_complete.update(
            {
                'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT,
                'numero_compte_autre_format': '',
            }
        )
        self.complete_proposition.comptabilite = Comptabilite(**self.comptabilite_complete)
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.verifier_commande)
        self.assertHasInstance(context.exception.exceptions, CarteBancaireRemboursementAutreFormatNonCompleteException)

    def test_should_retourner_erreur_si_code_bic_compte_bancaire_autre_format_non_renseigne(self):
        self.comptabilite_complete.update(
            {
                'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT,
                'code_bic_swift_banque': '',
            }
        )
        self.complete_proposition.comptabilite = Comptabilite(**self.comptabilite_complete)
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.verifier_commande)
        self.assertHasInstance(context.exception.exceptions, CarteBancaireRemboursementAutreFormatNonCompleteException)

    def test_should_retourner_erreur_si_type_compte_bancaire_non_renseigne(self):
        self.comptabilite_complete.update({'type_numero_compte': None})
        self.complete_proposition.comptabilite = Comptabilite(**self.comptabilite_complete)
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.verifier_commande)
        self.assertHasInstance(context.exception.exceptions, TypeCompteBancaireRemboursementNonCompleteException)

    def test_should_retourner_erreur_prenom_titulaire_compte_bancaire_autre_format_non_renseigne(self):
        self.comptabilite_complete.update(
            {
                'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT,
                'prenom_titulaire_compte': '',
            }
        )

        self.complete_proposition.comptabilite = Comptabilite(**self.comptabilite_complete)
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.verifier_commande)
        self.assertHasInstance(context.exception.exceptions, CarteBancaireRemboursementAutreFormatNonCompleteException)

    def test_should_retourner_erreur_nom_titulaire_compte_bancaire_autre_format_non_renseigne(self):
        self.comptabilite_complete.update(
            {
                'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT,
                'nom_titulaire_compte': '',
            }
        )

        self.complete_proposition.comptabilite = Comptabilite(**self.comptabilite_complete)
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.verifier_commande)
        self.assertHasInstance(context.exception.exceptions, CarteBancaireRemboursementAutreFormatNonCompleteException)

    def test_should_retourner_erreur_si_etudiant_solidaire_non_renseigne(self):
        self.comptabilite_complete.update({'etudiant_solidaire': None})
        self.complete_proposition.comptabilite = Comptabilite(**self.comptabilite_complete)
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.verifier_commande)
        self.assertHasInstance(context.exception.exceptions, AffiliationsNonCompleteesException)

    def test_should_etre_ok_si_compte_bancaire_iban_complet(self):
        self.comptabilite_complete.update({'type_numero_compte': ChoixTypeCompteBancaire.IBAN})
        self.complete_proposition.comptabilite = Comptabilite(**self.comptabilite_complete)
        self.assertEqual(
            self.message_bus.invoke(self.verifier_commande),
            self.complete_proposition.entity_id,
        )

    def test_should_etre_ok_si_compte_bancaire_autre_format_complet(self):
        self.comptabilite_complete.update({'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT})
        self.complete_proposition.comptabilite = Comptabilite(**self.comptabilite_complete)
        self.assertEqual(
            self.message_bus.invoke(self.verifier_commande),
            self.complete_proposition.entity_id,
        )

    def test_should_etre_ok_si_etudiant_solidaire_a_faux(self):
        self.comptabilite_complete.update({'etudiant_solidaire': False})
        self.complete_proposition.comptabilite = Comptabilite(**self.comptabilite_complete)
        self.assertEqual(
            self.message_bus.invoke(self.verifier_commande),
            self.complete_proposition.entity_id,
        )

    def test_should_retourner_erreur_si_questions_specifiques_pas_completees_pour_curriculum(self):
        with mock.patch.multiple(
            self.complete_proposition,
            reponses_questions_specifiques={
                **self.complete_proposition.reponses_questions_specifiques,
                '26de0c3d-3c06-4c93-8eb4-c8648f04f143': '',
            },
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.verifier_commande)
            self.assertHasInstance(context.exception.exceptions, QuestionsSpecifiquesCurriculumNonCompleteesException)

    def test_should_retourner_erreur_si_questions_specifiques_pas_completees_pour_etudes_secondaires(self):
        with mock.patch.multiple(
            self.complete_proposition,
            reponses_questions_specifiques={
                **self.complete_proposition.reponses_questions_specifiques,
                '26de0c3d-3c06-4c93-8eb4-c8648f04f144': '',
            },
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.verifier_commande)
            self.assertHasInstance(
                context.exception.exceptions,
                QuestionsSpecifiquesEtudesSecondairesNonCompleteesException,
            )

    def test_should_retourner_erreur_si_questions_specifiques_pas_completees_pour_informations_additionnelles(self):
        with mock.patch.multiple(
            self.complete_proposition,
            reponses_questions_specifiques={
                **self.complete_proposition.reponses_questions_specifiques,
                '26de0c3d-3c06-4c93-8eb4-c8648f04f145': '',
            },
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.verifier_commande)
            self.assertHasInstance(
                context.exception.exceptions,
                QuestionsSpecifiquesInformationsComplementairesNonCompleteesException,
            )

    def test_should_retourner_erreur_si_questions_specifiques_pas_completees_pour_choix_formation(self):
        with mock.patch.multiple(
            self.complete_proposition,
            reponses_questions_specifiques={
                **self.complete_proposition.reponses_questions_specifiques,
                '26de0c3d-3c06-4c93-8eb4-c8648f04f140': '',
            },
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.verifier_commande)
            self.assertHasInstance(
                context.exception.exceptions,
                QuestionsSpecifiquesChoixFormationNonCompleteesException,
            )
