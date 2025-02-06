# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid

from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    SpecifierInformationsAcceptationPropositionParCddCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    SituationPropositionNonCddException,
)
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPConfirmeeFactory,
)
from admission.ddd.admission.domain.model.complement_formation import (
    ComplementFormationIdentity,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestSpecifierInformationsAcceptationPropositionParCdd(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = SpecifierInformationsAcceptationPropositionParCddCommand
        cls.uuid_experience = str(uuid.uuid4())

    def setUp(self) -> None:
        self.proposition = PropositionAdmissionSC3DPConfirmeeFactory(
            est_confirmee=True,
            est_approuvee_par_fac=True,
            statut=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC,
        )
        self.proposition_repository.save(self.proposition)
        self.parametres_commande_par_defaut = {
            'uuid_proposition': 'uuid-SC3DP-confirmee',
            'avec_complements_formation': False,
            'uuids_complements_formation': [],
            'commentaire_complements_formation': '',
            'nom_personne_contact_programme_annuel': '',
            'email_personne_contact_programme_annuel': '',
            'commentaire_programme_conjoint': '',
            'gestionnaire': '0123456789',
        }

    def test_should_etre_ok_si_en_traitement_fac_avec_min_informations(self):
        self.proposition.statut = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC

        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-SC3DP-confirmee')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC)
        self.assertEqual(
            proposition.checklist_actuelle.decision_cdd.statut,
            ChoixStatutChecklist.INITIAL_CANDIDAT,
        )
        self.assertEqual(proposition.avec_complements_formation, False)
        self.assertEqual(proposition.complements_formation, [])
        self.assertEqual(proposition.commentaire_complements_formation, '')
        self.assertEqual(proposition.nom_personne_contact_programme_annuel_annuel, '')
        self.assertEqual(proposition.email_personne_contact_programme_annuel_annuel, '')
        self.assertEqual(proposition.commentaire_programme_conjoint, '')

    def test_should_etre_ok_si_completee_pour_fac_avec_max_informations(self):
        self.proposition.statut = ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC
        self.proposition.annee_calculee = 2020

        # Maximum d'informations données
        resultat = self.message_bus.invoke(
            self.command(
                uuid_proposition='uuid-SC3DP-confirmee',
                avec_complements_formation=True,
                uuids_complements_formation=['uuid-complement-formation-1'],
                commentaire_complements_formation='Mon commentaire concernant les compléments de formation',
                nom_personne_contact_programme_annuel='John Doe',
                email_personne_contact_programme_annuel='john.doe@uclouvain.be',
                commentaire_programme_conjoint='Mon commentaire concernant le programme conjoint',
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC)
        self.assertEqual(
            proposition.checklist_actuelle.decision_cdd.statut,
            ChoixStatutChecklist.INITIAL_CANDIDAT,
        )
        self.assertEqual(proposition.avec_complements_formation, True)
        self.assertEqual(
            proposition.complements_formation,
            [
                ComplementFormationIdentity(
                    uuid='uuid-complement-formation-1',
                )
            ],
        )
        self.assertEqual(
            proposition.commentaire_complements_formation,
            'Mon commentaire concernant les compléments de formation',
        )
        self.assertEqual(proposition.nom_personne_contact_programme_annuel_annuel, 'John Doe')
        self.assertEqual(proposition.email_personne_contact_programme_annuel_annuel, 'john.doe@uclouvain.be')
        self.assertEqual(proposition.commentaire_programme_conjoint, 'Mon commentaire concernant le programme conjoint')

    def test_should_lever_exception_si_statut_non_conforme(self):
        statuts_invalides = ChoixStatutPropositionDoctorale.get_names_except(
            ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC,
            ChoixStatutPropositionDoctorale.TRAITEMENT_FAC,
            ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC,
        )

        for statut in statuts_invalides:
            self.proposition.statut = ChoixStatutPropositionDoctorale[statut]
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
                self.assertIsInstance(context.exception.exceptions.pop(), SituationPropositionNonCddException)

    def test_should_etre_ok_si_en_attente_retour_candidat(self):
        self.proposition.statut = ChoixStatutPropositionDoctorale.A_COMPLETER_POUR_FAC
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
        self.assertEqual(resultat.uuid, 'uuid-SC3DP-confirmee')
