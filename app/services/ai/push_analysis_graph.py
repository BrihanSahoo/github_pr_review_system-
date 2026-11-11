from langgraph.graph import START,END,StateGraph
from app.services.ai.graph_state import PushAnalysisState
from app.services.ai.push_analysis_nodes import (
    fetch_changes_node,
    retrieve_context_node,
    analyze_changes_node
)


def create_push_analysis_graph():
    
    graph = StateGraph(PushAnalysisState)
    
    
    # Nodes
    graph.add_node(
        "fetch_changes",
        fetch_changes_node
    )
    graph.add_node(
        "retrieve_context",
        retrieve_context_node
    )
    graph.add_node(
        "analyze_changes",
        analyze_changes_node
    )
    
    
    
    # Edges
    graph.add_edge(
        START,
        "fetch_changes"
    )
    graph.add_edge(
        "fetch_changes",
        "retrieve_context"
    )
    graph.add_edge(
        "retrieve_context",
        "analyze_changes"
    )
    graph.add_edge(
        "analyze_changes",
        END
    )
    
    return graph.compile()




push_analysis_graph = create_push_analysis_graph()