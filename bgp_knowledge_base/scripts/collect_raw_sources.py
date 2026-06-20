#!/usr/bin/env python3
import csv
import ssl
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "raw_collection_report.csv"

SOURCES = [
    ("rfc4271", "https://www.rfc-editor.org/rfc/rfc4271.txt", "raw/standards/rfc4271.txt"),
    ("rfc6480", "https://www.rfc-editor.org/rfc/rfc6480.txt", "raw/standards/rfc6480.txt"),
    ("rfc6811", "https://www.rfc-editor.org/rfc/rfc6811.txt", "raw/standards/rfc6811.txt"),
    ("rfc7908", "https://www.rfc-editor.org/rfc/rfc7908.txt", "raw/standards/rfc7908.txt"),
    ("rfc8205", "https://www.rfc-editor.org/rfc/rfc8205.txt", "raw/standards/rfc8205.txt"),
    ("rfc8210", "https://www.rfc-editor.org/rfc/rfc8210.txt", "raw/standards/rfc8210.txt"),
    ("rfc9234", "https://www.rfc-editor.org/rfc/rfc9234.txt", "raw/standards/rfc9234.txt"),
    ("rfc2622", "https://www.rfc-editor.org/rfc/rfc2622.txt", "raw/standards/rfc2622.txt"),
    ("rfc3912", "https://www.rfc-editor.org/rfc/rfc3912.txt", "raw/standards/rfc3912.txt"),
    ("rfc9082", "https://www.rfc-editor.org/rfc/rfc9082.txt", "raw/standards/rfc9082.txt"),
    ("rfc9083", "https://www.rfc-editor.org/rfc/rfc9083.txt", "raw/standards/rfc9083.txt"),
    ("routeviews_api_doc", "https://api.routeviews.org/docs", "raw/data_docs/routeviews_api_doc.html"),
    ("routeviews_archive_index", "https://archive.routeviews.org/", "raw/data_docs/routeviews_archive_index.html"),
    ("ripe_ris_docs", "https://ris.ripe.net/docs/", "raw/data_docs/ripe_ris_docs.html"),
    ("ripe_ris_route_collectors", "https://ris.ripe.net/docs/route-collectors/", "raw/data_docs/ripe_ris_route_collectors.html"),
    ("ripe_ris_raw_data", "https://ris.ripe.net/docs/mrt/", "raw/data_docs/ripe_ris_raw_data.html"),
    ("bgpstream_docs", "https://bgpstream.caida.org/docs", "raw/tools_docs/bgpstream_docs.html"),
    ("bgpstream_tutorials", "https://bgpstream.caida.org/docs/tutorials", "raw/tools_docs/bgpstream_tutorials.html"),
    ("caida_as_relationships", "https://www.caida.org/catalog/datasets/as-relationships/", "raw/data_docs/caida_as_relationships.html"),
    ("caida_asrank_api", "https://asrank.caida.org/doc", "raw/data_docs/caida_asrank_api.html"),
    ("ripestat_api_docs", "https://stat.ripe.net/docs/02.data-api", "raw/data_docs/ripestat_api_docs.html"),
    ("peeringdb_api_docs", "https://www.peeringdb.com/s/2.79.0/api-schema.yaml", "raw/data_docs/peeringdb_api_docs.yaml"),
    ("manrs_measurement_framework", "https://manrs.org/manrs-observatory/measurement-framework/", "raw/data_docs/manrs_measurement_framework.html"),
    ("manrs_observatory_faq", "https://manrs.org/manrs-observatory/observatory-faq/", "raw/data_docs/manrs_observatory_faq.html"),
    ("manrs_netops_actions", "https://www.manrs.org/wp-content/uploads/2021/02/MANRS-Network-Operators-Actions-v2.4.4.pdf", "raw/data_docs/manrs_netops_actions.pdf"),
    ("arin_aspa_doc", "https://www.arin.net/resources/manage/rpki/aspa/", "raw/data_docs/arin_aspa_doc.html"),
    ("ripe_aspa_doc", "https://www.ripe.net/manage-ips-and-asns/resource-management/rpki/aspa/", "raw/data_docs/ripe_aspa_doc.html"),
    ("bear_2025", "https://arxiv.org/pdf/2506.04514", "raw/papers/bear_2025.pdf"),
    ("beam_2024", "https://www.usenix.org/system/files/usenixsecurity24-chen-yihao.pdf", "raw/papers/beam_2024.pdf"),
    ("bgpshield_2025", "https://arxiv.org/pdf/2511.14467", "raw/papers/bgpshield_2025.pdf"),
    ("artemis_2018", "https://www-old.caida.org/publications/papers/2018/artemis/artemis.pdf", "raw/papers/artemis_2018.pdf"),
    ("bgp2vec_2020", "https://www.eng.tau.ac.il/~shavitt/pub/NetAI2020.pdf", "raw/papers/bgp2vec_2020.pdf"),
    ("ap2vec_2022", "https://talshapira.github.io/publication/ap2vec_tnsm", "raw/papers/ap2vec_2022.html"),
    ("aswatch_2015", "https://collaborate.princeton.edu/en/publications/aswatch-an-as-reputation-system-to-expose-bulletproof-hosting-ase", "raw/papers/aswatch_2015.html"),
    ("cair_2016", "https://arxiv.org/pdf/1605.00618", "raw/papers/cair_2016.pdf"),
    ("bursty_announcements_2019", "https://arxiv.org/pdf/1905.05835", "raw/papers/bursty_announcements_2019.pdf"),
    ("peerlock_2020", "https://arxiv.org/pdf/2006.06576", "raw/papers/peerlock_2020.pdf"),
    ("global_bgp_attacks_2024", "https://arxiv.org/pdf/2408.09622", "raw/papers/global_bgp_attacks_2024.pdf"),
    ("oscilloscope_2023", "https://arxiv.org/pdf/2301.12843", "raw/papers/oscilloscope_2023.pdf"),
    ("practical_defenses_2007", "https://docs.lib.purdue.edu/ecetr/364/", "raw/papers/practical_defenses_2007.html"),
    ("youtube_hijack_google_2008", "https://research.google/pubs/youtube-hijacking-february-24th-2008-analysis-of-bgp-routing-dynamics/", "raw/cases/youtube_hijack_google_2008.html"),
    ("facebook_outage_cloudflare_2021", "https://blog.cloudflare.com/october-2021-facebook-outage", "raw/cases/facebook_outage_cloudflare_2021.html"),
    ("facebook_outage_meta_2021", "https://engineering.fb.com/2021/10/04/networking-traffic/outage/", "raw/cases/facebook_outage_meta_2021.html"),
    ("indosat_route_leak_2014", "https://www.theregister.com/2014/04/03/indosat_fatthumbs_route_announcements_again/", "raw/cases/indosat_route_leak_2014.html"),
    ("cloudflare_verizon_route_leak_2019", "https://blog.cloudflare.com/how-verizon-and-a-bgp-optimizer-knocked-large-parts-of-the-internet-offline-today", "raw/cases/cloudflare_verizon_route_leak_2019.html"),
    ("mainone_google_cloudflare_route_leak_2018", "https://blog.cloudflare.com/how-a-nigerian-isp-knocked-google-offline/", "raw/cases/mainone_google_cloudflare_route_leak_2018.html"),
    ("aws_route53_crypto_hijack_2018", "https://blog.cloudflare.com/bgp-leaks-and-crypto-currencies/", "raw/cases/aws_route53_crypto_hijack_2018.html"),
    ("fastly_rpki_hijack_2024", "https://labs.ripe.net/author/job_snijders/war-story-rpki-is-working-as-intended/", "raw/cases/fastly_rpki_hijack_2024.html"),
    ("cloudflare_outage_2026", "https://blog.cloudflare.com/cloudflare-outage-february-20-2026/", "raw/cases/cloudflare_outage_2026.html"),
    ("manrs_bgp_2020_review", "https://manrs.org/2021/02/bgp-rpki-and-manrs-2020-in-review/", "raw/cases/manrs_bgp_2020_review.html"),
    ("manrs_regional_bgp_incidents_2020", "https://manrs.org/2021/03/a-regional-look-into-bgp-incidents-in-2020/", "raw/cases/manrs_regional_bgp_incidents_2020.html"),
    ("china_telecom_europe_route_leak_2019", "https://arstechnica.com/information-technology/2019/06/bgp-mishap-sends-european-mobile-traffic-through-china-telecom-for-2-hours/", "raw/cases/china_telecom_europe_route_leak_2019.html"),
    ("cert_eu_china_telecom_route_leak_2019", "https://www.cert.europa.eu/publications/threat-intelligence/threat-memo-190611-1/pdf", "raw/cases/cert_eu_china_telecom_route_leak_2019.pdf"),
]


def download(source_id, url, relative_path):
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 Codex raw source collector",
            "Accept": "*/*",
        },
    )
    context = ssl.create_default_context()
    try:
        with urlopen(request, timeout=45, context=context) as response:
            data = response.read()
            status = getattr(response, "status", 200)
            content_type = response.headers.get("Content-Type", "")
    except HTTPError as exc:
        return {
            "source_id": source_id,
            "path": relative_path,
            "url": url,
            "status": "failed",
            "http_status": exc.code,
            "bytes": 0,
            "content_type": "",
            "error": str(exc),
        }
    except URLError as exc:
        return {
            "source_id": source_id,
            "path": relative_path,
            "url": url,
            "status": "failed",
            "http_status": "",
            "bytes": 0,
            "content_type": "",
            "error": str(exc.reason),
        }
    except Exception as exc:
        return {
            "source_id": source_id,
            "path": relative_path,
            "url": url,
            "status": "failed",
            "http_status": "",
            "bytes": 0,
            "content_type": "",
            "error": str(exc),
        }

    path.write_bytes(data)
    return {
        "source_id": source_id,
        "path": relative_path,
        "url": url,
        "status": "downloaded",
        "http_status": status,
        "bytes": len(data),
        "content_type": content_type,
        "error": "",
    }


def main():
    rows = []
    for index, (source_id, url, path) in enumerate(SOURCES, start=1):
        result = download(source_id, url, path)
        rows.append(result)
        print(f"{index:02d}/{len(SOURCES)} {source_id}: {result['status']} {result['bytes']} bytes")
        time.sleep(0.2)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source_id", "path", "url", "status", "http_status", "bytes", "content_type", "error"])
        writer.writeheader()
        writer.writerows(rows)

    failed = [row for row in rows if row["status"] != "downloaded"]
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Downloaded: {len(rows) - len(failed)}; failed: {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
