import logging
from time import perf_counter

from fastapi import APIRouter, HTTPException
from openai import APIError, APITimeoutError, RateLimitError
from pydantic import BaseModel, ConfigDict, Field

from app.rag import GENERATION_MODEL, rag_graph


logger = logging.getLogger(__name__)
router = APIRouter(tags=["answers"])


class AskRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=300)


@router.post("/ask")
def ask(request: AskRequest):
    started_at = perf_counter()

    try:
        state = rag_graph.invoke({
            "question": request.question,
        })

    except APITimeoutError:
        logger.exception("Answer generation timed out")
        raise HTTPException(
            status_code=504,
            detail="Answer generation timed out.",
        ) from None

    except RateLimitError:
        logger.exception("Generation rate or quota limit reached")
        raise HTTPException(
            status_code=503,
            detail="Answer generation is currently unavailable.",
        ) from None

    except APIError:
        logger.exception("Generation API request failed")
        raise HTTPException(
            status_code=502,
            detail="The generation service could not complete the request.",
        ) from None

    except ValueError:
        logger.exception("Generated answer failed validation")
        raise HTTPException(
            status_code=502,
            detail="Could not produce a valid cited answer.",
        ) from None

    return {
        "question": request.question,
        "retrieval_method": "semantic",
        "generation_model": GENERATION_MODEL,
        **state["result"],
        "generation_usage": state.get("usage", {}),
        "pipeline_ms": round(
            (perf_counter() - started_at) * 1000,
            2,
        ),
    }