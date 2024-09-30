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

from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _

from admission.views.common.mixins import LoadDossierViewMixin

__all__ = ['DoctorateAdmissionProjectDetailView']


class DoctorateAdmissionProjectDetailView(LoadDossierViewMixin, TemplateView):
    template_name = 'admission/doctorate/details/project.html'
    permission_required = 'admission.view_admission_project'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        # There is a bug with translated strings with percent signs
        # https://docs.djangoproject.com/en/3.2/topics/i18n/translation/#troubleshooting-gettext-incorrectly-detects-python-format-in-strings-with-percent-signs
        # xgettext:no-python-format
        context_data['fte_label'] = _("Full-time equivalent (as %)")
        # xgettext:no-python-format
        context_data['allocated_time_label'] = _("Time allocated for thesis (in %)")

        return context_data
