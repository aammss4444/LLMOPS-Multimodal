import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict


class ComplianceIssue(TypedDict):
    category: str
    description: str
    severity: str
    timestamp: Optional[str]


class VideoAuditState(TypedDict, total=False):
    video_url: str
    video_id: str

    local_file_path: Optional[str]
    audio_file_path: Optional[str]
    frame_paths: Optional[List[str]]
    video_metadata: Dict[str, Any]
    transcript: Optional[str]
    ocr_text: Optional[List[str]]
    fused_text: Optional[str]
    fused_payload: Optional[Dict[str, Any]]
    structured_output: Optional[Dict[str, Any]]
    checkpoint_status: Dict[str, str]
    checkpoint_details: Dict[str, Any]

    compliance_issues: Annotated[List[ComplianceIssue], operator.add]

    final_status: str
    final_report: Optional[str]

    errors: Annotated[List[str], operator.add]
