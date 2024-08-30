# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, override
from django.views import View
from django.views.generic import FormView
from django.views.generic.edit import FormMixin
from osis_mail_template.models import MailTemplate

from admission.models import CddMailTemplate
from admission.ddd.parcours_doctoral.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.parcours_doctoral.epreuve_confirmation.commands import (
    ConfirmerEchecCommand,
    ConfirmerRepassageCommand,
    ConfirmerReussiteCommand,
    TeleverserAvisRenouvellementMandatRechercheCommand,
)
from admission.forms.doctorate.cdd.generic_send_mail import BaseEmailTemplateForm, SelectCddEmailTemplateForm
from admission.forms.doctorate.confirmation import ConfirmationOpinionForm, ConfirmationRetakingForm
from admission.infrastructure.parcours_doctoral.epreuve_confirmation.domain.service.notification import (
    Notification,
)
from admission.mail_templates import (
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
)
from admission.views.doctorate.mixins import DoctorateAdmissionLastConfirmationMixin
from admission.views.mixins.business_exceptions_form_view_mixin import BusinessExceptionFormViewMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance
from osis_common.utils.htmx import HtmxMixin

__all__ = [
    "DoctorateAdmissionConfirmationFailureDecisionView",
    "DoctorateAdmissionConfirmationRetakingDecisionView",
    "DoctorateAdmissionConfirmationSuccessDecisionView",
    "DoctorateAdmissionConfirmationOpinionFormView",
]
__namespace__ = 'confirmation'


class DoctorateAdmissionConfirmationSuccessDecisionView(
    DoctorateAdmissionLastConfirmationMixin,
    View,
):
    urlpatterns = 'success'
    permission_required = 'admission.make_confirmation_decision'

    def post(self, *args, **kwargs):
        try:
            message_bus_instance.invoke(ConfirmerReussiteCommand(uuid=self.last_confirmation_paper.uuid))
            messages.success(
                self.request,
                _("The status has been changed to %(status)s.")
                % {'status': _(ChoixStatutDoctorat.PASSED_CONFIRMATION.value)},
            )
            messages.success(
                self.request,
                _('The certificate of achievement is being generated.'),
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                messages.error(self.request, exception.message)

        return HttpResponseRedirect(reverse('admission:doctorate:confirmation', args=[self.admission_uuid]))


class DoctorateAdmissionConfirmationDecisionMixin(
    HtmxMixin,
    DoctorateAdmissionLastConfirmationMixin,
    BusinessExceptionFormViewMixin,
    FormMixin,
):
    permission_required = 'admission.make_confirmation_decision'
    htmx_template_name = 'admission/doctorate/forms/send_mail_htmx_fields.html'
    template_name = 'admission/doctorate/forms/confirmation_decision.html'
    identifier = ''
    page_title = ''

    def get_initial(self):
        mail_identifier = self.request.GET.get('template')

        tokens = Notification.get_common_tokens(self.admission, self.last_confirmation_paper)

        if mail_identifier and mail_identifier.isnumeric():
            # Template is a custom one
            mail_template = CddMailTemplate.objects.get(
                pk=mail_identifier,
                cdd=self.admission.doctorate.management_entity,
            )
        else:
            # Template is the generic one
            mail_template = MailTemplate.objects.get(
                identifier=self.identifier,
                language=self.admission.candidate.language,
            )

        with override(language=self.admission.candidate.language):
            return {
                'subject': mail_template.render_subject(tokens),
                'body': mail_template.body_as_html(tokens),
            }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.htmx:
            return context

        context['select_template_form'] = SelectCddEmailTemplateForm(
            identifier=self.identifier,
            admission=self.admission,
            initial={
                'template': self.request.GET.get('template'),
            },
        )

        context['page_title'] = self.page_title
        context['submit_label'] = _('Confirm and send the message')

        return context

    def get_success_url(self):
        return reverse('admission:doctorate:confirmation', args=[self.admission_uuid])


class DoctorateAdmissionConfirmationFailureDecisionView(
    DoctorateAdmissionConfirmationDecisionMixin,
    FormView,
):
    urlpatterns = 'failure'
    form_class = BaseEmailTemplateForm
    identifier = ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT
    page_title = _('Failure of the confirmation paper')
    message_on_success = _("The status has been changed to %(status)s.") % {
        'status': _(ChoixStatutDoctorat.NOT_ALLOWED_TO_CONTINUE.value)
    }

    def call_command(self, form):
        message_bus_instance.invoke(
            ConfirmerEchecCommand(
                uuid=self.last_confirmation_paper.uuid,
                sujet_message=form.cleaned_data['subject'],
                corps_message=form.cleaned_data['body'],
            )
        )


class DoctorateAdmissionConfirmationRetakingDecisionView(
    DoctorateAdmissionConfirmationDecisionMixin,
    FormView,
):
    urlpatterns = 'retaking'
    form_class = ConfirmationRetakingForm
    identifier = ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT
    page_title = _('Retaking of the confirmation paper')
    message_on_success = _("The status has been changed to %(status)s.") % {
        'status': _(ChoixStatutDoctorat.CONFIRMATION_TO_BE_REPEATED.value)
    }

    def call_command(self, form):
        message_bus_instance.invoke(
            ConfirmerRepassageCommand(
                uuid=self.last_confirmation_paper.uuid,
                sujet_message=form.cleaned_data['subject'],
                corps_message=form.cleaned_data['body'],
                date_limite=form.cleaned_data['date_limite'],
            )
        )


class DoctorateAdmissionConfirmationOpinionFormView(
    DoctorateAdmissionLastConfirmationMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    urlpatterns = 'opinion'
    template_name = 'admission/doctorate/forms/confirmation_opinion.html'
    form_class = ConfirmationOpinionForm
    permission_required = 'admission.upload_pdf_confirmation'

    def get_initial(self):
        return {
            'avis_renouvellement_mandat_recherche': self.last_confirmation_paper.avis_renouvellement_mandat_recherche,
        }

    def call_command(self, form):
        # Save the confirmation paper
        message_bus_instance.invoke(
            TeleverserAvisRenouvellementMandatRechercheCommand(
                uuid=self.last_confirmation_paper.uuid,
                **form.cleaned_data,
            )
        )

    def get_success_url(self):
        return reverse('admission:doctorate:confirmation', args=[self.admission_uuid])
