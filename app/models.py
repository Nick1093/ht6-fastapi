from pydantic import BaseModel

# # prompt
# class OrchestrationLayer(BaseModel):
#     prompt: str
#     html: str 
#     css: str

# HTML GENERATION PROMPT
class HTMLGenerationPrompt(BaseModel):
    prompt: str
    html: str

# CSS GENERATION PROMPT
class CSSGenerationPrompt(BaseModel):
    prompt: str
    css: str

# RETURN MODEL
class ReturnData(BaseModel):
    html: str
    css: str