# Generated by Django 3.2.25 on 2024-06-18 09:42

from django.db import migrations
from django.db.models import F


def create_financabilite_reasons(apps, schema_editor):
    RefusalReason = apps.get_model('admission', 'RefusalReason')
    RefusalReasonCategory = apps.get_model('admission', 'RefusalReasonCategory')
    reasons = [
        "Une dérogation pour non-finançabilité vous a déjà été accordée antérieurement. Malgré l’octroi de cette mesure de faveur, la faculté estime que le nombre de crédits acquis demeure insuffisant.",
        "La faculté estime que vous n’apportez la preuve d’aucune circonstance exceptionnelle qui vous différencierait fondamentalement des autres étudiant·es et qui justifierait l’octroi d’une dérogation.",
        "Au vu des résultats obtenus dans le cadre de votre parcours antérieur, la faculté estime qu’il est préférable d’envisager une réorientation vers d'autres types de formation.",
        "La faculté estime que votre dossier ne comporte pas suffisamment d'éléments probants pour vous accorder une dérogation.",
        "La faculté estime que les informations contenues dans votre courrier ne permettent pas de justifier les échecs précédents. Les éléments fournis ne lui permettent pas de s'assurer d'une amélioration de votre cursus universitaire.",
        "Votre demande de dérogation a été introduite en dehors des délais fixés par la faculté conformément à l’article 22, al. 2 du Règlement général des études et des examens.",
        "La faculté est sensible aux éléments évoqués dans votre courrier mais estime que vos chances de réussite sont trop faibles pour vous accorder une dérogation.",
        "La faculté estime que votre rythme d'acquisition des crédits est trop faible pour pouvoir satisfaire les exigences en matière de finançabilité. Elle juge donc qu’il n’est pas raisonnable que vous poursuiviez ce projet de formation.",
        "La faculté estime que vos résultats académiques sont manifestement insuffisants, et ce d’autant plus que ces résultats se rapportent à des unités d’enseignement importantes dans le programme de cycle.",
    ]

    category = RefusalReasonCategory.objects.get(name='Finançabilité')
    order = 10
    for reason in reasons:
        RefusalReason.objects.create(
            order=order,
            name=reason,
            category=category,
        )
        order += 5
    RefusalReason.objects.filter(
        name="Vous ne remplissez pas les conditions de finançabilité liées à la nationalité (art. 3)."
    ).update(order=60)
    RefusalReason.objects.filter(
        name="Votre demande d'inscription vise des études qui ne donnent pas lieu à un financement (art. 2) - AESS / CAEAS"
    ).update(order=65)
    RefusalReason.objects.filter(
        name="Vous ne remplissez plus les conditions académiques de finançabilité (art. 5)."
    ).update(order=70)


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0190_baseadmission_internal_access_titles'),
    ]

    operations = [
        migrations.RunPython(create_financabilite_reasons, reverse_code=migrations.RunPython.noop),
    ]