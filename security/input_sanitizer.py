# security/input_sanitizer.py
# Sanitizes all user inputs

import re

MAX_QUESTION_LENGTH = 500


class InputSanitizer:
    @staticmethod
    def sanitize_question(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(
            r'(javascript|script|eval|exec)\s*:',
            '', text, flags=re.IGNORECASE)
        text = text[:MAX_QUESTION_LENGTH].strip()
        return text

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        name = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        return name[:100]

    @staticmethod
    def is_valid_question(text: str) -> tuple:
        if not text or len(text.strip()) < 3:
            return False, "Question too short"
        if len(text) > MAX_QUESTION_LENGTH:
            return False, (
                f"Question too long "
                f"(max {MAX_QUESTION_LENGTH})"
            )
        return True, text