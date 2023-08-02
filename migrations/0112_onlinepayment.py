# Generated by Django 3.2.20 on 2023-08-10 14:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0111_generaleducationadmission_cycle_pursuit'),
    ]

    operations = [
        migrations.CreateModel(
            name='OnlinePayment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_id', models.CharField(max_length=14)),
                ('status', models.CharField(choices=[('OPEN', 'open'), ('CANCELED', 'canceled'), ('PENDING', 'pending'), ('EXPIRED', 'expired'), ('FAILED', 'failed'), ('PAID', 'paid')], max_length=10)),
                ('expiration_date', models.DateTimeField(null=True)),
                ('method', models.CharField(blank=True, choices=[('BANCONTACT', 'bancontact'), ('CREDIT_CARD', 'creditcard'), ('BANK_TRANSFER', 'banktransfer')], max_length=17)),
                ('creation_date', models.DateTimeField()),
                ('updated_date', models.DateTimeField()),
                ('dashboard_url', models.URLField()),
                ('checkout_url', models.URLField(blank=True)),
                ('payment_url', models.URLField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=6)),
                ('admission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='online_payments', to='admission.baseadmission')),
            ],
        ),
    ]
