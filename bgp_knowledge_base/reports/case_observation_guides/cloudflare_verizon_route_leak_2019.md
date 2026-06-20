# cloudflare_verizon_route_leak_2019 案例观察值核验

## 来源

- 标题：How Verizon and a BGP Optimizer Knocked Large Parts of the Internet Offline Today
- 来源文本：`cleaned/cases/cloudflare_verizon_route_leak_2019.md`
- 观察值数量：12

## 类型统计

- asn：3
- ipv4_prefix：3
- iso_date：1
- month_date：4
- utc_time：1

## 核验边界

- 本文件只列出正则直接抽取的观察值和原文上下文。
- 事件角色、证据强度、影响范围和因果解释需要语义判断，本步骤跳过。

## 观察值清单

### 1. asn：`AS33154`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_verizon_route_leak_2019.md`
- 原文上下文：

> pointing your GPS to a state. This is where things went wrong today. An Internet Service Provider in Pennsylvania ( AS33154 - DQE Communications) was using a BGP optimizer in their network, which meant there were a lot of more specific routes

### 2. asn：`AS396531`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_verizon_route_leak_2019.md`
- 原文上下文：

> , Buckingham Palace is more specific than a route to London). DQE announced these specific routes to their customer ( AS396531 - Allegheny Technologies Inc). All of this routing information was then sent to their other transit provider ( AS701 -

### 3. asn：`AS701`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_verizon_route_leak_2019.md`
- 原文上下文：

> heart attack. A small company in Northern Pennsylvania became a preferred path of many Internet routes through Verizon (AS701), a major Internet transit provider. This was the equivalent of Waze routing an entire freeway down a neighborhood stre

### 4. ipv4_prefix：`104.20.0.0/20`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_verizon_route_leak_2019.md`
- 原文上下文：

> plits up received IP prefixes into smaller, contributing parts (called more-specifics). For example, our own IPv4 route 104.20.0.0/20 was turned into 104.20.0.0/21 and 104.20.8.0/21. It’s as if the road sign directing traffic to “Pennsylvania” was repla

### 5. ipv4_prefix：`104.20.0.0/21`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_verizon_route_leak_2019.md`
- 原文上下文：

> into smaller, contributing parts (called more-specifics). For example, our own IPv4 route 104.20.0.0/20 was turned into 104.20.0.0/21 and 104.20.8.0/21. It’s as if the road sign directing traffic to “Pennsylvania” was replaced by two road signs, one for

### 6. ipv4_prefix：`104.20.8.0/21`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_verizon_route_leak_2019.md`
- 原文上下文：

> ributing parts (called more-specifics). For example, our own IPv4 route 104.20.0.0/20 was turned into 104.20.0.0/21 and 104.20.8.0/21. It’s as if the road sign directing traffic to “Pennsylvania” was replaced by two road signs, one for “Pittsburgh, PA”

### 7. iso_date：`2019-06-24`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_verizon_route_leak_2019.md`
- 原文上下文：

> y Life at Cloudflare Partners How Verizon and a BGP Optimizer Knocked Large Parts of the Internet Offline Today 2019-06-24 Tom Strickx 5 min read This post is also available in 简体中文 , Deutsch , 日本語 and Français . Massive route leak im

### 8. month_date：`April 10, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_verizon_route_leak_2019.md`
- 原文上下文：

> d Belson Radar , Internet Shutdown , Internet Traffic , Outage , Internet Trends , AWS , BGP , IPv6 April 10, 2026 500 Tbps of capacity: 16 years of scaling our global network Cloudflare’s global network has officially crossed 500

### 9. month_date：`April 28, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_verizon_route_leak_2019.md`
- 原文上下文：

> y Bryton Herdes , Bryce Walters , Mingwei Zhang BGP , Routing , Routing Security , RPKI , Radar April 28, 2026 Shutdowns, power outages, and conflict: a review of Q1 2026 Internet disruptions The first quarter of 2026 saw a su

### 10. month_date：`February 27, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_verizon_route_leak_2019.md`
- 原文上下文：

> Services , Cloudflare Network , Peering , DDoS , BGP , RPKI , Workers AI , Cloudflare Workers , AI February 27, 2026 ASPA: making Internet routing more secure ASPA is the cryptographic upgrade for BGP that helps prevent route leaks

### 11. month_date：`June 03, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_verizon_route_leak_2019.md`
- 原文上下文：

> this problem was identified. BGP Follow on X Tom Strickx | @tstrickx Cloudflare | @cloudflare Related posts June 03, 2026 Enforcing the First AS in BGP AS_PATHs BGP is vulnerable to routing hijacks and path leaks that negatively impact t

### 12. utc_time：`10:30UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_verizon_route_leak_2019.md`
- 原文上下文：

> d Français . Massive route leak impacts major parts of the Internet, including Cloudflare What happened? Today at 10:30UTC, the Internet had a small heart attack. A small company in Northern Pennsylvania became a preferred path of many Intern

