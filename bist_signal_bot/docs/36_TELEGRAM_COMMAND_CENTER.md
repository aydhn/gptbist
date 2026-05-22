# Telegram Research Command Center

The Telegram Research Command Center is a robust, secure, and fully local interface for managing the BIST Signal Bot via Telegram. It is strictly limited to research and offline operational commands.

## Core Capabilities
1. **Research Commands:** Execute commands like `/status`, `/health`, `/signals`, `/review`, `/portfolio`, `/stress`, `/drift`, `/kb`, and `/report`.
2. **Strict Guardrails:** It actively blocks any commands related to real trading (e.g., "al", "sat", "emir gönder") using the `ForbiddenActionGuard`.
3. **Digest Orchestration:** Compiles system health, signal performance, and backtest results into concise Telegram digests.
4. **Notification Inbox:** Acts as a queue for all outgoing Telegram messages, allowing for retry mechanisms, muting, and deduplication.

## Security Model
- **No Broker API Access:** The Command Center cannot execute real market orders.
- **Secret Redaction:** `SecretRedactor` scrubs any sensitive configuration from the output.
- **Allowlisting:** Only chat IDs specified in `TELEGRAM_ALLOWED_CHAT_IDS` can interact with the bot.

## Example Commands
Send these from your allowed Telegram account:
- `/health` - Retrieve system health checks.
- `/signals ASELS` - Get the latest signal summary for ASELS.
- `/review` - View pending items in the Analyst Review Inbox.
- `/digest daily` - Request an immediate daily digest.
