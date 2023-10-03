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
import datetime
from unittest import TestCase, mock

import freezegun

from admission.contrib.models.online_payment import PaymentStatus
from admission.ddd.admission.formation_generale.commands import (
    SpecifierPaiementVaEtreOuvertParCandidatCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    PropositionPourPaiementInvalideException,
    PaiementDejaRealiseException,
)
from admission.ddd.admission.formation_generale.dtos.paiement import PaiementDTO
from admission.ddd.admission.formation_generale.test.factory.paiement import PaiementFactory
from admission.ddd.admission.formation_generale.test.factory.repository.paiement_frais_dossier import (
    PaiementFraisDossierInMemoryRepositoryFactory,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository


@freezegun.freeze_time('2020-11-01')
class TestSpecifierPaiementVaEtreOuvertParCandidat(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.academic_year_repository = AcademicYearInMemoryRepository()
        for annee in range(2016, 2023):
            cls.academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )
        cls.message_bus = message_bus_in_memory_instance

    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.candidat = self.candidat_translator.profil_candidats[1]
        self.proposition = self.proposition_repository.get(
            PropositionIdentity(
                uuid='uuid-MASTER-SCI-CONFIRMED',
            ),
        )

        self.command = SpecifierPaiementVaEtreOuvertParCandidatCommand(
            uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
        )

        self.paiement_repository = PaiementFraisDossierInMemoryRepositoryFactory()
        self.paiement_courant = next(
            paiement
            for paiement in self.paiement_repository.paiements
            if paiement.uuid_proposition == 'uuid-MASTER-SCI-CONFIRMED'
        )

    def test_should_specifier_paiement_va_etre_ouvert_par_candidat_etre_ok(self):
        with mock.patch.multiple(
            self.proposition,
            statut=ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE,
        ):
            # Si un paiement en cours n'existe pas pour cette proposition, un nouveau est créé
            self.paiement_repository.paiements = []

            nb_paiements = len(self.paiement_repository.recuperer_paiements_proposition(self.command.uuid_proposition))

            nouveau_paiement_1: PaiementDTO = self.message_bus.invoke(self.command)
            nb_paiements_apres_premier_ajout = len(
                self.paiement_repository.recuperer_paiements_proposition(self.command.uuid_proposition)
            )
            self.assertEqual(nb_paiements + 1, nb_paiements_apres_premier_ajout)

            # Si un paiement en cours existe déjà pour cette proposition, on le récupère
            nouveau_paiement_2 = self.message_bus.invoke(self.command)
            nb_paiements_apres_second_ajout = len(
                self.paiement_repository.recuperer_paiements_proposition(self.command.uuid_proposition)
            )

            self.assertEqual(nb_paiements_apres_second_ajout, nb_paiements_apres_premier_ajout)
            self.assertEqual(nouveau_paiement_1, nouveau_paiement_2)

    def test_should_lever_exception_si_pas_en_attente_de_paiement(self):
        with mock.patch.multiple(
            self.proposition,
            statut=ChoixStatutPropositionGenerale.CONFIRMEE,
        ):
            with self.assertRaises(PropositionPourPaiementInvalideException):
                self.message_bus.invoke(self.command)

    def test_should_lever_exception_si_paiement_deja_realise(self):
        with mock.patch.multiple(
            self.proposition,
            statut=ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE,
        ):
            self.paiement_repository.paiements.append(
                PaiementFactory(
                    uuid_proposition=self.proposition.entity_id.uuid,
                    statut=PaymentStatus.PAID.name,
                )
            )
            with self.assertRaises(PaiementDejaRealiseException):
                self.message_bus.invoke(self.command)
