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
import datetime
import uuid
from unittest import TestCase

import factory
import freezegun

from admission.ddd.admission.domain.model.complement_formation import ComplementFormationIdentity
from admission.ddd.admission.domain.model.condition_complementaire_approbation import (
    ConditionComplementaireApprobationIdentity,
)
from admission.ddd.admission.formation_generale.commands import (
    SpecifierInformationsAcceptationInscriptionParSicCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    SituationPropositionNonSICException,
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
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository


@freezegun.freeze_time('2020-11-01')
class TestSpecifierInformationsAcceptationInscriptionParSic(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = SpecifierInformationsAcceptationInscriptionParSicCommand
        cls.uuid_experience = str(uuid.uuid4())
        academic_year_repository = AcademicYearInMemoryRepository()
        for annee in range(2020, 2022):
            academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )

    def setUp(self) -> None:
        self.proposition = PropositionFactory(
            statut=ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC,
            entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-MASTER-SCI-APPROVED'),
            matricule_candidat='0000000001',
            formation_id=FormationIdentityFactory(sigle="MASTER-SCI", annee=2021),
            curriculum=['file1.pdf'],
            est_confirmee=True,
            est_approuvee_par_fac=True,
        )
        self.proposition_repository.save(self.proposition)
        self.parametres_commande_par_defaut = {
            'uuid_proposition': 'uuid-MASTER-SCI-APPROVED',
            'avec_conditions_complementaires': False,
            'uuids_conditions_complementaires_existantes': [],
            'conditions_complementaires_libres': [],
            'avec_complements_formation': False,
            'uuids_complements_formation': [],
            'commentaire_complements_formation': '',
            'nombre_annees_prevoir_programme': 2,
            'nom_personne_contact_programme_annuel': '',
            'email_personne_contact_programme_annuel': '',
            'gestionnaire': '0123456789',
        }

    def test_should_etre_ok_avec_min_informations(self):
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-MASTER-SCI-APPROVED')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)

        self.assertEqual(proposition.auteur_derniere_modification, '0123456789')
        self.assertEqual(proposition.avec_conditions_complementaires, False)
        self.assertEqual(proposition.conditions_complementaires_existantes, [])
        self.assertEqual(proposition.conditions_complementaires_libres, [])
        self.assertEqual(proposition.avec_complements_formation, False)
        self.assertEqual(proposition.complements_formation, [])
        self.assertEqual(proposition.commentaire_complements_formation, '')
        self.assertEqual(proposition.nombre_annees_prevoir_programme, 2)
        self.assertEqual(proposition.nom_personne_contact_programme_annuel_annuel, '')
        self.assertEqual(proposition.email_personne_contact_programme_annuel_annuel, '')

    def test_should_lever_exception_si_statut_proposition_non_valide(self):
        self.proposition.statut = ChoixStatutPropositionGenerale.TRAITEMENT_FAC

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        self.assertIsInstance(context.exception.exceptions.pop(), SituationPropositionNonSICException)

    def test_should_etre_ok_si_completee_avec_max_informations(self):
        # Maximum d'informations données
        resultat = self.message_bus.invoke(
            self.command(
                uuid_proposition='uuid-MASTER-SCI-APPROVED',
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
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(resultat)
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
        self.assertEqual(proposition.auteur_derniere_modification, '0123456789')
