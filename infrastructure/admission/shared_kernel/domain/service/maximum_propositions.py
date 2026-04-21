##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from typing import Optional

from django.db.models import Count, Q

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    STATUTS_PROPOSITION_AVANT_SOUMISSION,
    STATUTS_PROPOSITION_DOCTORALE_TERMINEE,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    PropositionIdentity,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    STATUTS_PROPOSITION_GENERALE_NON_SOUMISE_OU_FRAIS_DOSSIER_EN_ATTENTE,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_HORS_FRAIS_DOSSIER_CLOTUREE_ET_AUTORISEE,
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    Proposition as PropositionGenerale,
)
from admission.ddd.admission.shared_kernel.domain.service.i_maximum_propositions import (
    IMaximumPropositionsAutorisees,
)
from admission.ddd.admission.shared_kernel.domain.validator.exceptions import (
    DemandeEnBrouillonDejaExistantePourCetteFormationException,
    DemandePourCetteFormationDejaEnvoyeeException,
)
from admission.models import (
    ContinuingEducationAdmission,
    DoctorateAdmission,
    GeneralEducationAdmission,
)
from base.models.person import Person


class MaximumPropositionsAutorisees(IMaximumPropositionsAutorisees):
    @classmethod
    def nb_propositions_envoyees_formation_generale(cls, matricule: str, annee_cible: int) -> int:
        return GeneralEducationAdmission.objects.filter(
            candidate__global_id=matricule,
            status__in=STATUTS_PROPOSITION_GENERALE_SOUMISE_HORS_FRAIS_DOSSIER_CLOTUREE_ET_AUTORISEE,
            determined_academic_year__year=annee_cible,
        ).count()

    @classmethod
    def nb_propositions_envoyees_formation_continue(cls, matricule: str) -> int:
        return ContinuingEducationAdmission.objects.filter(
            candidate__global_id=matricule,
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
        ).count()

    @classmethod
    def nb_propositions_en_cours(cls, matricule: str) -> int:
        nb_propositions = (
            Person.objects.annotate(
                doctorate_propositions_nb=Count(
                    'baseadmissions__doctorateadmission',
                    filter=Q(
                        baseadmissions__doctorateadmission__status__in=STATUTS_PROPOSITION_AVANT_SOUMISSION,
                    ),
                ),
                general_propositions_nb=Count(
                    'baseadmissions__generaleducationadmission',
                    filter=Q(
                        baseadmissions__generaleducationadmission__status=(
                            ChoixStatutPropositionGenerale.EN_BROUILLON.name
                        ),
                    ),
                ),
                continuing_propositions_nb=Count(
                    'baseadmissions__continuingeducationadmission',
                    filter=Q(
                        baseadmissions__continuingeducationadmission__status=(
                            ChoixStatutPropositionContinue.EN_BROUILLON.name
                        ),
                    ),
                ),
            )
            .values_list(
                'doctorate_propositions_nb',
                'general_propositions_nb',
                'continuing_propositions_nb',
            )
            .get(global_id=matricule)
        )
        return sum(nb_propositions)

    @classmethod
    def nb_propositions_en_cours_formation_doctorale(
        cls,
        matricule: str,
        proposition_identity: Optional[PropositionIdentity] = None,
    ) -> int:
        qs = DoctorateAdmission.objects.filter(candidate__global_id=matricule).exclude(
            status__in=STATUTS_PROPOSITION_DOCTORALE_TERMINEE
        )

        if proposition_identity:
            qs = qs.exclude(uuid=proposition_identity.uuid)

        return qs.count()

    @classmethod
    def verifier_une_seule_demande_envoyee_par_formation_generale_par_annee(
        cls,
        proposition_candidat: PropositionGenerale,
        annee_soumise: int = None,
    ):
        target_year = annee_soumise or proposition_candidat.annee_calculee or proposition_candidat.formation_id.annee

        has_similar_application = (
            GeneralEducationAdmission.objects.filter(
                candidate__global_id=proposition_candidat.matricule_candidat,
                training__acronym=proposition_candidat.formation_id.sigle,
                training__academic_year__year=target_year,
            )
            .exclude(
                status__in=STATUTS_PROPOSITION_GENERALE_NON_SOUMISE_OU_FRAIS_DOSSIER_EN_ATTENTE,
            )
            .exclude(
                uuid=proposition_candidat.entity_id.uuid,
            )
            .exists()
        )

        if has_similar_application:
            raise DemandePourCetteFormationDejaEnvoyeeException(training_year=target_year)

    @classmethod
    def verifier_une_seule_demande_non_soumise_par_formation_generale(
        cls,
        matricule_candidat: str,
        sigle_formation: str,
        uuid_proposition: str = '',
    ):
        qs = GeneralEducationAdmission.objects.filter(
            candidate__global_id=matricule_candidat,
            training__acronym=sigle_formation,
            status__in=[
                ChoixStatutPropositionGenerale.EN_BROUILLON.name,
                ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
            ],
        )

        if uuid_proposition:
            qs = qs.exclude(uuid=uuid_proposition)

        similar_application_uuid = qs.values_list('uuid', flat=True).first()

        if similar_application_uuid:
            raise DemandeEnBrouillonDejaExistantePourCetteFormationException(
                admission_context='general-education',
                admission_uuid=str(similar_application_uuid),
            )
