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
from django.conf import settings
from django.db.models import Prefetch
from django.utils import translation

from admission.exports.utils import admission_generate_pdf
from admission.contrib.models import AdmissionTask, ConfirmationPaper, DoctorateAdmission
from base.models.enums.person_address_type import PersonAddressType
from base.models.person_address import PersonAddress
from reference.services.mandates import MandatesService, MandateFunctionEnum, MandatesException


def format_address(address, language):
    """Return the concatenation of the street, street number, postal code, city and state of an address."""
    address_parts = [
        '{street} {street_number}'.format_map(address),
        '{postal_code} {city}'.format_map(address),
        address.get('country__name' if language == settings.LANGUAGE_CODE else 'country__name_en'),
    ]
    return ', '.join(filter(lambda part: part and len(part) > 1, address_parts))


def admission_confirmation_success_attestation(task_uuid, language=None):
    admission_task = (
        AdmissionTask.objects.select_related('task')
        .prefetch_related(
            Prefetch(
                'admission',
                DoctorateAdmission.objects.select_related(
                    'candidate',
                    'training__management_entity',
                ).annotate_campus(),
            ),
        )
        .get(task__uuid=task_uuid)
    )

    current_language = language or admission_task.admission.candidate.language

    with translation.override(current_language):
        # Load additional data
        confirmation_paper = ConfirmationPaper.objects.filter(admission=admission_task.admission).first()

        addresses = (
            PersonAddress.objects.filter(person=admission_task.admission.candidate)
            .select_related('country')
            .values('street', 'street_number', 'postal_code', 'city', 'country__name', 'country__name_en')
        )

        contact_address = (
            format_address(
                address=addresses.filter(label=PersonAddressType.CONTACT.name).first()
                or addresses.filter(label=PersonAddressType.RESIDENTIAL.name).first()
                or addresses[0],
                language=current_language,
            )
            if addresses
            else None
        )

        cdd_president = []
        if settings.ESB_API_URL:
            acronym = admission_task.admission.doctorate.management_entity.most_recent_entity_version.acronym
            try:
                cdd_president = MandatesService.get(function=MandateFunctionEnum.PRESI, entity_acronym=acronym)
            except MandatesException:
                pass

        # Generate the pdf
        save_token = admission_generate_pdf(
            admission_task.admission,
            template='admission/exports/confirmation_success_attestation.html',
            filename='confirmation_attestation.pdf',
            context={
                'contact_address': contact_address,
                'cdd_president': cdd_president[0] if cdd_president else {},
                'confirmation_paper': confirmation_paper,
                'teaching_campus': admission_task.admission.teaching_campus,
            },
        )

        # Attach the file to the object
        confirmation_paper.certificate_of_achievement = [save_token]
        confirmation_paper.save()
