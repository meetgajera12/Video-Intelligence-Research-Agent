from pydantic import BaseModel, Field, ConfigDict
from typing import List

# summary agent
class Summary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary : str = Field(...,description='summary of provided youtube video transcript.')

# key point agent
class Key_points(BaseModel):
    model_config = ConfigDict(extra="forbid")
    KeyPoints : List[str] = Field(...,description='key points from provided youtube video transcript.')

# fact check agent
class FactCheckItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim: str = Field(
        description="A factual claim made in the YouTube transcript."
    )
    verdict: str = Field(
        description="One of: TRUE, FALSE, MISLEADING, or UNVERIFIED."
    )
    explanation: str = Field(
        description="Brief explanation of why the claim received this verdict."
    )
    evidence: str = Field(
        description="Evidence from reliable external sources."
    )
    sources: List[str] = Field(
        description="URLs of sources used to verify the claim."
    )

class FactCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claims: List[FactCheckItem]

# topic extractor agent
class Topics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topics : List[str] = Field(
        description=(
            "Important concepts, subjects, technologies, methods, "
            "or entities discussed in the transcript."
        )
    )

# reference agent
class ReferenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: str = Field(
        description="The topic this reference belongs to."
    )
    title: str = Field(
        description="Exact title of the selected source."
    )
    url: str = Field(
        description="Exact URL copied from the search result."
    )
    source_type: str = Field(
        description=(
            "Type of source: official documentation, research paper, "
            "university, government, textbook, or reputable article."
        )
    )
    relevance: str = Field(
        description="Briefly explain why this source is useful for this topic."
    )


class ReferenceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    references: List[ReferenceItem]


# Que.-Ans. agent
class QueAns(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(
        description="Answer to the user's question based only on the provided context."
    )

# Claim agent
class Claims(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claims: list[str]