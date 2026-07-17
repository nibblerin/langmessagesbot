#  German Vocabulary Telegram Bot
A Telegram bot for learning German vocabulary through scheduled daily words, translations, and AI-generated example sentences.
The bot sends users new German words at a customizable interval and helps memorize them by providing examples in German with Russian translations.
## Features
 German word of the day
- Russian translations
- AI-generated example sentences using Groq LLM
- Custom message intervals:
  - 30 minutes
  - 1 hour
  - 2 hours
  - 24 hours
- Start / Pause vocabulary delivery
- User data storage with database
- Automatic cleanup of old bot messages
- Telegram inline button interface
## How It Works
1. User starts the bot with `/start`
2. The bot creates a user profile in the database
3. User selects a message interval
4. Scheduler checks active users every minute
5. The bot sends:
   - German word
   - Translation
   - Example sentence in German
   - Russian translation of the example
6. Old messages are automatically removed to keep the chat clean
## AI Integration
The bot uses Groq LLM to generate natural German example sentences for vocabulary words.
Generated content:
- German example sentence
- Russian translation
To reduce API usage, generated words are cached and refreshed periodically.
