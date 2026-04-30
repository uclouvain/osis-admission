# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid
from unittest.mock import MagicMock, patch

import freezegun
import mock
from django.test import TestCase

from admission.ddd.admission.formation_generale.commands import SoumettrePropositionCommand
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
    ChoixStatutPropositionGenerale,
    RaisonPlusieursDemandesMemesCycleEtAnnee,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import StatutChecklist
from admission.ddd.admission.formation_generale.domain.service.checklist import Checklist
from admission.ddd.admission.formation_generale.test.factory.proposition import PropositionFactory
from admission.ddd.admission.shared_kernel.domain.model.assimilation import Assimilation
from admission.ddd.admission.shared_kernel.enums import (
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    LienParente,
    TypeSituationAssimilation,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.formation import (
    FormationGeneraleInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.question_specifique import (
    QuestionSpecifiqueInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.shared_kernel.domain.service.in_memory.elements_confirmation import (
    ElementsConfirmationInMemory,
)
from admission.infrastructure.admission.shared_kernel.domain.service.in_memory.profil_candidat import (
    ProfilCandidatInMemoryTranslator,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.community import CommunityEnum
from base.models.enums.education_group_types import TrainingType
from ddd.logic.financabilite.domain.model.enums.etat import EtatFinancabilite
from ddd.logic.financabilite.dtos.financabilite import FinancabiliteDTO
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository
from reference.models.enums.cycle import Cycle


class TestSoumettrePropositionGenerale(TestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance
        self.academic_year_repository = AcademicYearInMemoryRepository()
        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.candidat = self.candidat_translator.profil_candidats[1]
        patcher = mock.patch(
            'admission.ddd.admission.formation_generale.use_case.write.soumettre_proposition_service.Financabilite'
        )
        mock_financabilite = patcher.start()
        self.addCleanup(patcher.stop)
        mock_financabilite.return_value.determiner.return_value = FinancabiliteDTO(
            etat=EtatFinancabilite.NON_FINANCABLE.name, details=[]
        )

        for annee in range(2016, 2026):
            self.academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )

        # Mock publish
        patcher = mock.patch(
            'infrastructure.utils.MessageBus.publish',
        )
        self.mock_publish = patcher.start()
        self.addCleanup(patcher.stop)

    @freezegun.freeze_time('2023-11-01')
    def test_should_soumettre_proposition_etre_ok_si_admission_complete(self):
        elements_confirmation = ElementsConfirmationInMemory.get_elements_for_tests(
            self.proposition_repository.get(PropositionIdentity("uuid-MASTER-SCI")),
            FormationGeneraleInMemoryTranslator(),
        )
        proposition_id = self.message_bus.invoke(
            SoumettrePropositionCommand(
                uuid_proposition="uuid-BACHELIER-FINANCABILITE",
                pool=AcademicCalendarTypes.ADMISSION_POOL_VIP.name,
                annee=2024,
                elements_confirmation=elements_confirmation,
                raison_plusieurs_demandes_meme_cycle_meme_annee=(
                    RaisonPlusieursDemandesMemesCycleEtAnnee.SUIVRE_EN_PARALLELE.name
                ),
                justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee='1',
            ),
        )

        updated_proposition = self.proposition_repository.get(proposition_id)

        # Command result
        self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)
        # Updated proposition
        self.assertEqual(updated_proposition.statut, ChoixStatutPropositionGenerale.CONFIRMEE)
        self.assertEqual(updated_proposition.est_inscription_tardive, False)
        self.assertEqual(updated_proposition.auteur_derniere_modification, self.candidat.matricule)
        self.assertEqual(
            updated_proposition.raison_plusieurs_demandes_meme_cycle_meme_annee,
            RaisonPlusieursDemandesMemesCycleEtAnnee.SUIVRE_EN_PARALLELE,
        )
        self.assertEqual(updated_proposition.justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee, '1')

    @freezegun.freeze_time('2023-11-01')
    def test_should_soumettre_proposition_etre_ok_avec_assimilation_passee(self):
        with mock.patch(
            'admission.infrastructure.admission.shared_kernel.domain.service.in_memory.inscriptions_translator.'
            'InscriptionsInMemoryTranslator.recuperer_assimilation_inscription_formation_annee_precedente',
            return_value=Assimilation(
                type_situation_assimilation=TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2,
                sous_type_situation_assimilation_1=ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER,
                sous_type_situation_assimilation_2=ChoixAssimilation2.DEMANDEUR_ASILE,
                sous_type_situation_assimilation_3=ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT,
                relation_parente=LienParente.PERE,
                sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE,
                sous_type_situation_assimilation_6=ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT,
                source=Assimilation.Source.OSIS,
            ),
        ):
            elements_confirmation = ElementsConfirmationInMemory.get_elements_for_tests(
                self.proposition_repository.get(PropositionIdentity("uuid-MASTER-SCI")),
                FormationGeneraleInMemoryTranslator(),
            )
            proposition_id = self.message_bus.invoke(
                SoumettrePropositionCommand(
                    uuid_proposition="uuid-BACHELIER-FINANCABILITE",
                    pool=AcademicCalendarTypes.ADMISSION_POOL_VIP.name,
                    annee=2024,
                    elements_confirmation=elements_confirmation,
                    raison_plusieurs_demandes_meme_cycle_meme_annee=(
                        RaisonPlusieursDemandesMemesCycleEtAnnee.SUIVRE_EN_PARALLELE.name
                    ),
                    justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee='1',
                ),
            )

            updated_proposition = self.proposition_repository.get(proposition_id)

            # Command result
            self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)
            self.assertEqual(
                updated_proposition.comptabilite.type_situation_assimilation,
                TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2,
            )
            self.assertEqual(
                updated_proposition.comptabilite.sous_type_situation_assimilation_1,
                ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER,
            )
            self.assertEqual(
                updated_proposition.comptabilite.sous_type_situation_assimilation_2,
                ChoixAssimilation2.DEMANDEUR_ASILE,
            )
            self.assertEqual(
                updated_proposition.comptabilite.sous_type_situation_assimilation_3,
                ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT,
            )
            self.assertEqual(
                updated_proposition.comptabilite.relation_parente,
                LienParente.PERE,
            )
            self.assertEqual(
                updated_proposition.comptabilite.sous_type_situation_assimilation_5,
                ChoixAssimilation5.A_NATIONALITE_UE,
            )
            self.assertEqual(
                updated_proposition.comptabilite.sous_type_situation_assimilation_6,
                ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT,
            )

    @freezegun.freeze_time('22/10/2024')
    def test_should_soumettre_proposition_tardive(self):
        with patch.multiple(
            self.candidat,
            annee_derniere_inscription_ucl=2023,
            noma_derniere_inscription_ucl='00000001',
            pays_nationalite="AR",
        ):
            proposition = PropositionFactory(
                est_bachelier_en_reorientation=True,
                formation_id__sigle="ABCD1BA",
                formation_id__annee=2024,
                curriculum=['file1.pdf'],
                matricule_candidat=self.candidat.matricule,
                bourse_double_diplome_id=None,
                bourse_internationale_id=None,
                bourse_erasmus_mundus_id=None,
            )

            self.proposition_repository.save(proposition)

            elements_confirmation = ElementsConfirmationInMemory.get_elements_for_tests(
                self.proposition_repository.get(proposition.entity_id),
                FormationGeneraleInMemoryTranslator(),
                profil_translator=self.candidat_translator,
            )

            proposition_id = self.message_bus.invoke(
                SoumettrePropositionCommand(
                    uuid_proposition=proposition.entity_id.uuid,
                    pool=AcademicCalendarTypes.ADMISSION_POOL_HUE_UCL_PATHWAY_CHANGE.name,
                    annee=2024,
                    elements_confirmation=elements_confirmation,
                    raison_plusieurs_demandes_meme_cycle_meme_annee='',
                    justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee='',
                ),
            )

            proposition = self.proposition_repository.get(entity_id=proposition_id)
            self.assertEqual(proposition.est_inscription_tardive, True)

    @freezegun.freeze_time('22/09/2024')
    def test_should_soumettre_proposition_non_tardive_avant_limite(self):
        with patch.multiple(
            self.candidat,
            annee_derniere_inscription_ucl=2023,
            noma_derniere_inscription_ucl='00000001',
            pays_nationalite="AR",
        ):
            proposition = PropositionFactory(
                est_bachelier_en_reorientation=True,
                formation_id__sigle="ABCD1BA",
                formation_id__annee=2024,
                matricule_candidat=self.candidat.matricule,
                curriculum=['file1.pdf'],
                bourse_double_diplome_id=None,
                bourse_internationale_id=None,
                bourse_erasmus_mundus_id=None,
            )

            self.proposition_repository.save(proposition)

            elements_confirmation = ElementsConfirmationInMemory.get_elements_for_tests(
                self.proposition_repository.get(proposition.entity_id),
                FormationGeneraleInMemoryTranslator(),
                profil_translator=self.candidat_translator,
            )

            proposition_id = self.message_bus.invoke(
                SoumettrePropositionCommand(
                    uuid_proposition=proposition.entity_id.uuid,
                    pool=AcademicCalendarTypes.ADMISSION_POOL_HUE_UCL_PATHWAY_CHANGE.name,
                    annee=2024,
                    elements_confirmation=elements_confirmation,
                    raison_plusieurs_demandes_meme_cycle_meme_annee='',
                    justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee='',
                ),
            )

            proposition = self.proposition_repository.get(entity_id=proposition_id)
            self.assertEqual(proposition.est_inscription_tardive, False)

    @freezegun.freeze_time('22/10/2024')
    def test_should_soumettre_proposition_non_tardive_pot_sans_possibilite_inscription_tardive(self):
        elements_confirmation = ElementsConfirmationInMemory.get_elements_for_tests(
            self.proposition_repository.get(PropositionIdentity("uuid-MASTER-SCI")),
            FormationGeneraleInMemoryTranslator(),
        )
        proposition_id = self.message_bus.invoke(
            SoumettrePropositionCommand(
                uuid_proposition="uuid-BACHELIER-FINANCABILITE",
                pool=AcademicCalendarTypes.ADMISSION_POOL_VIP.name,
                annee=2024,
                elements_confirmation=elements_confirmation,
                raison_plusieurs_demandes_meme_cycle_meme_annee='',
                justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee='',
            ),
        )

        updated_proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(updated_proposition.est_inscription_tardive, False)

    @freezegun.freeze_time('22/09/2021')
    def test_should_soumettre_proposition_en_nettoyant_reponses_questions_specifiques(self):
        proposition = self.proposition_repository.get(PropositionIdentity("uuid-MASTER-SCI"))

        elements_confirmation = ElementsConfirmationInMemory.get_elements_for_tests(
            proposition,
            FormationGeneraleInMemoryTranslator(),
        )

        proposition.reponses_questions_specifiques = {
            '16de0c3d-3c06-4c93-8eb4-c8648f04f140': 'My response 0',
            # A default value will be set
            # '16de0c3d-3c06-4c93-8eb4-c8648f04f141': 'My response 1',
            '16de0c3d-3c06-4c93-8eb4-c8648f04f142': 'My response 2',
            '16de0c3d-3c06-4c93-8eb4-c8648f04f143': 'My response 3',
            '16de0c3d-3c06-4c93-8eb4-c8648f04f144': 'My response 4',
            '16de0c3d-3c06-4c93-8eb4-c8648f04f145': ['24de0c3d-3c06-4c93-8eb4-c8648f04f144'],
            # A default value will be set
            # '16de0c3d-3c06-4c93-8eb4-c8648f04f146': ['24de0c3d-3c06-4c93-8eb4-c8648f04f145'],
            # Will be deleted as it's a readonly element
            '16de0c3d-3c06-4c93-8eb4-c8648f04f149': 'MESSAGE',
            # Will be deleted as it's not interesting for this admission
            '26de0c3d-3c06-4c93-8eb4-c8648f04f140': 'Not interesting response 0',
            '26de0c3d-3c06-4c93-8eb4-c8648f04f141': 'Not interesting response 1',
        }

        self.proposition_repository.save(proposition)

        proposition_id = self.message_bus.invoke(
            SoumettrePropositionCommand(
                uuid_proposition="uuid-MASTER-SCI",
                pool=AcademicCalendarTypes.ADMISSION_POOL_VIP.name,
                annee=2021,
                elements_confirmation=elements_confirmation,
                raison_plusieurs_demandes_meme_cycle_meme_annee='',
                justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee='',
            ),
        )

        updated_proposition = self.proposition_repository.get(proposition_id)

        # Command result
        self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)

        # Updated proposition
        self.assertEqual(updated_proposition.statut, ChoixStatutPropositionGenerale.CONFIRMEE)

        self.assertEqual(
            updated_proposition.reponses_questions_specifiques,
            {
                '16de0c3d-3c06-4c93-8eb4-c8648f04f140': 'My response 0',
                '16de0c3d-3c06-4c93-8eb4-c8648f04f141': '',
                '16de0c3d-3c06-4c93-8eb4-c8648f04f142': 'My response 2',
                '16de0c3d-3c06-4c93-8eb4-c8648f04f143': 'My response 3',
                '16de0c3d-3c06-4c93-8eb4-c8648f04f144': 'My response 4',
                '16de0c3d-3c06-4c93-8eb4-c8648f04f145': ['24de0c3d-3c06-4c93-8eb4-c8648f04f144'],
                '16de0c3d-3c06-4c93-8eb4-c8648f04f146': [],
            },
        )

    def test_initialisation_checklist_assimilation(self):
        # UE
        statut_checklist = Checklist._recuperer_statut_checklist_initial_assimilation(
            proposition=MagicMock(),
            identification_dto=MagicMock(pays_nationalite_europeen=True),
            candidat_est_en_poursuite_directe=True,
            assimilation_passee=MagicMock(),
        )

        self.assertEqual(statut_checklist.statut, ChoixStatutChecklist.INITIAL_NON_CONCERNE)
        self.assertEqual(statut_checklist.libelle, 'Not concerned')

        # non UE sans poursuite
        # > avec assimilation
        statut_checklist = Checklist._recuperer_statut_checklist_initial_assimilation(
            proposition=MagicMock(
                comptabilite=MagicMock(
                    type_situation_assimilation=TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE
                )
            ),
            identification_dto=MagicMock(pays_nationalite_europeen=False),
            candidat_est_en_poursuite_directe=False,
            assimilation_passee=None,
        )

        self.assertEqual(statut_checklist.statut, ChoixStatutChecklist.INITIAL_CANDIDAT)
        self.assertEqual(statut_checklist.libelle, 'Declared assimilated')

        # > sans assimilation
        statut_checklist = Checklist._recuperer_statut_checklist_initial_assimilation(
            proposition=MagicMock(
                comptabilite=MagicMock(type_situation_assimilation=TypeSituationAssimilation.AUCUNE_ASSIMILATION)
            ),
            identification_dto=MagicMock(pays_nationalite_europeen=False),
            candidat_est_en_poursuite_directe=False,
            assimilation_passee=None,
        )

        self.assertEqual(statut_checklist.statut, ChoixStatutChecklist.INITIAL_CANDIDAT)
        self.assertEqual(statut_checklist.libelle, 'Declared not assimilated')

        statut_checklist = Checklist._recuperer_statut_checklist_initial_assimilation(
            proposition=MagicMock(comptabilite=MagicMock(type_situation_assimilation=None)),
            identification_dto=MagicMock(pays_nationalite_europeen=False),
            candidat_est_en_poursuite_directe=False,
            assimilation_passee=None,
        )

        self.assertEqual(statut_checklist.statut, ChoixStatutChecklist.INITIAL_CANDIDAT)
        self.assertEqual(statut_checklist.libelle, 'Declared not assimilated')

        # non UE avec poursuite
        # > avec assimilation passée complète
        statut_checklist = Checklist._recuperer_statut_checklist_initial_assimilation(
            proposition=MagicMock(
                comptabilite=MagicMock(
                    type_situation_assimilation=(
                        TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE
                    )
                )
            ),
            identification_dto=MagicMock(pays_nationalite_europeen=False),
            candidat_est_en_poursuite_directe=True,
            assimilation_passee=MagicMock(source=Assimilation.Source.OSIS),
        )

        self.assertEqual(statut_checklist.statut, ChoixStatutChecklist.GEST_REUSSITE)
        self.assertEqual(statut_checklist.libelle, 'Validated')

        # > avec assimilation passée incomplète
        statut_checklist = Checklist._recuperer_statut_checklist_initial_assimilation(
            proposition=MagicMock(
                comptabilite=MagicMock(
                    type_situation_assimilation=(
                        TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE
                    )
                )
            ),
            identification_dto=MagicMock(pays_nationalite_europeen=False),
            candidat_est_en_poursuite_directe=True,
            assimilation_passee=MagicMock(source=Assimilation.Source.EPC),
        )

        self.assertEqual(statut_checklist.statut, ChoixStatutChecklist.INITIAL_CANDIDAT)
        self.assertEqual(statut_checklist.libelle, 'Declared assimilated')

        # > sans assimilation passée et déclaré non assimilé
        statut_checklist = Checklist._recuperer_statut_checklist_initial_assimilation(
            proposition=MagicMock(
                comptabilite=MagicMock(type_situation_assimilation=TypeSituationAssimilation.AUCUNE_ASSIMILATION)
            ),
            identification_dto=MagicMock(pays_nationalite_europeen=False),
            candidat_est_en_poursuite_directe=True,
            assimilation_passee=None,
        )

        self.assertEqual(statut_checklist.statut, ChoixStatutChecklist.GEST_REUSSITE)
        self.assertEqual(statut_checklist.libelle, 'Validated')

        # > sans assimilation passée et déclaré assimilé
        statut_checklist = Checklist._recuperer_statut_checklist_initial_assimilation(
            proposition=MagicMock(
                comptabilite=MagicMock(
                    type_situation_assimilation=(
                        TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE
                    )
                )
            ),
            identification_dto=MagicMock(pays_nationalite_europeen=False),
            candidat_est_en_poursuite_directe=True,
            assimilation_passee=None,
        )

        self.assertEqual(statut_checklist.statut, ChoixStatutChecklist.INITIAL_CANDIDAT)
        self.assertEqual(statut_checklist.libelle, 'Declared assimilated')

        # > sans assimilation passée et sans nouvelle déclaration
        statut_checklist = Checklist._recuperer_statut_checklist_initial_assimilation(
            proposition=MagicMock(comptabilite=MagicMock(type_situation_assimilation=None)),
            identification_dto=MagicMock(pays_nationalite_europeen=False),
            candidat_est_en_poursuite_directe=True,
            assimilation_passee=None,
        )

        self.assertEqual(statut_checklist.statut, ChoixStatutChecklist.INITIAL_CANDIDAT)
        self.assertEqual(statut_checklist.libelle, 'Declared not assimilated')

    def test_initialisation_checklist_specificites_formation_avec_aucune_reponse(self):
        question_specifique_translator = QuestionSpecifiqueInMemoryTranslator()

        statut_suffisant = StatutChecklist(
            libelle="Sufficient",
            statut=ChoixStatutChecklist.GEST_REUSSITE,
        )

        statut_checklist = Checklist._recuperer_statut_checklist_initial_specificites_formation(
            proposition=MagicMock(
                documents_additionnels=[],
            ),
            identification_dto=MagicMock(est_concerne_par_visa=False),
            questions_specifiques_translator=question_specifique_translator,
            experiences_academiques=[],
            formation=MagicMock(type=TrainingType.BACHELOR.name),
            candidat_est_inscrit_recemment_ucl=False,
        )

        self.assertEqual(statut_checklist, statut_suffisant)

    def test_initialisation_checklist_specificites_formation_avec_documents_additionnels(self):
        question_specifique_translator = QuestionSpecifiqueInMemoryTranslator()

        statut_a_traiter = StatutChecklist(
            libelle="To be processed",
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
        )

        statut_checklist = Checklist._recuperer_statut_checklist_initial_specificites_formation(
            proposition=MagicMock(
                documents_additionnels=[uuid.uuid4()],
            ),
            identification_dto=MagicMock(est_concerne_par_visa=False),
            questions_specifiques_translator=question_specifique_translator,
            experiences_academiques=[],
            formation=MagicMock(type=TrainingType.BACHELOR.name),
            candidat_est_inscrit_recemment_ucl=False,
        )

        self.assertEqual(statut_checklist, statut_a_traiter)

    def test_initialisation_checklist_specificites_formation_avec_visa(self):
        question_specifique_translator = QuestionSpecifiqueInMemoryTranslator()

        statut_suffisant = StatutChecklist(
            libelle="Sufficient",
            statut=ChoixStatutChecklist.GEST_REUSSITE,
        )
        statut_a_traiter = StatutChecklist(
            libelle="To be processed",
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
        )

        statut_checklist = Checklist._recuperer_statut_checklist_initial_specificites_formation(
            proposition=MagicMock(
                documents_additionnels=[],
            ),
            identification_dto=MagicMock(est_concerne_par_visa=True),
            questions_specifiques_translator=question_specifique_translator,
            experiences_academiques=[],
            formation=MagicMock(type=TrainingType.BACHELOR.name),
            candidat_est_inscrit_recemment_ucl=False,
        )

        self.assertEqual(statut_checklist, statut_a_traiter)

        statut_checklist = Checklist._recuperer_statut_checklist_initial_specificites_formation(
            proposition=MagicMock(
                documents_additionnels=[],
            ),
            identification_dto=MagicMock(est_concerne_par_visa=True),
            questions_specifiques_translator=question_specifique_translator,
            experiences_academiques=[],
            formation=MagicMock(type=TrainingType.BACHELOR.name),
            candidat_est_inscrit_recemment_ucl=True,
        )

        self.assertEqual(statut_checklist, statut_suffisant)

    def test_initialisation_checklist_specificites_formation_avec_bama_15(self):
        question_specifique_translator = QuestionSpecifiqueInMemoryTranslator()

        statut_suffisant = StatutChecklist(
            libelle="Sufficient",
            statut=ChoixStatutChecklist.GEST_REUSSITE,
        )
        statut_a_traiter = StatutChecklist(
            libelle="To be processed",
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
        )

        statut_checklist = Checklist._recuperer_statut_checklist_initial_specificites_formation(
            proposition=MagicMock(
                documents_additionnels=[],
                annee_calculee=2026,
            ),
            identification_dto=MagicMock(est_concerne_par_visa=False),
            questions_specifiques_translator=question_specifique_translator,
            experiences_academiques=[
                MagicMock(
                    cycle_formation=Cycle.FIRST_CYCLE.name,
                    communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
                    a_obtenu_diplome=False,
                    formation_non_selectionnee_dans_liste_de_reference=False,
                    annees=[MagicMock(annee=2025)],
                )
            ],
            formation=MagicMock(type=TrainingType.MASTER_M1.name),
            candidat_est_inscrit_recemment_ucl=False,
        )

        self.assertEqual(statut_checklist, statut_a_traiter)

        statut_checklist = Checklist._recuperer_statut_checklist_initial_specificites_formation(
            proposition=MagicMock(
                documents_additionnels=[],
                annee_calculee=2026,
            ),
            identification_dto=MagicMock(est_concerne_par_visa=False),
            questions_specifiques_translator=question_specifique_translator,
            experiences_academiques=[
                MagicMock(
                    cycle_formation=Cycle.FIRST_CYCLE.name,
                    communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
                    a_obtenu_diplome=False,
                    formation_non_selectionnee_dans_liste_de_reference=False,
                    annees=[MagicMock(annee=2025)],
                )
            ],
            formation=MagicMock(type=TrainingType.MASTER_M1.name),
            candidat_est_inscrit_recemment_ucl=True,
        )

        self.assertEqual(statut_checklist, statut_suffisant)

    def test_initialisation_checklist_specificites_formation_avec_questions_specifiques(self):
        question_specifique_translator = QuestionSpecifiqueInMemoryTranslator()

        statut_suffisant = StatutChecklist(
            libelle="Sufficient",
            statut=ChoixStatutChecklist.GEST_REUSSITE,
        )
        statut_a_traiter = StatutChecklist(
            libelle="To be processed",
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
        )

        # Questions spécifiques
        with mock.patch.object(
            question_specifique_translator,
            'search_dto_by_proposition',
            return_value=[MagicMock(requis=True, valeur='ABC')],
        ):
            statut_checklist = Checklist._recuperer_statut_checklist_initial_specificites_formation(
                proposition=MagicMock(
                    documents_additionnels=[],
                ),
                identification_dto=MagicMock(est_concerne_par_visa=False),
                questions_specifiques_translator=question_specifique_translator,
                experiences_academiques=[],
                formation=MagicMock(type=TrainingType.BACHELOR.name),
                candidat_est_inscrit_recemment_ucl=False,
            )

            self.assertEqual(statut_checklist, statut_a_traiter)

        with mock.patch.object(
            question_specifique_translator,
            'search_dto_by_proposition',
            return_value=[MagicMock(requis=False, valeur='ABC')],
        ):
            statut_checklist = Checklist._recuperer_statut_checklist_initial_specificites_formation(
                proposition=MagicMock(
                    documents_additionnels=[],
                ),
                identification_dto=MagicMock(est_concerne_par_visa=False),
                questions_specifiques_translator=question_specifique_translator,
                experiences_academiques=[],
                formation=MagicMock(type=TrainingType.BACHELOR.name),
                candidat_est_inscrit_recemment_ucl=False,
            )

            self.assertEqual(statut_checklist, statut_a_traiter)

        with mock.patch.object(
            question_specifique_translator,
            'search_dto_by_proposition',
            return_value=[MagicMock(requis=False, valeur='')],
        ):
            statut_checklist = Checklist._recuperer_statut_checklist_initial_specificites_formation(
                proposition=MagicMock(
                    documents_additionnels=[],
                ),
                identification_dto=MagicMock(est_concerne_par_visa=False),
                questions_specifiques_translator=question_specifique_translator,
                experiences_academiques=[],
                formation=MagicMock(type=TrainingType.BACHELOR.name),
                candidat_est_inscrit_recemment_ucl=False,
            )

            self.assertEqual(statut_checklist, statut_suffisant)
