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
from unittest.mock import MagicMock

from django.test import TestCase

from admission.ddd.admission.enums.emplacement_document import StatutEmplacementDocument
from admission.infrastructure.admission.formation_generale.domain.service.notification import Notification
from admission.infrastructure.utils import get_requested_documents_html_lists


class GeneralNotificationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tab1_document_dto_1 = MagicMock(
            identifiant='11',
            onglet='tab1',
            nom_onglet_langue_candidat='Tab 1',
            libelle_langue_candidat='Document 11',
        )

        cls.tab1_document_dto_2 = MagicMock(
            identifiant='12',
            onglet='tab1',
            nom_onglet_langue_candidat='Tab 1',
            libelle_langue_candidat='Document 12',
        )

        cls.tab1_document_dto3 = MagicMock(
            identifiant='13',
            onglet='tab1',
            nom_onglet_langue_candidat='Tab 1',
            libelle_langue_candidat='Document 13',
        )

        cls.document_dto_2 = MagicMock(
            identifiant='2',
            onglet='tab2',
            nom_onglet_langue_candidat='Tab 2',
            libelle_langue_candidat='Document 2',
        )

        cls.document_dtos = [
            cls.tab1_document_dto_1,
            cls.tab1_document_dto_2,
            cls.tab1_document_dto3,
            cls.document_dto_2,
        ]

    def test_get_requested_documents_html_lists_with_no_requested_documents(self):
        lists = get_requested_documents_html_lists(
            requested_documents=[],
            requested_documents_dtos=[],
        )
        self.assertEqual(lists[StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION], '')
        self.assertEqual(lists[StatutEmplacementDocument.A_RECLAMER], '')

    def test_documents_with_only_submitted_documents(self):
        lists = get_requested_documents_html_lists(
            requested_documents=[
                MagicMock(
                    statut=StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION,
                    entity_id=MagicMock(identifiant=self.tab1_document_dto_1.identifiant),
                ),
                MagicMock(
                    statut=StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION,
                    entity_id=MagicMock(identifiant=self.tab1_document_dto_2.identifiant),
                ),
                MagicMock(
                    statut=StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION,
                    entity_id=MagicMock(identifiant=self.tab1_document_dto3.identifiant),
                ),
                MagicMock(
                    statut=StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION,
                    entity_id=MagicMock(identifiant=self.document_dto_2.identifiant),
                ),
            ],
            requested_documents_dtos=self.document_dtos,
        )

        self.assertEqual(lists[StatutEmplacementDocument.A_RECLAMER], '')

        self.assertEqual(
            lists[StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION],
            (
                '<ul>'
                f'<li>{self.tab1_document_dto_1.nom_onglet_langue_candidat}'
                '<ul>'
                f'<li>{self.tab1_document_dto_1.libelle_langue_candidat}</li>'
                f'<li>{self.tab1_document_dto_2.libelle_langue_candidat}</li>'
                f'<li>{self.tab1_document_dto3.libelle_langue_candidat}</li>'
                '</ul>'
                '</li>'
                f'<li>{self.document_dto_2.nom_onglet_langue_candidat}'
                '<ul>'
                f'<li>{self.document_dto_2.libelle_langue_candidat}</li>'
                '</ul>'
                '</li>'
                '</ul>'
            ),
        )

    def test_with_submitted_and_not_submitted_documents(self):
        lists = get_requested_documents_html_lists(
            requested_documents=[
                MagicMock(
                    statut=StatutEmplacementDocument.A_RECLAMER,
                    entity_id=MagicMock(identifiant=self.tab1_document_dto_1.identifiant),
                ),
                MagicMock(
                    statut=StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION,
                    entity_id=MagicMock(identifiant=self.tab1_document_dto_2.identifiant),
                ),
                MagicMock(
                    statut=StatutEmplacementDocument.A_RECLAMER,
                    entity_id=MagicMock(identifiant=self.tab1_document_dto3.identifiant),
                ),
                MagicMock(
                    statut=StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION,
                    entity_id=MagicMock(identifiant=self.document_dto_2.identifiant),
                ),
            ],
            requested_documents_dtos=self.document_dtos,
        )

        self.assertEqual(
            lists[StatutEmplacementDocument.A_RECLAMER],
            (
                '<ul>'
                f'<li>{self.tab1_document_dto_1.nom_onglet_langue_candidat}'
                '<ul>'
                f'<li>{self.tab1_document_dto_1.libelle_langue_candidat}</li>'
                f'<li>{self.tab1_document_dto3.libelle_langue_candidat}</li>'
                '</ul>'
                '</li>'
                '</ul>'
            ),
        )
        self.assertEqual(
            lists[StatutEmplacementDocument.COMPLETE_APRES_RECLAMATION],
            (
                '<ul>'
                f'<li>{self.tab1_document_dto_1.nom_onglet_langue_candidat}'
                '<ul>'
                f'<li>{self.tab1_document_dto_2.libelle_langue_candidat}</li>'
                '</ul>'
                '</li>'
                f'<li>{self.document_dto_2.nom_onglet_langue_candidat}'
                '<ul>'
                f'<li>{self.document_dto_2.libelle_langue_candidat}</li>'
                '</ul>'
                '</li>'
                '</ul>'
            ),
        )
