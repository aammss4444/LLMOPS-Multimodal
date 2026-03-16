import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict

# Define the schema for single compliance
# Error report 
class ComplianceIssue(TypedDict):
    category: str   #
    description: str   #specific description of the compliance issue
    severity: str   #Critical, Warning
    timestamp: Optional[str]


# Define Global state of the graph
# This defines the state that gets passed around in the agentic workflow
class VideoAuditState(TypedDict):
    '''
    Defines the data schema for langraph execution
    Main Container: It holds the all information about the audit
    right from the URL to final report 
    '''

# Input Parameters
    video_url: str
    video_id: str

# Ingestion and extarction data
    local_file_path: Optional[str]  # Local path where the video is stored after ingestion 
    video_metadata: Dict[str, Any]  # Duration: 15, Resolution: 1080p, Format: mp4, etc.
    transcript: Optional[str]  # Full transcript of the video
    ocr_text: Optional[str]  # Text extracted from video frames using OCR

# Analysis output
#  Store the list of all voilation by our AI
    compliance_issues: Annotated[List[ComplianceIssue], operator.add]  # List of compliance issues found in the video

# Final variables
    final_status: str  # Final compliance status of the video (e.g., "Compliant", "Non-Compliant")
    final_report: Optional[str]  # md format

# system observability
# errors: API timeout, sytem level errors, etc.
# Stores system level crashes in list
    errors: Annotated[List[str], operator.add]  # List of errors encountered during processing
