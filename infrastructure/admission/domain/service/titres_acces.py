# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
# ##############################################################################
from datetime import timedelta
from typing import List

from django.db import models

from admission.ddd.admission.domain.service.i_titres_acces import ITitresAcces
from admission.ddd.admission.dtos.conditions import AdmissionConditionsDTO
from base.models.enums.got_diploma import GotDiploma
from base.models.person import Person
from osis_profile.models import (
    BelgianHighSchoolDiploma,
    EducationalExperience,
    ForeignHighSchoolDiploma,
    HighSchoolDiplomaAlternative,
    ProfessionalExperience,
    EducationalExperienceYear,
)
from osis_profile.models.enums.curriculum import Result
from reference.models.enums.cycle import Cycle


class TitresAcces(ITitresAcces):
    @classmethod
    def conditions_remplies(cls, matricule_candidat: str, equivalence_diplome: List[str]) -> AdmissionConditionsDTO:
        repondu_oui_ou_en_cours = models.Q(
            graduated_from_high_school__in=[GotDiploma.YES.name, GotDiploma.THIS_YEAR.name]
        )
        result = (
            Person.objects.alias(
                diplome_belge=models.Exists(BelgianHighSchoolDiploma.objects.filter(person_id=models.OuterRef('pk'))),
                diplome_etranger=models.Exists(
                    ForeignHighSchoolDiploma.objects.filter(person_id=models.OuterRef('pk'))
                ),
                diplome_alternatif=models.Exists(
                    HighSchoolDiplomaAlternative.objects.filter(person_id=models.OuterRef('pk'))
                ),
            )
            .annotate(
                # à la question sur la diplomation du secondaire, avoir répondu "oui" OU "en cours"
                #     ET (qu'il s'agisse d'études secondaires belges OU que l'on n'a pas le détail du diplôme)
                diplomation_secondaire_belge=models.ExpressionWrapper(
                    repondu_oui_ou_en_cours
                    & (models.Q(diplome_belge=True) | models.Q(diplome_etranger=False, diplome_alternatif=False)),
                    output_field=models.BooleanField(),
                ),
                # à la question sur la diplomation du secondaire, avoir répondu "oui" OU "en cours"
                #     ET qu'il s'agisse d'études secondaires étrangères
                diplomation_secondaire_etranger=models.ExpressionWrapper(
                    repondu_oui_ou_en_cours & models.Q(diplome_etranger=True),
                    output_field=models.BooleanField(),
                ),
                # à la question sur la diplomation du secondaire, avoir répondu "non"
                #     ET avoir fourni la PJ d'attestation de réussite de l'examen d'admission aux études de
                #     premier cycle de l'enseignement supérieur
                alternative_etudes_secondaires=models.ExpressionWrapper(
                    models.Q(graduated_from_high_school=GotDiploma.NO.name, diplome_alternatif=True),
                    output_field=models.BooleanField(),
                ),
                # avoir suivi, sans en être diplômé, une formation académique belge
                #     de 1er cycle (c.-à-d. formation sélectionnée dans la liste déroulante ET étant de 1er cycle)
                #     OU en ayant coché "autre formation"
                potentiel_bachelier_belge_sans_diplomation=models.Exists(
                    EducationalExperience.objects.filter(
                        models.Q(person_id=models.OuterRef('pk')),
                        # formation académique de 1er cycle
                        models.Q(program__cycle=Cycle.FIRST_CYCLE.name)
                        # OU autre formation
                        | ~models.Q(education_name=''),
                        # belge dans les deux cas
                        country__iso_code="BE",
                        # sans en être diplomé
                        obtained_diploma=False,
                    )
                ),
                # diplômé d'une formation académique belge
                diplomation_academique_belge=models.Exists(
                    EducationalExperienceYear.objects.filter(
                        models.Q(result=Result.WAITING_RESULT.name)
                        | models.Q(educational_experience__obtained_diploma=True),
                        educational_experience__person_id=models.OuterRef('pk'),
                        educational_experience__country__iso_code="BE",
                    )
                ),
                # diplômé d'une formation académique étrangère
                diplomation_academique_etranger=models.Exists(
                    EducationalExperienceYear.objects.filter(
                        models.Q(result=Result.WAITING_RESULT.name)
                        | models.Q(educational_experience__obtained_diploma=True),
                        ~models.Q(educational_experience__country__iso_code="BE"),
                        educational_experience__person_id=models.OuterRef('pk'),
                    )
                ),
                # avoir suivi, sans en être diplômé, une formation académique belge
                #     de 2e cycle (c.-à-d. formation sélectionnée dans la liste déroulante ET étant de 2e cycle)
                #     OU de 3e cycle (c.-à-d. formation sélectionnée dans la liste déroulante ET étant de 3e cycle)
                #     OU en ayant coché "autre formation"
                potentiel_master_belge_sans_diplomation=models.Exists(
                    EducationalExperience.objects.filter(
                        models.Q(person_id=models.OuterRef('pk')),
                        # formation académique de 2e ou 3e cycle
                        models.Q(program__cycle__in=[Cycle.SECOND_CYCLE.name, Cycle.THIRD_CYCLE.name])
                        # OU autre formation
                        | ~models.Q(education_name=''),
                        # belge dans les deux cas
                        country__iso_code="BE",
                        # sans en être diplomé
                        obtained_diploma=False,
                    )
                ),
                # diplômé d'une formation académique belge
                #     de 2e cycle (c.-à-d. formation sélectionnée dans la liste déroulante ET étant de 2e cycle)
                #     OU en ayant coché "autre formation"
                diplomation_potentiel_master_belge=models.Exists(
                    EducationalExperienceYear.objects.filter(
                        models.Q(educational_experience__person_id=models.OuterRef('pk')),
                        # formation académique de 2e cycle
                        models.Q(educational_experience__program__cycle=Cycle.SECOND_CYCLE.name)
                        # OU autre formation
                        | ~models.Q(educational_experience__education_name=''),
                        # diplomé ou en attente de résultat ou ancient étudiant de l'UCL
                        models.Q(educational_experience__obtained_diploma=True)
                        | models.Q(result=Result.WAITING_RESULT.name)
                        | models.Q(educational_experience__person__last_registration_year__isnull=False),
                        # belge
                        educational_experience__country__iso_code="BE",
                    )
                ),
                # diplômé d'une formation académique étrangère
                #     ET présence de la PJ d'équivalence de(s) diplôme(s) étranger(s)
                diplomation_potentiel_master_etranger=models.Exists(
                    EducationalExperienceYear.objects.filter(
                        models.Q(educational_experience__person_id=models.OuterRef('pk')),
                        # étranger
                        ~models.Q(educational_experience__country__iso_code="BE"),
                        # diplomé ou en attente de résultat
                        models.Q(educational_experience__obtained_diploma=True)
                        | models.Q(result=Result.WAITING_RESULT.name),
                    )
                ),
                # diplômé d'une formation académique belge
                #     de 3e cycle (c.-à-d. formation sélectionnée dans la liste déroulante ET étant de 3e cycle)
                #     OU en ayant coché "autre formation"
                diplomation_potentiel_doctorat_belge=models.Exists(
                    EducationalExperienceYear.objects.filter(
                        models.Q(educational_experience__person_id=models.OuterRef('pk')),
                        # formation académique de 3e cycle
                        models.Q(educational_experience__program__cycle=Cycle.THIRD_CYCLE.name)
                        # OU autre formation
                        | ~models.Q(educational_experience__education_name=''),
                        # diplomé ou en attente de résultat
                        models.Q(educational_experience__obtained_diploma=True)
                        | models.Q(result=Result.WAITING_RESULT.name),
                        # belge
                        educational_experience__country__iso_code="BE",
                    )
                ),
                # avoir renseigné des activités non académiques dont le total fait au moins 36 mois.
                potentiel_acces_vae=models.Exists(
                    ProfessionalExperience.objects.filter(person_id=models.OuterRef('pk'))
                    .annotate(duration=models.F('end_date') - models.F('start_date'))
                    .order_by()
                    .values('person_id')  # group by person
                    .annotate(total_time=models.Sum('duration'))
                    .values('total_time')
                    .filter(total_time__gte=timedelta(days=36 * 30)),
                ),
            )
            .filter(global_id=matricule_candidat)
            .first()
        )
        return AdmissionConditionsDTO(
            diplomation_secondaire_belge=result.diplomation_secondaire_belge,
            diplomation_secondaire_etranger=result.diplomation_secondaire_etranger,
            alternative_etudes_secondaires=result.alternative_etudes_secondaires,
            potentiel_bachelier_belge_sans_diplomation=result.potentiel_bachelier_belge_sans_diplomation,
            diplomation_academique_belge=result.diplomation_academique_belge,
            diplomation_academique_etranger=result.diplomation_academique_etranger,
            potentiel_master_belge_sans_diplomation=result.potentiel_master_belge_sans_diplomation,
            diplomation_potentiel_master_belge=result.diplomation_potentiel_master_belge,
            diplomation_potentiel_master_etranger=bool(equivalence_diplome)
            and result.diplomation_potentiel_master_etranger,
            diplomation_potentiel_doctorat_belge=result.diplomation_potentiel_doctorat_belge,
            potentiel_acces_vae=result.potentiel_acces_vae,
        )
