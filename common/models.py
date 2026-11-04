"""Model profiles, selectable reasoning and provider request settings."""
from copy import deepcopy
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OPENROUTER_URL = 'https://openrouter.ai/api/v1'
DEFAULT_MODEL = 'gpt-5.4-mini'
FORMULATION_MODEL = 'gpt-5.5'
MODEL_PROFILES = (
    {'id':'moonshotai/kimi-k2.5','label':'Kimi K2.5','provider':'openrouter','reasoning':'enabled','reasoning_options':['none','enabled']},
    {'id':'deepseek/deepseek-v4-flash','label':'DeepSeek V4 Flash 0423','provider':'openrouter','reasoning':'high','reasoning_options':['none','high','xhigh']},
    {'id':'qwen/qwen3.5-27b','label':'Qwen3.5 27B','provider':'openrouter','reasoning':'enabled','reasoning_options':['none','enabled']},
    {'id':'google/gemini-3-flash-preview','label':'Gemini 3 Flash','provider':'openrouter','reasoning':'low','reasoning_options':['minimal','low','medium','high']},
    {'id':'anthropic/claude-haiku-4.5','label':'Claude Haiku 4.5','provider':'openrouter','reasoning':'enabled','reasoning_options':['none','enabled'],'reasoning_max_tokens':4096},
    {'id':DEFAULT_MODEL,'label':'GPT-5.4 mini','provider':'openai','reasoning':'low','reasoning_options':['none','low','medium','high','xhigh']},
)
FORMULATION_PROFILE = {'id':FORMULATION_MODEL,'label':'GPT-5.5 · Medium reasoning','provider':'openai','reasoning':'medium','reasoning_options':['medium']}


def profile(model):
    for item in (*MODEL_PROFILES, FORMULATION_PROFILE):
        if model == item['id']:
            return deepcopy(item)
    raise ValueError("Please choose from the specified six models. The formulation is fixed to GPT-5.5 medium.")


def credentials(provider='openai'):
    name = {'openai':'OPENAI_API_KEY','openrouter':'OPENROUTER_API_KEY'}[provider]
    if key := os.environ.get(name, '').strip():
        return key
    filename = {'openai':'.openai_key','openrouter':'.openrouter_key'}[provider]
    for path in (ROOT/filename,):
        if path.is_file() and (key := path.read_text().strip()):
            return key
    return ''


def reasoning_mode(model, value=None, *, strict=True):
    """Validate new choices; tolerate obsolete modes only when loading old settings."""
    selected=profile(model)
    if value is None or value=='default':return selected['reasoning']
    if not isinstance(value,str) or value not in selected['reasoning_options']:
        if not strict:return selected['reasoning']
        raise ValueError(selected['label']+"Please choose the inference setting supported by "+', '.join(selected['reasoning_options']))
    return value


def completion_options(model, max_tokens=16384, reasoning=None):
    """Apply each model's supported thinking toggle, effort or token budget."""
    selected = profile(model)
    mode=reasoning_mode(model,reasoning)
    if selected['provider'] == 'openai':
        return {'max_completion_tokens':max_tokens, 'store':False,
                'reasoning_effort':mode}
    if mode=='none':
        reasoning={'enabled':False, 'effort':'none'}
    elif mode=='enabled':
        reasoning={'enabled':True}
        if 'reasoning_max_tokens' in selected:
            reasoning['max_tokens']=selected['reasoning_max_tokens']
    else:
        reasoning={'enabled':True, 'effort':mode}
    return {'max_tokens':max_tokens, 'extra_body':{'reasoning':reasoning,
            'provider':{'require_parameters':True}}}
