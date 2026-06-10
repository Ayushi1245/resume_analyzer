# pyrefly: ignore [missing-import]
import tiktoken


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Count the number of tokens in a text string."""
    enc = tiktoken.get_encoding(model)
    return len(enc.encode(text))


def truncate_text(text: str, max_tokens: int = 4000, model: str = "cl100k_base") -> str:
    """Truncate text to a maximum number of tokens to stay within context windows."""
    enc = tiktoken.get_encoding(model)
    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return enc.decode(tokens[:max_tokens])


def format_skills_list(skills: list[str]) -> str:
    """Format a list of skills into a readable comma-separated string."""
    if not skills:
        return "None identified"
    return ", ".join(skills)
