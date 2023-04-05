# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from io import BytesIO
from typing import Dict, List, Union

from django.db.models import QuerySet
from django.utils.translation import override
from pikepdf import Pdf, OutlineItem

from admission.contrib.models import (
    AdmissionFormItemInstantiation,
    ContinuingEducationAdmission,
    GeneralEducationAdmission,
    DoctorateAdmission,
)
from admission.ddd.admission.doctorat.preparation import commands as doctorate_education_commands
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.enums import (
    Onglets,
)
from admission.ddd.admission.formation_continue import commands as continuing_education_commands
from admission.ddd.admission.formation_generale import commands as general_education_commands
from admission.exports.admission_recap.section import (
    get_identification_section,
    get_coordinates_section,
    get_training_choice_section,
    get_secondary_studies_section,
    get_curriculum_section,
    get_educational_experience_section,
    get_non_educational_experience_section,
    get_specific_questions_section,
    get_accounting_section,
    get_research_project_section,
    get_languages_section,
    get_cotutelle_section,
    get_supervision_section,
    get_confirmation_section,
)
from infrastructure.messages_bus import message_bus_instance
from osis_document.api.utils import get_several_remote_metadata, get_remote_tokens
from osis_document.utils import save_raw_content_remotely


def get_dynamic_questions_by_tab(
    specific_questions: QuerySet[AdmissionFormItemInstantiation],
) -> Dict[str, List[AdmissionFormItemInstantiation]]:
    """Returns the dynamic questions by tab."""
    lists = {tab: [] for tab in Onglets.get_names()}
    for question in specific_questions:
        lists[question.tab].append(question)
    return lists


def admission_pdf_recap(
    admission: Union[ContinuingEducationAdmission, GeneralEducationAdmission, DoctorateAdmission],
    language: str,
):
    """Generates the admission pdf and returns a token to access it."""
    from admission.exports.utils import get_pdf_from_template

    commands = {
        ContinuingEducationAdmission: continuing_education_commands,
        GeneralEducationAdmission: general_education_commands,
        DoctorateAdmission: doctorate_education_commands,
    }[type(admission)]

    with override(language=language):
        context: ResumePropositionDTO = message_bus_instance.invoke(
            commands.RecupererResumePropositionQuery(uuid_proposition=admission.uuid),
        )

        specific_questions = AdmissionFormItemInstantiation.objects.form_items_by_admission(admission).order_by(
            'display_according_education',
            'weight',
        )
        specific_questions_by_tab = get_dynamic_questions_by_tab(specific_questions)
        default_content = BytesIO(get_pdf_from_template('admission/exports/recap/default_content.html', [], {}))

        # The PDF contains several sections, each one containing the data following by the related attachments
        pdf_sections = [
            get_identification_section(context),
            get_coordinates_section(context),
            get_training_choice_section(context, language, specific_questions_by_tab),
        ]

        if context.est_proposition_continue or context.est_proposition_generale:
            pdf_sections.append(get_secondary_studies_section(context, language, specific_questions_by_tab))

        if context.est_proposition_doctorale:
            pdf_sections.append(get_languages_section(context))

        pdf_sections.append(get_curriculum_section(context, language, specific_questions_by_tab))

        for educational_experience in context.curriculum.experiences_academiques:
            pdf_sections.append(get_educational_experience_section(context, educational_experience))

        for non_educational_experience in context.curriculum.experiences_non_academiques:
            pdf_sections.append(get_non_educational_experience_section(context, non_educational_experience))

        if context.est_proposition_generale or context.est_proposition_continue:
            pdf_sections.append(get_specific_questions_section(context, language, specific_questions_by_tab))

        if context.est_proposition_doctorale or context.est_proposition_generale:
            pdf_sections.append(get_accounting_section(context))

        if context.est_proposition_doctorale:
            pdf_sections += [
                get_research_project_section(context),
                get_cotutelle_section(context),
                get_supervision_section(context),
            ]

        pdf_sections.append(get_confirmation_section(context))

        # Get a read token and metadata of all attachments
        all_file_uuids = [
            str(file_uuid)
            for section in pdf_sections
            for attachment in section.attachments
            for file_uuid in attachment.uuids
        ]

        file_tokens = get_remote_tokens(all_file_uuids)
        file_metadata = get_several_remote_metadata(list(file_tokens.values()))

        # Generate the PDF
        pdf = Pdf.new()
        version = pdf.pdf_version
        page_count = 0

        # If too much memory usage -> use temporary files or subprocess
        with pdf.open_outline() as outline:
            for section in pdf_sections:
                outline_item = OutlineItem(section.label, page_count)
                content = BytesIO(section.content)

                # Add section data
                with Pdf.open(content) as pdf_content:
                    version = max(version, pdf_content.pdf_version)
                    pdf.pages.extend(pdf_content.pages)
                    page_count += len(pdf_content.pages)

                # Add section attachments
                for attachment in section.attachments:
                    if attachment.uuids:
                        outline_item.children.append(OutlineItem(attachment.label, page_count))
                    for attachment_uuid in attachment.uuids:
                        token = file_tokens.get(str(attachment_uuid))
                        raw_content = attachment.get_raw(
                            token=token,
                            metadata=file_metadata.get(token),
                            default_content=default_content,
                        )
                        with Pdf.open(raw_content) as attachment_content:
                            version = max(version, attachment_content.pdf_version)
                            pdf.pages.extend(attachment_content.pages)
                            page_count += len(attachment_content.pages)

                outline.root.append(outline_item)

        # Finalize the PDF
        final_pdf = BytesIO()
        pdf.save(final_pdf, min_version=version)

        # Save the pdf
        token = save_raw_content_remotely(final_pdf.getvalue(), 'admission_archive.pdf', 'application/pdf')

        # Return the token
        return token
