# Generated by Django 3.2.25 on 2024-07-08 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0196_alter_workinglist_quarantine'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generaleducationadmission',
            name='financability_dispensation_status',
            field=models.CharField(blank=True, choices=[('NON_CONCERNE', 'NON_CONCERNE'), ('CANDIDAT_NOTIFIE', 'CANDIDAT_NOTIFIE'), ('ABANDON_DU_CANDIDAT', 'ABANDON_DU_CANDIDAT'), ('REFUS_DE_DEROGATION_FACULTAIRE', 'REFUS_DE_DEROGATION_FACULTAIRE'), ('ACCORD_DE_DEROGATION_FACULTAIRE', 'ACCORD_DE_DEROGATION_FACULTAIRE')], default='', max_length=100, verbose_name='Financability dispensation status'),
        ),
        migrations.AlterField(
            model_name='generaleducationadmission',
            name='financability_rule',
            field=models.CharField(blank=True, choices=[('PREMIERE_INSCRIPTION', 'Première inscription au cycle'), ('FINANCABLE_D_OFFICE', "Financable d'office"), ('DROIT_A_ANNEES_SUPPLEMENTAIRES', 'A droit à des années supplémentaires'), ('PARCOURS_A_TOILETTER', 'Parcours antérieur à toiletter'), ('REPRISE_APRES_5_ANS', 'Reprise après interruption de 5 ans'), ('DOUBLE_INSCRIPTION_MEME_CYCLE_A_CLARIFIER', 'Double inscription du même cycle'), ('A_PASSE_CONCOURS_2X', 'A passé 2 fois le concours'), ('ACQUIS_100_POURCENT_EN_N_MOINS_1', 'A acquis 100% année précédente'), ('PLUS_FINANCABLE', "N'est plus financable"), ('CREDITS_ACQUIS_A_CLARIFIER', 'Crédits acquis à clarifier'), ('MORATOIRE_ARTICLE2', 'Moratoire Article 2'), ('FINANCABILITE_2023_A_CARIFIER', 'Financabilité 2023 à clarifier'), ('PREMIERE_INSCRIPTION_FORMATION_DOCTORALE', 'Première inscription à la formation doctorale'), ('VALIDE_60_CREDITS_BLOC_1', 'A validé 60 crédits de bloc 1'), ('N_A_PAS_VALIDE_60_CREDITS_BLOC_1', "N'a pas validé 60 crédits de bloc 1"), ('REUSSI_1_UE_BLOC_1', 'A réussi 1 UE du bloc 1'), ('N_A_PAS_REUSSI_1_UE_BLOC_1', "N'a pas réussi 1 UE du bloc 1"), ('VALIDE_50_CREDITS_BLOC_1', 'A validé 50 crédits de bloc 1 (réorientation après 2 ans)'), ('N_A_PAS_VALIDE_50_CREDITS_BLOC_1', "N'a pas validé 50 crédits de bloc 1 (réorientation après 2 ans)"), ('VALIDE_120_CREDITS_BACHELIER', 'A validé 120 crédits du bachelier'), ('N_A_PAS_VALIDE_120_CREDITS_BACHELIER', "N'a pas validé 120 crédits du bachelier"), ('CREDIT_BLOC1_A_CLARIFIER', 'Crédits du bloc 1 à clarifier'), ('MORATOIRE_ARTICLE3', 'Moratoire Article 3'), ('N_A_PAS_VALIDE_MODULE_COMPLEMENTAIRE_EN_2_ANS', "N'a pas validé le module complémentaire en 2 ans"), ('A_ATTEINT_BALISES_MASTER', 'A atteint les balises de Master'), ('N_A_PAS_ATTEINT_BALISES_MASTER', "N'a pas atteint les balises de Master"), ('CREDIT_MODULE_COMPLEMENTAIRE_A_CLARIFIER', 'Crédits du module complémentaire à clarifier')], default='', max_length=100, verbose_name='Financability rule'),
        ),
    ]
