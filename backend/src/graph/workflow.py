from langgraph.graph import END, StateGraph

from backend.src.graph.nodes import (
    audio_content_node,
    fusion_layer_node,
    index_video,
    structured_output_node,
    visual_compliance_node,
)
from backend.src.graph.state import VideoAuditState


def build_workflow():
    graph = StateGraph(VideoAuditState)
    graph.add_node("index_video", index_video)
    graph.add_node("fusion_layer", fusion_layer_node)
    graph.add_node("structured_output_layer", structured_output_node)
    graph.add_node("audio_content_audit", audio_content_node)
    graph.add_node("visual_compliance_audit", visual_compliance_node)

    graph.set_entry_point("index_video")
    graph.add_edge("index_video", "fusion_layer")
    graph.add_edge("fusion_layer", "structured_output_layer")
    graph.add_edge("structured_output_layer", "audio_content_audit")
    graph.add_edge("audio_content_audit", "visual_compliance_audit")
    graph.add_edge("visual_compliance_audit", END)
    return graph.compile()
