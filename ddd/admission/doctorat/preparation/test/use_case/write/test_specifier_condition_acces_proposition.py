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

from django.test import SimpleTestCase

from admission.ddd.admission.doctorat.preparation.commands import SpecifierConditionAccesPropositionCommand
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    PropositionNonTrouveeException,
)
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPConfirmeeFactory,
)
from admission.ddd.admission.formation_generale.test.factory.titre_acces import TitreAccesSelectionnableFactory
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.titre_acces_selectionnable import (
    TitreAccesSelectionnableInMemoryRepositoryFactory,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from epc.models.enums.condition_acces import ConditionAcces


class TestSpecifierConditionAccesPropositionService(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.proposition = self.proposition_repository.get(PropositionIdentity(uuid='uuid-SC3DP-confirmee'))
        self.proposition.statut = ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC
        self.titre_acces_repository = TitreAccesSelectionnableInMemoryRepositoryFactory()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance

    def test_should_specifier_condition_acces_millesime_et_complements_formation_proposition(self):
        proposition_id = self.message_bus.invoke(
            SpecifierConditionAccesPropositionCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                condition_acces=ConditionAcces.BAC.name,
                millesime_condition_acces=2021,
                avec_complements_formation=True,
                gestionnaire='0123456789',
            )
        )
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.condition_acces, ConditionAcces.BAC)
        self.assertEqual(proposition.millesime_condition_acces, 2021)
        self.assertEqual(proposition.avec_complements_formation, True)

    def test_should_complements_formation_et_commentaire_associe_etre_vides_si_reponse_negative_aux_complements(self):
        proposition = PropositionAdmissionSC3DPConfirmeeFactory(
            formation_id=FormationIdentityFactory(sigle="uuid-SC3DP-confirmee", annee=2021),
            curriculum=['file1.pdf'],
            est_confirmee=True,
            est_approuvee_par_fac=True,
            statut=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC,
        )

        self.proposition_repository.save(proposition)

        with self.assertRaises(MultipleBusinessExceptions):
            self.message_bus.invoke(
                SpecifierConditionAccesPropositionCommand(
                    uuid_proposition='uuid-SC3DP-confirmee',
                    avec_complements_formation=False,
                    gestionnaire='0123456789',
                )
            )

        self.assertEqual(proposition.avec_complements_formation, True)
        self.assertNotEqual(proposition.complements_formation, [])
        self.assertNotEqual(proposition.commentaire_complements_formation, '')

        proposition.commentaire_complements_formation = ''
        self.proposition_repository.save(proposition)

        with self.assertRaises(MultipleBusinessExceptions):
            self.message_bus.invoke(
                SpecifierConditionAccesPropositionCommand(
                    uuid_proposition='uuid-SC3DP-confirmee',
                    avec_complements_formation=False,
                    gestionnaire='0123456789',
                )
            )

        self.assertEqual(proposition.avec_complements_formation, True)
        self.assertNotEqual(proposition.complements_formation, [])
        self.assertEqual(proposition.commentaire_complements_formation, '')

        proposition.complements_formation = []
        proposition.commentaire_complements_formation = 'Test'
        self.proposition_repository.save(proposition)

        with self.assertRaises(MultipleBusinessExceptions):
            self.message_bus.invoke(
                SpecifierConditionAccesPropositionCommand(
                    uuid_proposition='uuid-SC3DP-confirmee',
                    avec_complements_formation=False,
                    gestionnaire='0123456789',
                )
            )

        self.assertEqual(proposition.avec_complements_formation, True)
        self.assertEqual(proposition.complements_formation, [])
        self.assertNotEqual(proposition.commentaire_complements_formation, '')

        proposition.complements_formation = []
        proposition.commentaire_complements_formation = ''
        self.proposition_repository.save(proposition)

        proposition_id = self.message_bus.invoke(
            SpecifierConditionAccesPropositionCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                avec_complements_formation=False,
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(proposition.avec_complements_formation, False)
        self.assertEqual(proposition.complements_formation, [])
        self.assertEqual(proposition.commentaire_complements_formation, '')

    def test_should_remplir_automatiquement_millesime_si_un_titre_acces_selectionne(self):
        self.titre_acces_repository.entities.append(
            TitreAccesSelectionnableFactory(
                entity_id__uuid_proposition='uuid-SC3DP-confirmee',
                selectionne=True,
                annee=2022,
            )
        )

        proposition_id = self.message_bus.invoke(
            SpecifierConditionAccesPropositionCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                condition_acces=ConditionAcces.BAC.name,
                millesime_condition_acces=2021,
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.condition_acces, ConditionAcces.BAC)
        self.assertEqual(proposition.millesime_condition_acces, 2022)

    def test_should_pas_remplir_automatiquement_millesime_deux_titres_acces_selectionnes(self):
        self.titre_acces_repository.entities.append(
            TitreAccesSelectionnableFactory(
                entity_id__uuid_proposition='uuid-SC3DP-confirmee',
                selectionne=True,
                annee=2022,
            )
        )

        self.titre_acces_repository.entities.append(
            TitreAccesSelectionnableFactory(
                entity_id__uuid_proposition='uuid-SC3DP-confirmee',
                selectionne=True,
                annee=2023,
            )
        )

        proposition_id = self.message_bus.invoke(
            SpecifierConditionAccesPropositionCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                condition_acces=ConditionAcces.BAC.name,
                millesime_condition_acces=2021,
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.condition_acces, ConditionAcces.BAC)
        self.assertEqual(proposition.millesime_condition_acces, 2021)

    def test_should_remplir_automatiquement_question_complements_formation_si_snu_court_comme_condition_acces(self):
        proposition_id = self.message_bus.invoke(
            SpecifierConditionAccesPropositionCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                condition_acces=ConditionAcces.BAC.name,
                millesime_condition_acces=2021,
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.condition_acces, ConditionAcces.BAC)
        self.assertEqual(proposition.avec_complements_formation, None)

        proposition_id = self.message_bus.invoke(
            SpecifierConditionAccesPropositionCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                condition_acces=ConditionAcces.SNU_TYPE_COURT.name,
                millesime_condition_acces=2021,
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.condition_acces, ConditionAcces.SNU_TYPE_COURT)
        self.assertEqual(proposition.avec_complements_formation, True)

        proposition_id = self.message_bus.invoke(
            SpecifierConditionAccesPropositionCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                condition_acces=ConditionAcces.BAC.name,
                millesime_condition_acces=2021,
                gestionnaire='0123456789',
                avec_complements_formation=False,
            )
        )

        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.condition_acces, ConditionAcces.BAC)
        self.assertEqual(proposition.avec_complements_formation, False)

        proposition_id = self.message_bus.invoke(
            SpecifierConditionAccesPropositionCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                condition_acces=ConditionAcces.SNU_TYPE_COURT.name,
                millesime_condition_acces=2021,
                gestionnaire='0123456789',
                avec_complements_formation=False,
            )
        )

        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.condition_acces, ConditionAcces.SNU_TYPE_COURT)
        self.assertEqual(proposition.avec_complements_formation, True)

    def test_should_empecher_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(
                SpecifierConditionAccesPropositionCommand(
                    uuid_proposition='INCONNUE',
                    gestionnaire='0123456789',
                )
            )
