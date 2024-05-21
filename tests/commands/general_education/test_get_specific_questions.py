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

import uuid
from typing import List
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import translation

from admission.contrib.models import GeneralEducationAdmission
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.enums import CritereItemFormulaireFormation, Onglets, TypeItemFormulaire
from admission.ddd.admission.formation_generale.commands import RecupererQuestionsSpecifiquesQuery
from admission.tests.factories.form_item import (
    AdmissionFormItemInstantiationFactory,
    MessageAdmissionFormItemFactory,
    TextAdmissionFormItemFactory,
    DocumentAdmissionFormItemFactory,
    RadioButtonSelectionAdmissionFormItemFactory,
    CheckboxSelectionAdmissionFormItemFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from infrastructure.messages_bus import message_bus_instance


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/', LANGUAGE_CODE='en')
class GetSpecificQuestionsTestCase(TestCase):
    def setUp(self) -> None:
        school = EntityFactory()
        EntityVersionFactory(entity=school, acronym='SCH')

        self.admission: GeneralEducationAdmission = GeneralEducationAdmissionFactory(
            training__management_entity=school,
            erasmus_mundus_scholarship=None,
            double_degree_scholarship=None,
            international_scholarship=None,
            candidate__private_email='john.doe@example.com',
            candidate__language=settings.LANGUAGE_CODE_EN,
        )

        related_admission_questions_args = {
            'academic_year': self.admission.training.academic_year,
            'display_according_education': CritereItemFormulaireFormation.UNE_FORMATION.name,
            'education_group': self.admission.training.education_group,
            'tab': Onglets.CHOIX_FORMATION.name,
        }

        self.questions_configurations = [
            AdmissionFormItemInstantiationFactory(
                form_item=MessageAdmissionFormItemFactory(),
                **related_admission_questions_args,
                weight=1,
            ),
            AdmissionFormItemInstantiationFactory(
                form_item=TextAdmissionFormItemFactory(),
                **related_admission_questions_args,
                weight=2,
            ),
            AdmissionFormItemInstantiationFactory(
                form_item=DocumentAdmissionFormItemFactory(),
                **related_admission_questions_args,
                weight=3,
            ),
            AdmissionFormItemInstantiationFactory(
                form_item=RadioButtonSelectionAdmissionFormItemFactory(),
                **related_admission_questions_args,
                weight=5,
            ),
            AdmissionFormItemInstantiationFactory(
                form_item=CheckboxSelectionAdmissionFormItemFactory(),
                **related_admission_questions_args,
                weight=4,
            ),
        ]

        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document.api.utils.get_remote_metadata", return_value={"name": "myfile", "size": 1})
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.confirm_remote_upload",
            side_effect=lambda token, *args, **kwargs: token,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "osis_document.contrib.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.document_uuid = uuid.uuid4()

    def test_get_specific_questions_with_answers(self):
        self.admission.specific_question_answers = {
            str(self.questions_configurations[1].form_item.uuid): 'My answer',
            str(self.questions_configurations[2].form_item.uuid): [str(self.document_uuid), 'other-token'],
            str(self.questions_configurations[3].form_item.uuid): '1',
            str(self.questions_configurations[4].form_item.uuid): ['1', '2'],
        }
        self.admission.save()

        with translation.override(settings.LANGUAGE_CODE_FR):
            specific_questions: List[QuestionSpecifiqueDTO] = message_bus_instance.invoke(
                RecupererQuestionsSpecifiquesQuery(uuid_proposition=str(self.admission.uuid)),
            )

        # Check that all questions are returned in the right order
        self.assertEqual(len(specific_questions), 5)

        message_field, text_field, document_field, multiple_selection_field, selection_field = specific_questions

        self.assertEqual(message_field.uuid, str(self.questions_configurations[0].form_item.uuid))
        self.assertEqual(text_field.uuid, str(self.questions_configurations[1].form_item.uuid))
        self.assertEqual(document_field.uuid, str(self.questions_configurations[2].form_item.uuid))
        self.assertEqual(multiple_selection_field.uuid, str(self.questions_configurations[4].form_item.uuid))
        self.assertEqual(selection_field.uuid, str(self.questions_configurations[3].form_item.uuid))

        # Check properties for a message field
        self.assertEqual(message_field.type, TypeItemFormulaire.MESSAGE.name)
        self.assertEqual(message_field.requis, False)
        self.assertEqual(message_field.configuration, {})
        self.assertEqual(message_field.onglet, Onglets.CHOIX_FORMATION.name)
        self.assertEqual(message_field.label, '')
        self.assertEqual(message_field.label_langue_candidat, '')
        self.assertEqual(message_field.valeur_formatee, 'Mon très court message.')
        self.assertEqual(message_field.texte, 'Mon très court message.')
        self.assertEqual(message_field.texte_aide, '')
        self.assertEqual(message_field.valeur, None)

        # Check properties for a text field
        self.assertEqual(text_field.type, TypeItemFormulaire.TEXTE.name)
        self.assertEqual(text_field.requis, False)
        self.assertEqual(text_field.configuration, {})
        self.assertEqual(text_field.onglet, Onglets.CHOIX_FORMATION.name)
        self.assertEqual(text_field.label, 'Champ texte')
        self.assertEqual(text_field.label_langue_candidat, 'Text field')
        self.assertEqual(text_field.valeur_formatee, 'My answer')
        self.assertEqual(text_field.texte, 'Données détaillées.')
        self.assertEqual(text_field.texte_aide, 'Ecrivez ici')
        self.assertEqual(text_field.valeur, 'My answer')

        # Check properties for a document field
        self.assertEqual(document_field.type, TypeItemFormulaire.DOCUMENT.name)
        self.assertEqual(document_field.requis, False)
        self.assertEqual(document_field.configuration, {})
        self.assertEqual(document_field.onglet, Onglets.CHOIX_FORMATION.name)
        self.assertEqual(document_field.label, 'Champ document')
        self.assertEqual(document_field.label_langue_candidat, 'Document field')
        self.assertEqual(document_field.valeur_formatee, [self.document_uuid, 'other-token'])
        self.assertEqual(document_field.texte, 'Données détaillées.')
        self.assertEqual(document_field.texte_aide, '')
        self.assertEqual(document_field.valeur, [str(self.document_uuid), 'other-token'])

        # Check properties for a multiple selection field
        self.assertEqual(multiple_selection_field.type, TypeItemFormulaire.SELECTION.name)
        self.assertEqual(multiple_selection_field.requis, False)
        self.assertEqual(multiple_selection_field.configuration, {'TYPE_SELECTION': 'CASES_A_COCHER'})
        self.assertEqual(multiple_selection_field.onglet, Onglets.CHOIX_FORMATION.name)
        self.assertEqual(multiple_selection_field.label, 'Champ de sélection')
        self.assertEqual(multiple_selection_field.label_langue_candidat, 'Selection field')
        self.assertEqual(multiple_selection_field.valeur_formatee, 'Un, Deux')
        self.assertEqual(multiple_selection_field.texte, 'Données détaillées.')
        self.assertEqual(multiple_selection_field.texte_aide, '')
        self.assertEqual(multiple_selection_field.valeur, ['1', '2'])
        self.assertEqual(multiple_selection_field.valeurs_possibles, [('1', 'Un'), ('2', 'Deux'), ('3', 'Trois')])

        # Check properties for a selection field
        self.assertEqual(selection_field.type, TypeItemFormulaire.SELECTION.name)
        self.assertEqual(selection_field.requis, False)
        self.assertEqual(selection_field.configuration, {'TYPE_SELECTION': 'BOUTONS_RADIOS'})
        self.assertEqual(selection_field.onglet, Onglets.CHOIX_FORMATION.name)
        self.assertEqual(selection_field.label, 'Champ de sélection')
        self.assertEqual(selection_field.label_langue_candidat, 'Selection field')
        self.assertEqual(selection_field.valeur_formatee, 'Un')
        self.assertEqual(selection_field.texte, 'Données détaillées.')
        self.assertEqual(selection_field.texte_aide, '')
        self.assertEqual(selection_field.valeur, '1')
        self.assertEqual(selection_field.valeurs_possibles, [('1', 'Un'), ('2', 'Deux'), ('3', 'Trois')])

    def test_get_specific_questions_with_no_answer(self):
        specific_questions = message_bus_instance.invoke(
            RecupererQuestionsSpecifiquesQuery(uuid_proposition=str(self.admission.uuid)),
        )

        # Check values of all questions
        self.assertEqual(len(specific_questions), 5)

        message_field, text_field, document_field, multiple_selection_field, selection_field = specific_questions

        self.assertEqual(message_field.valeur_formatee, 'My very short message.')
        self.assertEqual(text_field.valeur_formatee, '')
        self.assertEqual(document_field.valeur_formatee, [])
        self.assertEqual(multiple_selection_field.valeur_formatee, '')
        self.assertEqual(selection_field.valeur_formatee, '')

    def test_get_specific_questions_of_a_specific_tab(self):
        self.questions_configurations[0].tab = Onglets.CURRICULUM.name
        self.questions_configurations[0].save()

        specific_questions = message_bus_instance.invoke(
            RecupererQuestionsSpecifiquesQuery(
                uuid_proposition=str(self.admission.uuid),
                onglets=[Onglets.CURRICULUM.name],
            ),
        )

        self.assertEqual(len(specific_questions), 1)
        self.assertEqual(specific_questions[0].uuid, str(self.questions_configurations[0].form_item.uuid))

    def test_get_specific_questions_of_a_specific_type(self):
        specific_questions = message_bus_instance.invoke(
            RecupererQuestionsSpecifiquesQuery(
                uuid_proposition=str(self.admission.uuid),
                type=TypeItemFormulaire.MESSAGE.name,
            ),
        )

        self.assertEqual(len(specific_questions), 1)
        self.assertEqual(specific_questions[0].uuid, str(self.questions_configurations[0].form_item.uuid))
