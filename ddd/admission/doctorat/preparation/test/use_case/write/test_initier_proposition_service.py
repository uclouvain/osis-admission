# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

import attr
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import InitierPropositionCommand
from admission.ddd.admission.doctorat.preparation.domain.model._detail_projet import projet_non_rempli
from admission.ddd.admission.doctorat.preparation.domain.model._experience_precedente_recherche import (
    aucune_experience_precedente_recherche,
)
from admission.ddd.admission.doctorat.preparation.domain.model._financement import (
    financement_non_rempli,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
    ChoixTypeAdmission,
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    CommissionProximiteInconsistantException,
    DoctoratNonTrouveException,
    JustificationRequiseException,
    MaximumPropositionsAtteintException,
)
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPMinimaleAnnuleeFactory,
)
from admission.ddd.admission.domain.service.i_maximum_propositions import MAXIMUM_PROPOSITIONS_EN_COURS
from admission.ddd.admission.enums.type_bourse import TypeBourse
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.domain.service.in_memory.bourse import BourseInMemoryTranslator
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestInitierPropositionService(TestCase):
    @classmethod
    def _get_une_bourse_par_type(cls, type_bourse: TypeBourse):
        return next(
            (bourse.entity_id.uuid for bourse in BourseInMemoryTranslator.ENTITIES if bourse.type == type_bourse),
            None,
        )

    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = InitierPropositionCommand(
            type_admission=ChoixTypeAdmission.ADMISSION.name,
            sigle_formation='ECGE3DP',
            annee_formation=2020,
            matricule_candidat='01234567',
            commission_proximite=ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
        )

        self.doctorat_non_CDE = self.doctorat_non_CDSS = 'AGRO3DP'
        self.doctorat_CLSM = "ECGM3DP"
        self.doctorat_CDSS = "ESP3DP"
        self.doctorat_science = "SC3DP"

    def test_should_initier(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition_id, proposition.entity_id)
        self.assertEqual(ChoixTypeAdmission[self.cmd.type_admission], proposition.type_admission)
        self.assertEqual(self.cmd.sigle_formation, proposition.formation_id.sigle)
        self.assertEqual(self.cmd.annee_formation, proposition.formation_id.annee)
        self.assertEqual(self.cmd.matricule_candidat, proposition.matricule_candidat)
        self.assertEqual(ChoixStatutPropositionDoctorale.EN_BROUILLON, proposition.statut)

    def test_should_initier_financement(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition.financement, financement_non_rempli)

    def test_should_initier_projet(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition.projet, projet_non_rempli)

    def test_should_initier_experience_precedente(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition.experience_precedente_recherche, aucune_experience_precedente_recherche)

    def test_should_initier_commission_proximite_CDE_vide_et_non_CDE(self):
        cmd = attr.evolve(self.cmd, commission_proximite='', sigle_formation=self.doctorat_non_CDE)
        proposition_id = self.message_bus.invoke(cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertIsNone(proposition.commission_proximite)

    def test_should_initier_commission_proximite_CLSM(self):
        cmd = attr.evolve(
            self.cmd,
            commission_proximite=ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
            sigle_formation=self.doctorat_CLSM,
        )
        proposition_id = self.message_bus.invoke(cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition.commission_proximite.name, ChoixCommissionProximiteCDEouCLSM.ECONOMY.name)

    def test_should_initier_commission_proximite_CDSS(self):
        cmd = attr.evolve(
            self.cmd,
            commission_proximite=ChoixCommissionProximiteCDSS.ECLI.name,
            sigle_formation=self.doctorat_CDSS,
        )
        proposition_id = self.message_bus.invoke(cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition.commission_proximite.name, ChoixCommissionProximiteCDSS.ECLI.name)

    def test_should_initier_sous_domaine_science(self):
        cmd = attr.evolve(
            self.cmd,
            commission_proximite=ChoixSousDomaineSciences.BIOLOGY.name,
            sigle_formation=self.doctorat_science,
        )
        proposition_id = self.message_bus.invoke(cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition.commission_proximite.name, ChoixSousDomaineSciences.BIOLOGY.name)

    def test_should_pas_initier_commission_proximite_CLSM_vide(self):
        cmd = attr.evolve(self.cmd, commission_proximite='', sigle_formation=self.doctorat_CLSM)
        with self.assertRaises(CommissionProximiteInconsistantException):
            self.message_bus.invoke(cmd)

    def test_should_pas_initier_commission_proximite_cdss_invalide(self):
        cmd = attr.evolve(
            self.cmd,
            sigle_formation=self.doctorat_non_CDSS,
            commission_proximite=ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
        )
        with self.assertRaises(CommissionProximiteInconsistantException):
            self.message_bus.invoke(cmd)

    def test_should_pas_initier_commission_proximite_cde_invalide(self):
        cmd = attr.evolve(self.cmd, commission_proximite=ChoixCommissionProximiteCDSS.ECLI.name)
        with self.assertRaises(CommissionProximiteInconsistantException):
            self.message_bus.invoke(cmd)

    def test_should_initier_commission_proximite_CDSS_vide_et_non_CDSS(self):
        cmd = attr.evolve(self.cmd, commission_proximite='', sigle_formation=self.doctorat_non_CDSS)
        proposition_id = self.message_bus.invoke(cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertIsNone(proposition.commission_proximite)

    def test_should_pas_initier_commission_proximite_CDE_vide_et_CDE(self):
        cmd = attr.evolve(self.cmd, commission_proximite='')
        with self.assertRaises(CommissionProximiteInconsistantException):
            self.message_bus.invoke(cmd)

    def test_should_pas_initier_commission_proximite_CDSS_vide_et_CDSS(self):
        cmd = attr.evolve(self.cmd, sigle_formation='ESP3DP', commission_proximite='')
        with self.assertRaises(CommissionProximiteInconsistantException):
            self.message_bus.invoke(cmd)

    def test_should_pas_initier_si_commission_proximite_CDE_et_non_CDE(self):
        cmd = attr.evolve(self.cmd, sigle_formation=self.doctorat_non_CDE)
        with self.assertRaises(CommissionProximiteInconsistantException):
            self.message_bus.invoke(cmd)

    def test_should_pas_initier_si_commission_proximite_CDSS_et_non_CDSS(self):
        cmd = attr.evolve(self.cmd, commission_proximite='ECLI', sigle_formation=self.doctorat_non_CDSS)
        with self.assertRaises(CommissionProximiteInconsistantException):
            self.message_bus.invoke(cmd)

    def test_should_pas_initier_si_sous_domaine_absent_et_doctorat_sciences(self):
        cmd = attr.evolve(self.cmd, commission_proximite='', sigle_formation=self.doctorat_science)
        with self.assertRaises(CommissionProximiteInconsistantException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_maximum_propositions_autorisees(self):
        cmd = attr.evolve(self.cmd, matricule_candidat="0123456789")
        with self.assertRaises(MaximumPropositionsAtteintException):
            self.message_bus.invoke(cmd)

    def test_should_initier_autre_proposition_si_premiere_annulee(self):
        # TODO This should be changed to the action that changes the status to cancelled
        self.proposition_repository.save(PropositionAdmissionSC3DPMinimaleAnnuleeFactory())
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition_id, proposition.entity_id)

    def test_should_empecher_si_pas_doctorat(self):
        not_doctorat = 'DROI1BA'
        cmd = attr.evolve(self.cmd, sigle_formation=not_doctorat)
        with self.assertRaises(DoctoratNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_empecher_si_pas_justification(self):
        cmd = attr.evolve(self.cmd, type_admission=ChoixTypeAdmission.PRE_ADMISSION.name)
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), JustificationRequiseException)

    def test_should_empecher_si_trop_demandes_en_parallele(self):
        for proposition_index in range(MAXIMUM_PROPOSITIONS_EN_COURS):
            self.message_bus.invoke(self.cmd)
        with self.assertRaises(MaximumPropositionsAtteintException):
            self.message_bus.invoke(self.cmd)
