#!/usr/bin/env python3
"""Ask an Axelor AI agent a question through the chat API and print its tool calls and answer.

  python3 -I chat_test.py <url> <agent-code> "<question>" [--chat <chatId>] [--approve] [--batch questions.txt]

--approve answers every approval card with "approved" (what a click on Approve does). Only use it on a
          disposable instance, and clean up what the test wrote.
--batch   runs one question per line (empty lines and lines starting with # are skipped), each in a new chat.

Protocol (AI SDK UI message stream, observed on AOP 8): POST /ws/ai/chat/completions with
{id: chatId, agent, messages: [last message only], options: {sessionId, context}}; the answer is a server-sent
event stream. An approval request arrives as `tool-approval-request`; it is answered by sending back the
assistant message with the tool part in state `approval-responded`.
"""
import argparse
import json
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from axelor_session import Session  # noqa: E402

QUIET = {"text-start", "text-end", "tool-input-start", "tool-input-delta", "start-step", "finish-step",
         "reasoning-start", "reasoning-delta", "reasoning-end", "data-usage", "finish", "data-chat-title"}


def ask(session, agent, question, chat_id=None, approve=False):
    chat_id = chat_id or str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    msg = {"id": str(uuid.uuid4()), "role": "user", "parts": [{"type": "text", "text": question}]}
    text, log, started = [], [], time.time()
    for _ in range(6):
        assistant_id, inputs, approvals = None, {}, []
        for ev in session.stream("/ws/ai/chat/completions", {"id": chat_id, "agent": agent, "messages": [msg],
                                                               "options": {"sessionId": session_id, "context": {}}}):
            t = ev.get("type", "")
            if t == "start":
                assistant_id = ev.get("messageId") or assistant_id
            elif t == "text-delta":
                text.append(ev.get("delta", ""))
            elif t == "tool-input-available":
                inputs[ev["toolCallId"]] = (ev.get("toolName"), ev.get("input"))
                log.append(f"-> {ev.get('toolName')} {json.dumps(ev.get('input'), ensure_ascii=False)[:300]}")
            elif t == "tool-output-available":
                log.append(f"   <- {json.dumps(ev.get('output'), ensure_ascii=False)[:300]}")
            elif t == "tool-approval-request":
                approvals.append(ev)
                log.append(f"   || approval requested ({inputs.get(ev['toolCallId'], ('?',))[0]})")
            elif t in ("error", "tool-output-error"):
                log.append(f"!! {json.dumps(ev, ensure_ascii=False)[:500]}")
            elif t == "data-notify":
                log.append(f"   .. {ev.get('data', {}).get('message')}")
            elif t not in QUIET:
                log.append(f"?? {json.dumps(ev, ensure_ascii=False)[:300]}")
        if not (approvals and approve):
            break
        parts = []
        for ap in approvals:
            name, inp = inputs.get(ap["toolCallId"], ("unknown", {}))
            parts.append({"type": f"tool-{name}", "toolCallId": ap["toolCallId"], "state": "approval-responded",
                          "input": inp, "approval": {"id": ap["approvalId"], "approved": True}})
            log.append(f"   ok approved ({name})")
        msg = {"id": assistant_id or str(uuid.uuid4()), "role": "assistant", "parts": parts}
    answer = "".join(text)
    print("\n".join(log))
    print("-" * 60)
    print(answer or "(EMPTY ANSWER - see pitfalls: maxOutputTokens)")
    print(f"\n[chatId {chat_id}] [{time.time() - started:.0f} s]")
    return chat_id, answer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("agent")
    ap.add_argument("question", nargs="?")
    ap.add_argument("--chat")
    ap.add_argument("--approve", action="store_true")
    ap.add_argument("--batch")
    args = ap.parse_args()
    s = Session(args.url)
    if args.batch:
        with open(args.batch, encoding="utf-8") as fh:
            questions = [q.strip() for q in fh if q.strip() and not q.startswith("#")]
        for q in questions:
            print("=" * 60 + f"\nQ: {q}")
            ask(s, args.agent, q, approve=args.approve)
    elif args.question:
        ask(s, args.agent, args.question, args.chat, args.approve)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
