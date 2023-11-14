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

from django.utils import translation

from admission.exports.utils import admission_generate_pdf
from admission.contrib.models import ConfirmationPaper


def admission_pdf_confirmation_canvas(admission, language, context):
    with translation.override(language=language):
        # Generate the pdf
        save_token = admission_generate_pdf(
            admission=admission,
            template='admission/exports/confirmation_export.html',
            filename='confirmation.pdf',
            context=context,
        )
        # Attach the file to the object
        confirmation_paper = ConfirmationPaper.objects.get(uuid=context.get('confirmation_paper').uuid)
        confirmation_paper.supervisor_panel_report_canvas = [save_token]
        confirmation_paper.save()
        # Return the file UUID
        return confirmation_paper.supervisor_panel_report_canvas[0]
