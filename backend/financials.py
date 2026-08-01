"""Recupere le code SNI officiel + les donnees financieres (Bokslut/Nyckeltal) d'une
entreprise depuis sa page detail allabolag.se.

Ces donnees ne sont PAS presentes dans l'API de recherche deja utilisee par pipeline.py
(qui expose seulement le code branche marketing d'allabolag, pas le SNI officiel). La
page detail (https://www.allabolag.se/{orgnr}) embarque en revanche un JSON complet
(hydration Next.js, balise <script id="__NEXT_DATA__">) contenant:
  - naceIndustries: le(s) code(s) SNI officiel(s), ex: ["43210 Elinstallationer"]
  - companyAccounts: jusqu'a 5 ans de Bokslut, en lignes {code, amount}

Le mapping code -> libelle ci-dessous a ete verifie manuellement en comparant les
valeurs brutes du JSON aux valeurs affichees sur la page (widgets Nyckeltal/Bokslut)
pour une entreprise reelle, plutot que devine depuis les abreviations.
"""

import json
import re

import requests

TARGET_SNI = "43210"

DETAIL_URL = "https://www.allabolag.se/{orgnr}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}

NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)

# Verifie contre les widgets "Bokslut" de la page detail.
BOKSLUT_CODES = {
    "revenue": "SDI",                              # Omsattning
    "resultEfterFinansnetto": "resultat_e_finansnetto",  # Resultat efter finansnetto
    "ebitda": "EBITDA",
    "aretsResultat": "DR",                          # Arets resultat
    "summaTillgangar": "SED",                       # Summa tillgangar
    "egetKapital": "SEK",                           # Eget kapital
}

# Verifie contre les jauges "Nyckeltal" de la page detail (valeurs en %).
NYCKELTAL_CODES = {
    "soliditet": "EKA",
    "vinstmarginal": "TR",
    "kassalikviditet": "RG",
}


def fetch_company_detail(orgnr, session=None):
    """Recupere et parse le JSON __NEXT_DATA__ de la page detail d'une entreprise.
    Renvoie None si la page est inaccessible ou si le JSON attendu est absent."""
    http = session or requests
    try:
        resp = http.get(DETAIL_URL.format(orgnr=orgnr), headers=HEADERS, timeout=20)
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None

    match = NEXT_DATA_RE.search(resp.text)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None

    return data.get("props", {}).get("pageProps", {}).get("company")


def extract_sni(company):
    """Renvoie (code, nom) du premier code SNI officiel, ou (None, None)."""
    nace = company.get("naceIndustries") or []
    if not nace:
        return None, None
    code, _, name = nace[0].partition(" ")
    return code.strip() or None, (name.strip() or None)


def matches_target_sni(company, target=TARGET_SNI):
    """Une entreprise peut avoir plusieurs codes SNI: on garde si l'un d'eux correspond."""
    nace = company.get("naceIndustries") or []
    return any(entry.split(" ", 1)[0].strip() == target for entry in nace)


def _amount(by_code, code):
    value = by_code.get(code)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_financials(company):
    """Renvoie (bokslut_annuel, nyckeltal_dernier_exercice)."""
    accounts = company.get("companyAccounts") or []

    yearly = []
    for entry in accounts:
        by_code = {item["code"]: item.get("amount") for item in entry.get("accounts", [])}
        yearly.append(
            {
                "year": entry.get("year"),
                "period": entry.get("period"),
                "currency": entry.get("currency"),
                "revenue": _amount(by_code, BOKSLUT_CODES["revenue"]),
                "resultEfterFinansnetto": _amount(by_code, BOKSLUT_CODES["resultEfterFinansnetto"]),
                "ebitda": _amount(by_code, BOKSLUT_CODES["ebitda"]),
                "aretsResultat": _amount(by_code, BOKSLUT_CODES["aretsResultat"]),
                "summaTillgangar": _amount(by_code, BOKSLUT_CODES["summaTillgangar"]),
                "egetKapital": _amount(by_code, BOKSLUT_CODES["egetKapital"]),
            }
        )

    key_figures = None
    if accounts:
        latest = {item["code"]: item.get("amount") for item in accounts[0].get("accounts", [])}
        key_figures = {
            "soliditet": _amount(latest, NYCKELTAL_CODES["soliditet"]),
            "vinstmarginal": _amount(latest, NYCKELTAL_CODES["vinstmarginal"]),
            "kassalikviditet": _amount(latest, NYCKELTAL_CODES["kassalikviditet"]),
        }

    return yearly, key_figures
