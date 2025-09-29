# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import csv
import io
from collections import defaultdict
from itertools import chain

from django.contrib import messages
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import F, Q, Value
from django.db.models.functions import Concat
from django.utils.translation import gettext
from django.views.generic import FormView

from admission.auth.roles.doctorate_committee_member import DoctorateCommitteeMember
from admission.forms.admission.doctorate_committee_members_import import (
    DoctorateCommitteeMembersImportForm,
)
from base.models.education_group import EducationGroup
from base.models.enums.education_group_types import TrainingType
from base.models.person import Person


class DoctorateCommitteeMembersImportView(FormView):
    template_name = 'admission/admin/doctorate_committee_members_import.html'
    form_class = DoctorateCommitteeMembersImportForm

    def form_valid(self, form):
        # Load data from the file
        uploaded_file = form.cleaned_data['file']

        with io.TextIOWrapper(uploaded_file.file, encoding='utf-8', newline='') as csv_file:
            reader = csv.DictReader(
                csv_file,
                fieldnames=['cdd'],
                restkey='members',
            )

            if form.cleaned_data['with_header']:
                next(reader)

            input_data = {row['cdd']: [member for member in row.get('members', []) if member] for row in reader}

            results = import_doctorate_committee_members(persons_keys_by_cdd_acronym=input_data)

            messages.info(self.request, gettext('The data import has been completed.'))

            if results['persons_not_found']:
                base_message = gettext('No one has been found for:')
                messages.warning(self.request, f"{base_message} {', '.join(results['persons_not_found'])}.")

            if results['persons_with_homonyms']:
                base_message = gettext('Several persons have been found for:')
                messages.warning(self.request, f"{base_message} {', '.join(results['persons_with_homonyms'])}.")

            if results['cdds_with_no_training']:
                base_message = gettext('No education group has been found for:')
                messages.warning(self.request, f"{base_message} {', '.join(results['cdds_with_no_training'])}.")

            return self.render_to_response(self.get_context_data(form=form))


def search_persons(persons_keys: list[str]) -> dict[str, list[Person]]:
    """
    Search all the persons whose the name or the global id are specified.
    :param persons_keys: The keys (name or global id) of the persons.
    :return: a dictionary containing for each key (name and id), the associated person
    """
    if not persons_keys:
        return {}

    persons_by_key: dict[str, list[Person]] = defaultdict(list)

    persons = Person.objects.annotate(
        concatenated_name=Concat(F('first_name'), Value(' '), F('last_name')),
    ).filter(
        Q(global_id__in=persons_keys) | Q(concatenated_name__in=persons_keys),
    )

    for person in persons:
        persons_by_key[person.concatenated_name].append(person)
        persons_by_key[person.global_id].append(person)

    return persons_by_key


def search_education_groups(cdd_acronyms: list[str]) -> dict[str, list[EducationGroup]]:
    """
    Search all the education groups whose the trainings are managed by the cdds whose acronyms are specified.
    :param cdd_acronyms: The cdd acronyms.
    :return: a dictionary containing for each cdd acronym, the list of managed education groups.
    """
    if not cdd_acronyms:
        return {}

    education_groups = EducationGroup.objects.filter(
        educationgroupyear__education_group_type__name=TrainingType.PHD.name,
        educationgroupyear__management_entity__entityversion__acronym__in=cdd_acronyms,
    ).annotate(
        management_entity_acronyms=ArrayAgg(
            'educationgroupyear__management_entity__entityversion__acronym',
            distinct=True,
            default=Value([]),
        ),
    )

    education_groups_by_entity_acronym = defaultdict(list)

    for education_group in education_groups:
        for management_entity_acronym in education_group.management_entity_acronyms:
            education_groups_by_entity_acronym[management_entity_acronym].append(education_group)

    return education_groups_by_entity_acronym


def import_doctorate_committee_members(persons_keys_by_cdd_acronym: dict[str, list[str]]):
    """
    Create doctorate committee members.

    :param persons_keys_by_cdd_acronym: a dictionary mapping a list of the persons keys for each cdd acronym.
    """
    # Retrieve the related models
    all_persons_keys = list(chain.from_iterable(persons_keys_by_cdd_acronym.values()))
    all_cdds_acronyms = list(persons_keys_by_cdd_acronym.keys())

    all_persons = search_persons(persons_keys=all_persons_keys)
    all_education_groups = search_education_groups(cdd_acronyms=all_cdds_acronyms)

    # Save unexpected results
    persons_not_found: set[str] = set()
    persons_with_homonyms: set[str] = set()
    cdds_with_no_training: set[str] = set()

    # Create the roles to save
    roles_to_create: list[DoctorateCommitteeMember] = []

    for cdd_acronym, persons_keys in persons_keys_by_cdd_acronym.items():
        education_groups = all_education_groups.get(cdd_acronym)

        if not education_groups:
            cdds_with_no_training.add(cdd_acronym)
            continue

        for person_key in persons_keys:
            persons = all_persons.get(person_key)

            if not persons:
                persons_not_found.add(person_key)
                continue

            if len(persons) > 1:
                persons_with_homonyms.add(person_key)
                continue

            person = persons[0]

            for education_group in education_groups:
                roles_to_create.append(
                    DoctorateCommitteeMember(
                        person=person,
                        education_group=education_group,
                    )
                )

    created_roles = DoctorateCommitteeMember.objects.bulk_create(
        objs=roles_to_create,
        ignore_conflicts=True,
    )

    return {
        'created_roles': created_roles,
        'persons_not_found': persons_not_found,
        'persons_with_homonyms': persons_with_homonyms,
        'cdds_with_no_training': cdds_with_no_training,
    }
