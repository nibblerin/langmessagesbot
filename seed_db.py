"""
Разовый скрипт наполнения базы словами.
Запуск: python seed_words.py
Безопасно перезапускать — слово уже существующим текстом просто пропускается (UNIQUE + INSERT OR IGNORE)
"""

from db import init_db, add_word, count_words

WORDS = [
    # 1. Наука и данные
    ("der Wissenschaftler", "ученый", "die Wissenschaftler"),
    ("das Loch", "дыра", "die Löcher"),
    ("die Berechnung", "расчет, вычисление", "die Berechnungen"),
    ("das Ergebnis", "результат", "die Ergebnisse"),
    ("die Auswertung", "анализ, обработка данных", "die Auswertungen"),
    ("die Entdeckung", "открытие", "die Entdeckungen"),
    ("die Auflösung", "разрешение (экрана); развязка, решение", "die Auflösungen"),
    ("der Durchlauf", "цикл, проход (программы)", "die Durchläufe"),

    # 2. Глаголы действия
    ("auswerten", "анализировать, обрабатывать", None),
    ("entwickeln", "разрабатывать, развивать", None),
    ("berichten (über + Akk)", "сообщать, докладывать", None),
    ("erwähnen", "упоминать", None),
    ("strahlen", "излучать, сиять", None),
    ("einfügen", "вставлять", None),
    ("wegnehmen", "убирать, отнимать", None),
    ("verwenden", "использовать", None),
    ("reichen", "хватать, быть достаточным", None),

    # 4. Описания и состояния
    ("heutzutage", "в наши дни, в наше время", None),
    ("bisherig", "прежний, имеющийся на данный момент", None),
    ("verzerrt", "искаженный", None),
    ("kommende", "предстоящий, будущий", None),
    ("eigenartig", "своеобразный, странный, необычный", None),
    ("locker", "расслабленный, свободный, непринужденный", None),
    ("der Weltuntergang", "конец света (часто иронично)", "die Weltuntergänge"),
    ("wie bereits erwähnt", "как уже упоминалось", None),

    # Was nervt?
    ("nerven", "раздражать", None),
    ("der Dreck", "грязь", None),
    ("schmutzig", "грязный", None),
    ("der Nahverkehr", "общественный транспорт", None),
    ("unzuverlässig", "ненадежный", None),
    ("unpünktlich", "непунктуальный", None),
    ("die Miete", "арендная плата, цены на аренду", "die Mieten"),
    ("der Lärm", "шум", None),
    ("die Lautstärke", "громкость", "die Lautstärken"),
    ("überfüllt", "переполненный", None),
    ("die Menschenmenge", "толпа людей", "die Menschenmengen"),
    ("aggressiv", "агрессивный", None),
    ("unpersönlich", "безличный, холодный в общении", None),
    ("die Langstrecke", "длинная дистанция", "die Langstrecken"),
    ("der Fahrtweg", "путь следования", "die Fahrtwege"),

    # Was lohnt sich?
    ("sich lohnen", "стоить того, иметь смысл", None),
    ("aufregend", "захватывающий, волнующий", None),
    ("die Offenheit", "открытость", None),
    ("die Verrücktheit", "сумасбродство, странность (позитивно)", "die Verrücktheiten"),
    ("vielfältig", "разнообразный", None),
    ("die Vielfalt", "разнообразие", None),
    ("multikulti", "мультикультурный", None),
    ("der Kiez", "район, квартал (свой микрорайон)", "die Kieze"),
    ("das Kulturangebot", "культурное предложение", "die Kulturangebote"),
    ("der Freiraum", "свободное пространство", "die Freiräume"),
    ("bürgerlich", "буржуазный, приличный", None),
    ("alternativ", "альтернативный", None),

    # Полезные фразы (1)
    ("im Grunde", "по сути, в самой основе", None),
    ("am Stadtrand", "на окраине города", None),
    ("einen Unfall haben", "попасть в аварию", None),
    ("sich langweilen", "скучать", None),
    ("zusammensuchen", "собирать воедино, искать", None),

    # Взаимоотношения и конфликты
    ("der Generationenkonflikt", "конфликт поколений", "die Generationenkonflikte"),
    ("das Missverständnis", "недопонимание", "die Missverständnisse"),
    ("die Meinungsverschiedenheit", "разногласие", "die Meinungsverschiedenheiten"),
    ("der Streit", "спор, ссора", "die Streite"),
    ("hinterfragen", "ставить под сомнение, задумываться почему", None),
    ("sich an etwas gewöhnen", "привыкать к чему-либо", None),
    ("akzeptieren", "принимать, одобрять", None),

    # Повседневные привычки и технологии
    ("die Angewohnheit", "привычка", "die Angewohnheiten"),
    ("sich auf etwas fokussieren", "фокусироваться на чем-то", None),
    ("mit Geräten umgehen", "пользоваться устройствами", None),
    ("jemanden zur Weißglut treiben", "приводить в бешенство", None),
    ("nachvollziehen", "понимать, прослеживать логику", None),

    # Работа и ценности
    ("die Belastbarkeit", "стрессоустойчивость, выносливость", None),
    ("die Kontinuität", "непрерывность, стабильность", None),
    ("die Work-Life-Balance", "баланс между работой и личной жизнью", None),
    ("sich inspirieren lassen", "вдохновляться", None),
    ("die Ziellosigkeit", "бесцельность", None),

    # Описания и состояния (2)
    ("traditionell", "традиционный", None),
    ("entspannt", "расслабленный", None),
    ("gelassen", "спокойный, невозмутимый", None),
    ("fleißig", "трудолюбивый", None),
    ("verblüfft sein", "быть ошарашенным, удивленным", None),
    ("erschöpft sein", "быть истощенным", None),

    # Полезные фразы (2)
    ("niemals ausgelernt haben", "век живи, век учись", None),
    ("etwas persönlich nehmen", "принимать на свой счет", None),
    ("auf etwas verzichten", "отказываться от чего-либо", None),
    ("sich etwas nicht gefallen lassen", "не позволять так с собой обращаться", None),

    # Глаголы и действия (2)
    ("vorhaben", "планировать, намереваться", None),
    ("frei haben", "быть свободным, иметь выходной", None),
    ("sich freuen auf (Akk.)", "радоваться чему-то предстоящему", None),
    ("besorgen", "доставать, покупать (мелкие поручения)", None),
    ("proben", "репетировать", None),
    ("ausräumen", "освобождать, выносить вещи", None),
    ("umziehen", "переезжать", None),
    ("sich verabschieden", "прощаться", None),
    ("entdecken", "открывать, обнаруживать", None),
    ("empfehlen", "рекомендовать", None),

    # Существительные и понятия
    ("der Spaziergang", "прогулка", "die Spaziergänge"),
    ("die Seele", "душа", "die Seelen"),
    ("die Ausbildung", "профессиональное обучение", "die Ausbildungen"),
    ("die Klausur", "экзаменационная работа (в университете)", "die Klausuren"),
    ("die Prüfung", "экзамен", "die Prüfungen"),
    ("die Unterkunft", "жилье, место проживания", "die Unterkünfte"),
    ("der Geheimtipp", "полезный совет, «секретное» место", "die Geheimtipps"),
    ("die Umgebung", "окружение, окрестности", "die Umgebungen"),
    ("der Ausblick", "вид, панорама", "die Ausblicke"),

    # Прилагательные и наречия
    ("bekannt", "известный", None),
    ("tatsächlich", "на самом деле, фактически", None),
    ("riesig", "огромный", None),
    ("ambivalent", "амбивалентный, двойственный", None),
    ("historisch verwurzelt", "имеющий исторические корни", None),
    ("wertvoll", "ценный", None),
    ("begeistert", "восторженный, в восторге", None),

    # Полезные выражения
    ("Besorgungen machen", "делать закупки, выполнять мелкие дела", None),
    ("was ... betrifft", "что касается...", None),
    ("es ist ein Muss", "это обязательно (нужно сделать/увидеть)", None),
    ("gesetzlich verboten", "запрещено законом", None),
    ("Lärm machen", "шуметь", None),
    ("die Ausnahme", "исключение", "die Ausnahmen"),

    # Список без раздела
    ("überzeugen", "убедить, убеждать, уговорить", None),
    ("solche", "такой, такие", None),
    ("zahlreiche", "многочисленные, множество", None),
    ("das Ereignis", "событие", "die Ereignisse"),
    ("ehemalige", "бывший, прежний", None),
    ("der Fortschritt", "прогресс, успех", "die Fortschritte"),
    ("beinhalten", "содержать, включать в себя", None),
    ("der Vorschlag", "предложение, идея, совет", "die Vorschläge"),
    ("zeigen", "показать, показывать, продемонстрировать", None),
    ("künftig", "в будущем, грядущий", None),
    ("neigen", "склоняться, иметь склонность", None),
    ("überlegen", "подумать, придумать, передумать", None),
    ("hartnäckig", "настойчивый, упрямый, упорный", None),
    ("das Feedback effektiv nutzen", "эффективно использовать обратную связь", None),
    ("den Wortschatz erweitern", "расширять словарный запас", None),
    ("einen Fehler vermeiden", "избегать ошибки", None),
    ("vorstellen", "представлять (кому-то — Dativ, что-то — Akkusativ)", None),
    ("unterstützen", "поддерживать (Akkusativ)", None),

    # 5. Психология и чувства
    ("vertrauen", "доверять, верить; доверие", None),
    ("enttäuscht", "разочарованный", None),
    ("der Neid", "зависть", None),
    ("die Eifersucht", "ревность", None),
    ("sonderlich", "особенный (часто: nicht sonderlich — не особо)", None),
    ("der Schmerz", "боль, страдание", "die Schmerzen"),
    ("belohnt", "вознагражденный", None),

    # 6. Глаголы
    ("aufpassen", "быть внимательным, присматривать", None),
    ("erkunden", "исследовать, разведывать, осматривать", None),
    ("aufhören", "прекращать, останавливаться", None),

    # 7. Качества и описания
    ("verantwortlich", "ответственный", None),
    ("undeutlich", "неразборчивый, невнятный, неясный", None),
    ("gemeinsam", "общий, совместный; вместе", None),
    ("getrennt", "отдельный, раздельный", None),
    ("hauptsächlich", "в основном, главным образом", None),
    ("umständlich", "затруднительный, хлопотный", None),
    ("trocken", "сухой, трезвый (в т.ч. о юморе)", None),
    ("hinterher", "потом, затем, вслед за чем-то", None),
    ("die Abwechslung", "разнообразие, смена обстановки", "die Abwechslungen"),

    # 9. Список слов
    ("benutzbar", "пригодный, годный", None),
    ("die Unterhaltung", "беседа, разговор; развлечение", "die Unterhaltungen"),
    ("der Pfad", "путь, тропа", "die Pfade"),
    ("ständig", "постоянный, постоянно", None),
    ("schlimm", "плохой, ужасный", None),
    ("der Berg", "гора", "die Berge"),
    ("wandern", "ходить в походы, бродить", None),
    ("zugeben", "признавать, допускать", None),
    ("unscheinbar", "непримечательный, незаметный, скромный", None),
    ("ehrlich", "честный, откровенный, искренний", None),
    ("zuversichtlich", "уверенный в себе, оптимистичный", None),
    ("ähnlich", "похожий, схожий, аналогичный", None),
    ("weiterentwickeln", "развивать, совершенствовать", None),
    ("bereuen", "сожалеть, раскаиваться", None),
    ("einmalig", "уникальный, единственный в своем роде", None),
    ("verdecken", "закрывать, скрывать, загораживать", None),
    ("unübersichtlich", "необозримый, запутанный, неясный", None),
    ("beheben", "устранять, исправлять", None),
    ("es fällt mir schwer", "мне это дается тяжело", None),
    ("vermeiden", "избегать, предотвращать", None),
    ("aufschieben", "откладывать на потом, медлить", None),
    ("bekämpfen", "бороться, подавлять", None),
    ("schaffen", "справляться, успевать, преодолевать", None),
]


def main():
    init_db()
    before = count_words()

    for word, translation, plural in WORDS:
        add_word(word=word, translation=translation, plural=plural)

    after = count_words()
    print(f"Готово. Слов в базе было: {before}, стало: {after} (добавлено новых: {after - before}).")
    print(f"Всего строк в списке сидера: {len(WORDS)}.")


if __name__ == "__main__":
    main()