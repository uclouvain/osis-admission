# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
from contextlib import suppress

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from osis_document.contrib import FileField
from rest_framework.settings import api_settings

from admission.contrib.models.base import BaseAdmission, BaseAdmissionQuerySet, admission_directory_path
from admission.ddd.admission.dtos.conditions import InfosDetermineesDTO
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
    ChoixInscriptionATitre,
    ChoixTypeAdresseFacturation,
    ChoixMoyensDecouverteFormation,
    ChoixEdition,
    ChoixMotifAttente,
    ChoixMotifRefus,
)
from base.models.academic_year import AcademicYear
from base.models.person import Person
from osis_common.ddd.interface import BusinessException


class ContinuingEducationAdmission(BaseAdmission):
    status = models.CharField(
        choices=ChoixStatutPropositionContinue.choices(),
        max_length=30,
        default=ChoixStatutPropositionContinue.EN_BROUILLON.name,
        # db_comment='Proposition.statut',
    )

    diploma_equivalence = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Diploma equivalence'),
        #         db_comment='Proposition.equivalence_diplome',
    )

    residence_permit = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Residence permit covering the entire course'),
        max_files=1,
        #         db_comment='Proposition.copie_titre_sejour',
    )

    registration_as = models.CharField(
        blank=True,
        choices=ChoixInscriptionATitre.choices(),
        default='',
        max_length=30,
        verbose_name=_('Registration as'),
        #         db_comment='Proposition.inscription_a_titre',
    )

    head_office_name = models.CharField(
        blank=True,
        default='',
        max_length=255,
        verbose_name=_('Head office name'),
        #         db_comment='Proposition.nom_siege_social',
    )

    unique_business_number = models.CharField(
        blank=True,
        default='',
        max_length=255,
        verbose_name=_('Unique business number'),
        #         db_comment='Proposition.numero_unique_entreprise',
    )

    vat_number = models.CharField(
        blank=True,
        default='',
        max_length=255,
        verbose_name=_('VAT number'),
        #         db_comment='Proposition.numero_tva_entreprise',
    )

    professional_email = models.CharField(
        blank=True,
        default='',
        max_length=255,
        verbose_name=_('Professional email'),
        #         db_comment='Proposition.adresse_mail_professionnelle',
    )

    billing_address_type = models.CharField(
        blank=True,
        choices=ChoixTypeAdresseFacturation.choices(),
        default='',
        max_length=30,
        verbose_name=_('Billing address type'),
        #         db_comment='Proposition.type_adresse_facturation',
    )

    billing_address_recipient = models.CharField(
        blank=True,
        default='',
        max_length=255,
        verbose_name=_('Billing address recipient'),
        #         db_comment='Proposition.adresse_facturation.destinataire',
    )

    billing_address_street = models.CharField(
        blank=True,
        default='',
        max_length=255,
        verbose_name=_('Billing address street'),
        #         db_comment='Proposition.adresse_facturation.rue',
    )

    billing_address_street_number = models.CharField(
        blank=True,
        default='',
        max_length=20,
        verbose_name=_('Billing address street number'),
        #         db_comment='Proposition.adresse_facturation.numero_rue',
    )

    billing_address_postal_box = models.CharField(
        blank=True,
        default='',
        max_length=20,
        verbose_name=_('Billing address postal box'),
        #         db_comment='Proposition.adresse_facturation.boite_postale',
    )

    billing_address_postal_code = models.CharField(
        blank=True,
        default='',
        max_length=20,
        verbose_name=_('Billing address postal code'),
        #         db_comment='Proposition.adresse_facturation.code_postal',
    )

    billing_address_city = models.CharField(
        blank=True,
        default='',
        max_length=255,
        verbose_name=_('Billing address city'),
        #         db_comment='Proposition.adresse_facturation.ville',
    )

    billing_address_country = models.ForeignKey(
        'reference.Country',
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_('Billing address country'),
        #         db_comment='Proposition.adresse_facturation.pays',
    )

    additional_documents = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Additional documents'),
        max_files=10,
        #         db_comment='Proposition.documents_additionnels',
    )

    motivations = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Motivations'),
        max_length=1000,
        #         db_comment='Proposition.motivations',
    )

    ways_to_find_out_about_the_course = ArrayField(
        models.CharField(max_length=30, choices=ChoixMoyensDecouverteFormation.choices()),
        blank=True,
        default=list,
        verbose_name=_('How did the candidate hear about this course?'),
        #         db_comment='Proposition.moyens_decouverte_formation',
    )

    other_way_to_find_out_about_the_course = models.TextField(
        blank=True,
        default='',
        verbose_name=_('How else did the candidate hear about this course?'),
        max_length=1000,
        #         db_comment='Proposition.autre_moyen_decouverte_formation',
    )

    interested_mark = models.BooleanField(
        verbose_name=_("Interested mark"),
        null=True,
        #         db_comment='Proposition.marque_d_interet',
    )

    edition = models.CharField(
        choices=ChoixEdition.choices(),
        max_length=30,
        verbose_name=_("Edition"),
        default='',
        blank=True,
        #         db_comment='Proposition.edition',
    )

    in_payement_order = models.BooleanField(
        verbose_name=_("In payement order"),
        null=True,
        #         db_comment='Proposition.en_ordre_de_paiement',
    )

    reduced_rights = models.BooleanField(
        verbose_name=_("Reduced rights"),
        null=True,
        #         db_comment='Proposition.droits_reduits',
    )

    pay_by_training_cheque = models.BooleanField(
        verbose_name=_("Pay by training cheque"),
        null=True,
        #         db_comment='Proposition.paye_par_cheque_formation',
    )

    cep = models.BooleanField(
        verbose_name=_("CEP"),
        null=True,
        #         db_comment='Proposition.cep',
    )

    payement_spread = models.BooleanField(
        verbose_name=_("Payement spread"),
        null=True,
        #         db_comment='Proposition.etalement_des_paiments',
    )

    training_spread = models.BooleanField(
        verbose_name=_("Training spread"),
        null=True,
        #         db_comment='Proposition.etalement_de_la_formation',
    )

    experience_knowledge_valorisation = models.BooleanField(
        verbose_name=_("Experience knowledge valorisation"),
        null=True,
        #         db_comment='Proposition.valorisation_des_acquis_d_experience',
    )

    assessment_test_presented = models.BooleanField(
        verbose_name=_("Assessment test presented"),
        null=True,
        #         db_comment='Proposition.a_presente_l_epreuve_d_evaluation',
    )

    assessment_test_succeeded = models.BooleanField(
        verbose_name=_("Assessment test succeeded"),
        null=True,
        #         db_comment='Proposition.a_reussi_l_epreuve_d_evaluation',
    )

    certificate_provided = models.BooleanField(
        verbose_name=_("Certificate provided"),
        null=True,
        #         db_comment='Proposition.diplome_produit',
    )

    tff_label = models.TextField(
        verbose_name=_("TFF label"),
        default='',
        blank=True,
        #         db_comment='Proposition.intitule_du_tff',
    )

    last_email_sent_at = models.DateTimeField(
        verbose_name=_("Last email sent the"),
        null=True,
        blank=True,
        #         db_comment='Proposition.decision_dernier_mail_envoye_le',
    )

    last_email_sent_by = models.ForeignKey(
        to="base.Person",
        verbose_name=_("Last email sent by"),
        on_delete=models.SET_NULL,
        related_name='+',
        null=True,
        blank=True,
        #         db_comment='Proposition.decision_dernier_mail_envoye_par',
    )

    on_hold_reason = models.TextField(
        verbose_name=_("On hold reason"),
        choices=ChoixMotifAttente.choices(),
        blank=True,
        #         db_comment='Proposition.motif_de_mise_en_attente',
    )

    on_hold_reason_other = models.TextField(
        verbose_name=_("On hold other reason"),
        default='',
        blank=True,
        #         db_comment='Proposition.motif_de_mise_en_attente_autre',
    )

    approval_condition_by_faculty = models.TextField(
        verbose_name=_("Approval condition by faculty"),
        default='',
        blank=True,
        #         db_comment='Proposition.condition_d_approbation_par_la_faculte',
    )

    refusal_reason = models.TextField(
        verbose_name=_("Refusal reason"),
        choices=ChoixMotifRefus.choices(),
        blank=True,
        #         db_comment='Proposition.motif_de_refus',
    )

    refusal_reason_other = models.TextField(
        verbose_name=_("Refusal reason other"),
        default='',
        blank=True,
        #         db_comment='Proposition.motif_de_refus_autre',
    )

    cancel_reason = models.TextField(
        verbose_name=_("Cancel reason"),
        default='',
        blank=True,
        #         db_comment='Proposition.motif_d_annulation',
    )

    class Meta:
        verbose_name = _("Continuing education admission")
        ordering = ('-created_at',)
        # db_table_comment = "Modèle utilisé dans le cadre d'une admission pour une formation continue"
        permissions = []

    def update_detailed_status(self, author: 'Person' = None):
        from admission.ddd.admission.formation_continue.commands import (
            VerifierPropositionQuery,
            DeterminerAnneeAcademiqueEtPotQuery,
        )
        from admission.utils import gather_business_exceptions
        from infrastructure.messages_bus import message_bus_instance

        error_key = api_settings.NON_FIELD_ERRORS_KEY
        self.detailed_status = gather_business_exceptions(VerifierPropositionQuery(self.uuid)).get(error_key, [])
        self.last_update_author = author

        update_fields = [
            'detailed_status',
            'determined_academic_year',
            'determined_pool',
        ]

        if author:
            self.last_update_author = author
            self.modified_at = datetime.datetime.now()
            update_fields.append('last_update_author')
            update_fields.append('modified_at')

        with suppress(BusinessException):
            dto: 'InfosDetermineesDTO' = message_bus_instance.invoke(DeterminerAnneeAcademiqueEtPotQuery(self.uuid))
            self.determined_academic_year = AcademicYear.objects.get(year=dto.annee)
            self.determined_pool = dto.pool.name

        self.save(update_fields=update_fields)

    def update_requested_documents(self):
        """Update the requested documents depending on the admission data."""
        from admission.ddd.admission.formation_continue.commands import (
            RecalculerEmplacementsDocumentsNonLibresPropositionCommand,
        )
        from infrastructure.messages_bus import message_bus_instance

        message_bus_instance.invoke(RecalculerEmplacementsDocumentsNonLibresPropositionCommand(self.uuid))


class ContinuingEducationAdmissionManager(models.Manager.from_queryset(BaseAdmissionQuerySet)):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "candidate__country_of_citizenship",
                "training__academic_year",
                "training__education_group_type",
                "training__specificiufcinformations",
                "determined_academic_year",
            )
            .annotate_pool_end_date()
        )

    def for_dto(self):
        return (
            self.get_queryset()
            .select_related(
                "training__main_domain",
                "training__enrollment_campus",
                "billing_address_country",
            )
            .annotate_campus()
            .annotate_training_management_entity()
            .annotate_training_management_faculty()
            .annotate_with_reference()
            .annotate_with_student_registration_id()
            .annotate_with_status_update_date()
            .annotate_several_admissions_in_progress()
            .annotate_submitted_profile_countries_names()
        )


class ContinuingEducationAdmissionProxy(ContinuingEducationAdmission):
    """Proxy model of base.ContinuingEducationAdmission"""

    objects = ContinuingEducationAdmissionManager()

    class Meta:
        proxy = True
