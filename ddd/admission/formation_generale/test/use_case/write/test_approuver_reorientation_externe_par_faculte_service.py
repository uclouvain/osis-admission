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

import factory
import freezegun
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.test.factory.person import PersonneConnueUclDTOFactory
from admission.ddd.admission.formation_generale.commands import (
    ApprouverReorientationExterneParFaculteCommand,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    SituationPropositionNonFACException,
    TitreAccesEtreSelectionnePourEnvoyerASICException,
    ReorientationExterneAvecConditionAccesException,
)
from admission.ddd.admission.formation_generale.test.factory.proposition import (
    PropositionFactory,
    _PropositionIdentityFactory,
)
from admission.ddd.admission.formation_generale.test.factory.titre_acces import TitreAccesSelectionnableFactory
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.titre_acces_selectionnable import (
    TitreAccesSelectionnableInMemoryRepositoryFactory,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from epc.models.enums.condition_acces import ConditionAcces
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import (
    PersonneConnueUclInMemoryTranslator,
)


@freezegun.freeze_time('2021-11-01')
class TestApprouverReorientationExterneParFaculte(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = ApprouverReorientationExterneParFaculteCommand
        academic_year_repository = AcademicYearInMemoryRepository()
        for annee in range(2020, 2022):
            academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )
        for matricule in ['00321234', '00987890']:
            PersonneConnueUclInMemoryTranslator.personnes_connues_ucl.add(
                PersonneConnueUclDTOFactory(matricule=matricule),
            )

    def setUp(self) -> None:
        self.proposition = PropositionFactory(
            entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-MASTER-SCI-APPROVED'),
            matricule_candidat='0000000001',
            formation_id=FormationIdentityFactory(sigle="MASTER-SCI", annee=2021),
            curriculum=['file1.pdf'],
            est_confirmee=True,
            est_approuvee_par_fac=True,
            statut=ChoixStatutPropositionGenerale.TRAITEMENT_FAC,
            est_reorientation_inscription_externe=True,
            condition_acces=ConditionAcces.BAC,
        )
        self.proposition_repository.save(self.proposition)
        self.parametres_commande_par_defaut = {
            'uuid_proposition': 'uuid-MASTER-SCI-APPROVED',
            'gestionnaire': '00321234',
        }
        self.titre_acces_repository = TitreAccesSelectionnableInMemoryRepositoryFactory()
        self.titre_acces = TitreAccesSelectionnableFactory(
            entity_id__uuid_proposition='uuid-MASTER-SCI-APPROVED',
            selectionne=True,
        )
        self.titre_acces_repository.save(self.titre_acces)

    def test_should_etre_ok_si_preconditions_verifiees(self):
        self.proposition.statut = ChoixStatutPropositionGenerale.TRAITEMENT_FAC

        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-MASTER-SCI-APPROVED')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionGenerale.RETOUR_DE_FAC)
        self.assertEqual(proposition.checklist_actuelle.decision_facultaire.statut, ChoixStatutChecklist.GEST_REUSSITE)
        self.assertEqual(proposition.auteur_derniere_modification, '00321234')

    def test_should_lever_exception_si_statut_non_conforme(self):
        statuts_invalides = ChoixStatutPropositionGenerale.get_names_except(
            ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC,
            ChoixStatutPropositionGenerale.TRAITEMENT_FAC,
        )

        for statut in statuts_invalides:
            self.proposition.statut = ChoixStatutPropositionGenerale[statut]
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
                self.assertIsInstance(context.exception.exceptions.pop(), SituationPropositionNonFACException)

    def test_should_lever_exception_si_inscription_ne_concerne_pas_reorientation_externer(self):
        self.proposition.est_reorientation_inscription_externe = None
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
            self.assertIsInstance(context.exception.exceptions.pop(), ReorientationExterneAvecConditionAccesException)

        self.proposition.est_reorientation_inscription_externe = False
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
            self.assertIsInstance(context.exception.exceptions.pop(), ReorientationExterneAvecConditionAccesException)

    def test_should_lever_exception_si_conditions_acces_non_completee(self):
        self.proposition.condition_acces = None
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
            self.assertIsInstance(context.exception.exceptions.pop(), ReorientationExterneAvecConditionAccesException)

    def test_should_lever_exception_si_aucun_titre_acces_est_selectionne(self):
        self.proposition.statut = ChoixStatutPropositionGenerale.TRAITEMENT_FAC
        self.titre_acces_repository.delete(self.titre_acces.entity_id)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
            self.assertIsInstance(context.exception.exceptions.pop(), TitreAccesEtreSelectionnePourEnvoyerASICException)

        titre_acces_non_selectionne = TitreAccesSelectionnableFactory(
            entity_id__uuid_proposition='uuid-MASTER-SCI-APPROVED',
            selectionne=False,
        )
        self.titre_acces_repository.save(titre_acces_non_selectionne)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
            self.assertIsInstance(context.exception.exceptions.pop(), TitreAccesEtreSelectionnePourEnvoyerASICException)
