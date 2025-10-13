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
from django.views.generic import RedirectView
from osis_document_components.utils import get_file_url

from admission.exports.admission_recap.admission_recap import admission_pdf_recap
from admission.views.common.mixins import LoadDossierViewMixin

__all__ = [
    "AdmissionPDFRecapExportView",
]


class AdmissionPDFRecapExportView(LoadDossierViewMixin, RedirectView):
    permission_required = 'admission.download_doctorateadmission_pdf_recap'

    def get(self, request, *args, **kwargs):
        reading_token = admission_pdf_recap(self.admission, settings.LANGUAGE_CODE, with_annotated_documents=True)
        self.url = get_file_url(reading_token)
        return super().get(request, *args, **kwargs)
