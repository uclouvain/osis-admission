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
import uuid
from unittest import TestCase

import factory

from admission.ddd.admission.domain.model.complement_formation import ComplementFormationIdentity
from admission.ddd.admission.domain.model.condition_complementaire_approbation import (
    ConditionComplementaireApprobationIdentity,
)
from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.formation_generale.commands import (
    SpecifierInformationsAcceptationPropositionParFaculteCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    SituationPropositionNonFACException,
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
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestSpecifierInformationsAcceptationPropositionParFaculte(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = SpecifierInformationsAcceptationPropositionParFaculteCommand
        cls.uuid_experience = str(uuid.uuid4())

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
            'sigle_autre_formation': '',
            'avec_conditions_complementaires': False,
            'uuids_conditions_complementaires_existantes': [],
            'conditions_complementaires_libres': [],
            'avec_complements_formation': False,
            'uuids_complements_formation': [],
            'commentaire_complements_formation': '',
            'nombre_annees_prevoir_programme': 2,
            'nom_personne_contact_programme_annuel': '',
            'email_personne_contact_programme_annuel': '',
            'commentaire_programme_conjoint': '',
            'gestionnaire': '0123456789',
        }

    def test_should_etre_ok_si_en_traitement_fac_avec_min_informations(self):
        self.proposition.statut = ChoixStatutPropositionGenerale.TRAITEMENT_FAC

        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-MASTER-SCI-APPROVED')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.TRAITEMENT_FAC)
        self.assertEqual(proposition.checklist_actuelle.decision_facultaire.statut, ChoixStatutChecklist.GEST_REUSSITE)
        self.assertEqual(proposition.autre_formation_choisie_fac_id, None)
        self.assertEqual(proposition.avec_conditions_complementaires, False)
        self.assertEqual(proposition.conditions_complementaires_existantes, [])
        self.assertEqual(proposition.conditions_complementaires_libres, [])
        self.assertEqual(proposition.avec_complements_formation, False)
        self.assertEqual(proposition.complements_formation, [])
        self.assertEqual(proposition.commentaire_complements_formation, '')
        self.assertEqual(proposition.nombre_annees_prevoir_programme, 2)
        self.assertEqual(proposition.nom_personne_contact_programme_annuel_annuel, '')
        self.assertEqual(proposition.email_personne_contact_programme_annuel_annuel, '')
        self.assertEqual(proposition.commentaire_programme_conjoint, '')

    def test_should_etre_ok_si_completee_pour_fac_avec_max_informations(self):
        self.proposition.statut = ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC
        self.proposition.annee_calculee = 2020

        # Maximum d'informations données
        resultat = self.message_bus.invoke(
            self.command(
                uuid_proposition='uuid-MASTER-SCI-APPROVED',
                sigle_autre_formation='BACHELIER-ECO',
                avec_conditions_complementaires=True,
                uuids_conditions_complementaires_existantes=['uuid-condition-complementaire-1'],
                conditions_complementaires_libres=[
                    {
                        'name_fr': 'Condition libre 1',
                        'name_en': 'Free condition 1',
                        'related_experience_id': self.uuid_experience,
                    },
                    {
                        'name_fr': 'Condition libre 2',
                    },
                ],
                avec_complements_formation=True,
                uuids_complements_formation=['uuid-complement-formation-1'],
                commentaire_complements_formation='Mon commentaire concernant les compléments de formation',
                nombre_annees_prevoir_programme=3,
                nom_personne_contact_programme_annuel='John Doe',
                email_personne_contact_programme_annuel='john.doe@uclouvain.be',
                commentaire_programme_conjoint='Mon commentaire concernant le programme conjoint',
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC)
        self.assertEqual(proposition.checklist_actuelle.decision_facultaire.statut, ChoixStatutChecklist.GEST_REUSSITE)
        self.assertEqual(
            proposition.autre_formation_choisie_fac_id,
            FormationIdentity(
                sigle='BACHELIER-ECO',
                annee=2020,
            ),
        )
        self.assertEqual(proposition.avec_conditions_complementaires, True)
        self.assertEqual(
            proposition.conditions_complementaires_existantes,
            [
                ConditionComplementaireApprobationIdentity(
                    uuid='uuid-condition-complementaire-1',
                )
            ],
        )
        self.assertEqual(len(proposition.conditions_complementaires_libres), 2)
        self.assertEqual(proposition.conditions_complementaires_libres[0].nom_fr, 'Condition libre 1')
        self.assertEqual(proposition.conditions_complementaires_libres[0].nom_en, 'Free condition 1')
        self.assertEqual(proposition.conditions_complementaires_libres[0].uuid_experience, self.uuid_experience)
        self.assertEqual(proposition.conditions_complementaires_libres[1].nom_fr, 'Condition libre 2')
        self.assertEqual(proposition.conditions_complementaires_libres[1].nom_en, '')
        self.assertEqual(proposition.conditions_complementaires_libres[1].uuid_experience, '')

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
        self.assertEqual(proposition.nombre_annees_prevoir_programme, 3)
        self.assertEqual(proposition.nom_personne_contact_programme_annuel_annuel, 'John Doe')
        self.assertEqual(proposition.email_personne_contact_programme_annuel_annuel, 'john.doe@uclouvain.be')
        self.assertEqual(proposition.commentaire_programme_conjoint, 'Mon commentaire concernant le programme conjoint')

    def test_should_lever_exception_si_statut_non_conforme(self):
        statuts_invalides = ChoixStatutPropositionGenerale.get_names_except(
            ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC,
            ChoixStatutPropositionGenerale.TRAITEMENT_FAC,
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC,
        )

        for statut in statuts_invalides:
            self.proposition.statut = ChoixStatutPropositionGenerale[statut]
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
                self.assertIsInstance(context.exception.exceptions.pop(), SituationPropositionNonFACException)

    def test_should_etre_ok_si_en_attente_retour_candidat(self):
        self.proposition.statut = ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
        self.assertEqual(resultat.uuid, 'uuid-MASTER-SCI-APPROVED')
