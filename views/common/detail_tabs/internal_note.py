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
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView

from admission.contrib.models.doctorate import InternalNote
from admission.views.doctorate.mixins import LoadDossierViewMixin

__all__ = ["InternalNoteView"]


class InternalNoteView(LoadDossierViewMixin, CreateView):
    model = InternalNote
    fields = ['text']
    template_name = 'admission/doctorate/forms/internal_note.html'
    message_on_success = _('Your note has been added.')

    @property
    def permission_required(self):
        if self.request.method == 'GET':
            return 'admission.view_internalnote'
        elif self.request.method == 'POST':
            return 'admission.add_internalnote'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data['internal_notes'] = InternalNote.objects.filter(admission=self.admission).values(
            'author__first_name',
            'author__last_name',
            'created_at',
            'text',
        )

        return context_data

    def form_valid(self, form):
        form.instance.author = self.request.user.person
        form.instance.admission = self.admission
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('admission:doctorate:internal-note', kwargs={'uuid': self.admission.uuid})
