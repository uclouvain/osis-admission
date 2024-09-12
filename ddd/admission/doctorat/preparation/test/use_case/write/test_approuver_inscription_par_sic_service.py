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

from admission.ddd.admission.doctorat.preparation.commands import (
    ApprouverInscriptionParSicCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import ChoixStatutChecklist
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    OngletsChecklist,
    BesoinDeDerogation,
)
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    InformationsAcceptationFacultaireNonSpecifieesException,
    ParcoursAnterieurNonSuffisantException,
    DocumentAReclamerImmediatException,
    SituationPropositionNonSICException,
)
from admission.ddd.admission.doctorat.preparation.test.factory.groupe_de_supervision import (
    GroupeDeSupervisionSC3DPFactory,
)
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    _PropositionIdentityFactory,
    PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
)
from admission.ddd.admission.enums.emplacement_document import (
    StatutEmplacementDocument,
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository


@freezegun.freeze_time('2020-11-01')
class TestApprouverInscriptionParSic(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = ApprouverInscriptionParSicCommand
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
        self.proposition = PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(
            entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-APPROVED'),
            matricule_candidat='0123456789',
            type_demande=TypeDemande.INSCRIPTION,
            formation_id=FormationIdentityFactory(sigle="SC3DP", annee=2020),
            curriculum=['file1.pdf'],
            est_confirmee=True,
            est_approuvee_par_sic=True,
            statut=ChoixStatutPropositionDoctorale.ATTENTE_VALIDATION_DIRECTION,
        )
        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.groupe_de_supervision_repository.save(
            GroupeDeSupervisionSC3DPFactory(
                proposition_id=self.proposition.entity_id,
            )
        )
        self.proposition.checklist_actuelle.parcours_anterieur.statut = ChoixStatutChecklist.GEST_REUSSITE
        self.proposition.checklist_actuelle.decision_sic.statut = ChoixStatutChecklist.INITIAL_CANDIDAT
        self.proposition_repository.save(self.proposition)
        self.parametres_commande_par_defaut = {
            'uuid_proposition': 'uuid-SC3DP-APPROVED',
            'auteur': '00321234',
            'objet_message': 'foo',
            'corps_message': 'bar',
        }

    def test_should_etre_ok_si_statut_correct(self):
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-SC3DP-APPROVED')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE)
        self.assertEqual(proposition.checklist_actuelle.decision_sic.statut, ChoixStatutChecklist.GEST_REUSSITE)

    def test_should_lever_exception_si_statut_checklist_incorrect(self):
        statuts_checklist_decision_sic = ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT[OngletsChecklist.decision_sic.name]

        for statut in [
            'A_COMPLETER',
            'REFUS_A_VALIDER',
            'AUTORISATION_A_VALIDER',
            'CLOTURE',
            'REFUSE',
            'AUTORISE',
        ]:
            statut_courant = statuts_checklist_decision_sic[statut]

            self.proposition.checklist_actuelle.decision_sic.statut = statut_courant.statut
            self.proposition.checklist_actuelle.decision_sic.extra = statut_courant.extra

            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
                self.assertIsInstance(
                    context.exception.exceptions.pop(),
                    SituationPropositionNonSICException,
                )

    def test_should_lever_exception_si_statut_derogation_incorrect(self):
        statut_derogation = ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT[OngletsChecklist.decision_sic.name][
            'BESOIN_DEROGATION'
        ]

        self.proposition.checklist_actuelle.decision_sic.statut = statut_derogation.statut
        self.proposition.checklist_actuelle.decision_sic.extra = statut_derogation.extra

        for besoin_de_derogation in BesoinDeDerogation.get_except(BesoinDeDerogation.ACCORD_DIRECTION):
            self.proposition.besoin_de_derogation = besoin_de_derogation

            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
                self.assertIsInstance(
                    context.exception.exceptions.pop(),
                    SituationPropositionNonSICException,
                )

        self.proposition.besoin_de_derogation = BesoinDeDerogation.ACCORD_DIRECTION

        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        self.assertEqual(resultat, self.proposition.entity_id)

    def test_should_lever_exception_si_conditions_complementaires_non_specifiees(self):
        self.proposition.avec_conditions_complementaires = True
        self.proposition.conditions_complementaires_existantes = []
        self.proposition.conditions_complementaires_libres = []
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
            self.assertIsInstance(
                context.exception.exceptions.pop(),
                InformationsAcceptationFacultaireNonSpecifieesException,
            )

    def test_should_etre_ok_si_presence_conditions_complementaires_non_specifiee(self):
        self.proposition.avec_conditions_complementaires = None
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE)
        self.assertEqual(proposition.checklist_actuelle.decision_sic.statut, ChoixStatutChecklist.GEST_REUSSITE)

    def test_should_etre_ok_si_presence_complements_formation_non_specifiee(self):
        self.proposition.avec_complements_formation = None
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE)
        self.assertEqual(proposition.checklist_actuelle.decision_sic.statut, ChoixStatutChecklist.GEST_REUSSITE)

    def test_should_etre_ok_si_complements_formation_non_specifies(self):
        self.proposition.avec_complements_formation = True
        self.proposition.complements_formation = []
        result = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
        self.assertEqual(result, self.proposition.entity_id)

    def test_should_lever_exception_si_parcours_anterieur_non_suffisant(self):
        self.proposition.checklist_actuelle.parcours_anterieur.statut = ChoixStatutChecklist.GEST_EN_COURS
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
            self.assertIsInstance(context.exception.exceptions.pop(), ParcoursAnterieurNonSuffisantException)

    def test_should_lever_exception_si_document_a_reclamer_immediatement(self):
        self.proposition.documents_demandes = {
            'CURRICULUM.CURRICULUM': {
                'status': StatutEmplacementDocument.A_RECLAMER.name,
                'request_status': StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
            },
        }
        self.proposition_repository.save(self.proposition)
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
            self.assertIsInstance(context.exception.exceptions.pop(), DocumentAReclamerImmediatException)
