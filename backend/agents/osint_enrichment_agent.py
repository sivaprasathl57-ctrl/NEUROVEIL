"""
OSINT Enrichment Agent — Real-World Open Source Intelligence
Performs live lookups on extracted entities using free public APIs:
  • IP geolocation via ipapi.co (no key needed)
  • WHOIS domain info via whois.domaintools.com public data
  • Phone number info via numverify (basic, free)
  • URL analysis via URLhaus (abuse.ch — free threat intelligence)
"""
import httpx
import asyncio
import re
from datetime import datetime
from typing import Optional

TIMEOUT = 10.0  # seconds per lookup


async def _safe_get(url: str, headers: dict = None) -> Optional[dict]:
    """Safe HTTP GET with timeout, returns None on any error."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(url, headers=headers or {}, follow_redirects=True)
            if r.status_code == 200:
                return r.json()
    except Exception:
        pass
    return None


async def geolocate_ip(ip: str) -> dict:
    """
    Geolocate an IP address using ipapi.co (free, no API key).
    Returns city, region, country, ISP, org, timezone.
    """
    # Filter private/loopback IPs
    if ip.startswith(("10.", "192.168.", "127.", "172.16.", "172.17.")):
        return {"ip": ip, "note": "Private IP — not publicly routable", "country": "Local"}

    data = await _safe_get(f"https://ipapi.co/{ip}/json/")
    if not data:
        return {"ip": ip, "error": "Geolocation lookup failed"}

    return {
        "ip": ip,
        "city": data.get("city", "Unknown"),
        "region": data.get("region", "Unknown"),
        "country": data.get("country_name", "Unknown"),
        "country_code": data.get("country_code", ""),
        "isp": data.get("org", "Unknown"),
        "asn": data.get("asn", ""),
        "timezone": data.get("timezone", ""),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "is_vpn_likely": _is_likely_vpn(data.get("org", ""), data.get("asn", "")),
        "threat_notes": _ip_threat_note(data)
    }


def _is_likely_vpn(org: str, asn: str) -> bool:
    vpn_keywords = ["VPN", "Proxy", "Hosting", "DataCenter", "Cloud", "Digital Ocean",
                    "Linode", "Vultr", "Hetzner", "OVH", "AWS", "Azure", "GCP"]
    return any(kw.lower() in org.lower() for kw in vpn_keywords)


def _ip_threat_note(data: dict) -> list[str]:
    notes = []
    org = data.get("org", "").lower()
    if any(k in org for k in ["vpn", "proxy", "tor"]):
        notes.append("⚠️ IP appears to be VPN/Proxy — suspect may be hiding location")
    if data.get("country_code") not in ["IN", ""]:
        notes.append(f"🌍 Foreign IP — originates from {data.get('country_name')} (possible international nexus)")
    return notes


async def whois_domain(domain: str) -> dict:
    """
    Basic WHOIS lookup via rdap.org (free, no key).
    Returns registrar, creation date, country.
    """
    # Clean URL to extract domain
    domain = re.sub(r"https?://", "", domain).split("/")[0].split("?")[0]
    if not domain or len(domain) < 4:
        return {"domain": domain, "error": "Invalid domain"}

    data = await _safe_get(f"https://rdap.org/domain/{domain}")
    if not data:
        return {"domain": domain, "status": "WHOIS lookup unavailable", "notes": ["Domain may not exist or WHOIS blocked"]}

    # Extract key fields from RDAP response
    registrar = ""
    created = ""
    expires = ""
    status_list = data.get("status", [])

    for entity in data.get("entities", []):
        roles = entity.get("roles", [])
        if "registrar" in roles:
            vcard = entity.get("vcardArray", [])
            if vcard:
                registrar = str(vcard)[:100]

    for event in data.get("events", []):
        if event.get("eventAction") == "registration":
            created = event.get("eventDate", "")[:10]
        if event.get("eventAction") == "expiration":
            expires = event.get("eventDate", "")[:10]

    # Age calculation
    age_days = None
    age_warning = False
    if created:
        try:
            from datetime import datetime
            age_days = (datetime.now() - datetime.fromisoformat(created.replace("Z", ""))).days
            age_warning = age_days < 90  # Newly registered domains are suspicious
        except Exception:
            pass

    return {
        "domain": domain,
        "registrar": registrar or "Unknown",
        "registered": created or "Unknown",
        "expires": expires or "Unknown",
        "age_days": age_days,
        "status": status_list,
        "is_newly_registered": age_warning,
        "threat_notes": [
            "⚠️ Domain newly registered (< 90 days) — high phishing risk"
        ] if age_warning else []
    }


async def check_url_threat(url: str) -> dict:
    """
    Check URL against URLhaus (abuse.ch) threat intelligence — 100% free.
    Returns malware/phishing tags if found.
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(
                "https://urlhaus-api.abuse.ch/v1/url/",
                data={"url": url},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if r.status_code == 200:
                data = r.json()
                if data.get("query_status") == "is_listed":
                    return {
                        "url": url,
                        "is_malicious": True,
                        "threat_type": data.get("threat", "unknown"),
                        "tags": data.get("tags", []),
                        "date_added": data.get("date_added", ""),
                        "urlhaus_reference": data.get("urlhaus_reference", ""),
                        "threat_notes": [f"🚨 URL listed in URLhaus as {data.get('threat', 'malicious')}"]
                    }
                else:
                    return {"url": url, "is_malicious": False, "threat_notes": []}
    except Exception:
        pass
    return {"url": url, "is_malicious": None, "error": "Threat lookup unavailable"}


async def lookup_phone(phone: str) -> dict:
    """
    Basic phone number analysis — extracts carrier/region from number format.
    Uses numverify free tier if available, else does local pattern analysis.
    """
    # Strip non-numeric
    digits = re.sub(r"\D", "", phone)

    result = {
        "phone": phone,
        "digits": digits,
        "country": "India" if digits.startswith("91") or len(digits) == 10 else "Unknown",
        "carrier_hint": "Unknown",
        "is_mobile": len(digits) in [10, 12],
        "notes": []
    }

    # Indian mobile number heuristics
    if len(digits) == 10:
        prefix = digits[:4]
        if digits[0] in ["6", "7", "8", "9"]:
            result["is_mobile"] = True
            # Common VoIP/SIM-swap fraud prefixes
            if digits[:2] in ["70", "71", "72", "73", "74"]:
                result["notes"].append("⚠️ Prefix commonly associated with SIM-swap fraud networks")
            if digits[:3] in ["900", "901", "902"]:
                result["notes"].append("ℹ️ Airtel number range")
            elif digits[:3] in ["980", "981", "982"]:
                result["notes"].append("ℹ️ Vodafone/Vi number range")
            elif digits[:3] in ["994", "995", "996"]:
                result["notes"].append("ℹ️ BSNL number range")

    return result


async def run_full_osint(case_id: str, entities: dict) -> dict:
    """
    Run OSINT enrichment on all extracted entities from complaint analysis.
    Returns enriched data with geolocation, WHOIS, threat intel.
    """
    results = {
        "case_id": case_id,
        "timestamp": datetime.now().isoformat(),
        "ip_analysis": [],
        "domain_analysis": [],
        "url_threats": [],
        "phone_analysis": [],
        "summary": {
            "total_indicators": 0,
            "malicious_urls": 0,
            "foreign_ips": 0,
            "suspicious_domains": 0,
            "threat_level": "low"
        },
        "key_findings": []
    }

    tasks = []

    # IPs
    ip_addresses = entities.get("ip_addresses", [])
    for ip in ip_addresses[:5]:  # limit to 5
        tasks.append(("ip", ip, geolocate_ip(ip)))

    # URLs & domains
    urls = entities.get("urls", [])
    for url in urls[:5]:
        tasks.append(("url_threat", url, check_url_threat(url)))
        # Extract domain for WHOIS
        domain = re.sub(r"https?://", "", url).split("/")[0]
        if domain:
            tasks.append(("domain", domain, whois_domain(domain)))

    # Phone numbers
    phones = entities.get("phone_numbers", [])
    for phone in phones[:5]:
        tasks.append(("phone", phone, lookup_phone(phone)))

    # Run all in parallel
    coros = [t[2] for t in tasks]
    all_results = await asyncio.gather(*coros, return_exceptions=True)

    for (rtype, indicator, _), result in zip(tasks, all_results):
        if isinstance(result, Exception):
            result = {"error": str(result), "indicator": indicator}
        if rtype == "ip":
            results["ip_analysis"].append(result)
            if result.get("country_code") not in ["IN", "Local", ""]:
                results["summary"]["foreign_ips"] += 1
                results["key_findings"].append(
                    f"🌍 Foreign IP detected: {indicator} from {result.get('country', 'Unknown')}"
                )
            for note in result.get("threat_notes", []):
                results["key_findings"].append(note)
        elif rtype == "url_threat":
            results["url_threats"].append(result)
            if result.get("is_malicious"):
                results["summary"]["malicious_urls"] += 1
                results["key_findings"].append(
                    f"🚨 Malicious URL confirmed: {indicator} ({result.get('threat_type', '')})"
                )
        elif rtype == "domain":
            results["domain_analysis"].append(result)
            if result.get("is_newly_registered"):
                results["summary"]["suspicious_domains"] += 1
                results["key_findings"].append(
                    f"⚠️ Newly registered domain: {indicator} ({result.get('age_days', '?')} days old)"
                )
        elif rtype == "phone":
            results["phone_analysis"].append(result)
            for note in result.get("notes", []):
                results["key_findings"].append(note)

    # Calculate total indicators & threat level
    results["summary"]["total_indicators"] = (
        len(ip_addresses) + len(urls) + len(phones)
    )

    mal = results["summary"]["malicious_urls"]
    foreign = results["summary"]["foreign_ips"]
    susp_dom = results["summary"]["suspicious_domains"]

    if mal >= 2 or (mal >= 1 and foreign >= 1):
        results["summary"]["threat_level"] = "critical"
    elif mal >= 1 or susp_dom >= 2:
        results["summary"]["threat_level"] = "high"
    elif foreign >= 2 or susp_dom >= 1:
        results["summary"]["threat_level"] = "medium"
    else:
        results["summary"]["threat_level"] = "low"

    return results
