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
import datetime

import factory
import freezegun
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    ApprouverPropositionParCddCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    InformationsAcceptationNonSpecifieesException,
    SituationPropositionNonCddException,
    TitreAccesEtreSelectionnePourEnvoyerASICException,
)
from admission.ddd.admission.doctorat.preparation.test.factory.groupe_de_supervision import (
    GroupeDeSupervisionSC3DPFactory,
)
from admission.ddd.admission.doctorat.preparation.test.factory.person import (
    PersonneConnueUclDTOFactory,
)
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    _PropositionIdentityFactory,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.test.factory.titre_acces import (
    TitreAccesSelectionnableFactory,
)
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.titre_acces_selectionnable import (
    TitreAccesSelectionnableInMemoryRepositoryFactory,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import (
    AcademicYear,
    AcademicYearIdentity,
)
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import (
    AcademicYearInMemoryRepository,
)
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import (
    PersonneConnueUclInMemoryTranslator,
)


@freezegun.freeze_time('2021-11-01')
class TestApprouverPropositionParCdd(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = ApprouverPropositionParCddCommand
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
        self.proposition = PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(
            entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-APPROVED'),
            matricule_candidat='0123456789',
            type_demande=TypeDemande.INSCRIPTION,
            formation_id=FormationIdentityFactory(sigle="SC3DP", annee=2020),
            curriculum=['file1.pdf'],
            est_confirmee=True,
            est_approuvee_par_fac=True,
            statut=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC,
        )
        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.groupe_de_supervision_repository.save(
            GroupeDeSupervisionSC3DPFactory(
                proposition_id=self.proposition.entity_id,
            )
        )
        self.proposition_repository.save(self.proposition)
        self.parametres_commande_par_defaut = {
            'uuid_proposition': 'uuid-SC3DP-APPROVED',
            'gestionnaire': '00321234',
            'objet_message': 'Objet du message',
            'corps_message': 'Corps du message',
        }
        self.titre_acces_repository = TitreAccesSelectionnableInMemoryRepositoryFactory()
        self.titre_acces = TitreAccesSelectionnableFactory(
            entity_id__uuid_proposition='uuid-SC3DP-APPROVED',
            selectionne=True,
        )
        self.titre_acces_repository.save(self.titre_acces)

    def test_should_etre_ok_si_statut_correct(self):
        self.proposition.statut = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC

        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-SC3DP-APPROVED')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.RETOUR_DE_FAC)
        self.assertEqual(proposition.checklist_actuelle.decision_cdd.statut, ChoixStatutChecklist.GEST_REUSSITE)

    def test_should_lever_exception_si_statut_non_conforme(self):
        statuts_invalides = ChoixStatutPropositionDoctorale.get_names_except(
            ChoixStatutPropositionDoctorale.COMPLETEE_POUR_FAC,
            ChoixStatutPropositionDoctorale.TRAITEMENT_FAC,
        )

        for statut in statuts_invalides:
            self.proposition.statut = ChoixStatutPropositionDoctorale[statut]
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
                self.assertIsInstance(context.exception.exceptions.pop(), SituationPropositionNonCddException)

    def test_should_lever_exception_si_presence_complements_formation_non_specifiee(self):
        self.proposition.avec_complements_formation = None
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.RETOUR_DE_FAC)
        self.assertEqual(proposition.checklist_actuelle.decision_cdd.statut, ChoixStatutChecklist.GEST_REUSSITE)

    def test_should_lever_exception_si_complements_formation_non_specifiees(self):
        self.proposition.avec_complements_formation = True
        self.proposition.complements_formation = []
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.RETOUR_DE_FAC)
        self.assertEqual(proposition.checklist_actuelle.decision_cdd.statut, ChoixStatutChecklist.GEST_REUSSITE)

    def test_should_lever_exception_si_aucun_titre_acces_est_selectionne(self):
        self.proposition.statut = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC
        self.titre_acces_repository.delete(self.titre_acces.entity_id)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
            self.assertIsInstance(context.exception.exceptions.pop(), TitreAccesEtreSelectionnePourEnvoyerASICException)

        titre_acces_non_selectionne = TitreAccesSelectionnableFactory(
            entity_id__uuid_proposition='uuid-SC3DP-APPROVED',
            selectionne=False,
        )
        self.titre_acces_repository.save(titre_acces_non_selectionne)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
            self.assertIsInstance(context.exception.exceptions.pop(), TitreAccesEtreSelectionnePourEnvoyerASICException)
