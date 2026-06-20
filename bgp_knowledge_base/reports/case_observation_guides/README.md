# 案例观察值人工核验指南

## 范围

本目录从 `datasets/case_observations.jsonl` 机械生成，用于人工逐案例核验正则抽取出的 ASN、前缀、日期和时间等观察值。生成过程不使用 LLM、不做语义判断、不下载资料、不写入 `entities/cases.jsonl`。

## 核验规则

- 先打开对应 `source_ref`，再用观察值和原文上下文定位证据。
- 只确认观察值是否真实出现在该案例来源中。
- 不在本步骤判断攻击者、受害者、泄露方、影响范围、证据强度或事件因果关系。
- 若这些判断必须依赖语义理解，继续按用户要求跳过并保留记录。

## 摘要

- 案例来源数：13
- 观察值总数：148
- asn：49
- bgp4mp_timestamp：2
- day_month_date：3
- ipv4_prefix：20
- iso_date：7
- month_date：44
- utc_time：23

## 案例入口

- `reports/case_observation_guides/aws_route53_crypto_hijack_2018.md`：aws_route53_crypto_hijack_2018，30 条，BGP leaks and cryptocurrencies
- `reports/case_observation_guides/cert_eu_china_telecom_route_leak_2019.md`：cert_eu_china_telecom_route_leak_2019，14 条，High volume of European mobile traffic rerouted through China Telecom
- `reports/case_observation_guides/china_telecom_europe_route_leak_2019.md`：china_telecom_europe_route_leak_2019，9 条，BGP event sends European mobile traffic through China Telecom for 2 hours
- `reports/case_observation_guides/cloudflare_outage_2026.md`：cloudflare_outage_2026，14 条，Cloudflare outage on February 20 2026
- `reports/case_observation_guides/cloudflare_verizon_route_leak_2019.md`：cloudflare_verizon_route_leak_2019，12 条，How Verizon and a BGP Optimizer Knocked Large Parts of the Internet Offline Today
- `reports/case_observation_guides/facebook_outage_cloudflare_2021.md`：facebook_outage_cloudflare_2021，26 条，Understanding How Facebook Disappeared from the Internet
- `reports/case_observation_guides/facebook_outage_meta_2021.md`：facebook_outage_meta_2021，3 条，More Details About the October 4 Outage
- `reports/case_observation_guides/fastly_rpki_hijack_2024.md`：fastly_rpki_hijack_2024，0 条，War Story: RPKI is Working as Intended
- `reports/case_observation_guides/indosat_route_leak_2014.md`：indosat_route_leak_2014，5 条，Indosat fat-thumbs route announcements again
- `reports/case_observation_guides/mainone_google_cloudflare_route_leak_2018.md`：mainone_google_cloudflare_route_leak_2018，15 条，How a Nigerian ISP Accidentally Knocked Google Offline
- `reports/case_observation_guides/manrs_bgp_2020_review.md`：manrs_bgp_2020_review，4 条，BGP, RPKI, and MANRS: 2020 in review
- `reports/case_observation_guides/manrs_regional_bgp_incidents_2020.md`：manrs_regional_bgp_incidents_2020，11 条，A Regional Look into BGP Incidents in 2020
- `reports/case_observation_guides/youtube_hijack_google_2008.md`：youtube_hijack_google_2008，5 条，YouTube Hijacking Analysis of BGP Routing Dynamics

## 已按规则跳过的语义事项

- `action_skipped_case_semantic_review`：案例观察值语义核验；原因：事件角色、证据强度和影响范围判断需要语义流程或 LLM 介入，按用户要求跳过。
