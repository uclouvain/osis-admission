# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################

from unittest.mock import patch

import freezegun
import mock
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    RecupererElementsConfirmationQuery as RecupererElementsConfirmationDoctoratQuery,
)
from admission.ddd.admission.domain.validator.exceptions import ElementsConfirmationNonConcordants
from admission.ddd.admission.formation_continue.commands import (
    RecupererElementsConfirmationQuery as RecupererElementsConfirmationContinueQuery,
    SoumettrePropositionCommand as SoumettrePropositionContinueCommand,
)
from admission.ddd.admission.formation_generale.commands import (
    RecupererElementsConfirmationQuery as RecupererElementsConfirmationGeneraleQuery,
    SoumettrePropositionCommand as SoumettrePropositionGeneraleCommand,
)
from admission.ddd.admission.test.factory.formation import FormationFactory
from admission.infrastructure.admission.domain.service.in_memory.elements_confirmation import (
    ElementsConfirmationInMemory,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository as PropositionContinueRepository,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.formation import (
    FormationGeneraleInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository as PropositionGeneraleRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from ddd.logic.financabilite.dtos.parcours import (
    ParcoursDTO, ParcoursAcademiqueInterneDTO,
    ParcoursAcademiqueExterneDTO,
)
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from ddd.logic.shared_kernel.academic_year.domain.service.get_current_academic_year import GetCurrentAcademicYear
from infrastructure.financabilite.domain.service.in_memory.financabilite import FinancabiliteInMemoryFetcher


@freezegun.freeze_time('2020-10-15')
class ElementsConfirmationTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ProfilCandidatInMemoryTranslator.reset()
        FinancabiliteInMemoryFetcher.reset()

    def setUp(self):
        # Mock publish
        patcher = mock.patch(
            'infrastructure.utils.MessageBus.publish',
        )
        self.mock_publish = patcher.start()
        self.addCleanup(patcher.stop)

    def test_recuperer_elements_confirmation_doctorat(self):
        elements = message_bus_in_memory_instance.invoke(
            RecupererElementsConfirmationDoctoratQuery(uuid_proposition="uuid-SC3DP")
        )
        expected = [
            'reglement_doctorat',
            'reglement_doctorat_deontologie',
            'protection_donnees',
            'professions_reglementees',
            'justificatifs',
            'declaration_sur_lhonneur',
        ]
        self.assertListEqual([e.nom for e in elements], expected)

    def test_recuperer_elements_confirmation_formation_continue_hors_delai(self):
        with patch.object(PropositionContinueRepository.entities[0], 'annee_calculee', 2021):
            elements = message_bus_in_memory_instance.invoke(
                RecupererElementsConfirmationContinueQuery(uuid_proposition="uuid-USCC4")
            )
            expected = [
                'hors_delai',
                'reglement_general',
                'protection_donnees',
                'professions_reglementees',
                'justificatifs',
                'declaration_sur_lhonneur',
                'droits_inscription_iufc',
            ]
            self.assertListEqual([e.nom for e in elements], expected)

    def test_recuperer_elements_confirmation_bachelier_medecine(self):
        new_trainings = [
            FormationFactory(
                intitule='Bachelier en sciences économiques et de gestion',
                entity_id__sigle='BACHELIER-ECO',
                entity_id__annee=2020,
                type=TrainingType.BACHELOR,
                campus='Mons',
                code_domaine='11',
            ),
        ]
        with patch.object(PropositionGeneraleRepository.entities[1], 'annee_calculee', 2020), patch.object(
            FormationGeneraleInMemoryTranslator, 'trainings', new_trainings
        ):
            elements = message_bus_in_memory_instance.invoke(
                RecupererElementsConfirmationGeneraleQuery(uuid_proposition="uuid-BACHELIER-ECO1")
            )
            expected = [
                'reglement_general',
                'protection_donnees',
                'professions_reglementees',
                'convention_cadre_stages',
                'communication_hopitaux',
                'justificatifs',
                'declaration_sur_lhonneur',
            ]
            self.assertListEqual([e.nom for e in elements], expected)

    def test_recuperer_elements_confirmation_frais_dossier(self):
        with patch.object(ProfilCandidatInMemoryTranslator.profil_candidats[1], 'pays_nationalite', 'AR'):
            elements = message_bus_in_memory_instance.invoke(
                RecupererElementsConfirmationGeneraleQuery(uuid_proposition="uuid-BACHELIER-ECO1")
            )
            expected = [
                'reglement_general',
                'protection_donnees',
                'professions_reglementees',
                'frais_dossier',
                'justificatifs',
                'declaration_sur_lhonneur',
            ]
            self.assertListEqual([e.nom for e in elements], expected)

    def test_recuperer_elements_confirmation_visa(self):
        candidat = ProfilCandidatInMemoryTranslator.profil_candidats[1]
        adresse_residence = next(
            adresse
            for adresse in ProfilCandidatInMemoryTranslator.adresses_candidats
            if adresse.personne == candidat.matricule
        )

        # Candidat de nationalité HORS UE+5 et de pays de résidence hors BE
        with patch.multiple(candidat, pays_nationalite='AR', pays_nationalite_europeen=False):
            with patch.multiple(adresse_residence, pays='FR'):
                elements = message_bus_in_memory_instance.invoke(
                    RecupererElementsConfirmationGeneraleQuery(uuid_proposition="uuid-BACHELIER-ECO1")
                )
                expected = [
                    'reglement_general',
                    'protection_donnees',
                    'professions_reglementees',
                    'frais_dossier',
                    'visa',
                    'justificatifs',
                    'declaration_sur_lhonneur',
                ]
                self.assertListEqual([e.nom for e in elements], expected)

        # Nationalité non spécifiée
        with patch.multiple(candidat, pays_nationalite='', pays_nationalite_europeen=False):
            with patch.multiple(adresse_residence, pays='FR'):
                elements = message_bus_in_memory_instance.invoke(
                    RecupererElementsConfirmationGeneraleQuery(uuid_proposition="uuid-BACHELIER-ECO1")
                )
                self.assertNotIn('visa', [e.nom for e in elements])

        # Nationalité dans UE
        with patch.multiple(candidat, pays_nationalite='FR', pays_nationalite_europeen=True):
            with patch.multiple(adresse_residence, pays='FR'):
                elements = message_bus_in_memory_instance.invoke(
                    RecupererElementsConfirmationGeneraleQuery(uuid_proposition="uuid-BACHELIER-ECO1")
                )
                self.assertNotIn('visa', [e.nom for e in elements])

        # Nationalité dans UE+5
        with patch.multiple(candidat, pays_nationalite='CH', pays_nationalite_europeen=False):
            with patch.multiple(adresse_residence, pays='FR'):
                elements = message_bus_in_memory_instance.invoke(
                    RecupererElementsConfirmationGeneraleQuery(uuid_proposition="uuid-BACHELIER-ECO1")
                )
                self.assertNotIn('visa', [e.nom for e in elements])

        # Nationalité hors UE+5
        # Pas d'adresse de résidence
        with patch.multiple(candidat, pays_nationalite='US', pays_nationalite_europeen=False):
            with patch.multiple(adresse_residence, pays=''):
                elements = message_bus_in_memory_instance.invoke(
                    RecupererElementsConfirmationGeneraleQuery(uuid_proposition="uuid-BACHELIER-ECO1")
                )
                self.assertNotIn('visa', [e.nom for e in elements])

        # Adresse de résidence en belgique
        with patch.multiple(candidat, pays_nationalite='US', pays_nationalite_europeen=False):
            with patch.multiple(adresse_residence, pays='BE'):
                elements = message_bus_in_memory_instance.invoke(
                    RecupererElementsConfirmationGeneraleQuery(uuid_proposition="uuid-BACHELIER-ECO1")
                )
                self.assertNotIn('visa', [e.nom for e in elements])

    def test_recuperer_elements_confirmation_etudes_contingentees(self):
        with patch.object(
            PropositionGeneraleRepository.entities[1],
            'pot_calcule',
            AcademicCalendarTypes.ADMISSION_POOL_NON_RESIDENT_QUOTA,
        ):
            elements = message_bus_in_memory_instance.invoke(
                RecupererElementsConfirmationGeneraleQuery(uuid_proposition="uuid-BACHELIER-ECO1")
            )
            expected = [
                'reglement_general',
                'protection_donnees',
                'professions_reglementees',
                'documents_etudes_contingentees',
                'justificatifs',
                'declaration_sur_lhonneur',
            ]
            self.assertListEqual([e.nom for e in elements], expected)

    def test_recuperer_elements_confirmation_etudes_communication_ecole(self):
        with patch.object(
            ElementsConfirmationInMemory,
            'est_candidat_avec_etudes_secondaires_belges_francophones',
            lambda _: True,
        ):
            elements = message_bus_in_memory_instance.invoke(
                RecupererElementsConfirmationGeneraleQuery(uuid_proposition="uuid-BACHELIER-ECO1")
            )
            expected = [
                'reglement_general',
                'protection_donnees',
                'professions_reglementees',
                'communication_ecole_secondaire',
                'justificatifs',
                'declaration_sur_lhonneur',
            ]
            self.assertListEqual([e.nom for e in elements], expected)

    def test_soumettre_elements_confirmation_manquants(self):
        with self.assertRaises(ElementsConfirmationNonConcordants):
            message_bus_in_memory_instance.invoke(
                SoumettrePropositionContinueCommand(
                    uuid_proposition="uuid-USCC1",
                    annee=2020,
                    pool=AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT.name,
                    elements_confirmation={
                        'reglement_general': ElementsConfirmationInMemory.REGLEMENT_GENERAL,
                    },
                )
            )

    def test_soumettre_elements_confirmation_differents(self):
        with self.assertRaises(ElementsConfirmationNonConcordants):
            message_bus_in_memory_instance.invoke(
                SoumettrePropositionContinueCommand(
                    uuid_proposition="uuid-USCC1",
                    annee=2020,
                    pool=AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT.name,
                    elements_confirmation={
                        'reglement_general': "Alors en fait non",
                        'protection_donnees': ElementsConfirmationInMemory.PROTECTION_DONNEES,
                        'professions_reglementees': ElementsConfirmationInMemory.PROFESSIONS_REGLEMENTEES,
                        'justificatifs': ElementsConfirmationInMemory.JUSTIFICATIFS,
                        'declaration_sur_lhonneur': ElementsConfirmationInMemory.DECLARATION_SUR_LHONNEUR,
                    },
                )
            )

    @freezegun.freeze_time('2024-10-15')
    def test_soumettre_elements_confirmation_differents_radio(self):
        FinancabiliteInMemoryFetcher.save(ParcoursDTO(
            matricule_fgs='0000000001',
            parcours_academique_interne=ParcoursAcademiqueInterneDTO(programmes_cycles=[]),
            parcours_academique_externe=ParcoursAcademiqueExterneDTO(experiences=[]),
            annee_diplome_etudes_secondaires=2015,
            nombre_tentative_de_passer_concours_pass_et_las=0,
        ))
        with patch.object(
            ElementsConfirmationInMemory,
            'est_candidat_avec_etudes_secondaires_belges_francophones',
            lambda _: True,
        ), patch.object(
            GetCurrentAcademicYear,
            'get_starting_academic_year',
            lambda *_: AcademicYear(AcademicYearIdentity(2024), None, None),
        ), self.assertRaises(
            ElementsConfirmationNonConcordants
        ):
            message_bus_in_memory_instance.invoke(
                SoumettrePropositionGeneraleCommand(
                    uuid_proposition="uuid-BACHELIER-FINANCABILITE",
                    annee=2024,
                    pool=AcademicCalendarTypes.ADMISSION_POOL_VIP.name,
                    elements_confirmation={
                        'reglement_general': ElementsConfirmationInMemory.REGLEMENT_GENERAL,
                        'protection_donnees': ElementsConfirmationInMemory.PROTECTION_DONNEES,
                        'professions_reglementees': ElementsConfirmationInMemory.PROFESSIONS_REGLEMENTEES,
                        'communication_ecole_secondaire': "Non en fait",
                        'justificatifs': ElementsConfirmationInMemory.JUSTIFICATIFS,
                        'declaration_sur_lhonneur': ElementsConfirmationInMemory.DECLARATION_SUR_LHONNEUR,
                    },
                )
            )
