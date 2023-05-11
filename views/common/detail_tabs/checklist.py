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
from typing import Dict, Set

from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from osis_comment.models import CommentEntry
from rest_framework import serializers, status
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from admission.ddd.admission.dtos.resume import ResumePropositionDTO, ResumeEtEmplacementsDocumentsPropositionDTO
from admission.ddd.admission.enums import OngletsDemande
from admission.ddd.admission.enums.emplacement_document import DocumentsAssimilation
from admission.ddd.admission.formation_generale.commands import (
    RecupererResumePropositionQuery,
    RecupererResumeEtEmplacementsDocumentsNonLibresPropositionQuery,
)
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutChecklist
from admission.forms.admission.checklist import CommentForm, AssimilationForm
from admission.infrastructure.admission.domain.service.emplacements_documents_proposition import (
    EmplacementsDocumentsPropositionTranslator,
)
from admission.views.doctorate.mixins import LoadDossierViewMixin
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import PersonneConnueUclTranslator

__all__ = [
    'ChecklistView',
    'ChangeStatusView',
    'ChangeExtraView',
    'SaveCommentView',
]


__namespace__ = False


class ChecklistView(LoadDossierViewMixin, TemplateView):
    urlpatterns = 'checklist'
    template_name = "admission/general_education/checklist.html"
    permission_required = 'admission.view_checklist'
    extra_context = {
        'checklist_tabs': {
            'assimilation': _("Assimilation"),
            'financabilite': _("Financeability"),
            'frais_dossier': _("Application fees"),
            'choix_formation': _("Training choice"),
            'parcours_anterieur': _("Previous experience"),
            'donnees_personnelles': _("Personal data"),
            'specificites_formation': _("Training specificities"),
        },
        'hide_files': True,
    }

    @classmethod
    def checklist_documents_by_tab(cls) -> Dict[str, Set[str]]:
        assimilation_documents = {
            'CARTE_IDENTITE',
            'PASSEPORT',
        }

        for document in DocumentsAssimilation:
            assimilation_documents.add(document)

        return {
            'assimilation': assimilation_documents,
            'financabilite': {},
            'frais_dossier': assimilation_documents,
            'choix_formation': {},
            'parcours_anterieur': {},
            'donnees_personnelles': assimilation_documents,
            'specificites_formation': {},
        }

    def get_template_names(self):
        if self.request.htmx:
            return ["admission/general_education/checklist_menu.html"]
        return ["admission/general_education/checklist.html"]

    def get_context_data(self, **kwargs):
        from infrastructure.messages_bus import message_bus_instance

        context = super().get_context_data(**kwargs)
        if not self.request.htmx:
            command_result: ResumeEtEmplacementsDocumentsPropositionDTO = message_bus_instance.invoke(
                RecupererResumeEtEmplacementsDocumentsNonLibresPropositionQuery(uuid_proposition=self.admission_uuid),
            )

            context['resume_proposition'] = command_result.resume

            tab_names = list(self.extra_context['checklist_tabs'].keys())
            comments = {
                c.tags[0]: c
                for c in CommentEntry.objects.filter(object_uuid=self.admission_uuid, tags__contained_by=tab_names)
            }
            context['comment_forms'] = {
                tab_name: CommentForm(
                    prefix=tab_name,
                    comment=comments.get(tab_name, None),
                )
                for tab_name in tab_names
            }
            context['assimilation_form'] = AssimilationForm(
                initial=self.admission.checklist.get('current', {}).get('assimilation', {}).get('extra'),
            )

            admission_documents = command_result.emplacements_documents

            context['documents'] = {
                tab_name: [
                    admission_document
                    for admission_document in admission_documents
                    if admission_document.identifiant.split('.')[-1] in tab_documents
                ]
                for tab_name, tab_documents in self.checklist_documents_by_tab().items()
            }
        return context


class ChangeStatusSerializer(serializers.Serializer):
    tab_name = serializers.CharField()
    status = serializers.ChoiceField(choices=ChoixStatutChecklist.choices(), required=False)
    extra = serializers.JSONField(default={}, required=False, binary=True)


class ChangeStatusView(LoadDossierViewMixin, APIView):
    urlpatterns = 'change-checklist-status'
    permission_required = 'admission.view_checklist'
    parser_classes = [FormParser]

    def post(self, request, *args, **kwargs):
        serializer = ChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admission = self.get_permission_object()
        if admission.checklist['current'] is None:
            admission.checklist['current'] = {}
        admission.checklist['current'][serializer.validated_data['tab_name']] = {
            'statut': serializer.validated_data['status'],
            **serializer.validated_data['extra'],
        }
        admission.save(update_fields=['checklist'])
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangeExtraSerializer(serializers.Serializer):
    tab_name = serializers.CharField()
    extra = serializers.JSONField(default={}, required=False, binary=True)


class ChangeExtraView(LoadDossierViewMixin, APIView):
    urlpatterns = 'change-checklist-extra'
    permission_required = 'admission.view_checklist'
    parser_classes = [FormParser]

    def post(self, request, *args, **kwargs):
        serializer = ChangeExtraSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admission = self.get_permission_object()
        tab_name = serializer.validated_data['tab_name']
        if admission.checklist['current'] is None:
            admission.checklist['current'] = {}
        admission.checklist['current'].setdefault(tab_name, {'extra': {}})
        admission.checklist['current'][tab_name].setdefault('extra', {})
        admission.checklist['current'][tab_name]['extra'].update(serializer.validated_data['extra'])
        admission.save(update_fields=['checklist'])
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentSerializer(serializers.Serializer):
    tab_name = serializers.CharField()
    comment = serializers.CharField(allow_blank=True)


class SaveCommentView(LoadDossierViewMixin, APIView):
    urlpatterns = 'save-comment'
    permission_required = 'admission.view_checklist'
    parser_classes = [FormParser]

    def post(self, request, *args, **kwargs):
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        CommentEntry.objects.update_or_create(
            object_uuid=self.admission_uuid,
            tags=[serializer.validated_data['tab_name']],
            defaults={
                'content': serializer.validated_data['comment'],
                'author': self.request.user.person,
            },
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
