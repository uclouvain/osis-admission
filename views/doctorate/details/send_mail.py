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

from django.forms import BaseForm
from django.utils.translation import gettext_lazy as _, override
from django.views.generic import FormView
from osis_mail_template.models import MailTemplate

from admission.ddd.admission.doctorat.preparation.commands import EnvoyerMessageCandidatCommand
from admission.forms.doctorate.cdd.send_mail import CddDoctorateSendMailForm
from admission.infrastructure.admission.doctorat.preparation.domain.service.notification import Notification
from admission.mail_templates import ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED
from admission.views.common.mixins import AdmissionFormMixin, LoadDossierViewMixin
from infrastructure.messages_bus import message_bus_instance
from osis_common.utils.htmx import HtmxMixin

__all__ = [
    "DoctorateSendMailView",
]


class DoctorateSendMailView(HtmxMixin, AdmissionFormMixin, LoadDossierViewMixin, FormView):
    template_name = 'admission/doctorate/forms/send_mail.html'
    htmx_template_name = 'admission/doctorate/forms/send_mail_htmx.html'
    form_class = CddDoctorateSendMailForm
    permission_required = 'admission.send_message'

    def get_success_url(self):
        return self.request.get_full_path()

    def get_extra_form_kwargs(self):
        return {
            'admission': self.admission,
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.get_extra_form_kwargs())
        return kwargs

    def get_initial(self):
        mail_template = MailTemplate.objects.get(
            identifier=ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED,
            language=self.admission.candidate.language,
        )
        tokens = Notification.get_common_tokens(self.proposition, self.admission.candidate)

        with override(language=self.admission.candidate.language):
            return {
                **self.request.GET,
                'subject': mail_template.render_subject(tokens),
                'body': mail_template.body_as_html(tokens),
            }

    def form_valid(self, form: BaseForm):
        message_bus_instance.invoke(
            EnvoyerMessageCandidatCommand(
                matricule_emetteur=self.request.user.person.global_id,
                proposition_uuid=self.admission.uuid,
                sujet=form.cleaned_data['subject'],
                message=form.cleaned_data['body'],
                cc_promoteurs=form.cleaned_data['cc_promoteurs'],
                cc_membres_ca=form.cleaned_data['cc_membres_ca'],
            )
        )
        self.message_on_success = _("Message sent successfully")
        return super().form_valid(self.form_class(**self.get_extra_form_kwargs()))
