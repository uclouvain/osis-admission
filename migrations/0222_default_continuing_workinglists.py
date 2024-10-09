from django.conf import settings
from django.db import migrations

from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
    OngletsChecklist,
)


def initialize_default_working_lists(apps, schema_editor):
    ContinuingWorkingList = apps.get_model('admission', 'ContinuingWorkingList')

    default_working_lists = [
        ContinuingWorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Dossiers confirmés admission',
                settings.LANGUAGE_CODE_EN: 'Confirmed admission applications',
            },
            order=1,
            admission_statuses=[
                ChoixStatutPropositionContinue.CONFIRMEE.name,
            ],
            checklist_filters_mode=ModeFiltrageChecklist.EXCLUSION.name,
            checklist_filters={
                OngletsChecklist.decision.name: [
                    'ACCORD_FAC',
                    'PRISE_EN_CHARGE',
                ],
            },
        ),
        ContinuingWorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Dossiers pris en charge',
                settings.LANGUAGE_CODE_EN: 'Applications taken in charge',
            },
            order=2,
            admission_statuses=[
                ChoixStatutPropositionContinue.CONFIRMEE.name,
            ],
            checklist_filters_mode=ModeFiltrageChecklist.INCLUSION.name,
            checklist_filters={
                OngletsChecklist.decision.name: [
                    'PRISE_EN_CHARGE',
                ],
            },
        ),
        ContinuingWorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Dossiers à valider',
                settings.LANGUAGE_CODE_EN: 'Applications to validate',
            },
            order=3,
            admission_statuses=[
                ChoixStatutPropositionContinue.CONFIRMEE.name,
            ],
            checklist_filters_mode=ModeFiltrageChecklist.INCLUSION.name,
            checklist_filters={
                OngletsChecklist.decision.name: [
                    'ACCORD_FAC',
                ],
            },
        ),
        ContinuingWorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Dossiers à valider IUFC',
                settings.LANGUAGE_CODE_EN: 'Applications to validate for IUFC',
            },
            order=4,
            admission_statuses=[
                ChoixStatutPropositionContinue.CONFIRMEE.name,
            ],
            checklist_filters_mode=ModeFiltrageChecklist.INCLUSION.name,
            checklist_filters={
                OngletsChecklist.decision.name: [
                    'A_VALIDER',
                ],
            },
        ),
        ContinuingWorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Dossiers validés IUFC',
                settings.LANGUAGE_CODE_EN: 'Validated applications for IUFC',
            },
            order=5,
            admission_statuses=[
                ChoixStatutPropositionContinue.INSCRIPTION_AUTORISEE.name,
            ],
            checklist_filters_mode=ModeFiltrageChecklist.INCLUSION.name,
            checklist_filters={
                OngletsChecklist.decision.name: [],
            },
        ),
        ContinuingWorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Dossiers refusés par la fac',
                settings.LANGUAGE_CODE_EN: 'Refused applications by the fac',
            },
            order=6,
            admission_statuses=[
                ChoixStatutPropositionContinue.INSCRIPTION_REFUSEE.name,
            ],
            checklist_filters_mode=ModeFiltrageChecklist.INCLUSION.name,
            checklist_filters={
                OngletsChecklist.decision.name: [],
            },
        ),
        ContinuingWorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Dossiers mis en attente',
                settings.LANGUAGE_CODE_EN: 'Applications on hold',
            },
            order=7,
            admission_statuses=[
                ChoixStatutPropositionContinue.EN_ATTENTE.name,
            ],
            checklist_filters_mode=ModeFiltrageChecklist.INCLUSION.name,
            checklist_filters={
                OngletsChecklist.decision.name: [],
            },
        ),
        ContinuingWorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Dossiers annulés',
                settings.LANGUAGE_CODE_EN: 'Cancelled applications',
            },
            order=8,
            admission_statuses=[
                ChoixStatutPropositionContinue.ANNULEE.name,
            ],
            checklist_filters_mode=ModeFiltrageChecklist.INCLUSION.name,
            checklist_filters={
                OngletsChecklist.decision.name: [],
            },
        ),
    ]

    ContinuingWorkingList.objects.bulk_create(default_working_lists)


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0221_continuingworkinglist'),
    ]

    operations = [
        migrations.RunPython(code=initialize_default_working_lists, reverse_code=migrations.RunPython.noop),
    ]
