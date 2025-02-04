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
from django.utils.functional import cached_property
from django.views.generic import FormView
from osis_mail_template.exceptions import EmptyMailTemplateContent
from osis_mail_template.models import MailTemplate

from admission.ddd.admission.doctorat.preparation.commands import (
    DemanderCandidatModificationCACommand,
)
from admission.forms.admission.doctorate.checklist import ProjetRechercheDemanderModificationCAForm
from admission.mail_templates import ADMISSION_EMAIL_SUPERVISION_MODIFICATION_DOCTORATE
from admission.utils import get_portal_admission_url
from admission.views.common.mixins import AdmissionFormMixin
from admission.views.doctorate.details.checklist.mixins import CheckListDefaultContextMixin
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.utils.htmx import HtmxPermissionRequiredMixin
from base.utils.utils import format_academic_year
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    'ProjetRechercheDemanderModificationCAView',
]


__namespace__ = False


class ProjetRechercheContextMixin(CheckListDefaultContextMixin):
    @cached_property
    def projet_recherche_demander_modification_ca_form(self):
        candidate = self.admission.candidate
        person = self.request.user.person

        training_title = {
            settings.LANGUAGE_CODE_FR: self.proposition.formation.intitule_fr,
            settings.LANGUAGE_CODE_EN: self.proposition.formation.intitule,
        }[candidate.language]

        tokens = {
            'admission_reference': self.proposition.reference,
            'candidate_first_name': self.proposition.prenom_candidat,
            'candidate_last_name': self.proposition.nom_candidat,
            'academic_year': format_academic_year(self.proposition.formation.annee),
            'training_title': training_title,
            'training_acronym': self.proposition.formation.sigle,
            'admissions_link_front': get_portal_admission_url('doctorate', str(self.admission_uuid)) + 'supervision/',
            'sender_name': f'{person.first_name} {person.last_name}',
            'phd_committee': self.proposition.formation.intitule_entite_gestion,
        }

        try:
            mail_template: MailTemplate = MailTemplate.objects.get_mail_template(
                ADMISSION_EMAIL_SUPERVISION_MODIFICATION_DOCTORATE,
                self.admission.candidate.language,
            )

            subject = mail_template.render_subject(tokens=tokens)
            body = mail_template.body_as_html(tokens=tokens)
        except EmptyMailTemplateContent:
            subject = ''
            body = ''

        form_kwargs = {
            'prefix': 'projet-recherche-demander-modification-ca',
        }
        if self.request.method == 'POST' and 'projet-recherche-demander-modification-ca-body' in self.request.POST:
            form_kwargs['data'] = self.request.POST
        else:
            form_kwargs['initial'] = {
                'subject': subject,
                'body': body,
            }

        return ProjetRechercheDemanderModificationCAForm(**form_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['projet_recherche_demander_modification_ca_form'] = self.projet_recherche_demander_modification_ca_form

        return context


class ProjetRechercheDemanderModificationCAView(
    AdmissionFormMixin,
    ProjetRechercheContextMixin,
    HtmxPermissionRequiredMixin,
    FormView,
):
    urlpatterns = 'projet-recherche-demander-modification-ca'
    permission_required = 'admission.change_admission_supervision'
    template_name = 'admission/doctorate/includes/checklist/projet_recherche_demander_modification_form.html'
    htmx_template_name = 'admission/doctorate/includes/checklist/projet_recherche_demander_modification_form.html'

    def get_form(self, form_class=None):
        return self.projet_recherche_demander_modification_ca_form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                DemanderCandidatModificationCACommand(
                    uuid_proposition=self.admission_uuid,
                    auteur=self.request.user.person.global_id,
                    objet_message=form.cleaned_data['subject'],
                    corps_message=form.cleaned_data['body'],
                )
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                form.add_error(None, exception.message)
            return self.form_invalid(form)

        self.htmx_refresh = True
        return super().form_valid(form)
