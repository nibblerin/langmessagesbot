import os
from groq import Groq

client = Groq()

GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")


def generate_sentence(word: str, translation: str, plural: str | None = None) -> dict:
    """
    Просит LLM составить одно простое предложение на немецком с данным словом
    и его перевод на русский. Возвращает {"de": "...", "ru": "..."}.
    """
    plural_hint = f" (множественное число: {plural})" if plural else ""

    prompt = f"""Ты преподаватель немецкого языка  (уровень B1-B2).

Слово: {word}{plural_hint}
Перевод: {translation}

Составь ОДНО простое короткое предложение на немецком языке с этим словом
и переведи его на русский (уровень B1-B2). 
Перед ответом обязательно проверь:
1. Использовано ли слово в правильной форме.
2. Правильно ли выбран артикль для существительного.
3. Правильно ли согласованы род, число и падеж.
4. Правильно ли изменены окончания прилагательных.
5. Правильно ли используется управление глагола.
6. Правильный ли порядок слов в немецком предложении.
7. Соответствует ли русский перевод немецкому предложению.Не забывай, что в русском языке окончание глаголов и 
прилагательных зависят от рода и числа существительных.

Ответь строго в формате, без пояснений и лишнего текста:
DE: <предложение на немецком>
RU: <перевод на русский>"""

    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "Ты помощник для изучения немецкого языка."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_completion_tokens=200,
        top_p=1,
        stream=False,  # нужен готовый текст целиком,
    )

    content = completion.choices[0].message.content.strip()
    return _parse_response(content)


def _parse_response(content: str) -> dict:
    """Парсит ответ вида 'DE: ...\\nRU: ...' в словарь. С фолбэком, если формат сломан."""
    de, ru = "", ""
    for line in content.splitlines():
        line = line.strip()
        if line.upper().startswith("DE:"):
            de = line.split(":", 1)[1].strip()
        elif line.upper().startswith("RU:"):
            ru = line.split(":", 1)[1].strip()

    if not de or not ru:
        de = de or content
        ru = ru or ""

    return {"de": de, "ru": ru}