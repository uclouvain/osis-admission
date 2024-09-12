# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    SpecifierBesoinDeDerogationSicCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import BesoinDeDerogation
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPConfirmeeFactory,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestSpecifierBesoinDeDerogation(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = SpecifierBesoinDeDerogationSicCommand

    def setUp(self) -> None:
        self.proposition = PropositionAdmissionSC3DPConfirmeeFactory(
            est_confirmee=True,
            est_approuvee_par_sic=True,
            statut=ChoixStatutPropositionDoctorale.ATTENTE_VALIDATION_DIRECTION,
        )
        self.proposition_repository.save(self.proposition)
        self.parametres_commande_par_defaut = {
            'uuid_proposition': self.proposition.entity_id.uuid,
            'besoin_de_derogation': BesoinDeDerogation.AVIS_DIRECTION_DEMANDE.name,
            'gestionnaire': '0123456789',
        }

    def test_should_etre_ok_si_statut_correct(self):
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, self.proposition.entity_id.uuid)

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.besoin_de_derogation, BesoinDeDerogation.AVIS_DIRECTION_DEMANDE)
