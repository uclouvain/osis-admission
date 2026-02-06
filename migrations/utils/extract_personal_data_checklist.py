# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.db.models import Case, Max, Value, When

from base.models.enums.personal_data import ChoixStatutValidationDonneesPersonnelles


def extract_personal_data_checklist(person_model_class):
    """Extract the personal data checklist status from the admissions to the related person."""
    # Set the priorities of the statuses (FRAUDEUR > VALIDEES > AVIS_EXPERT > A_COMPLETER > TOILETTEES > A_TRAITER)
    statuses_indexes: dict[str, int] = {
        ChoixStatutValidationDonneesPersonnelles.A_TRAITER.name: 0,
        ChoixStatutValidationDonneesPersonnelles.TOILETTEES.name: 1,
        ChoixStatutValidationDonneesPersonnelles.A_COMPLETER.name: 2,
        ChoixStatutValidationDonneesPersonnelles.AVIS_EXPERT.name: 3,
        ChoixStatutValidationDonneesPersonnelles.VALIDEES.name: 4,
        ChoixStatutValidationDonneesPersonnelles.FRAUDEUR.name: 5,
    }
    indexes_statuses: dict[int, str] = {value: key for key, value in statuses_indexes.items()}

    persons = person_model_class.objects.filter(
        baseadmissions__checklist__current__donnees_personnelles__statut__in=[
            'GEST_EN_COURS',
            'GEST_BLOCAGE',
            'GEST_REUSSITE',
        ],
    ).annotate(
        personal_data_validation_status_index=Max(
            Case(
                When(
                    baseadmissions__checklist__current__donnees_personnelles__statut='GEST_BLOCAGE',
                    baseadmissions__checklist__current__donnees_personnelles__extra__fraud='1',
                    then=Value(statuses_indexes[ChoixStatutValidationDonneesPersonnelles.FRAUDEUR.name]),
                ),
                When(
                    baseadmissions__checklist__current__donnees_personnelles__statut='GEST_REUSSITE',
                    then=Value(statuses_indexes[ChoixStatutValidationDonneesPersonnelles.VALIDEES.name]),
                ),
                When(
                    baseadmissions__checklist__current__donnees_personnelles__statut='GEST_EN_COURS',
                    baseadmissions__checklist__current__donnees_personnelles__extra__en_cours='expert_opinion',
                    then=Value(statuses_indexes[ChoixStatutValidationDonneesPersonnelles.AVIS_EXPERT.name]),
                ),
                When(
                    baseadmissions__checklist__current__donnees_personnelles__statut='GEST_BLOCAGE',
                    baseadmissions__checklist__current__donnees_personnelles__extra__fraud='0',
                    then=Value(statuses_indexes[ChoixStatutValidationDonneesPersonnelles.A_COMPLETER.name]),
                ),
                When(
                    baseadmissions__checklist__current__donnees_personnelles__statut='GEST_EN_COURS',
                    baseadmissions__checklist__current__donnees_personnelles__extra__en_cours='cleaned',
                    then=Value(statuses_indexes[ChoixStatutValidationDonneesPersonnelles.TOILETTEES.name]),
                ),
                default=Value(statuses_indexes[ChoixStatutValidationDonneesPersonnelles.A_TRAITER.name]),
            ),
        ),
    )

    for person in persons:
        person.personal_data_validation_status = indexes_statuses[person.personal_data_validation_status_index]

    person_model_class.objects.bulk_update(objs=persons, fields=['personal_data_validation_status'], batch_size=500)
