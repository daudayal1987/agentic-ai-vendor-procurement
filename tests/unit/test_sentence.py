from app.documents.processing.sentence import (
    split_sentences,
)


def test_split_basic_sentences():
    text = (
        "The vendor submitted the contract. "
        "The buyer reviewed it. "
        "The contract was approved."
    )

    result = split_sentences(text)

    assert result == (
        "The vendor submitted the contract.",
        "The buyer reviewed it.",
        "The contract was approved.",
    )


def test_empty_text():
    assert split_sentences("") == ()


def test_preserve_question_and_exclamation():
    text = "Is the contract valid? Yes!"

    result = split_sentences(text)

    assert result == (
        "Is the contract valid?",
        "Yes!",
    )


def test_common_abbreviations():
    text = (
        "Dr. Smith reviewed the contract. "
        "The vendor submitted it."
    )

    result = split_sentences(text)

    assert result == (
        "Dr. Smith reviewed the contract.",
        "The vendor submitted it.",
    )


def test_single_sentence():
    text = (
        "The vendor shall pay within 30 days."
    )

    result = split_sentences(text)

    assert result == (
        "The vendor shall pay within 30 days.",
    )