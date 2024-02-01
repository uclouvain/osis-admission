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

from typing import List, Optional

from django.conf import settings
from django.utils.translation import get_language

from admission.auth.roles.candidate import Candidate
from admission.contrib.models import ContinuingEducationAdmissionProxy
from admission.contrib.models.continuing_education import ContinuingEducationAdmission
from admission.ddd.admission.domain.builder.formation_identity import FormationIdentityBuilder
from admission.ddd.admission.dtos import AdressePersonnelleDTO
from admission.ddd.admission.dtos.campus import CampusDTO
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.formation_continue.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.formation_continue.domain.model._adresse import Adresse
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
    ChoixInscriptionATitre,
    ChoixTypeAdresseFacturation,
    ChoixMoyensDecouverteFormation,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition, PropositionIdentity
from admission.ddd.admission.formation_continue.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.formation_continue.dtos import PropositionDTO
from admission.ddd.admission.formation_continue.repository.i_proposition import IPropositionRepository
from admission.infrastructure.admission.repository.proposition import GlobalPropositionRepository
from base.models.academic_year import AcademicYear
from base.models.campus import Campus as CampusDb
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
        qs = ContinuingEducationAdmissionProxy.objects.for_dto().all()

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
                'submitted_at': entity.soumise_le,
                'specific_question_answers': entity.reponses_questions_specifiques,
                'curriculum': entity.curriculum,
                'diploma_equivalence': entity.equivalence_diplome,
                'residence_permit': entity.copie_titre_sejour,
                'confirmation_elements': entity.elements_confirmation,
                'additional_documents': entity.documents_additionnels,
                'registration_as': entity.inscription_a_titre.name if entity.inscription_a_titre else '',
                'head_office_name': entity.nom_siege_social,
                'unique_business_number': entity.numero_unique_entreprise,
                'vat_number': entity.numero_tva_entreprise,
                'professional_email': entity.adresse_mail_professionnelle,
                'billing_address_type': entity.type_adresse_facturation.name if entity.type_adresse_facturation else '',
                'motivations': entity.motivations,
                'ways_to_find_out_about_the_course': [way.name for way in entity.moyens_decouverte_formation],
                **adresse_facturation,
            },
        )

        Candidate.objects.get_or_create(person=candidate)

    @classmethod
    def get_dto(cls, entity_id: 'PropositionIdentity') -> 'PropositionDTO':
        return cls._load_dto(ContinuingEducationAdmissionProxy.objects.for_dto().get(uuid=entity_id.uuid))

    @classmethod
    def _load(cls, admission: 'ContinuingEducationAdmission') -> 'Proposition':
        return Proposition(
            entity_id=PropositionIdentityBuilder().build_from_uuid(admission.uuid),
            matricule_candidat=admission.candidate.global_id,
            statut=ChoixStatutPropositionContinue[admission.status],
            creee_le=admission.created_at,
            modifiee_le=admission.modified_at,
            soumise_le=admission.submitted_at,
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
            copie_titre_sejour=admission.residence_permit,
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
            )
            if admission.billing_address_type == ChoixTypeAdresseFacturation.AUTRE.name
            else None,
            documents_additionnels=admission.additional_documents,
            motivations=admission.motivations,
            moyens_decouverte_formation=[
                ChoixMoyensDecouverteFormation[way] for way in admission.ways_to_find_out_about_the_course
            ],
        )

    @classmethod
    def _load_dto(cls, admission: ContinuingEducationAdmission) -> 'PropositionDTO':
        language_is_french = get_language() == settings.LANGUAGE_CODE_FR
        campus = (
            CampusDb.objects.select_related('country')
            .filter(
                teaching_campus__educationgroupversion__version_name='',
                teaching_campus__educationgroupversion__transition_name='',
                teaching_campus__educationgroupversion__offer_id=admission.training_id,
            )
            .first()
        )

        return PropositionDTO(
            uuid=admission.uuid,
            statut=admission.status,
            creee_le=admission.created_at,
            modifiee_le=admission.modified_at,
            soumise_le=admission.submitted_at,
            erreurs=admission.detailed_status or [],
            date_fin_pot=admission.pool_end_date,  # from annotation
            formation=FormationDTO(
                sigle=admission.training.acronym,
                code=admission.training.partial_acronym,
                annee=admission.training.academic_year.year,
                date_debut=admission.training.academic_year.start_date,
                intitule=admission.training.title if language_is_french else admission.training.title_english,
                intitule_fr=admission.training.title,
                intitule_en=admission.training.title_english,
                campus=CampusDTO(
                    nom=campus.name,
                    code_postal=campus.postal_code,
                    ville=campus.city,
                    pays_iso_code=campus.country.iso_code if campus.country else '',
                    nom_pays=campus.country.name if campus.country else '',
                    rue=campus.street,
                    numero_rue=campus.street_number,
                    boite_postale=campus.postal_box,
                    localisation=campus.location,
                    email=campus.email,
                )
                if campus is not None
                else None,
                type=admission.training.education_group_type.name,
                code_domaine=admission.training.main_domain.code if admission.training.main_domain else '',
                campus_inscription=CampusDTO(
                    nom=admission.training.enrollment_campus.name,
                    code_postal=admission.training.enrollment_campus.postal_code,
                    ville=admission.training.enrollment_campus.city,
                    pays_iso_code=admission.training.enrollment_campus.country.iso_code
                    if admission.training.enrollment_campus.country
                    else '',
                    nom_pays=admission.training.enrollment_campus.country.name
                    if admission.training.enrollment_campus.country
                    else '',
                    rue=admission.training.enrollment_campus.street,
                    numero_rue=admission.training.enrollment_campus.street_number,
                    boite_postale=admission.training.enrollment_campus.postal_box,
                    localisation=admission.training.enrollment_campus.location,
                    email=admission.training.enrollment_campus.email,
                )
                if admission.training.enrollment_campus is not None
                else None,
                sigle_entite_gestion=admission.training_management_faculty
                or admission.sigle_entite_gestion,  # from annotation
            ),
            reference=admission.formatted_reference,
            annee_calculee=admission.determined_academic_year and admission.determined_academic_year.year,
            pot_calcule=admission.determined_pool or '',
            matricule_candidat=admission.candidate.global_id,
            prenom_candidat=admission.candidate.first_name,
            nom_candidat=admission.candidate.last_name,
            pays_nationalite_candidat=admission.candidate.country_of_citizenship.iso_code
            if admission.candidate.country_of_citizenship
            else '',
            pays_nationalite_ue_candidat=admission.candidate.country_of_citizenship
            and admission.candidate.country_of_citizenship.european_union,
            reponses_questions_specifiques=admission.specific_question_answers,
            curriculum=admission.curriculum,
            equivalence_diplome=admission.diploma_equivalence,
            copie_titre_sejour=admission.residence_permit,
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
                nom_pays=getattr(admission.billing_address_country, 'name' if language_is_french else 'name_en')
                if admission.billing_address_country
                else '',
                destinataire=admission.billing_address_recipient,
                boite_postale=admission.billing_address_postal_box,
            )
            if admission.billing_address_type == ChoixTypeAdresseFacturation.AUTRE.name
            else None,
            elements_confirmation=admission.confirmation_elements,
            pdf_recapitulatif=admission.pdf_recap,
            documents_additionnels=admission.additional_documents,
            motivations=admission.motivations,
            moyens_decouverte_formation=admission.ways_to_find_out_about_the_course,
        )
