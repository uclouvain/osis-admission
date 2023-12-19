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

import unittest
from django.test import SimpleTestCase
from mock.mock import Mock

from admission.ddd.admission.commands import InitialiserPropositionFusionPersonneCommand
from admission.ddd.admission.domain.model.proposition_fusion_personne import PropositionFusionPersonneIdentity
from admission.ddd.admission.use_case.write.initialiser_proposition_fusion_personne import \
    initialiser_proposition_fusion_personne
from admission.infrastructure.admission.repository.in_memory.proposition_fusion_personne import \
    PropositionPersonneFusionInMemoryRepository


class TestInitialiserPropositionFusionPersonne(SimpleTestCase):

    def setUp(self):
        self.repository = PropositionPersonneFusionInMemoryRepository()

    def test_initialiser_proposition_fusion_personne_with_valid_inputs(self):
        # Arrange
        cmd = InitialiserPropositionFusionPersonneCommand(
            original_global_id="1",
            nom='John Doe',
            prenom='Jane Doe',
            autres_prenoms='Bob Smith',
            date_naissance='1980-01-01',
            lieu_naissance='New York',
            email='johndoe@example.com',
            genre='Male',
            etat_civil='Single',
            nationalite='French',
            numero_national="123456789",
            numero_carte_id="1234",
            numero_passeport="987654321",
            dernier_noma_connu='John Doe',
            expiration_carte_id='2030-01-01',
            educational_curex_uuids=['uc1', 'uc2'],
            professional_curex_uuids=['pc1', 'pc2']
        )
        result = initialiser_proposition_fusion_personne(cmd, self.repository)
        self.assertEqual(result, PropositionFusionPersonneIdentity(
            uuid="uuid"
        ))
