"""Distinguish actionable alternatives from requests for independent inputs."""
from typing import Annotated, Literal
from enum import Enum
from pydantic import Field, create_model
from common.schema import Record, Text


class Option(Record):
    label: Text
    description: Text


class InputQuestion(Record):
    question_type: Literal['input']
    question: Text = Field(description='Ask for information needed to resolve the target fields.')
    options: Annotated[list[Option],Field(max_length=0,description='Direct input has no alternatives.')]


class ChoiceQuestion(Record):
    question_type: Literal['choice']
    question: Text = Field(description='Ask the user to choose an alternative for one decision.')
    options: Annotated[list[Option],Field(min_length=1,
        description='Substantive alternatives, rather than input instructions or settled facts. Use recommendations for numerical candidates.')]


Number=Annotated[float,Field(allow_inf_nan=False)]
Vector=Annotated[list[Number],Field(min_length=1)]
Matrix=Annotated[list[Vector],Field(min_length=1)]


class SuggestedValue(Record):
    name: Text
    value: Number|Vector|Matrix
    unit: str


class ValueRecommendation(Option):
    description: Text = Field(description='Explain this numerical proposal and its assumptions, separately from approved facts.')
    values: Annotated[list[SuggestedValue],Field(min_length=1,
        description='Numerical values and units forming a coherent candidate.')]


class RecommendationQuestion(Record):
    question_type: Literal['recommendation']
    question: Text = Field(description='Present proposed values and assumptions for review; the user may supply different values.')
    options: Annotated[list[ValueRecommendation],Field(min_length=1,max_length=2,
        description='Distinct numerical candidates; manual entry remains available in the dialogue.')]


Question=InputQuestion|ChoiceQuestion|RecommendationQuestion


def scoped_questions(label,targets,recommendation_names=(),kind=None):
    """Constrain question targets and numerical suggestions to the active card."""
    if not targets:raise ValueError('No fields in the current stage can be questioned.')
    Target=Enum(label+'QuestionTarget',{f'field_{i}':p for i,p in enumerate(targets)},type=str)
    fields={'targets':(Annotated[list[Target],Field(min_length=1,
        description='Unresolved fields in the active card.')],...)}
    if kind is not None:fields['kind']=(Literal[kind],...)
    Input=create_model(label+'InputQuestion',__base__=InputQuestion,
        question=(Text,Field(description='Ask for information needed to resolve the target fields.')),**fields)
    Choice=create_model(label+'ChoiceQuestion',__base__=ChoiceQuestion,
        question=(Text,Field(description='Ask the user to choose an alternative for the target fields.')),
        options=(Annotated[list[Option],Field(min_length=1,description='Substantive alternatives for one decision, rather than input instructions or settled facts.')],...),**fields)
    if not recommendation_names:return Input|Choice
    Name=Enum(label+'RecommendedName',{f'item_{i}':p for i,p in enumerate(recommendation_names)},type=str)
    Value=create_model(label+'SuggestedValue',__base__=SuggestedValue,name=(Name,...))
    OptionModel=create_model(label+'ValueOption',__base__=ValueRecommendation,
        values=(Annotated[list[Value],Field(min_length=1)],...))
    Recommendation=create_model(label+'RecommendationQuestion',__base__=RecommendationQuestion,
        options=(Annotated[list[OptionModel],Field(min_length=1,max_length=2)],...),**fields)
    return Input|Choice|Recommendation
