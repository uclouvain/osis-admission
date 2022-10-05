# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import PropositionNonTrouveeException
from admission.infrastructure.projet_doctoral.preparation.repository.proposition import PropositionRepository


class PropositionRepositoryTestCase(TestCase):
    def setUp(self):
        self.repository = PropositionRepository()

    def test_proposition_non_trouvee(self):
        entity_id = PropositionIdentityBuilder().build_from_uuid("fdc1ef28-c368-443c-8501-fe0c3ef66d6d")
        with self.assertRaises(PropositionNonTrouveeException):
            # Test with real instance so that it fires the exception from DB
            self.repository.get(entity_id)
