#!/usr/bin/env python3
"""Idempotent deployment of Axelor AI tools, skills and agents from a JSON spec.

  python3 -I deploy_ai_spec.py <url> <spec.json> [--only tools,skills,agents] [--dry-run]

Every record is matched by its `code` (skill references by skill + name): an existing record is updated
with its current version, a missing one is created. Nothing is ever deleted. Order: tools, skills, agents
(an agent references tools and skills by code, and sub-agents by code).

Spec format (paths are relative to the spec file): see resources/spec-template.json.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from axelor_session import Session  # noqa: E402

AI = "com.axelor.ai.db."


class Deployer:
    def __init__(self, session, root, dry_run):
        self.s = session
        self.root = root
        self.dry = dry_run

    def read(self, rel):
        with open(os.path.join(self.root, rel), encoding="utf-8") as fh:
            return fh.read()

    def find(self, model, domain, ctx):
        rows = self.s.search(model, domain, ctx, ("id", "version"), limit=1)
        return rows[0] if rows else None

    def upsert(self, model, data, domain="self.code = :k", ctx=None):
        rec = self.find(model, domain, ctx or {"k": data["code"]})
        verb = "update" if rec else "create"
        if self.dry:
            return verb, {"id": rec["id"] if rec else None}
        if rec:
            data = dict(data, id=rec["id"], version=rec["version"])
            return verb, self.s.rest("POST", f"/ws/rest/{model}", {"data": data})["data"][0]
        return verb, self.s.rest("PUT", f"/ws/rest/{model}", {"data": data})["data"][0]

    def ids(self, model, codes, field="code"):
        out = []
        for code in codes:
            rec = self.find(model, f"self.{field} = :k", {"k": code})
            if not rec:
                sys.exit(f"{model} not found: {code} (deploy it first or fix the spec)")
            out.append({"id": rec["id"]})
        return out

    def tools(self, specs):
        for t in specs:
            script = "".join(self.read(p) + "\n" for p in t.get("prelude_files", [])) + self.read(t["script_file"])
            script = "(function () {\n" + script + "\n})()"
            data = {"code": t["code"], "name": t["name"], "type": "SCRIPT", "description": t["description"],
                    "inputSchema": json.dumps(t["inputSchema"], ensure_ascii=False), "script": script,
                    "isEnabled": True, "requiresApproval": t.get("requiresApproval", False),
                    "isDestructive": t.get("isDestructive", False)}
            verb, _ = self.upsert(AI + "AiTool", data)
            print(f"tool   {verb:6} {t['code']} ({len(script)} chars)")

    def skills(self, specs):
        for sk in specs:
            data = {"code": sk["code"], "name": sk["name"], "description": sk["description"],
                    "instructions": self.read(sk["instructions_file"]), "isEnabled": True, "sortOrder": sk.get("sortOrder", 50)}
            verb, rec = self.upsert(AI + "AiSkill", data)
            print(f"skill  {verb:6} {sk['code']}")
            for ref in sk.get("references", []):
                content = self.read(ref["file"])
                rdata = {"name": ref["name"], "title": ref["title"], "content": content}
                if self.dry or not rec.get("id"):
                    print(f"  ref  {ref['name']} ({len(content)} chars)")
                    continue
                rdata["skill"] = {"id": rec["id"]}
                rverb, _ = self.upsert(AI + "AiSkillReference", rdata, "self.skill.id = :s and self.name = :n",
                                       {"s": rec["id"], "n": ref["name"]})
                print(f"  ref  {rverb:6} {ref['name']} ({len(content)} chars)")

    def agents(self, specs):
        for ag in specs:
            data = {k: ag[k] for k in ("code", "name", "audience", "toolPolicy", "maxSteps", "maxOutputTokens",
                                       "isEnabled", "isDefault", "sortOrder", "allowedModels", "temperature") if k in ag}
            data["systemPrompt"] = self.read(ag["systemPrompt_file"])
            data["suggestions"] = "\n".join(ag.get("suggestions", []))
            if self.dry:
                print(f"agent  check  {ag['code']} tools={len(ag['tools'])} skills={len(ag.get('skills', []))}")
                continue
            data["tools"] = self.ids(AI + "AiTool", ag["tools"])
            data["skills"] = self.ids(AI + "AiSkill", ag.get("skills", []))
            data["subAgents"] = self.ids(AI + "AiAgent", ag.get("subAgents", []))
            data["model"] = self.ids(AI + "AiModel", [ag["model_code"]])[0]
            data["groups"] = self.ids("com.axelor.auth.db.Group", ag.get("groups", []))
            verb, _ = self.upsert(AI + "AiAgent", data)
            print(f"agent  {verb:6} {ag['code']} -> model {ag['model_code']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("spec")
    ap.add_argument("--only", default="tools,skills,agents")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    with open(args.spec, encoding="utf-8") as fh:
        spec = json.load(fh)
    d = Deployer(Session(args.url), os.path.dirname(os.path.abspath(args.spec)), args.dry_run)
    only = set(args.only.split(","))
    if "tools" in only:
        d.tools(spec.get("tools", []))
    if "skills" in only:
        d.skills(spec.get("skills", []))
    if "agents" in only:
        d.agents(spec.get("agents", []))


if __name__ == "__main__":
    main()
