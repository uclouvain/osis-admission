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
from collections import defaultdict
from typing import Any, Dict

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.utils.translation import get_language
from django.views import generic

from admission.auth.roles.cdd_manager import CddManager
from admission.contrib.models import CddMailTemplate
from admission.forms.cdd_mail_template import NameMailTemplateForm
from osis_mail_template.forms import MailTemplateConfigureForm
from osis_mail_template.models import MailTemplate
from osis_role.contrib.views import PermissionRequiredMixin


class CddMailTemplateListView(PermissionRequiredMixin, generic.ListView):
    template_name = 'admission/config/cdd_mail_template_list.html'
    permission_required = 'admission.change_cddmailtemplate'

    def get_queryset(self):
        qs = CddMailTemplate.objects.filter(
            cdd_id=CddManager.objects.filter(person=self.request.user.person).first().entity_id,
            language=get_language(),
        ).order_by('name')
        object_list = defaultdict(list)
        for template in qs:
            object_list[template.identifier].append(template)
        return object_list

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        from osis_mail_template import templates
        from admission.contrib.models.cdd_mail_template import ALLOWED_CUSTOM_IDENTIFIERS

        kwargs['descriptions'] = {
            identifier: templates.get_description(identifier) for identifier in ALLOWED_CUSTOM_IDENTIFIERS
        }
        return super().get_context_data(**kwargs)


class CddMailTemplateChangeView(PermissionRequiredMixin, generic.FormView):
    forms = None
    template_name = 'admission/config/cdd_mail_template_change.html'
    success_url = reverse_lazy('admission:config:cdd_mail_template:list')
    permission_required = 'admission.change_cddmailtemplate'

    def get_forms(self, form_class=None):
        if not self.forms:  # pragma: no branch
            identifier = self.kwargs['identifier']
            if self.kwargs.get('pk'):
                self.forms = [
                    NameMailTemplateForm(
                        data=self.request.POST or None,
                        initial={'name': CddMailTemplate.objects.get(pk=self.kwargs['pk']).name},
                    )
                ]
                instances = CddMailTemplate.objects.get_by_id_and_pk(identifier, self.kwargs['pk'])
                self.forms += [
                    MailTemplateConfigureForm(
                        data=self.request.POST or None,
                        instance=instance,
                        prefix=instance.language,
                    )
                    for instance in instances
                ]
            else:
                cdd = CddManager.objects.filter(person=self.request.user.person).first()
                if not cdd:
                    raise PermissionDenied('Current user has no CDD')
                self.forms = [
                    NameMailTemplateForm(
                        data=self.request.POST or None,
                    )
                ]
                original = {
                    template.language: template for template in MailTemplate.objects.filter(identifier=identifier)
                }
                self.forms += [
                    MailTemplateConfigureForm(
                        data=self.request.POST or None,
                        prefix=language,
                        instance=CddMailTemplate(identifier=identifier, cdd_id=cdd.entity_id, language=language),
                        initial={'subject': original[language].subject, 'body': original[language].body},
                    )
                    for language in dict(settings.LANGUAGES)
                ]
        return self.forms

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        # Get the cdd of the user
        if all(form.is_valid() for form in forms):
            for form in forms[1:]:
                form.instance.name = forms[0].cleaned_data['name']
                form.save()
            return self.form_valid(forms)
        return self.form_invalid(forms)

    def form_invalid(self, forms):
        return self.render_to_response(self.get_context_data(forms=forms))

    def get_context_data(self, **kwargs):
        from osis_mail_template import templates

        identifier = self.kwargs['identifier']

        kwargs['view'] = self
        kwargs['identifier'] = identifier
        kwargs['tokens'] = templates.get_tokens(identifier)
        kwargs['description'] = templates.get_description(identifier)
        kwargs['languages'] = dict(settings.LANGUAGES)

        if 'forms' not in kwargs:
            kwargs['forms'] = self.get_forms()
        return kwargs


class CddMailTemplatePreview(PermissionRequiredMixin, generic.TemplateView):
    template_name = 'admission/config/cdd_mail_template_preview.html'
    permission_required = 'admission.change_cddmailtemplate'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        identifier = self.kwargs['identifier']
        context['instances'] = CddMailTemplate.objects.get_by_id_and_pk(identifier, self.kwargs['pk'])
        return context
