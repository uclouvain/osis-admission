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
    ApprouverAdmissionParSicCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    InformationsAcceptationFacultaireNonSpecifieesException,
    ParcoursAnterieurNonSuffisantException,
    DocumentAReclamerImmediatException,
)
from admission.ddd.admission.doctorat.preparation.test.factory.groupe_de_supervision import (
    GroupeDeSupervisionSC3DPFactory,
)
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
)
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import _PropositionIdentityFactory
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocumentIdentity
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.enums.emplacement_document import (
    OngletsDemande,
    StatutEmplacementDocument,
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.emplacement_document import (
    emplacement_document_in_memory_repository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository


@freezegun.freeze_time('2020-11-01')
class TestApprouverAdmissionParSic(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = ApprouverAdmissionParSicCommand
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
        self.addCleanup(self.groupe_de_supervision_repository.reset)
        self.proposition.checklist_actuelle.parcours_anterieur.statut = ChoixStatutChecklist.GEST_REUSSITE
        self.proposition_repository.save(self.proposition)
        self.parametres_commande_par_defaut = {
            'uuid_proposition': 'uuid-SC3DP-APPROVED',
            'objet_message': 'foo',
            'corps_message': 'bar',
            'auteur': '00321234',
        }

    def test_should_etre_ok_si_statut_correct(self):
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-SC3DP-APPROVED')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE)
        self.assertEqual(proposition.checklist_actuelle.decision_sic.statut, ChoixStatutChecklist.GEST_REUSSITE)

        # Vérifier que les documents concernés sont bien à réclamer
        emplacement_autorisation = emplacement_document_in_memory_repository.get(
            entity_id=EmplacementDocumentIdentity(
                identifiant=f'{OngletsDemande.SUITE_AUTORISATION.name}.AUTORISATION_PDF_SIGNEE',
                proposition_id=PropositionIdentity(uuid=self.proposition.entity_id.uuid),
            )
        )

        emplacement_visa_etudes = emplacement_document_in_memory_repository.get(
            entity_id=EmplacementDocumentIdentity(
                identifiant=f'{OngletsDemande.SUITE_AUTORISATION.name}.VISA_ETUDES',
                proposition_id=PropositionIdentity(uuid=self.proposition.entity_id.uuid),
            )
        )

        self.assertEqual(emplacement_autorisation.statut, StatutEmplacementDocument.A_RECLAMER)
        self.assertEqual(
            emplacement_autorisation.statut_reclamation,
            StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT,
        )

        self.assertNotEqual(emplacement_visa_etudes.statut, StatutEmplacementDocument.A_RECLAMER)

        # Avec une demande de visa d'études, le visa d'études doit être réclamé
        self.proposition.doit_fournir_visa_etudes = True

        self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-SC3DP-APPROVED')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE)
        self.assertEqual(proposition.checklist_actuelle.decision_sic.statut, ChoixStatutChecklist.GEST_REUSSITE)

        self.assertEqual(emplacement_autorisation.statut, StatutEmplacementDocument.A_RECLAMER)
        self.assertEqual(
            emplacement_autorisation.statut_reclamation,
            StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT,
        )

        self.assertEqual(emplacement_visa_etudes.statut, StatutEmplacementDocument.A_RECLAMER)
        self.assertEqual(
            emplacement_visa_etudes.statut_reclamation,
            StatutReclamationEmplacementDocument.ULTERIEUREMENT_BLOQUANT,
        )

    def test_should_lever_exception_si_presence_conditions_complementaires_non_specifiee(self):
        self.proposition.avec_conditions_complementaires = None
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
            self.assertIsInstance(
                context.exception.exceptions.pop(), InformationsAcceptationFacultaireNonSpecifieesException
            )

    def test_should_lever_exception_si_conditions_complementaires_non_specifiees(self):
        self.proposition.avec_conditions_complementaires = True
        self.proposition.conditions_complementaires_existantes = []
        self.proposition.conditions_complementaires_libres = []
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
            self.assertIsInstance(
                context.exception.exceptions.pop(), InformationsAcceptationFacultaireNonSpecifieesException
            )

    def test_should_lever_exception_si_presence_complements_formation_non_specifiee(self):
        self.proposition.avec_complements_formation = None
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE)
        self.assertEqual(proposition.checklist_actuelle.decision_sic.statut, ChoixStatutChecklist.GEST_REUSSITE)

    def test_should_etre_ok_si_complements_formation_non_specifiees(self):
        self.proposition.avec_complements_formation = True
        self.proposition.complements_formation = []
        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.statut, ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE)
        self.assertEqual(proposition.checklist_actuelle.decision_sic.statut, ChoixStatutChecklist.GEST_REUSSITE)

    def test_should_lever_exception_si_nombre_annees_prevoir_programme_non_specifie(self):
        self.proposition.nombre_annees_prevoir_programme = None
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))
            self.assertIsInstance(
                context.exception.exceptions.pop(), InformationsAcceptationFacultaireNonSpecifieesException
            )

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
