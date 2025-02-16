from typing import List, Callable
from ragas.evaluation import evaluate, EvaluationDataset, EvaluationResult
from pydantic import BaseModel, Field
from typing import Union, Sequence
from ragas.metrics import (
    AspectCritic,
    Faithfulness,
    LLMContextPrecisionWithoutReference,
    ResponseRelevancy,
    ResponseRelevancy,
)


from langchain_core.runnables import Runnable


# Define a type that can accept AspectCritic for now, but can be expanded later, maybe using Enum, we shall see
Metric = Union[
    AspectCritic,
    Faithfulness,
    LLMContextPrecisionWithoutReference,
    ResponseRelevancy,
]


class TestSample(BaseModel):
    user_input: str = Field(description="Question, context and possible template")
    response: str = Field(description="The answer to the question")
    retrieved_contexts: List[str] = Field(description="The retrieved contexts")
    # reference: str = Field(description="The reference answer / ground truth")


# Define optional callback functions
def upload_result(result: EvaluationResult) -> None:
    result.upload()


def to_csv(result: EvaluationResult) -> None:
    from datetime import datetime
    from dynaconf import Dynaconf
    from pathlib import Path

    settings = Dynaconf(settings_files=Path(__file__).parents[1] / "config.toml")
    results_folder = Path(str(settings.paths.results_folder))  # type:ignore

    df = result.to_pandas()
    df.to_csv(results_folder / f"results_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")


def sample_rag_chain(
    final_chain: Runnable,
    questions: List[str],
    collection_name: str,
    metrics: Sequence[Metric],
    callbacks: List[Callable] = [upload_result, to_csv],
) -> EvaluationResult:  # TODO: Subtype Runnable, as its not specific enough
    """Tests our only Rag Chain. Needs disambiguation as soon as we have multiples."""
    real_dataset = []

    for question in questions:

        result = final_chain.invoke({"question": question, "collection_name": collection_name})
        answer = result["answer"]
        retrieved_context = [x.page_content for x in result["docs"]]
        real_dataset.append(
            TestSample(
                # user_input=filled_prompt.messages[0].content, # Not the filled prompt, but the raw question
                user_input=question,
                response=answer.content,
                retrieved_contexts=retrieved_context,
            ).model_dump()  # TODO: FIx indexing, bound to fail
        )

    dataset = EvaluationDataset.from_list(real_dataset)
    result = evaluate(dataset, metrics=metrics)

    # Execute any provided callbacks
    for _callback in callbacks:
        _callback(result)

    return result
