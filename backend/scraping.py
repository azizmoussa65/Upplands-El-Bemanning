import math
import os
import sys
import threading
import time
import uuid
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pipeline  # noqa: E402  (module at project root, reused as-is)

import financials  # noqa: E402
from db import companies_col  # noqa: E402
from models import get_setting, utcnow  # noqa: E402

_jobs = {}


def start_scrape_job(app, params):
    """Lance le scraping+enrichissement de pipeline.py dans un thread, retourne un job_id."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": "running",
        "processed": 0,
        "total": None,
        "new": 0,
        "updated": 0,
        "unchanged": 0,
        "skippedSni": 0,
        "error": None,
    }
    thread = threading.Thread(target=_run_scrape_job, args=(app, job_id, params), daemon=True)
    thread.start()
    return job_id


def get_job(job_id):
    return _jobs.get(job_id)


def _run_scrape_job(app, job_id, params):
    with app.app_context():
        job = _jobs[job_id]
        try:
            scrape_args = SimpleNamespace(
                query=params.get("query") or None,
                industry_code=params.get("industryCode") or None,
                pages=params.get("pages"),
                start_page=1,
                max_companies=params.get("maxCompanies"),
                county=params.get("county") or None,
                revenue_min=None,
                revenue_max=None,
                employees_min=None,
                employees_max=None,
                delay=params.get("delay", 1.0),
            )
            df = pipeline.scrape_allabolag(scrape_args)
            job["total"] = len(df)

            orgnrs = [o for o in df["orgnr"].tolist() if isinstance(o, str) and o]
            existing_by_orgnr = (
                {doc["orgnr"]: doc for doc in companies_col.find({"orgnr": {"$in": orgnrs}})}
                if orgnrs
                else {}
            )

            api_key = get_setting("serper_api_key")
            if api_key and not params.get("noEnrich"):
                # Pre-fill found_website for companies we already enriched before, so
                # enrich_dataframe's resume mode skips them (no wasted Serper credits
                # or repeat site visits for companies we already know).
                if "found_website" not in df.columns:
                    df["found_website"] = None
                for idx, row in df.iterrows():
                    existing = existing_by_orgnr.get(row.get("orgnr"))
                    if existing and existing.get("foundWebsite"):
                        df.at[idx, "found_website"] = existing["foundWebsite"]

                enrich_args = SimpleNamespace(
                    api_key=api_key,
                    resume=True,
                    debug=False,
                    save_every=10**9,
                    output=None,
                    delay=params.get("delay", 1.0),
                )
                df = pipeline.enrich_dataframe(df, enrich_args)

            for _, row in df.iterrows():
                orgnr = _clean(row.get("orgnr"))
                existing = existing_by_orgnr.get(orgnr)
                job["processed"] += 1

                if existing is not None and existing.get("sniCode"):
                    # Deja verifie lors d'un scraping precedent (une entreprise change
                    # rarement de SNI): on evite de refaire la requete detail.
                    sni_code = existing["sniCode"]
                    sni_name = existing.get("sniName")
                    financial_years = existing.get("financials")
                    key_figures = existing.get("keyFigures")
                else:
                    if not orgnr:
                        job["skippedSni"] += 1
                        continue
                    detail = financials.fetch_company_detail(orgnr)
                    time.sleep(params.get("delay", 1.0))
                    if detail is None or not financials.matches_target_sni(detail):
                        job["skippedSni"] += 1
                        continue
                    sni_code, sni_name = financials.extract_sni(detail)
                    financial_years, key_figures = financials.extract_financials(detail)

                result = _upsert_company(
                    row, params.get("industryCode"), existing,
                    sni_code, sni_name, financial_years, key_figures,
                )
                job[result] += 1

            job["status"] = "done"
        except Exception as exc:  # noqa: BLE001 - reported to the frontend via job status
            job["status"] = "error"
            job["error"] = str(exc)


def _clean(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _pick_mobile(row):
    """Numero mobile: priorite au mobile trouve sur le site (found_mobiles, le plus a
    jour), puis a tout champ telephone (mobile/mobile2/phone/phone2) qui a le format
    d'un mobile suedois 07X (allabolag range souvent un mobile dans le champ 'phone'
    sans le signaler)."""
    found = _clean(row.get("found_mobiles"))
    if found:
        return found.split(" | ")[0].strip()

    for field in ("mobile", "mobile2", "phone", "phone2", "best_phone"):
        candidate = _clean(row.get(field))
        if candidate and pipeline.MOBILE_REGEX.search(str(candidate)):
            return pipeline.clean_mobile(candidate)

    return _clean(row.get("mobile")) or _clean(row.get("mobile2"))


def _upsert_company(row, fallback_industry_code, existing, sni_code, sni_name, financial_years, key_figures):
    """Insere si nouvelle entreprise (orgnr inconnu), met a jour seulement si au moins
    un champ a reellement change, sinon ne touche pas la base. Renvoie 'new', 'updated'
    ou 'unchanged' pour que l'appelant puisse resumer le resultat du scraping."""
    orgnr = _clean(row.get("orgnr"))

    fields = {
        "name": _clean(row.get("name")),
        "contactPersonName": _clean(row.get("contactPerson_name")),
        "contactPersonRole": _clean(row.get("contactPerson_role")),
        "revenue": pipeline.to_number(row.get("revenue")),
        "employees": pipeline.to_number(row.get("employees")),
        "county": _clean(row.get("county")),
        "municipality": _clean(row.get("municipality")),
        "bestEmail": _clean(row.get("best_email")) or _clean(row.get("email")),
        "bestPhone": _clean(row.get("best_phone")) or _clean(row.get("phone")),
        "mobile": _pick_mobile(row),
        "foundWebsite": _clean(row.get("found_website")) or _clean(row.get("homePage")),
        "confidence": _clean(row.get("confidence")),
        "industryCode": _clean(row.get("currentIndustry_code")) or fallback_industry_code,
        "industryName": _clean(row.get("currentIndustry_name")),
        "sniCode": sni_code,
        "sniName": sni_name,
        "financials": financial_years,
        "keyFigures": key_figures,
    }

    if existing is not None:
        # Fields skipped during enrichment (resume mode) or when scraping without an
        # API key would otherwise wipe out data we already found in a previous run.
        for key in ("foundWebsite", "bestEmail", "bestPhone", "confidence", "mobile"):
            if not fields[key] and existing.get(key):
                fields[key] = existing[key]

    if existing is None:
        fields.update(
            {
                "orgnr": orgnr,
                "status": "nouveau",
                "emailStatus": "not_contacted",
                "assignedUserId": None,
                "createdAt": utcnow(),
                "callLogs": [],
                "aiRecommendation": None,
                "aiScore": None,
                "aiReason": None,
            }
        )
        companies_col.insert_one(fields)
        return "new"

    if any(existing.get(key) != value for key, value in fields.items()):
        companies_col.update_one({"_id": existing["_id"]}, {"$set": fields})
        return "updated"

    return "unchanged"
