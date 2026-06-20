# 解析报告

## 范围

本轮解析低风险原始格式：RFC TXT、HTML 文档、YAML/OpenAPI schema、HTML 论文页面、HTML 案例报告，以及可由 `pypdf` 确定性抽取文本的 PDF 文件。

## 摘要

- 扫描目标数：53
- 已解析：53
- 已跳过：0

## 已解析文件

- raw/standards/rfc2622.txt：38 个章节，120272 个字符
- raw/standards/rfc3912.txt：8 个章节，6944 个字符
- raw/standards/rfc4271.txt：83 个章节，186132 个字符
- raw/standards/rfc6480.txt：41 个章节，55549 个字符
- raw/standards/rfc6811.txt：15 个章节，17555 个字符
- raw/standards/rfc7908.txt：17 个章节，21332 个字符
- raw/standards/rfc8205.txt：54 个章节，101911 个字符
- raw/standards/rfc8210.txt：42 个章节，64842 个字符
- raw/standards/rfc9082.txt：29 个章节，40952 个字符
- raw/standards/rfc9083.txt：55 个章节，97089 个字符
- raw/standards/rfc9234.txt：26 个章节，25545 个字符
- raw/data_docs/arin_aspa_doc.html：1 个章节，7678 个字符
- raw/data_docs/caida_as_relationships.html：1 个章节，23316 个字符
- raw/data_docs/caida_asrank_api.html：1 个章节，11419 个字符
- raw/data_docs/manrs_measurement_framework.html：1 个章节，14780 个字符
- raw/data_docs/manrs_netops_actions.pdf：9 个章节，20954 个字符
- raw/data_docs/manrs_observatory_faq.html：1 个章节，5376 个字符
- raw/data_docs/peeringdb_api_docs.yaml：3 个章节，2484741 个字符
- raw/data_docs/ripe_aspa_doc.html：1 个章节，18613 个字符
- raw/data_docs/ripe_ris_docs.html：1 个章节，967 个字符
- raw/data_docs/ripe_ris_raw_data.html：1 个章节，2605 个字符
- raw/data_docs/ripe_ris_route_collectors.html：1 个章节，4823 个字符
- raw/data_docs/ripestat_api_docs.html：1 个章节，9350 个字符
- raw/data_docs/routeviews_api_doc.html：1 个章节，40629 个字符
- raw/data_docs/routeviews_archive_index.html：1 个章节，8135 个字符
- raw/tools_docs/bgpstream_docs.html：1 个章节，1576 个字符
- raw/tools_docs/bgpstream_tutorials.html：1 个章节，1627 个字符
- raw/papers/ap2vec_2022.html：1 个章节，2124 个字符
- raw/papers/artemis_2018.pdf：16 个章节，100224 个字符
- raw/papers/aswatch_2015.html：1 个章节，13558 个字符
- raw/papers/beam_2024.pdf：19 个章节，91833 个字符
- raw/papers/bear_2025.pdf：10 个章节，51627 个字符
- raw/papers/bgp2vec_2020.pdf：7 个章节，33050 个字符
- raw/papers/bgpshield_2025.pdf：18 个章节，89228 个字符
- raw/papers/bursty_announcements_2019.pdf：16 个章节，88576 个字符
- raw/papers/cair_2016.pdf：14 个章节，69432 个字符
- raw/papers/global_bgp_attacks_2024.pdf：10 个章节，49250 个字符
- raw/papers/oscilloscope_2023.pdf：20 个章节，99930 个字符
- raw/papers/peerlock_2020.pdf：16 个章节，75312 个字符
- raw/papers/practical_defenses_2007.html：1 个章节，2427 个字符
- raw/cases/aws_route53_crypto_hijack_2018.html：1 个章节，11912 个字符
- raw/cases/cert_eu_china_telecom_route_leak_2019.pdf：1 个章节，5527 个字符
- raw/cases/china_telecom_europe_route_leak_2019.html：1 个章节，11248 个字符
- raw/cases/cloudflare_outage_2026.html：1 个章节，21658 个字符
- raw/cases/cloudflare_verizon_route_leak_2019.html：1 个章节，11339 个字符
- raw/cases/facebook_outage_cloudflare_2021.html：1 个章节，12984 个字符
- raw/cases/facebook_outage_meta_2021.html：1 个章节，5266 个字符
- raw/cases/fastly_rpki_hijack_2024.html：1 个章节，12486 个字符
- raw/cases/indosat_route_leak_2014.html：1 个章节，9294 个字符
- raw/cases/mainone_google_cloudflare_route_leak_2018.html：1 个章节，9694 个字符
- raw/cases/manrs_bgp_2020_review.html：1 个章节，13881 个字符
- raw/cases/manrs_regional_bgp_incidents_2020.html：1 个章节，9306 个字符
- raw/cases/youtube_hijack_google_2008.html：1 个章节，4944 个字符

## 已跳过文件

- 无

## 说明

- HTML 论文页和案例页已经作为来源文本解析，但对应记录在人审前仍保持 `pending`。
- YAML/OpenAPI schema 只按顶层键做机械分段，不做 API 语义归纳。
- PDF 解析只做文本抽取和按页切分，不做论文方法、案例角色、证据强度或影响范围等语义判断。
- `reports/source_snapshots/peeringdb_api_docs_redoc_shell.html` 保留了 PeeringDB ReDoc 外壳快照；当前主来源使用其指向的 OpenAPI YAML。
