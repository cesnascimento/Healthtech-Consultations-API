from app.services.summarizers.base import SummarizerProtocol, SummarizerResult
from app.services.summarizers.factory import get_summarizer, get_rule_based_summarizer
from app.services.summarizers.rule_based import RuleBasedSummarizer

# LLMBasedSummarizer é importado via factory (lazy) para evitar
# dependência obrigatória do google-generativeai

__all__ = [
    "SummarizerProtocol",
    "SummarizerResult",
    "RuleBasedSummarizer",
    "get_summarizer",
    "get_rule_based_summarizer",
]
