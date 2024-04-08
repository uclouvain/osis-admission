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
import datetime

from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.views.generic import FormView
from osis_comment.models import CommentEntry
from rest_framework import serializers, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
)
from admission.forms.admission.checklist import (
    CommentForm,
)
from admission.views.common.detail_tabs.comments import COMMENT_TAG_SIC, COMMENT_TAG_FAC
from admission.views.common.mixins import LoadDossierViewMixin, AdmissionFormMixin

__all__ = [
    'ChangeStatusView',
    'SaveCommentView',
]

__namespace__ = False


class ChangeStatusSerializer(serializers.Serializer):
    tab_name = serializers.CharField()
    status = serializers.ChoiceField(choices=ChoixStatutChecklist.choices(), required=False)
    extra = serializers.DictField(default={}, required=False)


def change_admission_status(tab, admission_status, extra, admission, author, replace_extra=False, global_status=None):
    """Change the status of the admission of a specific tab"""
    update_fields = ['checklist', 'last_update_author', 'modified_at']

    admission.last_update_author = author
    admission.modified_at = datetime.datetime.today()

    serializer = ChangeStatusSerializer(
        data={
            'tab_name': tab,
            'status': admission_status,
            'extra': extra,
        }
    )
    serializer.is_valid(raise_exception=True)

    if admission.checklist.get('current') is None:
        admission.checklist['current'] = {}

    admission.checklist['current'].setdefault(serializer.validated_data['tab_name'], {})
    tab_data = admission.checklist['current'][serializer.validated_data['tab_name']]
    tab_data['statut'] = serializer.validated_data['status']
    tab_data['libelle'] = ''
    tab_data.setdefault('extra', {})
    if replace_extra:
        tab_data['extra'] = serializer.validated_data['extra']
    else:
        tab_data['extra'].update(serializer.validated_data['extra'])

    if global_status is not None:
        admission.status = global_status
        update_fields.append('status')

    admission.save(update_fields=update_fields)

    return serializer.data


class ChangeStatusView(LoadDossierViewMixin, APIView):
    urlpatterns = {'change-checklist-status': 'change-checklist-status/<str:tab>/<str:status>'}
    permission_required = 'admission.change_checklist'
    parser_classes = [FormParser]
    authentication_classes = [SessionAuthentication]

    def post(self, request, *args, **kwargs):
        admission = self.get_permission_object()

        serializer_data = change_admission_status(
            tab=self.kwargs['tab'],
            admission_status=self.kwargs['status'],
            extra=request.data.dict(),
            admission=admission,
            author=self.request.user.person,
        )

        return Response(serializer_data, status=status.HTTP_200_OK)


class SaveCommentView(AdmissionFormMixin, FormView):
    urlpatterns = {'save-comment': 'save-comment/<str:tab>'}
    form_class = CommentForm
    template_name = 'admission/forms/default_form.html'

    def get_permission_required(self):
        if f'__{COMMENT_TAG_FAC}' in self.kwargs['tab']:
            self.permission_required = 'admission.checklist_change_fac_comment'
        elif f'__{COMMENT_TAG_SIC}' in self.kwargs['tab']:
            self.permission_required = 'admission.checklist_change_sic_comment'
        elif '__authentication' in self.kwargs['tab']:
            self.permission_required = 'admission.checklist_change_past_experiences'
        else:
            self.permission_required = 'admission.checklist_change_comment'
        return super().get_permission_required()

    @cached_property
    def form_url(self):
        return resolve_url(
            f'{self.base_namespace}:save-comment',
            uuid=self.admission_uuid,
            tab=self.kwargs['tab'],
        )

    def get_prefix(self):
        return self.kwargs['tab']

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['form_url'] = self.form_url
        return form_kwargs

    def form_valid(self, form):
        comment, _ = CommentEntry.objects.update_or_create(
            object_uuid=self.admission_uuid,
            tags=self.kwargs['tab'].split('__'),
            defaults={
                'content': form.cleaned_data['comment'],
                'author': self.request.user.person,
            },

        )
        return super().form_valid(CommentForm(comment=comment, **self.get_form_kwargs()))
