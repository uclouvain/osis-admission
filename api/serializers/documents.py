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
from django.conf import settings
from rest_framework import serializers

from admission.constants import SUPPORTED_MIME_TYPES
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums import TypeItemFormulaire, CleConfigurationItemFormulaire
from admission.ddd.admission.enums.emplacement_document import StatutReclamationEmplacementDocument
from admission.ddd.admission.formation_generale.commands import CompleterEmplacementsDocumentsParCandidatCommand
from admission.infrastructure.utils import get_document_from_identifier
from base.utils.serializers import DTOSerializer

__all__ = [
    'DocumentSpecificQuestionSerializer',
    'CompleterEmplacementsDocumentsParCandidatCommandSerializer',
    'DocumentSpecificQuestionsListSerializer',
]


class DocumentSpecificQuestionSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    type = serializers.CharField()
    title = serializers.JSONField()
    text = serializers.JSONField()
    help_text = serializers.JSONField()
    configuration = serializers.JSONField()
    values = serializers.ListField(child=serializers.JSONField())
    tab = serializers.CharField()
    tab_name = serializers.CharField()
    required = serializers.BooleanField()

    def to_representation(self, instance: EmplacementDocumentDTO):
        document = get_document_from_identifier(
            admission=self.context['admission'],
            document_identifier=instance.identifiant,
        )

        return {
            'uuid': instance.identifiant,
            'type': TypeItemFormulaire.DOCUMENT.name,
            'title': {
                settings.LANGUAGE_CODE_FR: instance.libelle_langue_candidat,
                settings.LANGUAGE_CODE_EN: instance.libelle_langue_candidat,
            },
            'text': {
                settings.LANGUAGE_CODE_FR: instance.justification_gestionnaire,
                settings.LANGUAGE_CODE_EN: instance.justification_gestionnaire,
            },
            'help_text': {},
            'configuration': {
                CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name: document.mimetypes,
                CleConfigurationItemFormulaire.NOMBRE_MAX_DOCUMENTS.name: document.max_documents_number,
            }
            if document
            else {
                CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name: list(SUPPORTED_MIME_TYPES),
            },
            'values': [],
            'tab': instance.onglet,
            'tab_name': instance.nom_onglet_langue_candidat,
            'required': instance.statut_reclamation == StatutReclamationEmplacementDocument.IMMEDIATEMENT.name,
        }


class DocumentSpecificQuestionsListSerializer(serializers.Serializer):
    immediate_requested_documents = DocumentSpecificQuestionSerializer(many=True)
    later_requested_documents = DocumentSpecificQuestionSerializer(many=True)
    deadline = serializers.DateField(allow_null=True)


class CompleterEmplacementsDocumentsParCandidatCommandSerializer(DTOSerializer):
    uuid_proposition = None
    reponses_documents_a_completer = serializers.JSONField()

    class Meta:
        source = CompleterEmplacementsDocumentsParCandidatCommand
