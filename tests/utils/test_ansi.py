from agent_arsenal.utils.ansi import strip_ansi


def test_strip_ansi_with_colors():
    # Green text: \x1b[32mSome text\x1b[0m
    text = "\x1b[32mGreen\x1b[0m and \x1b[31mRed\x1b[0m"
    expected = "Green and Red"
    assert strip_ansi(text) == expected


def test_strip_ansi_with_bold_and_underline():
    # Bold: \x1b[1m, Underline: \x1b[4m
    text = "\x1b[1mBold\x1b[22m and \x1b[4mUnderline\x1b[24m"
    expected = "Bold and Underline"
    assert strip_ansi(text) == expected


def test_strip_ansi_with_complex_codes():
    # Moving cursor, clearing screen, etc.
    text = "\x1b[2J\x1b[H\x1b[33mYellow\x1b[0m"
    expected = "Yellow"
    assert strip_ansi(text) == expected


def test_strip_ansi_with_plain_string():
    text = "Just some plain text."
    assert strip_ansi(text) == text


def test_strip_ansi_with_empty_string():
    assert strip_ansi("") == ""


def test_strip_ansi_with_no_ansi_but_escape_char():
    # An escape character not followed by valid ANSI sequence should (theoretically) remain,
    # but the regex should only match valid ones.
    text = "\x1b This is not an ANSI sequence"
    assert strip_ansi(text) == text
