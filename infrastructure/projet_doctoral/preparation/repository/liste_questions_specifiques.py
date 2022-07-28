##############################################################################
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
##############################################################################
from django.db.models import QuerySet

from admission.contrib.models import AdmissionFormItem
from admission.ddd.projet_doctoral.preparation.domain.model._enums import TypeItemFormulaire
from admission.ddd.projet_doctoral.preparation.domain.model.question_specifique import (
    ListeDesQuestionsSpecifiquesDeLaFormation,
    ListeDesQuestionsSpecifiquesDeLaFormationIdentity,
    QuestionSpecifique,
    QuestionSpecifiqueIdentity,
)
from admission.ddd.projet_doctoral.preparation.repository.i_liste_questions_specifiques import (
    IListeQuestionsSpecifiquesRepository,
)


class ListeQuestionsSpecifiquesRepository(IListeQuestionsSpecifiquesRepository):
    @classmethod
    def get(
        cls,
        entity_id: 'ListeDesQuestionsSpecifiquesDeLaFormationIdentity',
    ) -> 'ListeDesQuestionsSpecifiquesDeLaFormation':
        form_items: QuerySet[AdmissionFormItem] = AdmissionFormItem.objects.filter(
            education__acronym=entity_id.sigle,
            education__academic_year__year=entity_id.annee,
        ).exclude(deleted=True)

        return ListeDesQuestionsSpecifiquesDeLaFormation(
            entity_id=entity_id,
            questions=[
                QuestionSpecifique(
                    entity_id=QuestionSpecifiqueIdentity(uuid=item.uuid),
                    type=TypeItemFormulaire.get_value(item.type),
                    poids=item.weight,
                    supprimee=item.deleted,
                    label_interne=item.internal_label,
                    requis=item.required,
                    titre=item.title,
                    texte=item.text,
                    texte_aide=item.help_text,
                    configuration=item.config,
                )
                for item in form_items
            ]
            if form_items
            else [],
        )
