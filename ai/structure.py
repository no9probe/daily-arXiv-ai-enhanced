from pydantic import BaseModel, Field

class Structure(BaseModel):
  tldr: str = Field(description="generate a too long; didn't read summary in Chinese")
  motivation: str = Field(description="describe the motivation in this paper in Chinese")
  method: str = Field(description="method of this paper in Chinese")
  result: str = Field(description="result of this paper in Chinese")
  conclusion: str = Field(description="conclusion of this paper in Chinese")
  paper_title_zh: str = Field(description="translate the paper title to Chinese")
  abstract_zh: str = Field(description="translate the abstract to Chinese")