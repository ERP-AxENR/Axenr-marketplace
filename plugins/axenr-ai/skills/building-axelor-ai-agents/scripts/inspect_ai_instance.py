#!/usr/bin/env python3
"""Read-only inventory of the Axelor AI module of an instance, before designing an agent.

  python3 -I inspect_ai_instance.py <url> [--agent <code>] [--out <dir>]

Prints: AI models present and their volumes, chat models enabled and really used (usage log),
existing agents (model, tool policy, steps, output cap), tools by type, skills, knowledge bases.
--agent exports one existing agent (prompt, tools, skills, allowedModels) and the scripts of its SCRIPT
tools into --out, to reuse it as a pattern.
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from axelor_session import Session  # noqa: E402

AI = "com.axelor.ai.db."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--agent")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()
    s = Session(args.url)

    models = s.search("com.axelor.meta.db.MetaModel", "self.packageName like 'com.axelor.ai%'", fields=("fullName",), limit=100)
    print("== AI module models")
    for m in models:
        total = s.rest("POST", f"/ws/rest/{m['fullName']}/search", {"limit": 1, "fields": ["id"]}).get("total")
        print(f"  {m['fullName']}: {total}")

    print("\n== Chat models (enabled) and real usage over the last 500 calls")
    usage = s.search(AI + "AiUsageLog", fields=("modelCode", "status"), limit=500, sort=["-id"])
    used = collections.Counter((u.get("modelCode"), u.get("status")) for u in usage)
    for m in s.search(AI + "AiModel", "self.isEnabled = true", fields=("code", "type", "provider"), limit=200):
        calls = {st: n for (code, st), n in used.items() if code == m["code"]}
        print(f"  [{m['id']}] {m['code']} {m.get('type')} {calls or ''}")

    print("\n== Agents")
    for a in s.search(AI + "AiAgent", fields=("code", "name", "model", "toolPolicy", "maxSteps", "maxOutputTokens", "isDefault", "isEnabled"), limit=200):
        print(f"  {a['code']}: {a['name']} | model={(a.get('model') or {}).get('name')} policy={a.get('toolPolicy')} "
              f"steps={a.get('maxSteps')} maxOut={a.get('maxOutputTokens')} default={a.get('isDefault')} enabled={a.get('isEnabled')}")

    print("\n== Tools by type")
    by_type = collections.defaultdict(list)
    for t in s.search(AI + "AiTool", fields=("code", "type", "requiresApproval", "isDestructive"), limit=500):
        flag = ("*" if t.get("requiresApproval") else "") + ("!" if t.get("isDestructive") else "")
        by_type[t["type"]].append(t["code"] + flag)
    for typ, codes in sorted(by_type.items()):
        print(f"  {typ} ({len(codes)}): {', '.join(sorted(codes))}")
    print("  (* = approval card, ! = destructive)")

    print("\n== Skills")
    for sk in s.search(AI + "AiSkill", fields=("code", "description"), limit=500):
        print(f"  {sk['code']}: {(sk.get('description') or '')[:100]}")

    print("\n== Knowledge bases")
    for kb in s.search(AI + "AiKnowledgeBase", fields=("code", "embeddingModel", "isGlobal", "isEnabled"), limit=100):
        print(f"  {kb['code']}: embedding={(kb.get('embeddingModel') or {}).get('name')} global={kb.get('isGlobal')}")
    for src in s.search(AI + "AiKnowledgeSource", fields=("type", "model", "status", "chunkCount", "errorMessage"), limit=100):
        print(f"    source {src['type']} {src.get('model')} status={src.get('status')} chunks={src.get('chunkCount')} {src.get('errorMessage') or ''}")

    if args.agent:
        rows = s.search(AI + "AiAgent", "self.code = :c", {"c": args.agent}, ("id",), limit=1)
        if not rows:
            sys.exit(f"agent {args.agent} not found")
        fields = ["code", "name", "systemPrompt", "suggestions", "tools", "skills", "subAgents", "model", "utilityModel", "maxSteps",
                  "temperature", "maxOutputTokens", "allowedModels", "toolPolicy", "audience", "groups", "roles", "users", "reasoningEffort"]
        agent = s.rest("POST", f"/ws/rest/{AI}AiAgent/{rows[0]['id']}/fetch", {"fields": fields})["data"][0]
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, f"agent-{args.agent}.json"), "w", encoding="utf-8") as fh:
            json.dump(agent, fh, ensure_ascii=False, indent=1)
        for tool in agent.get("tools") or []:
            t = s.rest("POST", f"/ws/rest/{AI}AiTool/{tool['id']}/fetch",
                       {"fields": ["code", "type", "description", "inputSchema", "script", "requiresApproval"]})["data"][0]
            if t.get("type") == "SCRIPT":
                with open(os.path.join(args.out, f"tool-{t['code']}.json"), "w", encoding="utf-8") as fh:
                    json.dump(t, fh, ensure_ascii=False, indent=1)
        print(f"\nAgent {args.agent} exported to {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
