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

from django.contrib import messages
from django.forms import BaseForm
from django.utils.translation import gettext_lazy as _, override
from django.views.generic import FormView

from admission.contrib.models import CddMailTemplate
from admission.ddd.parcours_doctoral.commands import EnvoyerMessageDoctorantCommand
from admission.forms.doctorate.cdd.send_mail import CddDoctorateSendMailForm
from admission.infrastructure.parcours_doctoral.domain.service.notification import (
    Notification as NotificationDoctorat,
)
from admission.infrastructure.parcours_doctoral.epreuve_confirmation.domain.service.notification import (
    Notification as NotificationEpreuveConfirmation,
)
from admission.mail_templates import CONFIRMATION_PAPER_TEMPLATES_IDENTIFIERS
from admission.views.doctorate.mixins import LoadDossierViewMixin
from base.utils.htmx import HtmxMixin
from infrastructure.messages_bus import message_bus_instance
from osis_mail_template.models import MailTemplate

__all__ = [
    "DoctorateSendMailView",
]


class DoctorateSendMailView(HtmxMixin, LoadDossierViewMixin, FormView):
    template_name = 'admission/doctorate/forms/send_mail.html'
    htmx_template_name = 'admission/doctorate/forms/send_mail_htmx.html'
    form_class = CddDoctorateSendMailForm
    permission_required = 'admission.send_message'

    def get_success_url(self):
        return self.request.get_full_path()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['admission'] = self.admission
        return kwargs

    def get_tokens(self, identifier):
        if identifier in CONFIRMATION_PAPER_TEMPLATES_IDENTIFIERS:
            return NotificationEpreuveConfirmation.get_common_tokens(self.admission, self.last_confirmation_paper)
        return NotificationDoctorat.get_common_tokens(self.admission)

    def get_initial(self):
        identifier = self.request.GET.get('template')
        if identifier:
            if identifier.isnumeric():
                # Template is a custom one
                mail_template = CddMailTemplate.objects.get(pk=identifier)
                identifier = mail_template.identifier
            else:
                # Template is a generic one
                mail_template = MailTemplate.objects.get(
                    identifier=identifier,
                    language=self.admission.candidate.language,
                )
            tokens = self.get_tokens(identifier)

            with override(language=self.admission.candidate.language):
                return {
                    **self.request.GET,
                    'subject': mail_template.render_subject(tokens),
                    'body': mail_template.body_as_html(tokens),
                }
        return super().get_initial()

    def form_valid(self, form: BaseForm):
        message_bus_instance.invoke(
            EnvoyerMessageDoctorantCommand(
                matricule_emetteur=self.request.user.person.global_id,
                doctorat_uuid=self.admission.uuid,
                sujet=form.cleaned_data['subject'],
                message=form.cleaned_data['body'],
                cc_promoteurs=form.cleaned_data['cc_promoteurs'],
                cc_membres_ca=form.cleaned_data['cc_membres_ca'],
            )
        )
        messages.info(self.request, _("Message sent successfully"))
        return super().form_valid(form)
