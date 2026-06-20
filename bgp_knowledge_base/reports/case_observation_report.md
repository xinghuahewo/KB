# 案例观察值抽取报告

## 范围

本报告只记录从已清洗案例文本中用正则规则直接抽取到的观察值，不进行语义判断，不推断 AS 角色，不判断攻击者/受害者，不写入结构化 Case 实体。

## 摘要

- 案例来源数：13
- 已处理 cleaned 案例数：13
- 缺失 cleaned 案例数：0
- 观察值总数：148
- JSONL 输出：`datasets/case_observations.jsonl`
- CSV 输出：`datasets/case_observations.csv`

## 按观察类型统计

- asn：49
- bgp4mp_timestamp：2
- day_month_date：3
- ipv4_prefix：20
- iso_date：7
- month_date：44
- utc_time：23

## 按案例统计

- aws_route53_crypto_hijack_2018：asn=6，bgp4mp_timestamp=2，ipv4_prefix=13，iso_date=1，month_date=5，utc_time=3
- cert_eu_china_telecom_route_leak_2019：asn=6，month_date=6，utc_time=2
- china_telecom_europe_route_leak_2019：asn=8，month_date=1
- cloudflare_outage_2026：iso_date=3，month_date=6，utc_time=5
- cloudflare_verizon_route_leak_2019：asn=3，ipv4_prefix=3，iso_date=1，month_date=4，utc_time=1
- facebook_outage_cloudflare_2021：asn=7，ipv4_prefix=3，iso_date=1，month_date=5，utc_time=10
- facebook_outage_meta_2021：month_date=3
- indosat_route_leak_2014：asn=2，month_date=2，utc_time=1
- mainone_google_cloudflare_route_leak_2018：asn=6，day_month_date=1，iso_date=1，month_date=6，utc_time=1
- manrs_bgp_2020_review：asn=4
- manrs_regional_bgp_incidents_2020：asn=5，day_month_date=1，month_date=5
- youtube_hijack_google_2008：asn=2，day_month_date=1，ipv4_prefix=1，month_date=1

## 跳过边界

- 未抽取事件责任方、受害方、泄露方、攻击方等角色，因为这需要语义判断。
- 未抽取证据强度和影响范围，因为这需要结合上下文解释。
- 未自动更新 `entities/cases.jsonl`，观察值仍需人工核验后才能进入结构化实体。
