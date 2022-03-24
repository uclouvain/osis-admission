from typing import Optional

import attr

from osis_common.ddd.interface import QueryRequest


@attr.s(frozen=True, slots=True, auto_attribs=True)
class SortedQueryRequest(QueryRequest):
    tri_inverse: bool = False
    champ_tri: Optional[str] = None

