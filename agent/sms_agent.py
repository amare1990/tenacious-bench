from __future__ import annotations

STOP_WORDS = {'stop', 'unsubscribe', 'unsb', 'cancel', 'end', 'quit'}
HELP_WORDS = {'help', 'info'}


def handle_inbound_sms(message: str) -> dict:
    text = (message or '').strip().lower()
    if text in STOP_WORDS:
        return {
            'action': 'suppress_outreach',
            'reply': 'You have been unsubscribed from Tenacious follow-up messages. Reply START if you want to resume.',
            'compliant': True,
        }
    if text in HELP_WORDS:
        return {
            'action': 'send_help',
            'reply': 'Tenacious scheduling assistant: reply STOP to opt out, or send a preferred time window for a short intro call.',
            'compliant': True,
        }
    return {
        'action': 'continue',
        'reply': 'Thanks — I can keep coordination here by SMS if that is easier.',
        'compliant': True,
    }
