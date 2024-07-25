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

import uuid

import attr
from django.test import SimpleTestCase

from admission.ddd.admission.domain.validator.exceptions import BourseNonTrouveeException
from admission.ddd.admission.doctorat.preparation.commands import (
    ModifierTypeAdmissionCommand,
    ModifierChoixFormationParGestionnaireCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixTypeAdmission,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    PropositionNonTrouveeException,
    JustificationRequiseException,
    CommissionProximiteInconsistantException,
)
from admission.infrastructure.admission.domain.service.in_memory.bourse import BourseInMemoryTranslator
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestModifierChoixFormationParGestionnaireService(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = ModifierChoixFormationParGestionnaireCommand(
            commission_proximite=ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
            type_admission=ChoixTypeAdmission.PRE_ADMISSION.name,
            justification='Ma justification',
            uuid_proposition='uuid-ECGE3DP',
            auteur='0123456789',
            reponses_questions_specifiques={
                str(uuid.uuid4()): '1',
            },
        )

    def test_should_modifier_choix_formation(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.entity_id, proposition_id)
        self.assertEqual(proposition.type_admission, ChoixTypeAdmission[self.cmd.type_admission])
        self.assertEqual(proposition.justification, self.cmd.justification)
        self.assertEqual(proposition.auteur_derniere_modification, proposition.matricule_candidat)
        self.assertEqual(proposition.commission_proximite, ChoixCommissionProximiteCDEouCLSM.ECONOMY)
        self.assertEqual(proposition.reponses_questions_specifiques, self.cmd.reponses_questions_specifiques)
        self.assertEqual(proposition.auteur_derniere_modification, self.cmd.auteur)

    def test_should_modifier_choix_formation_avec_commission_proximite_cde(self):
        cmd = attr.evolve(
            self.cmd,
            commission_proximite=ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
            uuid_proposition="uuid-ECGE3DP",
        )
        proposition_id = self.message_bus.invoke(cmd)
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(cmd.commission_proximite, proposition.commission_proximite.name)

    def test_should_modifier_choix_formation_avec_commission_proximite_cdss(self):
        cmd = attr.evolve(
            self.cmd,
            commission_proximite=ChoixCommissionProximiteCDSS.ECLI.name,
            uuid_proposition="uuid-ESP3DP",
        )
        proposition_id = self.message_bus.invoke(cmd)
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(cmd.commission_proximite, proposition.commission_proximite.name)

    def test_should_modifier_choix_formation_avec_commission_proximite_sciences(self):
        cmd = attr.evolve(
            self.cmd,
            commission_proximite=ChoixSousDomaineSciences.BIOLOGY.name,
            uuid_proposition="uuid-SC3DP-pre-admission",
        )
        proposition_id = self.message_bus.invoke(cmd)
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(cmd.commission_proximite, proposition.commission_proximite.name)

    def test_should_empecher_si_proposition_non_trouvee(self):
        cmd = attr.evolve(self.cmd, uuid_proposition='INCONNUE')
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_justification_non_precisee(self):
        cmd = attr.evolve(self.cmd, justification='')
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), JustificationRequiseException)

    def test_should_empecher_si_commission_proximite_inconnue(self):
        cmd = attr.evolve(self.cmd, commission_proximite='INCONNU')
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), CommissionProximiteInconsistantException)

    def test_should_empecher_si_commission_proximite_cde_ou_clsm_vide_et_requis(self):
        cmd = attr.evolve(
            self.cmd,
            commission_proximite='',
            uuid_proposition="uuid-ECGE3DP",
        )
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), CommissionProximiteInconsistantException)

    def test_should_empecher_si_commission_proximite_cdds_vide_et_requis(self):
        cmd = attr.evolve(
            self.cmd,
            commission_proximite='',
            uuid_proposition="uuid-ESP3DP",
        )
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), CommissionProximiteInconsistantException)

    def test_should_empecher_si_commission_proximite_sciences_vide_et_requis(self):
        cmd = attr.evolve(
            self.cmd,
            commission_proximite='',
            uuid_proposition="uuid-SC3DP-pre-admission",
        )
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), CommissionProximiteInconsistantException)

    def test_should_empecher_si_commission_proximite_cde_ou_clsm_non_vide_et_invalide(self):
        cmd = attr.evolve(
            self.cmd,
            commission_proximite=ChoixCommissionProximiteCDSS.ECLI.name,
            uuid_proposition="uuid-ECGE3DP",
        )
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), CommissionProximiteInconsistantException)

    def test_should_empecher_si_commission_proximite_cdds_non_vide_et_invalide(self):
        cmd = attr.evolve(
            self.cmd,
            commission_proximite=ChoixSousDomaineSciences.BIOLOGY.name,
            uuid_proposition="uuid-ESP3DP",
        )
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), CommissionProximiteInconsistantException)

    def test_should_empecher_si_commission_proximite_sciences_non_vide_et_invalide(self):
        cmd = attr.evolve(
            self.cmd,
            commission_proximite=ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
            uuid_proposition="uuid-SC3DP-pre-admission",
        )
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), CommissionProximiteInconsistantException)
