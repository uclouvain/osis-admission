from django.conf import settings
from django.db import migrations

from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    OngletsChecklist,
    BesoinDeDerogation,
)


def _get_checklist_filters_with_default_tabs(custom_checklist_filters):
    for tab_name in OngletsChecklist.get_names():
        if tab_name not in custom_checklist_filters:
            custom_checklist_filters[tab_name] = []
    return custom_checklist_filters


def initialize_default_working_lists(apps, schema_editor):
    WorkingList = apps.get_model('admission', 'WorkingList')

    default_working_lists = [
        WorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Dossiers confirmés admission',
                settings.LANGUAGE_CODE_EN: 'Confirmed admission applications',
            },
            order=1,
            admission_statuses=[
                ChoixStatutPropositionGenerale.CONFIRMEE.name,
            ],
            checklist_filters_mode=ModeFiltrageChecklist.EXCLUSION.name,
            admission_type=TypeDemande.ADMISSION.name,
            checklist_filters=_get_checklist_filters_with_default_tabs(
                {
                    OngletsChecklist.assimilation.name: [
                        'AVIS_EXPERT',
                    ],
                    OngletsChecklist.experiences_parcours_anterieur.name: [
                        f'AUTHENTIFICATION.{EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name}',
                        f'AUTHENTIFICATION.{EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name}',
                        'AVIS_EXPERT',
                    ],
                    OngletsChecklist.financabilite.name: [
                        'AVIS_EXPERT',
                    ],
                    OngletsChecklist.decision_sic.name: [
                        'A_COMPLETER',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.AVIS_DIRECTION_DEMANDE.name}',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.BESOIN_DE_COMPLEMENT.name}',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.REFUS_DIRECTION.name}',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.ACCORD_DIRECTION.name}',
                    ],
                }
            ),
        ),
        WorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Dossiers complétés SIC admission',
                settings.LANGUAGE_CODE_EN: 'SIC completed admission applications',
            },
            order=2,
            admission_statuses=[
                ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC.name,
            ],
            checklist_filters_mode=ModeFiltrageChecklist.EXCLUSION.name,
            admission_type=TypeDemande.ADMISSION.name,
            checklist_filters=_get_checklist_filters_with_default_tabs(
                {
                    OngletsChecklist.assimilation.name: [
                        'AVIS_EXPERT',
                    ],
                    OngletsChecklist.experiences_parcours_anterieur.name: [
                        f'AUTHENTIFICATION.{EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name}',
                        f'AUTHENTIFICATION.{EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name}',
                        'AVIS_EXPERT',
                    ],
                    OngletsChecklist.financabilite.name: [
                        'AVIS_EXPERT',
                    ],
                    OngletsChecklist.decision_sic.name: [
                        'A_COMPLETER',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.AVIS_DIRECTION_DEMANDE.name}',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.BESOIN_DE_COMPLEMENT.name}',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.REFUS_DIRECTION.name}',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.ACCORD_DIRECTION.name}',
                    ],
                }
            ),
        ),
        WorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Dossiers validés par la faculté / CDD admission',
                settings.LANGUAGE_CODE_EN: 'Admission applications validated by the faculty / CDD',
            },
            order=3,
            admission_statuses=[
                ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name,
            ],
            checklist_filters_mode=ModeFiltrageChecklist.EXCLUSION.name,
            admission_type=TypeDemande.ADMISSION.name,
            checklist_filters=_get_checklist_filters_with_default_tabs(
                {
                    OngletsChecklist.assimilation.name: [
                        'AVIS_EXPERT',
                    ],
                    OngletsChecklist.experiences_parcours_anterieur.name: [
                        f'AUTHENTIFICATION.{EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name}',
                        f'AUTHENTIFICATION.{EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name}',
                        'AVIS_EXPERT',
                    ],
                    OngletsChecklist.financabilite.name: [
                        'AVIS_EXPERT',
                    ],
                    OngletsChecklist.decision_facultaire.name: [
                        'A_COMPLETER_PAR_SIC',
                        'REFUS',
                    ],
                    OngletsChecklist.decision_sic.name: [
                        'A_COMPLETER',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.AVIS_DIRECTION_DEMANDE.name}',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.BESOIN_DE_COMPLEMENT.name}',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.REFUS_DIRECTION.name}',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.ACCORD_DIRECTION.name}',
                    ],
                }
            ),
        ),
        WorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Dossiers refusés/retour SIC par la faculté',
                settings.LANGUAGE_CODE_EN: 'Rejected / returned for SIC applications by the faculty',
            },
            order=4,
            admission_statuses=[
                ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name,
            ],
            checklist_filters_mode=ModeFiltrageChecklist.EXCLUSION.name,
            admission_type=TypeDemande.ADMISSION.name,
            checklist_filters=_get_checklist_filters_with_default_tabs(
                {
                    OngletsChecklist.assimilation.name: [
                        'AVIS_EXPERT',
                    ],
                    OngletsChecklist.experiences_parcours_anterieur.name: [
                        f'AUTHENTIFICATION.{EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name}',
                        f'AUTHENTIFICATION.{EtatAuthentificationParcours.ETABLISSEMENT_CONTACTE.name}',
                        'AVIS_EXPERT',
                    ],
                    OngletsChecklist.financabilite.name: [
                        'AVIS_EXPERT',
                    ],
                    OngletsChecklist.decision_facultaire.name: [
                        'ACCORD',
                    ],
                    OngletsChecklist.decision_sic.name: [
                        'A_COMPLETER',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.AVIS_DIRECTION_DEMANDE.name}',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.BESOIN_DE_COMPLEMENT.name}',
                    ],
                }
            ),
        ),
        WorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Suivi gestionnaire',
                settings.LANGUAGE_CODE_EN: 'Manager follow-up',
            },
            order=5,
            admission_statuses=[
                ChoixStatutPropositionGenerale.CONFIRMEE.name,
                ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC.name,
                ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name,
            ],
            checklist_filters_mode=ModeFiltrageChecklist.INCLUSION.name,
            admission_type=TypeDemande.ADMISSION.name,
            checklist_filters=_get_checklist_filters_with_default_tabs(
                {
                    OngletsChecklist.experiences_parcours_anterieur.name: [
                        f'AUTHENTIFICATION.{EtatAuthentificationParcours.VRAI.name}',
                    ],
                    OngletsChecklist.decision_sic.name: [
                        'A_COMPLETER',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.BESOIN_DE_COMPLEMENT.name}',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.REFUS_DIRECTION.name}',
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.ACCORD_DIRECTION.name}',
                    ],
                }
            ),
        ),
        WorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Refus à valider',
                settings.LANGUAGE_CODE_EN: 'Refusal to validate',
            },
            order=6,
            admission_statuses=[
                ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION.name,
            ],
            checklist_filters_mode=ModeFiltrageChecklist.INCLUSION.name,
            checklist_filters=_get_checklist_filters_with_default_tabs(
                {
                    OngletsChecklist.decision_sic.name: [
                        'REFUS_A_VALIDER',
                    ],
                }
            ),
        ),
        WorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Autorisation à valider',
                settings.LANGUAGE_CODE_EN: 'Approval to validate',
            },
            order=7,
            admission_statuses=[
                ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION.name,
            ],
            checklist_filters_mode=ModeFiltrageChecklist.INCLUSION.name,
            checklist_filters=_get_checklist_filters_with_default_tabs(
                {
                    OngletsChecklist.decision_sic.name: [
                        'AUTORISATION_A_VALIDER',
                    ],
                }
            ),
        ),
        WorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Avis expert métier',
                settings.LANGUAGE_CODE_EN: 'Business expert opinion',
            },
            order=8,
            checklist_filters_mode=ModeFiltrageChecklist.INCLUSION.name,
            checklist_filters=_get_checklist_filters_with_default_tabs(
                {
                    OngletsChecklist.assimilation.name: [
                        'AVIS_EXPERT',
                    ],
                    OngletsChecklist.experiences_parcours_anterieur.name: [
                        'AVIS_EXPERT',
                    ],
                }
            ),
        ),
        WorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Finançabilité demandée',
                settings.LANGUAGE_CODE_EN: 'Financability requested',
            },
            order=9,
            checklist_filters_mode=ModeFiltrageChecklist.INCLUSION.name,
            checklist_filters=_get_checklist_filters_with_default_tabs(
                {
                    OngletsChecklist.financabilite.name: [
                        'AVIS_EXPERT',
                    ],
                }
            ),
        ),
        WorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Vérification cursus demandée',
                settings.LANGUAGE_CODE_EN: 'Curriculum check requested',
            },
            order=10,
            checklist_filters_mode=ModeFiltrageChecklist.INCLUSION.name,
            checklist_filters=_get_checklist_filters_with_default_tabs(
                {
                    OngletsChecklist.experiences_parcours_anterieur.name: [
                        f'AUTHENTIFICATION.{EtatAuthentificationParcours.AUTHENTIFICATION_DEMANDEE.name}',
                    ],
                }
            ),
        ),
        WorkingList(
            name={
                settings.LANGUAGE_CODE_FR: 'Dérogation admission',
                settings.LANGUAGE_CODE_EN: 'Dispensation admission',
            },
            order=11,
            checklist_filters_mode=ModeFiltrageChecklist.INCLUSION.name,
            checklist_filters=_get_checklist_filters_with_default_tabs(
                {
                    OngletsChecklist.decision_sic.name: [
                        f'BESOIN_DEROGATION.{BesoinDeDerogation.AVIS_DIRECTION_DEMANDE.name}',
                    ],
                }
            ),
        ),
    ]

    WorkingList.objects.bulk_create(default_working_lists)


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0163_initialize_past_experiences_checklist'),
    ]

    operations = [
        migrations.RunPython(code=initialize_default_working_lists, reverse_code=migrations.RunPython.noop),
    ]
