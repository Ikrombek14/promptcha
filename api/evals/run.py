"""Eval: real soʻrovlar toʻplamini pipeline orqali oʻtkazib, sifat va tezlikni jadvalga yigʻadi.

Ishlatish (API ishlab turishi kerak, lokal 8001 yoki prod):
  uv run python evals/run.py --base http://127.0.0.1:8001 --limit 5 --pause 15
Natija: evals/results/<sana>.json va .md (jadval: tur/arxetip toʻgʻriligi, savollar, ball, vaqt, faktlar).
Savollarga avtomatik javob: har savolning birinchi varianti (real foydalanuvchi oʻrniga).
Groq tekin tarifida ketma-ket yugurish 429 beradi — `--pause` bilan oraliq qoʻying.
"""

import argparse
import json
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

HERE = Path(__file__).parent
HEADERS = {"X-Requested-With": "promptcha", "Origin": "http://localhost:3000"}


def parse_sse(body: str) -> list[tuple[str, dict]]:
    out = []
    for block in body.replace("\r", "").split("\n\n"):
        ev, data = None, []
        for line in block.split("\n"):
            if line.startswith("event:"):
                ev = line[6:].strip()
            elif line.startswith("data:"):
                data.append(line[5:].strip())
        if ev:
            out.append((ev, json.loads("\n".join(data)) if data else {}))
    return out


def run_job(c: httpx.Client, base: str, body: dict) -> tuple[list[tuple[str, dict]], float]:
    r = c.post(f"{base}/api/prompts/generate", json=body, headers=HEADERS)
    r.raise_for_status()
    job = r.json()["job_id"]
    t0 = time.time()
    with c.stream("GET", f"{base}/api/prompts/jobs/{job}", headers=HEADERS) as s:
        text = "".join(s.iter_text())
    return parse_sse(text), time.time() - t0


def evaluate(c: httpx.Client, base: str, item: dict, locale: str) -> dict:
    res: dict = {"id": item["id"], "text": item["text"]}
    t0 = time.time()
    a = c.post(
        f"{base}/api/prompts/analyze",
        json={"text": item["text"], "locale": locale},
        headers=HEADERS,
    ).json()
    res["analyze_s"] = round(time.time() - t0, 2)
    res["kind"], res["archetype"], res["tools"] = a["kind"], a.get("archetype"), a["tools"]
    res["kind_ok"] = a["kind"] == item["expect_kind"]
    res["archetype_ok"] = a.get("archetype") == item["expect_archetype"]
    time.sleep(4)  # prefetch tugasin
    ev, t_q = run_job(c, base, {"text": item["text"], "locale": locale})
    questions = next((d["questions"] for e, d in ev if e == "clarify"), [])
    res["questions"] = [q["id"] for q in questions]
    res["questions_s"] = round(t_q, 2)
    answers = {q["id"]: q["options"][0] for q in questions if q.get("options")}
    if questions:
        ev, t_g = run_job(c, base, {"text": item["text"], "locale": locale, "answers": answers})
    else:
        t_g = t_q
    done = next((d for e, d in ev if e == "done"), {})
    ex = next((d for e, d in ev if e == "explain"), {})
    err = next((d for e, d in ev if e == "error"), None)
    prompt = done.get("prompt", "")
    res["generate_s"] = round(t_g, 2)
    res["error"] = err["detail"] if err else None
    res["score"] = ex.get("score")
    res["failed"] = [cr["name"] for cr in ex.get("criteria", []) if not cr["ok"]]
    low = prompt.lower()
    res["facts_ok"] = all(m.lower() in low for m in item.get("must_contain", []))
    res["missing_facts"] = [m for m in item.get("must_contain", []) if m.lower() not in low]
    res["words"] = len(prompt.split())
    res["prompt"] = prompt
    res["notes"] = ex.get("notes", [])
    return res


def to_markdown(rows: list[dict]) -> str:
    lines = [
        "| id | tur | arxetip | savollar | ball | kamchilik | faktlar | tahlil s | prompt s |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {'✓' if r['kind_ok'] else '✗ ' + r['kind']} | "
            f"{'✓' if r['archetype_ok'] else '✗ ' + str(r['archetype'])} | "
            f"{', '.join(r['questions']) or '—'} | {r['score'] if r['score'] is not None else 'xato'} | "
            f"{', '.join(r['failed']) or '—'} | {'✓' if r['facts_ok'] else '✗ ' + ', '.join(r['missing_facts'])} | "
            f"{r['analyze_s']} | {r['generate_s']} |"
        )
    scores = [r["score"] for r in rows if r["score"] is not None]
    if scores:
        lines.append("")
        lines.append(
            f"Oʻrtacha ball: {statistics.mean(scores):.1f} · tur toʻgʻri: "
            f"{sum(r['kind_ok'] for r in rows)}/{len(rows)} · arxetip toʻgʻri: "
            f"{sum(r['archetype_ok'] for r in rows)}/{len(rows)} · faktlar saqlangan: "
            f"{sum(r['facts_ok'] for r in rows)}/{len(rows)} · oʻrtacha prompt vaqti: "
            f"{statistics.mean(r['generate_s'] for r in rows):.1f} s"
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8001")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--pause", type=float, default=15.0)
    ap.add_argument("--locale", default="uz")
    ap.add_argument("--only", default="", help="vergul bilan id'lar")
    args = ap.parse_args()

    items = [
        json.loads(line)
        for line in (HERE / "requests.jsonl").read_text("utf-8").splitlines()
        if line.strip()
    ]
    if args.only:
        wanted = set(args.only.split(","))
        items = [i for i in items if i["id"] in wanted]
    if args.limit:
        items = items[: args.limit]

    rows = []
    with httpx.Client(timeout=240) as c:
        for i, item in enumerate(items):
            if i:
                time.sleep(args.pause)
            try:
                r = evaluate(c, args.base, item, args.locale)
            except Exception as e:  # noqa: BLE001 — eval davom etsin
                r = {
                    "id": item["id"],
                    "text": item["text"],
                    "error": str(e)[:200],
                    "kind_ok": False,
                    "archetype_ok": False,
                    "kind": "?",
                    "archetype": "?",
                    "tools": [],
                    "questions": [],
                    "score": None,
                    "failed": [],
                    "facts_ok": False,
                    "missing_facts": [],
                    "analyze_s": 0,
                    "questions_s": 0,
                    "generate_s": 0,
                    "words": 0,
                    "prompt": "",
                    "notes": [],
                }
            rows.append(r)
            print(
                f"{r['id']:16} kind={'ok' if r['kind_ok'] else r['kind']} arch={'ok' if r['archetype_ok'] else r['archetype']} q={r['questions']} score={r['score']} facts={'ok' if r['facts_ok'] else r['missing_facts']} t={r['generate_s']}s {('ERR ' + str(r['error'])) if r.get('error') else ''}"
            )

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y-%m-%d-%H%M")
    (out_dir / f"{stamp}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), "utf-8")
    md = to_markdown(rows)
    (out_dir / f"{stamp}.md").write_text(md, "utf-8")
    print("\n" + md)


if __name__ == "__main__":
    main()
