# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Optional

from django.conf import settings
from django.utils.translation import get_language

from admission.auth.roles.candidate import Candidate
from admission.contrib.models import ContinuingEducationAdmissionProxy, Accounting
from admission.contrib.models.continuing_education import ContinuingEducationAdmission
from admission.ddd.admission.domain.builder.formation_identity import FormationIdentityBuilder
from admission.ddd.admission.dtos import AdressePersonnelleDTO
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.formation_continue.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_continue.domain.model._adresse import Adresse
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutProposition,
    ChoixInscriptionATitre,
    ChoixTypeAdresseFacturation,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.formation_continue.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.formation_continue.dtos import PropositionDTO
from admission.ddd.admission.formation_continue.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.repository.i_proposition import formater_reference
from admission.infrastructure.admission.repository.proposition import GlobalPropositionRepository
from base.models.academic_year import AcademicYear
from admission.infrastructure.admission.formation_continue.repository._comptabilite import get_accounting_from_admission
from base.models.education_group_year import EducationGroupYear
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.person import Person
from osis_common.ddd.interface import ApplicationService
from reference.models.country import Country


class PropositionRepository(GlobalPropositionRepository, IPropositionRepository):
    @classmethod
    def search(
        cls,
        entity_ids: Optional[List['PropositionIdentity']] = None,
        matricule_candidat: str = None,
        **kwargs,
    ) -> List['Proposition']:
        raise NotImplementedError

    @classmethod
    def search_dto(cls, matricule_candidat: Optional[str] = '') -> List['PropositionDTO']:
        # Default queryset
        qs = ContinuingEducationAdmissionProxy.objects.all()

        # Add filters
        if matricule_candidat:
            qs = qs.filter(candidate__global_id=matricule_candidat)

        # Return dtos
        return [cls._load_dto(proposition) for proposition in qs]

    @classmethod
    def delete(cls, entity_id: 'PropositionIdentity', **kwargs: ApplicationService) -> None:
        raise NotImplementedError

    @classmethod
    def get(cls, entity_id: 'PropositionIdentity') -> 'Proposition':
        try:
            return cls._load(
                ContinuingEducationAdmissionProxy.objects.select_related('billing_address_country').get(
                    uuid=entity_id.uuid
                )
            )
        except ContinuingEducationAdmission.DoesNotExist:
            raise PropositionNonTrouveeException

    @classmethod
    def save(cls, entity: 'Proposition') -> None:
        training = EducationGroupYear.objects.get(
            acronym=entity.formation_id.sigle,
            academic_year__year=entity.formation_id.annee,
        )
        candidate = Person.objects.get(global_id=entity.matricule_candidat)

        adresse_facturation = (
            {
                'billing_address_recipient': entity.adresse_facturation.destinataire,
                'billing_address_street': entity.adresse_facturation.rue,
                'billing_address_street_number': entity.adresse_facturation.numero_rue,
                'billing_address_postal_box': entity.adresse_facturation.boite_postale,
                'billing_address_postal_code': entity.adresse_facturation.code_postal,
                'billing_address_city': entity.adresse_facturation.ville,
                'billing_address_country': Country.objects.filter(
                    iso_code=entity.adresse_facturation.pays,
                ).first()
                if entity.adresse_facturation
                else None,
                'billing_address_place': entity.adresse_facturation.lieu_dit,
            }
            if entity.adresse_facturation
            else {
                'billing_address_recipient': '',
                'billing_address_street': '',
                'billing_address_street_number': '',
                'billing_address_postal_box': '',
                'billing_address_postal_code': '',
                'billing_address_city': '',
                'billing_address_country': None,
                'billing_address_place': '',
            }
        )

        admission, _ = ContinuingEducationAdmission.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            defaults={
                'candidate': candidate,
                'training': training,
                'reference': entity.reference,
                'determined_academic_year': (
                    entity.annee_calculee and AcademicYear.objects.get(year=entity.annee_calculee)
                ),
                'determined_pool': entity.pot_calcule and entity.pot_calcule.name,
                'status': entity.statut.name,
                'specific_question_answers': entity.reponses_questions_specifiques,
                'curriculum': entity.curriculum,
                'diploma_equivalence': entity.equivalence_diplome,
                'confirmation_elements': entity.elements_confirmation,
                'registration_as': entity.inscription_a_titre.name if entity.inscription_a_titre else '',
                'head_office_name': entity.nom_siege_social,
                'unique_business_number': entity.numero_unique_entreprise,
                'vat_number': entity.numero_tva_entreprise,
                'professional_email': entity.adresse_mail_professionnelle,
                'billing_address_type': entity.type_adresse_facturation.name if entity.type_adresse_facturation else '',
                **adresse_facturation,
            },
        )

        Candidate.objects.get_or_create(person=candidate)
        cls._sauvegarder_comptabilite(admission, entity)

    @classmethod
    def _sauvegarder_comptabilite(cls, admission: ContinuingEducationAdmission, entity: Proposition):
        Accounting.objects.update_or_create(
            admission=admission,
            defaults={
                'solidarity_student': entity.comptabilite.etudiant_solidaire,
                'account_number_type': entity.comptabilite.type_numero_compte.name
                if entity.comptabilite.type_numero_compte
                else '',
                'iban_account_number': entity.comptabilite.numero_compte_iban,
                'valid_iban': entity.comptabilite.iban_valide,
                'other_format_account_number': entity.comptabilite.numero_compte_autre_format,
                'bic_swift_code': entity.comptabilite.code_bic_swift_banque,
                'account_holder_first_name': entity.comptabilite.prenom_titulaire_compte,
                'account_holder_last_name': entity.comptabilite.nom_titulaire_compte,
            },
        )

    @classmethod
    def get_dto(cls, entity_id: 'PropositionIdentity') -> 'PropositionDTO':
        return cls._load_dto(ContinuingEducationAdmissionProxy.objects.get(uuid=entity_id.uuid))

    @classmethod
    def _load(cls, admission: 'ContinuingEducationAdmission') -> 'Proposition':
        return Proposition(
            entity_id=PropositionIdentityBuilder().build_from_uuid(admission.uuid),
            matricule_candidat=admission.candidate.global_id,
            statut=ChoixStatutProposition[admission.status],
            creee_le=admission.created,
            modifiee_le=admission.modified,
            reference=admission.reference,
            formation_id=FormationIdentityBuilder.build(
                sigle=admission.training.acronym,
                annee=admission.training.academic_year.year,
            ),
            annee_calculee=admission.determined_academic_year and admission.determined_academic_year.year,
            pot_calcule=admission.determined_pool and AcademicCalendarTypes[admission.determined_pool],
            reponses_questions_specifiques=admission.specific_question_answers,
            curriculum=admission.curriculum,
            equivalence_diplome=admission.diploma_equivalence,
            comptabilite=get_accounting_from_admission(admission=admission),
            elements_confirmation=admission.confirmation_elements,
            inscription_a_titre=ChoixInscriptionATitre[admission.registration_as]
            if admission.registration_as
            else None,
            nom_siege_social=admission.head_office_name,
            numero_unique_entreprise=admission.unique_business_number,
            numero_tva_entreprise=admission.vat_number,
            adresse_mail_professionnelle=admission.professional_email,
            type_adresse_facturation=ChoixTypeAdresseFacturation[admission.billing_address_type]
            if admission.billing_address_type
            else None,
            adresse_facturation=Adresse(
                rue=admission.billing_address_street,
                numero_rue=admission.billing_address_street_number,
                code_postal=admission.billing_address_postal_code,
                ville=admission.billing_address_city,
                pays=admission.billing_address_country.iso_code if admission.billing_address_country else '',
                destinataire=admission.billing_address_recipient,
                boite_postale=admission.billing_address_postal_box,
                lieu_dit=admission.billing_address_place,
            )
            if admission.billing_address_type == ChoixTypeAdresseFacturation.AUTRE.name
            else None,
        )

    @classmethod
    def _load_dto(cls, admission: ContinuingEducationAdmission) -> 'PropositionDTO':
        return PropositionDTO(
            uuid=admission.uuid,
            statut=admission.status,
            creee_le=admission.created,
            modifiee_le=admission.modified,
            erreurs=admission.detailed_status or [],
            date_fin_pot=admission.pool_end_date,  # from annotation
            formation=FormationDTO(
                sigle=admission.training.acronym,
                annee=admission.training.academic_year.year,
                intitule=admission.training.title
                if get_language() == settings.LANGUAGE_CODE
                else admission.training.title_english,
                campus=admission.teaching_campus or '',  # from annotation
                type=admission.training.education_group_type.name,
                code_domaine=admission.training.main_domain.code if admission.training.main_domain else '',
                campus_inscription=admission.training.enrollment_campus.name,
                sigle_entite_gestion=admission.sigle_entite_gestion,  # from annotation
            ),
            reference=formater_reference(
                reference=admission.reference,
                nom_campus_inscription=admission.training.enrollment_campus.name,
                sigle_entite_gestion=admission.sigle_entite_gestion,  # From annotation
                annee=admission.training.academic_year.year,
            ),
            annee_calculee=admission.determined_academic_year and admission.determined_academic_year.year,
            pot_calcule=admission.determined_pool or '',
            matricule_candidat=admission.candidate.global_id,
            prenom_candidat=admission.candidate.first_name,
            nom_candidat=admission.candidate.last_name,
            reponses_questions_specifiques=admission.specific_question_answers,
            curriculum=admission.curriculum,
            equivalence_diplome=admission.diploma_equivalence,
            inscription_a_titre=admission.registration_as,
            nom_siege_social=admission.head_office_name,
            numero_unique_entreprise=admission.unique_business_number,
            numero_tva_entreprise=admission.vat_number,
            adresse_mail_professionnelle=admission.professional_email,
            type_adresse_facturation=admission.billing_address_type,
            adresse_facturation=AdressePersonnelleDTO(
                rue=admission.billing_address_street,
                numero_rue=admission.billing_address_street_number,
                code_postal=admission.billing_address_postal_code,
                ville=admission.billing_address_city,
                pays=admission.billing_address_country.iso_code if admission.billing_address_country else '',
                destinataire=admission.billing_address_recipient,
                boite_postale=admission.billing_address_postal_box,
                lieu_dit=admission.billing_address_place,
            )
            if admission.billing_address_type == ChoixTypeAdresseFacturation.AUTRE.name
            else None,
        )
