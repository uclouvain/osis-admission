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

from django.conf import settings
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _, pgettext, override
from django.views.generic import TemplateView, FormView
from django.views.generic.base import View
from django_htmx.http import HttpResponseClientRefresh
from osis_comment.models import CommentEntry
from osis_mail_template.exceptions import EmptyMailTemplateContent
from osis_mail_template.models import MailTemplate

from admission.ddd.admission.doctorat.preparation.commands import (
    SpecifierFinancabiliteRegleCommand,
    SpecifierDerogationFinancabiliteCommand,
    NotifierCandidatDerogationFinancabiliteCommand,
    SpecifierFinancabiliteNonConcerneeCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
    DerogationFinancement,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixGenre
from admission.forms import disable_unavailable_forms
from admission.forms.admission.checklist import (
    CommentForm,
    DoctorateFinancabiliteApprovalForm,
    DoctorateFinancabiliteNotFinanceableForm,
)
from admission.forms.admission.checklist import (
    FinancabiliteApprovalForm,
    FinancabiliteDispensationForm,
    FinancabilityDispensationRefusalForm,
    FinancabiliteNotificationForm,
    FinancabiliteNotFinanceableForm,
)
from admission.mail_templates import (
    ADMISSION_EMAIL_FINANCABILITY_DISPENSATION_NOTIFICATION,
    ADMISSION_EMAIL_FINANCABILITY_DISPENSATION_NOTIFICATION_DOCTORATE,
)
from admission.utils import (
    add_close_modal_into_htmx_response,
    format_academic_year,
    get_training_url,
)
from admission.views.common.detail_tabs.checklist import change_admission_status
from admission.views.common.mixins import AdmissionFormMixin
from admission.views.doctorate.details.checklist.mixins import CheckListDefaultContextMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    'FinancabiliteComputeRuleView',
    'FinancabiliteChangeStatusView',
    'FinancabiliteApprovalView',
    'FinancabiliteDerogationNonConcerneView',
    'FinancabiliteDerogationNotificationView',
    'FinancabiliteDerogationAbandonCandidatView',
    'FinancabiliteDerogationRefusView',
    'FinancabiliteDerogationAccordView',
    'FinancabiliteApprovalSetRuleView',
    'FinancabiliteNotFinanceableSetRuleView',
    'FinancabiliteNotFinanceableView',
    'FinancabiliteNotConcernedView',
]


__namespace__ = False


class FinancabiliteContextMixin(CheckListDefaultContextMixin):
    @cached_property
    def financability_dispensation_refusal_form(self):
        form_kwargs = {
            'prefix': 'financability-dispensation-refusal',
        }
        if self.request.method == 'POST' and 'financability-dispensation-refusal-reasons' in self.request.POST:
            form_kwargs['data'] = self.request.POST
        else:
            form_kwargs['initial'] = {
                'reasons': [reason.uuid for reason in self.admission.refusal_reasons.all()]
                + self.admission.other_refusal_reasons,
            }

        return FinancabilityDispensationRefusalForm(**form_kwargs)

    @cached_property
    def financability_dispensation_notification_form(self):
        candidate = self.admission.candidate

        training_title = {
            settings.LANGUAGE_CODE_FR: self.proposition.formation.intitule_fr,
            settings.LANGUAGE_CODE_EN: self.proposition.formation.intitule,
        }[candidate.language]

        with override(language=candidate.language):
            greetings = {
                ChoixGenre.H.name: pgettext('male gender', 'Dear'),
                ChoixGenre.F.name: pgettext('female gender', 'Dear'),
                ChoixGenre.X.name: _("For the attention of"),
            }.get(candidate.gender or ChoixGenre.X.name)

            greetings_ends = {
                ChoixGenre.H.name: _('Sir'),
                ChoixGenre.F.name: _('Madam'),
                ChoixGenre.X.name: _("Sir, Madam"),
            }.get(candidate.gender or ChoixGenre.X.name)

        tokens = {
            'admission_reference': self.proposition.reference,
            'candidate_first_name': self.proposition.prenom_candidat,
            'candidate_last_name': self.proposition.nom_candidat,
            'academic_year': format_academic_year(self.proposition.formation.annee),
            'training_title': training_title,
            'training_acronym': self.proposition.formation.sigle,
            'training_campus': self.proposition.formation.campus.nom,
            'greetings': greetings,
            'greetings_end': greetings_ends,
            'contact_link': get_training_url(
                training_type=self.admission.training.education_group_type.name,
                training_acronym=self.admission.training.acronym,
                partial_training_acronym=self.admission.training.partial_acronym,
                suffix='contacts',
            ),
        }

        try:
            mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
                ADMISSION_EMAIL_FINANCABILITY_DISPENSATION_NOTIFICATION_DOCTORATE,
                self.admission.candidate.language,
            )

            subject = mail_template.render_subject(tokens=tokens)
            body = mail_template.body_as_html(tokens=tokens)
        except EmptyMailTemplateContent:
            subject = ''
            body = ''

        form_kwargs = {
            'prefix': 'financability-dispensation-notification',
        }
        if self.request.method == 'POST' and 'financability-dispensation-notification-body' in self.request.POST:
            form_kwargs['data'] = self.request.POST
        else:
            form_kwargs['initial'] = {
                'subject': subject,
                'body': body,
            }

        return FinancabiliteNotificationForm(**form_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        admission = self.get_permission_object()

        context['financabilite_show_verdict_different_alert'] = (
            (
                admission.checklist['current']['financabilite']['statut']
                in {
                    ChoixStatutChecklist.INITIAL_NON_CONCERNE.name,
                    ChoixStatutChecklist.GEST_REUSSITE.name,
                }
                or (
                    admission.checklist['current']['financabilite']['statut'] == ChoixStatutChecklist.GEST_BLOCAGE.name
                    and admission.checklist['current']['financabilite']['extra'].get('to_be_completed') == '0'
                )
            )
            and admission.financability_rule
            and admission.financability_computed_rule_situation != admission.financability_rule
        )

        context['financabilite_approval_form'] = DoctorateFinancabiliteApprovalForm(
            instance=self.admission,
            prefix='financabilite-approval',
        )
        context['financabilite_not_financeable_form'] = DoctorateFinancabiliteNotFinanceableForm(
            instance=self.admission,
            prefix='financabilite-not-financeable',
        )

        context['financability_dispensation_form'] = FinancabiliteDispensationForm(
            is_central_manager=self.request.user.has_perm(
                'admission.checklist_financability_dispensation',
                self.admission,
            ),
            is_program_manager=self.request.user.has_perm(
                'admission.checklist_financability_dispensation_fac',
                self.admission,
            ),
            initial={
                'dispensation_status': self.admission.financability_dispensation_status,
            },
            prefix='financabilite_derogation',
        )

        context['financability_dispensation_refusal_form'] = self.financability_dispensation_refusal_form
        context['financability_dispensation_notification_form'] = self.financability_dispensation_notification_form

        if self.request.htmx:
            comments = {
                ('__'.join(c.tags)): c
                for c in CommentEntry.objects.filter(
                    object_uuid=self.admission_uuid,
                    tags__contains=['financabilite'],
                )
            }

            context['comment_forms'] = {
                'financabilite': CommentForm(
                    comment=comments.get('financabilite'),
                    form_url=resolve_url(
                        f'{self.base_namespace}:save-comment',
                        uuid=self.admission_uuid,
                        tab='financabilite',
                    ),
                    prefix='financabilite',
                ),
                'financabilite__derogation': CommentForm(
                    comment=comments.get('financabilite__derogation'),
                    form_url=resolve_url(
                        f'{self.base_namespace}:save-comment',
                        uuid=self.admission_uuid,
                        tab='financabilite__derogation',
                    ),
                    prefix='financabilite__derogation',
                    permission='admission.checklist_change_fac_comment',
                ),
            }
            disable_unavailable_forms(
                {
                    comment_form: self.request.user.has_perm(
                        comment_form.permission,
                        self.admission,
                    )
                    for comment_form in context['comment_forms'].values()
                }
            )

        return context


class FinancabiliteComputeRuleView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, TemplateView):
    urlpatterns = {'financability-compute-rule': 'financability-compute-rule'}
    template_name = 'admission/general_education/includes/checklist/financabilite.html'
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        admission = self.get_permission_object()
        admission.update_financability_computed_rule(author=self.request.user.person)
        return self.render_to_response(self.get_context_data())


class FinancabiliteChangeStatusView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, TemplateView):
    urlpatterns = {'financability-change-status': 'financability-change-checklist-status/<str:status>'}
    template_name = 'admission/general_education/includes/checklist/financabilite.html'
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        admission = self.get_permission_object()

        try:
            status, extra = self.kwargs['status'].split('-')
            if status == 'GEST_BLOCAGE':
                extra = {'to_be_completed': extra}
            elif status == 'GEST_EN_COURS':
                extra = {'en_cours': extra}
            elif status == 'GEST_REUSSITE':
                extra = {'reussite': extra}
        except ValueError:
            status = self.kwargs['status']
            extra = {}

        change_admission_status(
            tab='financabilite',
            admission_status=status,
            extra=extra,
            admission=admission,
            replace_extra=True,
            author=self.request.user.person,
        )

        admission.financability_rule = ''
        admission.financability_established_by = None
        admission.save(update_fields=['financability_rule', 'financability_established_by'])

        return HttpResponseClientRefresh()


class FinancabiliteApprovalSetRuleView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, FormView):
    urlpatterns = {'financability-approval-set-rule': 'financability-checklist-approval-set-rule'}
    template_name = 'admission/general_education/includes/checklist/financabilite_approval_form.html'
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def get_form(self, form_class=None):
        return DoctorateFinancabiliteApprovalForm(
            instance=self.admission if self.request.method != 'POST' else None,
            data=self.request.POST if self.request.method == 'POST' else None,
            prefix='financabilite-approval',
        )

    def form_valid(self, form):
        message_bus_instance.invoke(
            SpecifierFinancabiliteRegleCommand(
                uuid_proposition=self.admission_uuid,
                financabilite_regle=form.cleaned_data['financability_rule'],
                etabli_par=self.request.user.person.uuid,
                gestionnaire=self.request.user.person.global_id,
            )
        )

        return HttpResponseClientRefresh()


class FinancabiliteApprovalView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, View):
    urlpatterns = {'financability-approval': 'financability-approval'}
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        message_bus_instance.invoke(
            SpecifierFinancabiliteRegleCommand(
                uuid_proposition=self.admission_uuid,
                financabilite_regle=self.admission.financability_computed_rule_situation,
                etabli_par=self.request.user.person.uuid,
                gestionnaire=self.request.user.person.global_id,
            )
        )

        return HttpResponseClientRefresh()


class FinancabiliteNotFinanceableSetRuleView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, FormView):
    urlpatterns = {'financability-not-financeable-set-rule': 'financability-checklist-not-financeable-set-rule'}
    template_name = 'admission/general_education/includes/checklist/financabilite_non_financable_form.html'
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def get_form(self, form_class=None):
        return DoctorateFinancabiliteNotFinanceableForm(
            instance=self.admission if self.request.method != 'POST' else None,
            data=self.request.POST if self.request.method == 'POST' else None,
            prefix='financabilite-not-financeable',
        )

    def form_valid(self, form):
        message_bus_instance.invoke(
            SpecifierFinancabiliteRegleCommand(
                uuid_proposition=self.admission_uuid,
                financabilite_regle=form.cleaned_data['financability_rule'],
                etabli_par=self.request.user.person.uuid,
                gestionnaire=self.request.user.person.global_id,
            )
        )

        return HttpResponseClientRefresh()


class FinancabiliteNotFinanceableView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, View):
    urlpatterns = {'financability-not-financeable': 'financability-not-financeable'}
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        message_bus_instance.invoke(
            SpecifierFinancabiliteRegleCommand(
                uuid_proposition=self.admission_uuid,
                financabilite_regle=self.admission.financability_computed_rule_situation,
                etabli_par=self.request.user.person.uuid,
                gestionnaire=self.request.user.person.global_id,
            )
        )

        return HttpResponseClientRefresh()


class FinancabiliteNotConcernedView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, View):
    urlpatterns = {'financability-not-concerned': 'financability-checklist-not-concerned'}
    template_name = 'admission/general_education/includes/checklist/financabilite.html'
    permission_required = 'admission.change_checklist'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        message_bus_instance.invoke(
            SpecifierFinancabiliteNonConcerneeCommand(
                uuid_proposition=self.admission_uuid,
                etabli_par=self.request.user.person.uuid,
                gestionnaire=self.request.user.person.global_id,
            )
        )
        return HttpResponseClientRefresh()


class FinancabiliteDerogationNonConcerneView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, TemplateView):
    urlpatterns = {'financability-derogation-non-concerne': 'financability-derogation-non-concerne'}
    template_name = 'admission/general_education/includes/checklist/financabilite.html'
    permission_required = 'admission.checklist_financability_dispensation'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        message_bus_instance.invoke(
            SpecifierDerogationFinancabiliteCommand(
                uuid_proposition=self.admission_uuid,
                statut=DerogationFinancement.NON_CONCERNE.name,
                gestionnaire=self.request.user.person.global_id,
            )
        )

        response = self.render_to_response(self.get_context_data())
        add_close_modal_into_htmx_response(response=response)
        return response


class FinancabiliteDerogationNotificationView(
    AdmissionFormMixin,
    FinancabiliteContextMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    urlpatterns = {'financability-derogation-notification': 'financability-derogation-notification'}
    permission_required = 'admission.checklist_financability_dispensation'
    template_name = (
        htmx_template_name
    ) = 'admission/general_education/includes/checklist/financabilite_derogation_candidat_notifie_form.html'
    htmx_template_name = (
        'admission/general_education/includes/checklist/financabilite_derogation_candidat_notifie_form.html'
    )

    def get_form(self, form_class=None):
        return self.financability_dispensation_notification_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                NotifierCandidatDerogationFinancabiliteCommand(
                    uuid_proposition=self.admission_uuid,
                    gestionnaire=self.request.user.person.global_id,
                    objet_message=form.cleaned_data['subject'],
                    corps_message=form.cleaned_data['body'],
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                form.add_error(None, exception.message)
            return self.form_invalid(form)

        return super().form_valid(form)


class FinancabiliteDerogationAbandonCandidatView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, TemplateView):
    urlpatterns = {'financability-derogation-abandon': 'financability-derogation-abandon'}
    template_name = 'admission/general_education/includes/checklist/financabilite.html'
    permission_required = 'admission.checklist_financability_dispensation_fac'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        message_bus_instance.invoke(
            SpecifierDerogationFinancabiliteCommand(
                uuid_proposition=self.admission_uuid,
                statut=DerogationFinancement.ABANDON_DU_CANDIDAT.name,
                gestionnaire=self.request.user.person.global_id,
            )
        )

        response = self.render_to_response(self.get_context_data())
        add_close_modal_into_htmx_response(response=response)
        return response


class FinancabiliteDerogationRefusView(
    AdmissionFormMixin,
    FinancabiliteContextMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    urlpatterns = {'financability-derogation-refus': 'financability-derogation-refus'}
    permission_required = 'admission.checklist_financability_dispensation_fac'
    template_name = (
        htmx_template_name
    ) = 'admission/general_education/includes/checklist/financabilite_derogation_refus_form.html'
    htmx_template_name = 'admission/general_education/includes/checklist/financabilite_derogation_refus_form.html'

    def get_form(self, form_class=None):
        return self.financability_dispensation_refusal_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                SpecifierDerogationFinancabiliteCommand(
                    uuid_proposition=self.admission_uuid,
                    statut=DerogationFinancement.REFUS_DE_DEROGATION_FACULTAIRE.name,
                    gestionnaire=self.request.user.person.global_id,
                    refus_uuids_motifs=form.cleaned_data['reasons'],
                    refus_autres_motifs=form.cleaned_data['other_reasons'],
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                form.add_error(None, exception.message)
            return self.form_invalid(form)

        self.htmx_refresh = True
        return super().form_valid(form)


class FinancabiliteDerogationAccordView(HtmxPermissionRequiredMixin, FinancabiliteContextMixin, TemplateView):
    urlpatterns = {'financability-derogation-accord': 'financability-derogation-accord'}
    template_name = 'admission/general_education/includes/checklist/financabilite.html'
    permission_required = 'admission.checklist_financability_dispensation_fac'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        message_bus_instance.invoke(
            SpecifierDerogationFinancabiliteCommand(
                uuid_proposition=self.admission_uuid,
                statut=DerogationFinancement.ACCORD_DE_DEROGATION_FACULTAIRE.name,
                gestionnaire=self.request.user.person.global_id,
            )
        )

        response = self.render_to_response(self.get_context_data())
        add_close_modal_into_htmx_response(response=response)
        response.headers['HX-Refresh'] = 'true'
        return response
