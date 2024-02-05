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

from unittest import TestCase

from admission.ddd.admission.enums.type_bourse import TypeBourse
from admission.ddd.admission.formation_generale.commands import RecupererPropositionGestionnaireQuery
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.validator.exceptions import PropositionNonTrouveeException
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class RecupererPropositionGestionnaireServiceTestCase(TestCase):
    def setUp(self):
        self.cmd = RecupererPropositionGestionnaireQuery(uuid_proposition='uuid-MASTER-SCI')
        self.message_bus = message_bus_in_memory_instance

    def test_get_proposition(self):
        result = self.message_bus.invoke(self.cmd)
        self.assertEqual(result.formation.sigle, 'MASTER-SCI')
        self.assertEqual(result.formation.annee, 2021)
        self.assertEqual(result.formation.intitule, 'Master en sciences')
        self.assertEqual(result.formation.campus.nom, 'Louvain-la-Neuve')
        self.assertEqual(result.statut, ChoixStatutPropositionGenerale.EN_BROUILLON.name)
        self.assertEqual(result.matricule_candidat, '0000000001')
        self.assertEqual(result.prenom_candidat, 'Jane')
        self.assertEqual(result.nom_candidat, 'Smith')
        self.assertEqual(
            result.bourse_internationale.type,
            TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE.name,
        )
        self.assertEqual(result.bourse_internationale.nom_court, 'AFEPA')
        self.assertEqual(result.bourse_internationale.nom_long, 'AFEPA --')
        self.assertEqual(result.bourse_erasmus_mundus.type, TypeBourse.ERASMUS_MUNDUS.name)
        self.assertEqual(result.bourse_erasmus_mundus.nom_court, 'EMDI')
        self.assertEqual(result.bourse_erasmus_mundus.nom_long, 'EMDI --')
        self.assertEqual(result.bourse_double_diplome.type, TypeBourse.DOUBLE_TRIPLE_DIPLOMATION.name)
        self.assertEqual(result.bourse_double_diplome.nom_court, 'AGRO DD UCLOUVAIN/GEM')
        self.assertEqual(result.bourse_double_diplome.nom_long, 'AGRO DD UCLOUVAIN/GEM --')
        self.assertEqual(result.genre_candidat, 'H')
        self.assertEqual(result.adresse_email_candidat, 'john.doe@ucl.be')
        self.assertEqual(result.langue_contact_candidat, 'fr-be')
        self.assertEqual(result.nationalite_candidat, 'BE')
        self.assertEqual(result.nationalite_candidat_fr, 'Belgique')
        self.assertEqual(result.nationalite_candidat_en, 'Belgique')
        self.assertEqual(result.nationalite_ue_candidat, True)
        self.assertEqual(result.photo_identite_candidat, ['uuid11'])
        self.assertEqual(result.candidat_a_plusieurs_demandes, False)
        self.assertEqual(result.candidat_assimile, False)
        self.assertEqual(result.est_inscription_tardive, False)

    def test_get_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(RecupererPropositionGestionnaireQuery(uuid_proposition='inexistant'))
