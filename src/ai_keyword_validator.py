"""AI Keyword Validator — Auto-approve/reject keywords using HuggingFace models.

Uses the existing HF zero-shot classifier pipeline to:
  1. Verify if a keyword is actually cybersecurity-related
  2. Assign the correct category (Red Team, Blue Team, Malware, Exploit, OSINT, Cloud, Forensics, etc.)
  3. Auto-approve valid keywords, flag dubious ones for manual review
"""

import logging
import time
from src.database import get_db_connection
from src.hf_client import classify_zero_shot

CYBER_CATEGORIES = [
    "Red Team", "Blue Team", "Malware", "Exploit", "OSINT",
    "Cloud Security", "Forensics", "Network Security", "Cryptography",
    "Web Security", "Mobile Security", "IoT Security", "Reverse Engineering",
    "Threat Intelligence", "Incident Response", "DevSecOps",
]

REJECT_CATEGORIES = [
    "not cybersecurity", "generic programming", "gaming",
    "finance", "healthcare", "education", "entertainment",
    "sports", "politics", "food", "travel", "shopping",
]


def validate_keyword(term: str) -> dict:
    """Validate if a keyword is cybersecurity-related and assign category."""
    result = classify_zero_shot(term, CYBER_CATEGORIES + ["not cybersecurity"])
    all_scores = result.get("all", {})

    cyber_score = sum(all_scores.get(cat, 0) for cat in CYBER_CATEGORIES if cat in all_scores)
    not_cyber = all_scores.get("not cybersecurity", 0)

    # Determine best category
    best_cat = "Unknown"
    best_score = 0
    for cat in CYBER_CATEGORIES:
        if cat in all_scores and all_scores[cat] > best_score:
            best_score = all_scores[cat]
            best_cat = cat

    is_cyber = cyber_score > not_cyber and cyber_score > 0.3

    return {
        "term": term,
        "is_cyber": is_cyber,
        "category": best_cat,
        "confidence": round(best_score, 3),
        "cyber_score": round(cyber_score, 3),
        "not_cyber_score": round(not_cyber, 3),
    }


def batch_validate_keywords(limit: int = 200, auto_approve_threshold: float = 0.6) -> dict:
    """Batch validate pending keywords and auto-approve/reject."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch pending keywords
    cur.execute("""
        SELECT term, score FROM discovered_keywords
        WHERE status = 'pending'
        ORDER BY score DESC
        LIMIT %s
    """, (limit,))

    rows = cur.fetchall()
    approved = 0
    rejected = 0
    categorized = 0
    errors = 0

    logging.info(f"🤖 AI Validator: validating {len(rows)} pending keywords...")

    for row in rows:
        term = row[0]
        try:
            result = validate_keyword(term)
            if result["is_cyber"] and result["confidence"] >= auto_approve_threshold:
                cur.execute(
                    """UPDATE discovered_keywords
                       SET status = 'approved', category_guess = %s,
                           reviewed_at = CURRENT_TIMESTAMP
                       WHERE term = %s""",
                    (result["category"], term),
                )
                approved += 1
                if result["category"] != "Unknown":
                    categorized += 1
            elif not result["is_cyber"] or result["confidence"] < 0.2:
                cur.execute(
                    """UPDATE discovered_keywords
                       SET status = 'rejected', reviewed_at = CURRENT_TIMESTAMP
                       WHERE term = %s""",
                    (term,),
                )
                rejected += 1
            # Leave borderline cases (0.2-0.6) for manual review
            time.sleep(0.1)  # Rate limit HF API
        except Exception as e:
            logging.error(f"Error validating {term}: {e}")
            errors += 1
            time.sleep(1)

    conn.commit()
    cur.close()
    conn.close()

    stats = {"pending": len(rows), "approved": approved, "categorized": categorized,
             "rejected": rejected, "errors": errors}
    logging.info(f"🤖 AI Validator done: {stats}")
    return stats


def get_keyword_stats() -> dict:
    """Statistics on keyword validation status."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT status, COUNT(*) FROM discovered_keywords GROUP BY status")
    by_status = {r[0]: r[1] for r in cur.fetchall()}
    cur.execute("SELECT category_guess, COUNT(*) FROM discovered_keywords WHERE status='approved' GROUP BY category_guess ORDER BY COUNT(*) DESC LIMIT 15")
    by_category = [{"category": r[0] or "Unknown", "count": r[1]} for r in cur.fetchall()]
    cur.execute("SELECT COUNT(*) FROM discovered_keywords WHERE status='pending'")
    pending = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {"by_status": by_status, "by_category": by_category, "pending_to_review": pending}
