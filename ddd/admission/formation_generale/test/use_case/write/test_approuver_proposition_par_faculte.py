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
from unittest import TestCase

import factory

from admission.ddd.admission.formation_generale.commands import (
    ApprouverPropositionParFaculteCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    SituationPropositionNonFACException,
    InformationsAcceptationFacultaireNonSpecifieesException,
)
from admission.ddd.admission.formation_generale.test.factory.proposition import (
    PropositionFactory,
    _PropositionIdentityFactory,
)
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestApprouverPropositionParFaculte(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = ApprouverPropositionParFaculteCommand

    def setUp(self) -> None:
        self.proposition = PropositionFactory(
            entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-MASTER-SCI-APPROVED'),
            matricule_candidat='0000000001',
            formation_id=FormationIdentityFactory(sigle="MASTER-SCI", annee=2021),
            curriculum=['file1.pdf'],
            est_confirmee=True,
            est_approuvee_par_fac=True,
            statut=ChoixStatutPropositionGenerale.TRAITEMENT_FAC,
        )
        self.proposition_repository.save(self.proposition)
        self.parametres_commande_par_defaut = {
            'uuid_proposition': 'uuid-MASTER-SCI-APPROVED',
            'gestionnaire': '00321234',
        }

    def test_should_etre_ok_si_statut_correct(self):
        self.proposition.statut = ChoixStatutPropositionGenerale.TRAITEMENT_FAC

        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-MASTER-SCI-APPROVED')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.RETOUR_DE_FAC)
        self.assertEqual(proposition.checklist_actuelle.decision_facultaire.statut, ChoixStatutChecklist.GEST_REUSSITE)

    def test_should_lever_exception_si_statut_non_conforme(self):
        statuts_invalides = ChoixStatutPropositionGenerale.get_names_except(
            ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC,
            ChoixStatutPropositionGenerale.TRAITEMENT_FAC,
        )

        for statut in statuts_invalides:
            self.proposition.statut = ChoixStatutPropositionGenerale[statut]
            with self.assertRaises(
                SituationPropositionNonFACException,
                msg=f'The following status must raise an exception: {statut}',
            ):
                self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

    def test_should_lever_exception_si_presence_conditions_complementaires_non_specifiee(self):
        self.proposition.avec_conditions_complementaires = None
        with self.assertRaises(InformationsAcceptationFacultaireNonSpecifieesException):
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

    def test_should_lever_exception_si_conditions_complementaires_non_specifiees(self):
        self.proposition.avec_conditions_complementaires = True
        self.proposition.conditions_complementaires_existantes = []
        self.proposition.conditions_complementaires_libres = []
        with self.assertRaises(InformationsAcceptationFacultaireNonSpecifieesException):
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

    def test_should_lever_exception_si_presence_complements_formation_non_specifiee(self):
        self.proposition.avec_complements_formation = None
        with self.assertRaises(InformationsAcceptationFacultaireNonSpecifieesException):
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

    def test_should_lever_exception_si_complements_formation_non_specifiees(self):
        self.proposition.avec_complements_formation = True
        self.proposition.complements_formation = []
        with self.assertRaises(InformationsAcceptationFacultaireNonSpecifieesException):
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

    def test_should_lever_exception_si_nombre_annees_prevoir_programme_non_specifie(self):
        self.proposition.nombre_annees_prevoir_programme = None
        with self.assertRaises(InformationsAcceptationFacultaireNonSpecifieesException):
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
