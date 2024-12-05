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

from django.db import transaction
from osis_signature.enums import SignatureState
from osis_signature.models import Process, StateHistory

from admission.ddd.admission.doctorat.preparation.builder.proposition_builder import IPropositionBuilder
from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.commands import InitierPropositionCommand
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from admission.models import DoctorateAdmission, SupervisionActor, Accounting
from admission.utils import copy_documents


class PropositionBuilder(IPropositionBuilder):
    @classmethod
    @transaction.atomic
    def initier_nouvelle_proposition_attachee_a_pre_admission(
        cls,
        cmd: 'InitierPropositionCommand',
        doctorat_translator: 'IDoctoratTranslator',
        proposition_repository: 'IPropositionRepository',
    ) -> PropositionIdentity:
        new_reference = proposition_repository.recuperer_reference_suivante()

        pre_admission = DoctorateAdmission.objects.get(
            uuid=cmd.pre_admission_associee,
            candidate__global_id=cmd.matricule_candidat,
        )

        new_admission = DoctorateAdmission(
            uuid=PropositionIdentityBuilder.build().uuid,
            related_pre_admission=pre_admission,
            reference=new_reference,
            type=cmd.type_admission,
            status=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            training_id=pre_admission.training_id,
            comment=cmd.justification,
            candidate_id=pre_admission.candidate_id,
            proximity_commission=pre_admission.proximity_commission,
            financing_type=pre_admission.financing_type,
            financing_work_contract=pre_admission.financing_work_contract,
            financing_eft=pre_admission.financing_eft,
            international_scholarship_id=pre_admission.international_scholarship_id,
            other_international_scholarship=pre_admission.other_international_scholarship,
            scholarship_start_date=pre_admission.scholarship_start_date,
            scholarship_end_date=pre_admission.scholarship_end_date,
            scholarship_proof=pre_admission.scholarship_proof,
            planned_duration=pre_admission.planned_duration,
            dedicated_time=pre_admission.dedicated_time,
            is_fnrs_fria_fresh_csc_linked=pre_admission.is_fnrs_fria_fresh_csc_linked,
            financing_comment=pre_admission.financing_comment,
            project_title=pre_admission.project_title,
            project_abstract=pre_admission.project_abstract,
            thesis_language_id=pre_admission.thesis_language_id,
            thesis_institute_id=pre_admission.thesis_institute_id,
            thesis_location=pre_admission.thesis_location,
            phd_alread_started=pre_admission.phd_alread_started,
            phd_alread_started_institute=pre_admission.phd_alread_started_institute,
            work_start_date=pre_admission.work_start_date,
            project_document=pre_admission.project_document,
            gantt_graph=pre_admission.gantt_graph,
            program_proposition=pre_admission.program_proposition,
            additional_training_project=pre_admission.additional_training_project,
            recommendation_letters=pre_admission.recommendation_letters,
            phd_already_done=pre_admission.phd_already_done,
            phd_already_done_institution=pre_admission.phd_already_done_institution,
            phd_already_done_thesis_domain=pre_admission.phd_already_done_thesis_domain,
            phd_already_done_defense_date=pre_admission.phd_already_done_defense_date,
            phd_already_done_no_defense_reason=pre_admission.phd_already_done_no_defense_reason,
            curriculum=pre_admission.curriculum,
        )

        # Duplicate the documents
        copy_documents([new_admission])

        # Duplicate the supervision group of the pre-admission
        new_supervision_group = cls._duplicate_supervision_group(pre_admission)
        new_admission.supervision_group = new_supervision_group

        new_admission.save()

        Accounting.objects.create(admission=new_admission)

        return PropositionIdentityBuilder.build_from_uuid(uuid=str(new_admission.uuid))

    @classmethod
    def _duplicate_supervision_group(cls, admission: DoctorateAdmission) -> Process:
        process = Process.objects.create()
        states = []
        for admission_actor in SupervisionActor.objects.filter(process_id=admission.supervision_group_id):
            person_kwargs = (
                {'person_id': admission_actor.person_id}
                if admission_actor.person_id
                else {
                    'first_name': admission_actor.first_name,
                    'last_name': admission_actor.last_name,
                    'email': admission_actor.email,
                    'institute': admission_actor.institute,
                    'city': admission_actor.city,
                    'country_id': admission_actor.country_id,
                    'language': admission_actor.language,
                }
            )

            actor = SupervisionActor.objects.create(
                process=process,
                type=admission_actor.type,
                is_doctor=admission_actor.is_doctor,
                is_reference_promoter=admission_actor.is_reference_promoter,
                **person_kwargs,
            )
            states.append(StateHistory(actor=actor, state=SignatureState.NOT_INVITED.name))

        StateHistory.objects.bulk_create(states)

        return process
