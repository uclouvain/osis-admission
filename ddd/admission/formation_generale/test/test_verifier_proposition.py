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

from django.test import TestCase

from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.service.verifier_proposition import VerifierProposition
from admission.ddd.admission.formation_generale.test.factory.proposition import PropositionFactory
from admission.infrastructure.admission.domain.service.in_memory.calendrier_inscription import (
    CalendrierInscriptionInMemory,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from admission.infrastructure.admission.domain.service.in_memory.titres_acces import TitresAccesInMemory
from admission.tests.factories.conditions import AdmissionConditionsDTOFactory
from base.models.enums.education_group_types import TrainingType


class TypeDemandeTestCase(TestCase):
    def setUp(self):
        self.calendrier_inscription = CalendrierInscriptionInMemory()
        self.profil_candidat_translator = ProfilCandidatInMemoryTranslator()
        self.titres_acces_in_memory = TitresAccesInMemory()

    def tearDown(self):
        self.titres_acces_in_memory.reset()

    def test_type_demande_belge_diplomes_tous_belges(self):
        self.titres_acces_in_memory.results['0000000001'] = AdmissionConditionsDTOFactory(
            diplomation_potentiel_master_belge=True,
        )
        titres = self.titres_acces_in_memory.recuperer_titres_access('0000000001', TrainingType.CAPAES)
        type_demande = VerifierProposition.determiner_type_demande(
            PropositionFactory(matricule_candidat='0000000001'),
            titres,
            self.calendrier_inscription,
            self.profil_candidat_translator,
        )
        self.assertEqual(type_demande, TypeDemande.INSCRIPTION)

    def test_type_demande_belge_diplome_belge_et_etranger(self):
        self.titres_acces_in_memory.results['0000000001'] = AdmissionConditionsDTOFactory(
            diplomation_potentiel_master_belge=True,
            diplomation_potentiel_master_etranger=True,
        )
        titres = self.titres_acces_in_memory.recuperer_titres_access('0000000001', TrainingType.CAPAES)
        type_demande = VerifierProposition.determiner_type_demande(
            PropositionFactory(matricule_candidat='0000000001'),
            titres,
            self.calendrier_inscription,
            self.profil_candidat_translator,
        )
        self.assertEqual(type_demande, TypeDemande.ADMISSION)

    def test_type_demande_belge_diplome_belge_et_etranger_pas_condition_access(self):
        self.titres_acces_in_memory.results['0000000001'] = AdmissionConditionsDTOFactory(
            diplomation_secondaire_etranger=True,
            diplomation_potentiel_master_belge=True,
        )
        titres = self.titres_acces_in_memory.recuperer_titres_access('0000000001', TrainingType.CAPAES)
        type_demande = VerifierProposition.determiner_type_demande(
            PropositionFactory(matricule_candidat='0000000001'),
            titres,
            self.calendrier_inscription,
            self.profil_candidat_translator,
        )
        self.assertEqual(type_demande, TypeDemande.INSCRIPTION)

    def test_type_demande_etranger_diplome_belge(self):
        self.titres_acces_in_memory.results['0000000003'] = AdmissionConditionsDTOFactory(
            diplomation_potentiel_master_belge=True,
        )
        titres = self.titres_acces_in_memory.recuperer_titres_access('0000000003', TrainingType.CAPAES)
        type_demande = VerifierProposition.determiner_type_demande(
            PropositionFactory(matricule_candidat='0000000003'),
            titres,
            self.calendrier_inscription,
            self.profil_candidat_translator,
        )
        self.assertEqual(type_demande, TypeDemande.ADMISSION)
