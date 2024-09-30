import dataclasses
from enum import Enum


@dataclasses.dataclass
class ModelInformation:
    model_name: str
    max_tokens: int
    max_context_size: int


class Models(Enum):
    GPT_3_5 = ModelInformation(model_name='gpt-3.5-turbo', max_tokens=4096, max_context_size=4096)
    GPT_3_5_updated = ModelInformation(model_name='gpt-3.5-turbo-1106', max_tokens=4096, max_context_size=16385)
    GPT_4_0125 = ModelInformation(model_name='gpt-4-0125-preview', max_tokens=4096, max_context_size=128000)
    GPT_4_1106 = ModelInformation(model_name='gpt-4-1106-preview', max_tokens=4096, max_context_size=128000)
    GPT_4_turbo_2024_04_09 = ModelInformation(model_name='gpt-4-turbo-2024-04-09', max_tokens=4096, max_context_size=128000)
    GPT_4o_2024_05_13 = ModelInformation(model_name='gpt-4o-2024-05-13', max_tokens=4096, max_context_size=128000)
    GPT_4o_mini_2024_07_18 = ModelInformation(model_name='gpt-4o-mini-2024-07-18', max_tokens=16000, max_context_size=128000)
    CLAUDE_3_OPUS_20240229 = ModelInformation(model_name='claude-3-opus-20240229', max_tokens=4096, max_context_size=200000)
    MISTRAL_LARGE_2402 = ModelInformation(model_name='mistral-large-2402', max_tokens=4096, max_context_size=32000)
    QWEN1_5_72B_CHAT = ModelInformation(model_name='Qwen/Qwen1.5-72B-Chat', max_tokens=4096, max_context_size=32000)
    QWEN1_5_72B_CHAT_FIREWORKS = ModelInformation(model_name='accounts/fireworks/models/qwen1p5-72b-chat', max_tokens=4096, max_context_size=32000)
    QWEN1_5_72B_INSTRUCT_FIREWORKS = ModelInformation(model_name='accounts/fireworks/models/qwen2-72b-instruct', max_tokens=4096, max_context_size=32000)
    # YI_LARGE = ModelInformation(model_name='zero-one-ai/Yi-34B-Chat', max_tokens=4096, max_context_size=32000)
    YI_LARGE = ModelInformation(model_name='accounts/fireworks/models/yi-large', max_tokens=4096, max_context_size=32000)
    Llama_3_1_405B = ModelInformation(model_name='accounts/fireworks/models/llama-v3p1-405b-instruct', max_tokens=4096, max_context_size=128000)
    Llama_3_1_70B = ModelInformation(model_name='accounts/fireworks/models/llama-v3p1-70b-instruct', max_tokens=4096, max_context_size=128000)
    Llama_3_1_405B_AIML = ModelInformation(model_name='meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo', max_tokens=4096, max_context_size=128000)
    Llama_3_1_70B_AIML = ModelInformation(model_name='meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo', max_tokens=4096, max_context_size=128000)
    Llama_3_1_8B_AIML = ModelInformation(model_name='meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo', max_tokens=4096, max_context_size=128000)