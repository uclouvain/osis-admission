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
import datetime
from typing import Dict, Set

from django import forms
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import resolve_url, redirect
from django.urls import reverse
from django.utils import translation
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, FormView
from osis_comment.models import CommentEntry
from osis_history.models import HistoryEntry
from osis_mail_template.models import MailTemplate
from rest_framework import serializers, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from admission.ddd import MONTANT_FRAIS_DOSSIER
from admission.ddd.admission.dtos.resume import ResumeEtEmplacementsDocumentsPropositionDTO
from admission.ddd.admission.enums import Onglets, TypeItemFormulaire
from admission.ddd.admission.enums.emplacement_document import DocumentsAssimilation
from admission.ddd.admission.formation_generale.commands import (
    RecupererResumeEtEmplacementsDocumentsNonLibresPropositionQuery,
    ModifierChecklistChoixFormationCommand,
    SpecifierPaiementNecessaireCommand,
    EnvoyerRappelPaiementCommand,
    SpecifierPaiementPlusNecessaireCommand,
    RecupererQuestionsSpecifiquesQuery,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
)
from admission.forms.admission.checklist import CommentForm, AssimilationForm, ChoixFormationForm
from admission.mail_templates import ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL
from admission.utils import (
    add_messages_into_htmx_response,
    get_portal_admission_list_url,
    get_backoffice_admission_url,
    get_portal_admission_url,
)
from admission.views.doctorate.mixins import LoadDossierViewMixin, AdmissionFormMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance
from osis_common.ddd.interface import BusinessException
from osis_common.utils.htmx import HtmxMixin

__all__ = [
    'ChecklistView',
    'ChangeStatusView',
    'ChangeExtraView',
    'SaveCommentView',
    'ApplicationFeesView',
    'ChoixFormationFormView',
    'ChoixFormationDetailView',
]


__namespace__ = False


class RequestApplicationFeesContextDataMixin(LoadDossierViewMixin):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['last_request'] = (
            HistoryEntry.objects.filter(
                object_uuid=self.admission_uuid,
                tags__contains=['proposition', 'application-fees-payment', 'request'],
            )
            .order_by('-created')
            .first()
        )

        context['application_fees_amount'] = MONTANT_FRAIS_DOSSIER

        # Checklist specificities
        context['fees_already_payed'] = bool(
            self.admission.checklist.get('current')
            and self.admission.checklist['current']['frais_dossier']['statut']
            == ChoixStatutChecklist.SYST_REUSSITE.name
        )

        # Get the email to submit
        mail_template = MailTemplate.objects.get(
            identifier=ADMISSION_EMAIL_REQUEST_APPLICATION_FEES_GENERAL,
            language=self.admission.candidate.language,
        )

        proposition = self.proposition

        # Needed to get the complete reference
        with translation.override(proposition.langue_contact_candidat):
            tokens = {
                'admission_reference': proposition.reference,
                'candidate_first_name': proposition.prenom_candidat,
                'candidate_last_name': proposition.nom_candidat,
                'training_title': {
                    settings.LANGUAGE_CODE_FR: self.admission.training.title,
                    settings.LANGUAGE_CODE_EN: self.admission.training.title_english,
                }[proposition.langue_contact_candidat],
                'admissions_link_front': get_portal_admission_list_url(),
                'admission_link_front': get_portal_admission_url('general-education', self.admission_uuid),
                'admission_link_back': get_backoffice_admission_url('general-education', self.admission_uuid),
            }

            context['request_message_subject'] = mail_template.render_subject(tokens)
            context['request_message_body'] = mail_template.body_as_html(tokens)

        return context


class ChecklistView(RequestApplicationFeesContextDataMixin, TemplateView):
    urlpatterns = 'checklist'
    template_name = "admission/general_education/checklist.html"
    permission_required = 'admission.view_checklist'

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
            'financabilite': set(),
            'frais_dossier': assimilation_documents,
            'choix_formation': {
                'ATTESTATION_INSCRIPTION_REGULIERE',
                'FORMULAIRE_MODIFICATION_INSCRIPTION',
            },
            'parcours_anterieur': set(),
            'donnees_personnelles': assimilation_documents,
            'specificites_formation': set(),
        }

    def get_template_names(self):
        if self.request.htmx:
            return ["admission/general_education/checklist_menu.html"]
        return ["admission/general_education/checklist.html"]

    def get_context_data(self, **kwargs):
        from infrastructure.messages_bus import message_bus_instance

        context = super().get_context_data(**kwargs)
        if not self.request.htmx:
            # Retrieve data related to the proposition
            command_result: ResumeEtEmplacementsDocumentsPropositionDTO = message_bus_instance.invoke(
                RecupererResumeEtEmplacementsDocumentsNonLibresPropositionQuery(uuid_proposition=self.admission_uuid),
            )

            context['resume_proposition'] = command_result.resume

            context['questions_specifiques'] = message_bus_instance.invoke(
                RecupererQuestionsSpecifiquesQuery(
                    uuid_proposition=self.admission_uuid,
                    onglets=[Onglets.INFORMATIONS_ADDITIONNELLES.name],
                )
            )

            # Initialize forms
            tab_names = list(self.extra_context['checklist_tabs'].keys())
            comments = {
                c.tags[0]: c
                for c in CommentEntry.objects.filter(object_uuid=self.admission_uuid, tags__contained_by=tab_names)
            }

            context['comment_forms'] = {
                tab_name: CommentForm(
                    comment=comments.get(tab_name, None),
                    form_url=resolve_url(f'{self.base_namespace}:save-comment', uuid=self.admission_uuid, tab=tab_name),
                )
                for tab_name in tab_names
            }
            context['assimilation_form'] = AssimilationForm(
                initial=self.admission.checklist.get('current', {}).get('assimilation', {}).get('extra'),
                form_url=resolve_url(
                    f'{self.base_namespace}:change-checklist-extra',
                    uuid=self.admission_uuid,
                    tab='assimilation',
                ),
            )

            # Documents
            admission_documents = command_result.emplacements_documents
            question_specifiques_documents_uuids = [
                valeur
                for question in context['questions_specifiques']
                for valeur in (question.valeur if question.valeur else [])
                if question.type == TypeItemFormulaire.DOCUMENT.name
            ]

            context['documents'] = {
                tab_name: [
                    admission_document
                    for admission_document in admission_documents
                    if admission_document.identifiant.split('.')[-1] in tab_documents
                ]
                for tab_name, tab_documents in self.checklist_documents_by_tab().items()
            }
            context['documents']['specificites_formation'] += [
                document
                for document_uuid in question_specifiques_documents_uuids
                for document in admission_documents
                if document_uuid in document.document_uuids
            ]

            # Experiences
            context['experiences'] = self._get_experiences(command_result.resume)

        return context

    def _get_experiences(self, resume):
        experiences = {}

        for experience_academique in resume.curriculum.experiences_academiques:
            for annee_academique in experience_academique.annees:
                experiences.setdefault(annee_academique.annee, [])
                if experience_academique.a_obtenu_diplome:
                    experiences[annee_academique.annee].insert(0, experience_academique)
                else:
                    experiences[annee_academique.annee].append(experience_academique)

        experiences_non_academiques = {}
        for experience_non_academique in resume.curriculum.experiences_non_academiques:
            date_courante = experience_non_academique.date_debut
            while True:
                annee = date_courante.year if date_courante.month >= 9 else date_courante.year - 1
                if experience_non_academique not in experiences_non_academiques.get(annee, []):
                    experiences_non_academiques.setdefault(annee, []).append(experience_non_academique)
                if date_courante == experience_non_academique.date_fin:
                    break
                date_courante = min(
                    date_courante.replace(year=date_courante.year + 1), experience_non_academique.date_fin
                )
        for annee, experiences_annee in experiences_non_academiques.items():
            experiences_annee.sort(key=lambda x: x.date_fin, reverse=True)
            experiences.setdefault(annee, []).extend(experiences_annee)

        etudes_secondaires = resume.etudes_secondaires
        if etudes_secondaires and etudes_secondaires.annee_diplome_etudes_secondaires:
            experiences.setdefault(etudes_secondaires.annee_diplome_etudes_secondaires, []).append(etudes_secondaires)

        experiences = {annee: experiences[annee] for annee in sorted(experiences.keys(), reverse=True)}

        return experiences


class ChangeStatusSerializer(serializers.Serializer):
    tab_name = serializers.CharField()
    status = serializers.ChoiceField(choices=ChoixStatutChecklist.choices(), required=False)
    extra = serializers.DictField(default={}, required=False)


class ApplicationFeesView(
    RequestApplicationFeesContextDataMixin,
    HtmxPermissionRequiredMixin,
    HtmxMixin,
    FormView,
):
    name = 'application-fees'
    urlpatterns = {'application-fees': 'application-fees/<str:status>'}
    permission_required = 'admission.view_checklist'
    template_name = 'admission/general_education/includes/checklist/application_fees_request.html'
    htmx_template_name = 'admission/general_education/includes/checklist/application_fees_request.html'
    cmd = SpecifierPaiementNecessaireCommand
    form_class = forms.Form

    def post(self, request, *args, **kwargs):
        current_status = self.kwargs.get('status')
        remind = self.request.GET.get('remind')

        if current_status == ChoixStatutChecklist.GEST_BLOCAGE.name:
            if remind:
                cmd = EnvoyerRappelPaiementCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
            else:
                cmd = SpecifierPaiementNecessaireCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                )
        else:
            cmd = SpecifierPaiementPlusNecessaireCommand(
                uuid_proposition=self.admission_uuid,
                gestionnaire=self.request.user.person.global_id,
                statut_checklist_frais_dossier=self.kwargs['status'],
            )

        has_error = False
        try:
            message_bus_instance.invoke(cmd)
        except BusinessException as exception:
            has_error = True
            messages.error(request, exception.message)

        response = self.get(request, *args, **kwargs)

        if has_error:
            response.status_code = HTTP_400_BAD_REQUEST
            add_messages_into_htmx_response(request=request, response=response)

        return response


class ChangeStatusView(LoadDossierViewMixin, APIView):
    urlpatterns = {'change-checklist-status': 'change-checklist-status/<str:tab>/<str:status>'}
    permission_required = 'admission.view_checklist'
    parser_classes = [FormParser]
    authentication_classes = [SessionAuthentication]

    def post(self, request, *args, **kwargs):
        serializer = ChangeStatusSerializer(
            data={
                'tab_name': self.kwargs['tab'],
                'status': self.kwargs['status'],
                'extra': request.data.dict(),
            }
        )
        serializer.is_valid(raise_exception=True)

        admission = self.get_permission_object()

        if admission.checklist.get('current') is None:
            admission.checklist['current'] = {}

        admission.checklist['current'].setdefault(serializer.validated_data['tab_name'], {})
        tab_data = admission.checklist['current'][serializer.validated_data['tab_name']]
        tab_data['statut'] = serializer.validated_data['status']
        tab_data['libelle'] = ''
        tab_data.setdefault('extra', {})
        tab_data['extra'].update(serializer.validated_data['extra'])

        admission.save(update_fields=['checklist'])

        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangeExtraView(AdmissionFormMixin, FormView):
    urlpatterns = {'change-checklist-extra': 'change-checklist-extra/<str:tab>'}
    permission_required = 'admission.view_checklist'
    template_name = 'admission/forms/default_form.html'

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['form_url'] = resolve_url(
            f'{self.base_namespace}:change-checklist-extra',
            uuid=self.admission_uuid,
            tab=self.kwargs['tab'],
        )
        return form_kwargs

    def get_form_class(self):
        return {
            'assimilation': AssimilationForm,
        }[self.kwargs['tab']]

    def form_valid(self, form):
        admission = self.get_permission_object()
        tab_name = self.kwargs['tab']

        if admission.checklist.get('current') is None:
            admission.checklist['current'] = {}

        admission.checklist['current'].setdefault(tab_name, {})
        tab_data = admission.checklist['current'][tab_name]
        tab_data.setdefault('extra', {})
        tab_data['extra'].update(form.cleaned_data)
        admission.save(update_fields=['checklist'])
        return super().form_valid(form)


class SaveCommentView(AdmissionFormMixin, FormView):
    urlpatterns = {'save-comment': 'save-comment/<str:tab>'}
    permission_required = 'admission.view_checklist'
    form_class = CommentForm
    template_name = 'admission/forms/default_form.html'

    @cached_property
    def form_url(self):
        return resolve_url(
            f'{self.base_namespace}:save-comment',
            uuid=self.admission_uuid,
            tab=self.kwargs['tab'],
        )

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['form_url'] = self.form_url
        return form_kwargs

    def form_valid(self, form):
        comment, _ = CommentEntry.objects.update_or_create(
            object_uuid=self.admission_uuid,
            tags=[self.kwargs['tab']],
            defaults={
                'content': form.cleaned_data['comment'],
                'author': self.request.user.person,
            },
        )
        return super().form_valid(CommentForm(comment=comment, form_url=self.form_url))


class ChoixFormationFormView(LoadDossierViewMixin, FormView):
    urlpatterns = 'choix-formation-update'
    permission_required = 'admission.view_checklist'
    template_name = 'admission/general_education/checklist/choix_formation_form.html'
    form_class = ChoixFormationForm

    def dispatch(self, request, *args, **kwargs):
        if not request.htmx:
            return redirect(
                reverse('admission:general-education:checklist', kwargs={'uuid': self.admission_uuid})
                + '#choix_formation'
            )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['formation'] = self.proposition.formation
        return kwargs

    def get_initial(self):
        return {
            'type_demande': self.proposition.type,
            'annee_academique': self.proposition.annee_calculee,
            'formation': self.proposition.formation.sigle,
            'poursuite_cycle': self.proposition.poursuite_de_cycle,
        }

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                ModifierChecklistChoixFormationCommand(
                    uuid_proposition=str(self.kwargs['uuid']),
                    type_demande=form.cleaned_data['type_demande'],
                    sigle_formation=form.cleaned_data['formation'],
                    annee_formation=form.cleaned_data['annee_academique'],
                    poursuite_de_cycle=form.cleaned_data['poursuite_cycle'],
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                form.add_error(None, exception.message)
            return self.form_invalid(form)
        return HttpResponse(headers={'HX-Refresh': 'true'})


class ChoixFormationDetailView(LoadDossierViewMixin, TemplateView):
    urlpatterns = 'choix-formation-detail'
    permission_required = 'admission.view_checklist'
    template_name = 'admission/general_education/checklist/choix_formation_detail.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.htmx:
            return redirect(
                reverse('admission:general-education:checklist', kwargs={'uuid': self.admission_uuid})
                + '#choix_formation'
            )
        return super().dispatch(request, *args, **kwargs)
