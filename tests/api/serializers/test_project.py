# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest.mock import Mock

from django.test import TestCase

from admission.api.serializers.project import (
    GeneralEducationPropositionStatusMixin,
    ContinuingEducationPropositionStatusMixin,
    STATUT_A_COMPLETER,
    STATUT_TRAITEMENT_UCLOUVAIN_EN_COURS,
)
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale


class GeneralEducationPropositionStatusMixinTestCase(TestCase):
    def test_get_original_status(self):
        statuses = [
            ChoixStatutPropositionGenerale.EN_BROUILLON.name,
            ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
            ChoixStatutPropositionGenerale.CONFIRMEE.name,
            ChoixStatutPropositionGenerale.ANNULEE.name,
            ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
            ChoixStatutPropositionGenerale.INSCRIPTION_REFUSEE.name,
            ChoixStatutPropositionGenerale.CLOTUREE.name,
        ]

        for status in statuses:
            instance = Mock(statut=status)
            serializer = GeneralEducationPropositionStatusMixin(instance=instance)

            self.assertEqual(serializer.data['statut'], status)

    def test_get_to_complete_status(self):
        statuses = [
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
            ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name,
        ]

        for status in statuses:
            instance = Mock(statut=status)
            serializer = GeneralEducationPropositionStatusMixin(instance=instance)

            self.assertEqual(serializer.data['statut'], STATUT_A_COMPLETER)

    def test_get_in_progress_status(self):
        statuses = [
            ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC.name,
            ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name,
            ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC.name,
            ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name,
            ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION.name,
        ]

        for status in statuses:
            instance = Mock(statut=status)
            serializer = GeneralEducationPropositionStatusMixin(instance=instance)

            self.assertEqual(serializer.data['statut'], STATUT_TRAITEMENT_UCLOUVAIN_EN_COURS)


class ContinuingEducationPropositionStatusMixinTestCase(TestCase):
    def test_get_original_status(self):
        statuses = [
            ChoixStatutPropositionContinue.EN_BROUILLON.name,
            ChoixStatutPropositionContinue.CONFIRMEE.name,
            ChoixStatutPropositionContinue.INSCRIPTION_REFUSEE.name,
            ChoixStatutPropositionContinue.ANNULEE.name,
            ChoixStatutPropositionContinue.INSCRIPTION_AUTORISEE.name,
            ChoixStatutPropositionContinue.CLOTUREE.name,
            ChoixStatutPropositionContinue.ANNULEE_PAR_GESTIONNAIRE.name,
        ]

        for status in statuses:
            instance = Mock(statut=status)
            serializer = ContinuingEducationPropositionStatusMixin(instance=instance)

            self.assertEqual(serializer.data['statut'], status)

    def test_get_to_complete_status(self):
        statuses = [
            ChoixStatutPropositionContinue.A_COMPLETER_POUR_FAC.name,
        ]

        for status in statuses:
            instance = Mock(statut=status)
            serializer = ContinuingEducationPropositionStatusMixin(instance=instance)

            self.assertEqual(serializer.data['statut'], STATUT_A_COMPLETER)

    def test_get_in_progress_status(self):
        statuses = [
            ChoixStatutPropositionContinue.COMPLETEE_POUR_FAC.name,
            ChoixStatutPropositionContinue.EN_ATTENTE.name,
        ]

        for status in statuses:
            instance = Mock(statut=status)
            serializer = ContinuingEducationPropositionStatusMixin(instance=instance)

            self.assertEqual(serializer.data['statut'], STATUT_TRAITEMENT_UCLOUVAIN_EN_COURS)
