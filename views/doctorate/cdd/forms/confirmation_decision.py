# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.functional import cached_property

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages import error
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import override
from django.views import View
from django.views.generic import FormView
from osis_mail_template.models import MailTemplate

from admission.auth.mixins import CddRequiredMixin
from admission.contrib.models import CddMailTemplate
from admission.ddd.projet_doctoral.doctorat.commands import RecupererDoctoratQuery
from admission.ddd.projet_doctoral.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.projet_doctoral.doctorat.domain.validator.exceptions import DoctoratNonTrouveException
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.commands import (
    ConfirmerReussiteCommand,
    RecupererDerniereEpreuveConfirmationQuery,
    ConfirmerEchecCommand,
)
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationNonTrouveeException,
)
from admission.forms.doctorate.cdd.generic_send_mail import BaseEmailTemplateForm, SelectCddEmailTemplateForm
from admission.infrastructure.projet_doctoral.doctorat.epreuve_confirmation.domain.service.notification import (
    Notification,
)
from admission.mail_templates import ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT
from admission.utils import get_cached_admission_perm_obj
from admission.views.mixins.business_exceptions_form_view_mixin import BusinessExceptionFormViewMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.utils.htmx import HtmxMixin
from infrastructure.messages_bus import message_bus_instance


class CddDoctorateAdmissionConfirmationSuccessDecisionView(LoginRequiredMixin, CddRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            last_confirmation_paper: EpreuveConfirmationDTO = message_bus_instance.invoke(
                RecupererDerniereEpreuveConfirmationQuery(doctorat_uuid=self.kwargs.get('pk'))
            )
            message_bus_instance.invoke(ConfirmerReussiteCommand(uuid=last_confirmation_paper.uuid))
            return HttpResponseRedirect(reverse('admission:doctorate:cdd:confirmation', kwargs=kwargs))
        except (DoctoratNonTrouveException, EpreuveConfirmationNonTrouveeException) as e:
            raise Http404(e.message)
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                error(request, exception.message)
            return HttpResponseRedirect(reverse('admission:doctorate:cdd:confirmation', kwargs=kwargs))


class CddDoctorateAdmissionConfirmationFailureDecisionView(
    HtmxMixin,
    LoginRequiredMixin,
    CddRequiredMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    template_name = 'admission/doctorate/cdd/forms/confirmation_decision_on_failure.html'
    htmx_template_name = 'admission/doctorate/cdd/forms/send_mail_htmx.html'

    form_class = BaseEmailTemplateForm

    @property
    def admission(self):
        return get_cached_admission_perm_obj(self.kwargs.get('pk'))

    @cached_property
    def last_confirmation_paper(self):
        try:
            return message_bus_instance.invoke(RecupererDerniereEpreuveConfirmationQuery(self.kwargs.get('pk')))
        except (DoctoratNonTrouveException, EpreuveConfirmationNonTrouveeException) as e:
            raise Http404(e.message)

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
                identifier=ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
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

        try:
            context['doctorate'] = message_bus_instance.invoke(
                RecupererDoctoratQuery(self.kwargs.get('pk')),
            )
        except DoctoratNonTrouveException as e:
            raise Http404(e.message)

        context['confirmation_paper'] = self.last_confirmation_paper

        context['select_template_form'] = SelectCddEmailTemplateForm(
            identifier=ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
            admission=self.admission,
            initial={
                'template': self.request.GET.get('template'),
            }
        )

        return context

    def call_command(self, form):
        message_bus_instance.invoke(
            ConfirmerEchecCommand(
                uuid=self.last_confirmation_paper.uuid,
                sujet_message=form.cleaned_data['subject'],
                corps_message=form.cleaned_data['body'],
            )
        )

    def get_success_url(self):
        return reverse('admission:doctorate:cdd:confirmation', args=[self.kwargs.get('pk')])
