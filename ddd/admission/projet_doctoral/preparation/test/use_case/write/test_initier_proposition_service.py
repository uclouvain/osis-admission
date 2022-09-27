# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import SimpleTestCase

from admission.ddd.admission.projet_doctoral.preparation.commands import InitierPropositionCommand
from admission.ddd.admission.projet_doctoral.preparation.domain.model._enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
    ChoixTypeAdmission,
)
from admission.ddd.admission.projet_doctoral.preparation.domain.model._experience_precedente_recherche import (
    ChoixDoctoratDejaRealise,
    aucune_experience_precedente_recherche,
)
from admission.ddd.admission.projet_doctoral.preparation.domain.model._financement import (
    ChoixTypeFinancement,
    financement_non_rempli,
)
from admission.ddd.admission.projet_doctoral.preparation.domain.model.proposition import Proposition
from admission.ddd.admission.projet_doctoral.preparation.domain.validator.exceptions import (
    CommissionProximiteInconsistantException,
    ContratTravailInconsistantException,
    DoctoratNonTrouveException,
    DomaineTheseInconsistantException,
    InstitutionInconsistanteException,
    JustificationRequiseException,
    MaximumPropositionsAtteintException,
)
from admission.ddd.admission.projet_doctoral.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPMinimaleAnnuleeFactory,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.admission.projet_doctoral.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestInitierPropositionService(SimpleTestCase):
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
            type_financement=ChoixTypeFinancement.WORK_CONTRACT.name,
            type_contrat_travail='assistant_uclouvain',
            titre_projet='Mon projet',
            resume_projet='LE résumé de mon projet',
            documents_projet=[],
            doctorat_deja_realise=ChoixDoctoratDejaRealise.YES.name,
            institution="psychiatrique",
            domaine_these="Psy",
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
        self.assertEqual(self.cmd.sigle_formation, proposition.doctorat_id.sigle)
        self.assertEqual(self.cmd.annee_formation, proposition.doctorat_id.annee)
        self.assertEqual(self.cmd.matricule_candidat, proposition.matricule_candidat)

    def test_should_initier_financement(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(ChoixTypeFinancement[self.cmd.type_financement], proposition.financement.type)
        self.assertEqual(self.cmd.type_contrat_travail, proposition.financement.type_contrat_travail)

    def test_should_initier_projet(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(self.cmd.titre_projet, proposition.projet.titre)
        self.assertEqual(self.cmd.resume_projet, proposition.projet.resume)
        self.assertEqual(self.cmd.documents_projet, proposition.projet.documents)

    def test_should_initier_experience_precedente(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(
            ChoixDoctoratDejaRealise[self.cmd.doctorat_deja_realise],
            proposition.experience_precedente_recherche.doctorat_deja_realise,
        )
        self.assertEqual(self.cmd.institution, proposition.experience_precedente_recherche.institution)

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

    def test_should_empecher_si_doctorat_pas_deja_realise_et_institution(self):
        cmd = attr.evolve(self.cmd, doctorat_deja_realise=ChoixDoctoratDejaRealise.NO.name, domaine_these="")
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), InstitutionInconsistanteException)

    def test_should_empecher_si_doctorat_deja_realise_et_institution_manquante(self):
        cmd = attr.evolve(self.cmd, institution="")
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), InstitutionInconsistanteException)

    def test_should_empecher_si_doctorat_pas_deja_realise_et_domaine(self):
        cmd = attr.evolve(self.cmd, doctorat_deja_realise=ChoixDoctoratDejaRealise.NO.name, institution="")
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), DomaineTheseInconsistantException)

    def test_should_empecher_si_doctorat_deja_realise_et_domaine_manquant(self):
        cmd = attr.evolve(self.cmd, domaine_these="")
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), DomaineTheseInconsistantException)

    def test_should_empecher_si_pas_contrat_travail(self):
        cmd = attr.evolve(self.cmd, type_contrat_travail="")
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), ContratTravailInconsistantException)

    def test_should_empecher_si_financement_pas_contrat_travail(self):
        cmd = attr.evolve(self.cmd, type_financement=ChoixTypeFinancement.SELF_FUNDING.name)
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), ContratTravailInconsistantException)

    def test_should_initier_sans_financement(self):
        cmd = attr.evolve(self.cmd, type_financement='', type_contrat_travail='')
        proposition_id = self.message_bus.invoke(cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition.financement, financement_non_rempli)

    def test_should_initier_sans_projet(self):
        cmd = attr.evolve(self.cmd, titre_projet='', resume_projet='', documents_projet=[])
        proposition_id = self.message_bus.invoke(cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition.projet.titre, '')
        self.assertEqual(proposition.projet.resume, '')
        self.assertEqual(proposition.projet.documents, [])

    def test_should_initier_sans_experience(self):
        cmd = attr.evolve(
            self.cmd,
            doctorat_deja_realise=ChoixDoctoratDejaRealise.NO.name,
            institution='',
            domaine_these="",
        )
        proposition_id = self.message_bus.invoke(cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition.experience_precedente_recherche, aucune_experience_precedente_recherche)
