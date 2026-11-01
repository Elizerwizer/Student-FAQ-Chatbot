"""AIOU Student FAQ chatbot engine (no external dependencies).

Usage:
    from chatbot import FAQBot
    bot = FAQBot()
    print(bot.reply("How do I submit my assignment?")["text"])
"""
import difflib
import json
import re
from pathlib import Path

KB_PATH = Path(__file__).with_name("knowledge_base.json")

# Synonym dictionary: variant -> canonical word used in the knowledge base.
SYNONYMS = {
    "homework": "assignment", "tma": "assignment", "assignments": "assignment",
    "tutor marked assignment": "assignment",
    "final examination": "exam", "test": "exam", "exams": "exam", "examination": "exam",
    "financial assistance": "scholarship", "scholarships": "scholarship",
    "enrollment": "admission", "enrolment": "admission", "registration": "admission",
    "admissions": "admission",
    "similarity": "plagiarism", "academic dishonesty": "plagiarism", "copying": "plagiarism",
}

# Common spelling fixes.
SPELLING = {"asignment": "assignment", "assigment": "assignment", "exma": "exam",
            "schoolarship": "scholarship", "scolarship": "scholarship",
            "adminssion": "admission", "addmission": "admission", "plagarism": "plagiarism"}

CHEAT_PATTERNS = [
    r"\bwrite (my|the|an?) (assignment|thesis|essay|paper|answers?)\b",
    r"\b(do|solve|complete) my (assignment|homework|exam|paper)\b",
    r"\b(give|send) me (the )?(solved|complete) (assignment|answers?)\b",
    r"\bbypass\b", r"\bfake (certificate|degree|marks)\b", r"\bcheat\b",
]

ESCALATION_PATTERNS = {
    "personal record": r"\bmy (result|marks|grade|roll number|record|transcript|degree)\b",
    "technical or payment problem": r"\b(payment|paid|refund|challan).*(problem|failed|not|issue|error)\b|\b(not working|error|cannot login|can't login|locked out)\b",
    "misconduct or appeal": r"\b(appeal|penalty|misconduct|unfair means|rechecking|recheck)\b",
    "document request": r"\b(verify|verification|issue|duplicate|migration|character certificate|name correction)\b",
}

SUPPORT = {"name": "AIOU Support", "email": "support@aiou.edu.pk", "phone": "051-111-112-468"}
EXAM_SUPPORT = {"name": "AIOU Examination Support", "email": "exam@aiou.edu.pk", "phone": "051-9571701"}

MIN_SCORE = 2.0


def normalize(text: str) -> str:
    text = re.sub(r"[^\w\s\-]", " ", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    words = [SPELLING.get(w, w) for w in text.split()]
    text = " ".join(words)
    for variant in sorted(SYNONYMS, key=len, reverse=True):  # longest first
        text = re.sub(rf"\b{re.escape(variant)}\b", SYNONYMS[variant], text)
    return text


class FAQBot:
    def __init__(self, kb_path: Path = KB_PATH):
        self.kb = json.loads(Path(kb_path).read_text(encoding="utf-8"))
        for rec in self.kb:
            rec["_kw"] = [normalize(k) for k in rec["keywords"]]

    # ---- matching -------------------------------------------------------
    def _score(self, query: str, rec: dict) -> float:
        q_words = query.split()
        score = 0.0
        for kw in rec["_kw"]:
            if re.search(rf"\b{re.escape(kw)}\b", query):          # exact phrase
                score += 2.0 + len(kw.split())
                continue
            kw_words = kw.split()
            hits = 0
            for kw_word in kw_words:                                  # fuzzy per word
                if kw_word in q_words or difflib.get_close_matches(kw_word, q_words, n=1, cutoff=0.85):
                    hits += 1
            if hits == len(kw_words) and hits > 1:
                score += 1.5 * hits
            elif hits and len(kw_words) == 1:
                score += 1.0
        return score

    def match(self, query: str):
        q = normalize(query)
        ranked = sorted(((self._score(q, r), r) for r in self.kb), key=lambda x: x[0], reverse=True)
        if not ranked or ranked[0][0] < MIN_SCORE:
            return None, 0.0
        return ranked[0][1], ranked[0][0]

    # ---- response -------------------------------------------------------
    def reply(self, message: str) -> dict:
        message = (message or "").strip()
        if not message:
            return self._out("Please type your question about AIOU or HEC.", kind="empty")

        low = message.lower()

        # Guardrail: academic dishonesty
        if any(re.search(p, low) for p in CHEAT_PATTERNS):
            return self._out(
                "I can't write assignments or exam answers, or help bypass university rules. "
                "I can explain the question, suggest a structure, explain concepts, and teach "
                "citation and referencing so you can write it in your own words.",
                kind="guardrail",
            )

        rec, score = self.match(message)

        # Escalation triggers
        reasons = [name for name, pat in ESCALATION_PATTERNS.items() if re.search(pat, low)]

        if rec is None:
            if reasons:
                contact = EXAM_SUPPORT if re.search(r"result|marks|grade|recheck|roll", low) else SUPPORT
                text = (f"Your question involves a {reasons[0]}. I can't access personal student data or decide "
                        "such cases, so please contact the official channel:\n\n"
                        f"- {contact['name']}: {contact['email']}\n- Phone: {contact['phone']}")
                return self._out(text, kind="escalation", escalate=True, contact=contact)
            text = ("I could not verify this in the official guidelines. Please contact AIOU/HEC directly.\n\n"
                    f"- AIOU Support: {SUPPORT['email']}\n- Phone: {SUPPORT['phone']}")
            return self._out(text, kind="no_match", contact=SUPPORT)

        # Missing information (program-dependent answers)
        if rec.get("needs_program") and not re.search(
                r"\b(bs|bed|ma|msc|mcom|m\.com|matric|fa|ba|associate|ad|ssc|hssc|postgraduate|ms|mphil|phd)\b", low):
            text = (f"{rec['answer']}\n\nTo give the exact figure I need one more detail: "
                    "**which program are you enrolled in?**")
            return self._out(text, kind="need_info", record=rec)

        contact = rec["contact"] if rec["contact"].get("email") else SUPPORT
        parts = [f"**Answer:** {rec['answer']}"]
        if rec.get("time_sensitive") or rec["confidence"] == "low":
            parts.append("**Important:** This depends on the current semester schedule or your specific case, "
                         "so please check the latest official AIOU notification.")
        if reasons:
            parts.append(f"**Important:** Your question involves a {reasons[0]}. I can't access personal data or "
                         "decide such cases, so please contact the official channel below.")
            contact = EXAM_SUPPORT if rec["topic"] == "Examinations" else contact
        src = rec["source"]
        parts.append(f"**Official source:** [{src['title']}]({src['url']})")
        contact_line = f"{contact['name']}"
        if contact.get("email"):
            contact_line += f": {contact['email']}"
        if contact.get("phone"):
            contact_line += f" | {contact['phone']}"
        parts.append(f"**Need more help:** {contact_line}")
        return self._out("\n\n".join(parts), kind="answer", record=rec, score=score,
                         escalate=bool(reasons), contact=contact)

    @staticmethod
    def _out(text, kind, record=None, score=0.0, escalate=False, contact=None):
        return {
            "text": text,
            "kind": kind,
            "id": record["id"] if record else None,
            "confidence": record["confidence"] if record else None,
            "score": round(score, 2),
            "escalate": escalate,
            "source": record["source"] if record else None,
            "contact": contact,
        }


if __name__ == "__main__":
    bot = FAQBot()
    print("AIOU FAQ bot (type 'quit' to exit)")
    while True:
        q = input("\nYou: ").strip()
        if q.lower() in {"quit", "exit"}:
            break
        print("\nBot:", bot.reply(q)["text"])
