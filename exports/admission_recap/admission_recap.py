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
import unicodedata
from io import BytesIO
from typing import Union, Optional

from django.utils.translation import override
from pikepdf import Pdf, OutlineItem, PdfError

from admission.contrib.models import (
    ContinuingEducationAdmission,
    GeneralEducationAdmission,
    DoctorateAdmission,
)
from admission.contrib.models.base import BaseAdmission
from admission.ddd.admission.doctorat.preparation import commands as doctorate_education_commands
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.formation_continue import commands as continuing_education_commands
from admission.ddd.admission.formation_generale import commands as general_education_commands
from admission.exports.admission_recap.section import (
    get_sections,
)
from infrastructure.messages_bus import message_bus_instance
from osis_document.utils import save_raw_content_remotely


def admission_pdf_recap(
    admission: Union[BaseAdmission, ContinuingEducationAdmission, GeneralEducationAdmission, DoctorateAdmission],
    language: str,
    admission_class: Optional[type] = None,
    with_annotated_documents=False,
):
    """Generates the admission pdf and returns a token to access it."""
    from admission.exports.utils import get_pdf_from_template
    from osis_document.api.utils import get_several_remote_metadata, get_remote_tokens

    commands = {
        ContinuingEducationAdmission: continuing_education_commands,
        GeneralEducationAdmission: general_education_commands,
        DoctorateAdmission: doctorate_education_commands,
    }[admission_class or type(admission)]

    # Get admission with proper annotation if needed
    if not hasattr(admission, 'formatted_reference'):
        if admission_class:
            admission = admission_class.objects.with_training_management_and_reference().get(pk=admission.pk)
        else:
            admission = BaseAdmission.objects.with_training_management_and_reference().get(pk=admission.pk)

    with override(language=language):
        context: ResumePropositionDTO = message_bus_instance.invoke(
            commands.RecupererResumePropositionQuery(uuid_proposition=admission.uuid),
        )

        default_content = BytesIO(get_pdf_from_template('admission/exports/recap/default_content.html', [], {}))

        specific_questions = message_bus_instance.invoke(
            commands.RecupererQuestionsSpecifiquesQuery(uuid_proposition=admission.uuid),
        )

        pdf_sections = get_sections(
            context,
            specific_questions,
            load_content=True,
            hide_curriculum=True,
            with_additional_documents=False,
            with_free_requestable_documents=True,
        )

        # Get a read token and metadata of all attachments
        all_file_uuids = [
            file_uuid
            for section in pdf_sections
            for attachment in section.attachments
            for file_uuid in attachment.uuids
        ]

        file_tokens = get_remote_tokens(all_file_uuids, for_modified_upload=with_annotated_documents)
        file_metadata = get_several_remote_metadata(list(file_tokens.values()))

        # Generate the PDF
        pdf = Pdf.new()
        version = pdf.pdf_version
        page_count = 0

        # If too much memory usage -> use temporary files or subprocess
        with pdf.open_outline() as outline:
            for section in pdf_sections:
                if section.content is not None:
                    # There is a content to display so we create an outline item to put it and the related attachments
                    outline_item = OutlineItem(str(section.label), page_count)
                    outline_item_children = outline_item.children

                    content = BytesIO(section.content)

                    # Add section data
                    with Pdf.open(content) as pdf_content:
                        version = max(version, pdf_content.pdf_version)
                        pdf.pages.extend(pdf_content.pages)
                        page_count += len(pdf_content.pages)
                else:
                    # There is no content to display so the attachments will be directly added to the outline root
                    outline_item_children = outline.root

                # Add section attachments
                for attachment in section.attachments:
                    if attachment.uuids:
                        outline_item_children.append(OutlineItem(str(attachment.label), page_count))
                    for attachment_uuid in attachment.uuids:
                        token = file_tokens.get(attachment_uuid)
                        raw_content = attachment.get_raw(
                            token=token,
                            metadata=file_metadata.get(token),
                            default_content=default_content,
                        )
                        try:
                            with Pdf.open(raw_content) as attachment_content:
                                version = max(version, attachment_content.pdf_version)
                                pdf.pages.extend(attachment_content.pages)
                                page_count += len(attachment_content.pages)
                        except PdfError:
                            # If an error occurs when opening the attachment, we add the default content
                            with Pdf.open(default_content) as attachment_content:
                                version = max(version, attachment_content.pdf_version)
                                pdf.pages.extend(attachment_content.pages)
                                page_count += len(attachment_content.pages)

                if section.content is not None:
                    outline.root.append(outline_item)

        # Finalize the PDF
        final_pdf = BytesIO()
        pdf.save(final_pdf, min_version=version)

        # Generate the filename
        def format_value_for_filename(value):
            value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
            value = value.replace(' ', '_')
            value = value[:30]
            return value

        first_name = format_value_for_filename(admission.candidate.first_name)
        last_name = format_value_for_filename(admission.candidate.last_name)
        reference = admission.formatted_reference
        filename = f'{last_name} - {first_name} - {reference}.pdf'

        # Save the pdf
        token = save_raw_content_remotely(final_pdf.getvalue(), filename, 'application/pdf')

        # Return the token
        return token
