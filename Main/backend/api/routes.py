from fastapi import APIRouter, HTTPException
from backend.agents.query_agent import QueryAgent
from backend.models.query_models import QueryRequest, QueryResponse

router = APIRouter(
    prefix="/query",
    tags=["Query"]
)

query_agent = QueryAgent()


@router.post("", response_model=QueryResponse)
def execute_query(request: QueryRequest):
    """
    Submits a natural language query to the Expert Copilot.
    Retrieves information using both document vectors and the knowledge graph.
    """
    try:
        results = query_agent.query(request.question)
        return results
    except Exception as e:
        print(f"Error executing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the query: {str(e)}"
        )
