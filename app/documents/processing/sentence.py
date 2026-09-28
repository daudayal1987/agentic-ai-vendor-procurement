import re


_COMMON_ABBREVIATIONS = {
    "mr.",
    "mrs.",
    "ms.",
    "dr.",
    "prof.",
    "e.g.",
    "i.e.",
    "etc.",
    "vs.",
}


_ABBR_PATTERN = re.compile(
    r"\b("
    + "|".join(
        re.escape(abbreviation)
        for abbreviation in _COMMON_ABBREVIATIONS
    )
    + ")",
    re.IGNORECASE,
)


def split_sentences(
    text: str,
) -> tuple[str, ...]:
    """
    Split text into sentences using lightweight
    deterministic rules.

    This is intentionally not a full NLP tokenizer.
    """

    if not text.strip():
        return ()

    placeholders: dict[str, str] = {}

    def replace_abbreviation(
        match: re.Match,
    ) -> str:
        matched_text = match.group(0)

        placeholder = (
            f"__ABBR_{len(placeholders)}__"
        )

        placeholders[placeholder] = matched_text

        return placeholder

    protected = _ABBR_PATTERN.sub(
        replace_abbreviation,
        text,
    )

    parts = re.split(
        r"(?<=[.!?])\s+",
        protected,
    )

    sentences: list[str] = []

    for part in parts:
        sentence = part.strip()

        if not sentence:
            continue

        for placeholder, abbreviation in (
            placeholders.items()
        ):
            sentence = sentence.replace(
                placeholder,
                abbreviation,
            )

        sentences.append(sentence)

    return tuple(sentences)