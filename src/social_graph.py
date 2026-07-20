import logging
import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "cybergraph")
NEO4J_AUTH_NONE = os.getenv("NEO4J_AUTH_NONE", "true").lower() == "true"

_driver = None


def get_driver():
    global _driver
    try:
        if _driver is None:
            if NEO4J_AUTH_NONE:
                _driver = GraphDatabase.driver(NEO4J_URI, auth=None)
            else:
                _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            _driver.verify_connectivity()
            logging.info("Connecte a Neo4j (%s)", NEO4J_URI)
        return _driver
    except Exception as e:
        logging.warning("Neo4j non disponible: %s", e)
        if _driver:
            try: _driver.close()
            except: pass
            _driver = None
        return None


def close():
    global _driver
    if _driver:
        _driver.close()
        _driver = None


def init_graph():
    driver = get_driver()
    if not driver:
        return False
    with driver.session() as session:
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (h:Hacker) REQUIRE h.github_id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:APTCampaign) REQUIRE c.name IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:Tool) REQUIRE t.name IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:CVE) REQUIRE c.cve_id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repo) REQUIRE r.full_name IS UNIQUE")
    logging.info("Contraintes Neo4j initialisees")
    return True


def seed_from_repos(repos: list[dict]):
    driver = get_driver()
    if not driver:
        return 0
    count = 0
    with driver.session() as session:
        for repo in repos:
            full_name = repo.get("full_name") or repo.get("name", "")
            if not full_name:
                continue
            session.run(
                """
                MERGE (r:Repo {full_name: $full_name})
                SET r.description = $desc, r.language = $lang,
                    r.stars = $stars, r.topics = $topics,
                    r.security_verdict = $verdict, r.updated_at = $updated
                """,
                full_name=full_name,
                desc=(repo.get("description") or "")[:4000],
                lang=repo.get("language") or "",
                stars=repo.get("stars", 0),
                topics=",".join(repo.get("topics", []) or []),
                verdict=repo.get("security_verdict") or "",
                updated=str(repo.get("updated_at", "")),
            )
            count += 1
    return count


def seed_from_news(news: list[dict]):
    driver = get_driver()
    if not driver:
        return 0
    count = 0
    with driver.session() as session:
        for item in news:
            title = (item.get("title") or "")[:200]
            if not title:
                continue
            tags = item.get("tags") or item.get("categories") or []
            for tag in tags:
                tag_str = str(tag).strip()
                if not tag_str or len(tag_str) > 80:
                    continue
                session.run(
                    """
                    MERGE (t:Tool {name: $name})
                    SET t.source = 'news', t.label = $name
                    """,
                    name=tag_str.lower(),
                )
                count += 1
            desc = (item.get("description") or item.get("summary") or "")[:2000]
            if desc:
                import re
                apt_matches = re.findall(r'\bAPT\d+\b', desc, re.IGNORECASE)
                for apt in set(apt_matches):
                    session.run(
                        """
                        MERGE (c:APTCampaign {name: $name})
                        SET c.description = $desc
                        """,
                        name=apt.upper(),
                        desc=desc[:1000],
                    )
                    count += 1
    return count


def seed_from_cves(cves: list[dict]):
    driver = get_driver()
    if not driver:
        return 0
    count = 0
    with driver.session() as session:
        for cve in cves:
            cve_id = cve.get("cve_id", "")
            if not cve_id:
                continue
            session.run(
                """
                MERGE (c:CVE {cve_id: $cve_id})
                SET c.description = $desc, c.severity = $severity,
                    c.cvss_score = $score, c.published = $pub,
                    c.weaknesses = $weak
                """,
                cve_id=cve_id,
                desc=(cve.get("description") or "")[:4000],
                severity=cve.get("severity", ""),
                score=cve.get("cvss_score"),
                pub=str(cve.get("published") or ""),
                weak=",".join(cve.get("weaknesses") or []),
            )
            count += 1
    return count


def link_contributors(repo_full_name: str, contributors: list[dict]):
    driver = get_driver()
    if not driver:
        return
    with driver.session() as session:
        for c in contributors:
            login = c.get("login", "")
            if not login:
                continue
            session.run(
                """
                MERGE (h:Hacker {username: $login})
                SET h.github_id = $gh_id, h.avatar_url = $avatar,
                    h.profile_url = $url
                WITH h
                MATCH (r:Repo {full_name: $repo})
                MERGE (h)-[:CONTRIBUTES_TO]->(r)
                """,
                login=login,
                gh_id=str(c.get("id", "")),
                avatar=c.get("avatar_url", ""),
                url=c.get("html_url", ""),
                repo=repo_full_name,
            )


def link_collaborations(threshold: int = 2):
    driver = get_driver()
    if not driver:
        return 0
    with driver.session() as session:
        result = session.run(
            """
            MATCH (h1:Hacker)-[:CONTRIBUTES_TO]->(r:Repo)<-[:CONTRIBUTES_TO]-(h2:Hacker)
            WHERE h1.username < h2.username
            WITH h1, h2, COUNT(r) AS common
            WHERE common >= $threshold
            MERGE (h1)-[:COLLABORATES_WITH {weight: common}]-(h2)
            RETURN count(*) AS created
            """,
            threshold=threshold,
        )
        record = result.single()
        return record["created"] if record else 0


def get_graph_stats():
    driver = get_driver()
    if not driver:
        return {"available": False, "nodes": 0, "relationships": 0}
    with driver.session() as session:
        nodes = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rels = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        labels = session.run(
            "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt ORDER BY cnt DESC"
        ).data()
        return {
            "available": True,
            "nodes": nodes,
            "relationships": rels,
            "by_label": {r["label"]: r["cnt"] for r in labels},
        }


def query_graph(label: str = "", limit: int = 50):
    driver = get_driver()
    if not driver:
        return {"available": False, "nodes": [], "links": []}
    with driver.session() as session:
        if label:
            result = session.run(
                f"MATCH (n:{label})-[r]-(m) RETURN n, r, m LIMIT $limit",
                limit=limit,
            )
        else:
            result = session.run(
                "MATCH (n)-[r]-(m) RETURN n, r, m LIMIT $limit",
                limit=limit,
            )
        nodes_set: dict[str, dict] = {}
        links: list[dict] = []
        for record in result:
            for node_key in ["n", "m"]:
                node = record[node_key]
                if node:
                    nid = str(node.element_id)
                    if nid not in nodes_set:
                        labels = list(node.labels)
                        nodes_set[nid] = {
                            "id": nid,
                            "label": labels[0] if labels else "Unknown",
                            "name": node.get("username") or node.get("name") or node.get("cve_id") or node.get("full_name") or str(node.get("title", "")),
                            "properties": dict(node.items()),
                        }
            rel = record.get("r")
            if rel:
                links.append({
                    "source": str(rel.start_node.element_id),
                    "target": str(rel.end_node.element_id),
                    "type": rel.type,
                    "weight": rel.get("weight", 1),
                })
        return {
            "available": True,
            "nodes": list(nodes_set.values()),
            "links": links,
        }
