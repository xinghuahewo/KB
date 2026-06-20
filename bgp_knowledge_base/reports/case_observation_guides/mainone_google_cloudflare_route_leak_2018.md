# mainone_google_cloudflare_route_leak_2018 案例观察值核验

## 来源

- 标题：How a Nigerian ISP Accidentally Knocked Google Offline
- 来源文本：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 观察值数量：15

## 类型统计

- asn：6
- day_month_date：1
- iso_date：1
- month_date：6
- utc_time：1

## 核验边界

- 本文件只列出正则直接抽取的观察值和原文上下文。
- 事件角色、证据强度、影响范围和因果解释需要语义判断，本步骤跳过。

## 观察值清单

### 1. asn：`AS15169`

- review_status：`pending`
- source_ref：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 原文上下文：

> 's corner of the Internet and where Google traffic should end up... by the fastest path. A Typical view of how Google/AS15169’s routes are propagated to Tier-1 Networks. As seen above, Google is directly connected to most of the Tier-1 network

### 2. asn：`AS174`

- review_status：`pending`
- source_ref：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 原文上下文：

> e, the AS Path that you would see is “174 6453 15169”. That string of numbers is like a sequence of waypoints: start on AS 174 (Cogent), go to Tata (AS 6453), then go to Google (AS 15169). So, Cogent subscribers reach Google via Tata, a huge Tier

### 3. asn：`AS20485`

- review_status：`pending`
- source_ref：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 原文上下文：

> e gone via Tata (AS 6453) as they should have. Instead, they were routed first through TransTelecom (a Russian Carrier, AS 20485), then to China Telecom CN2 (a cross border Chinese carrier, AS 4809), then on to MainOne (the Nigerian ISP that miscon

### 4. asn：`AS37282`

- review_status：`pending`
- source_ref：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 原文上下文：

> ecom CN2 (a cross border Chinese carrier, AS 4809), then on to MainOne (the Nigerian ISP that misconfigured everything, AS 37282), and only then were they finally handed off to Google (AS 15169). In other words, a user in London could have had the

### 5. asn：`AS4809`

- review_status：`pending`
- source_ref：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 原文上下文：

> ed first through TransTelecom (a Russian Carrier, AS 20485), then to China Telecom CN2 (a cross border Chinese carrier, AS 4809), then on to MainOne (the Nigerian ISP that misconfigured everything, AS 37282), and only then were they finally handed

### 6. asn：`AS6453`

- review_status：`pending`
- source_ref：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 原文上下文：

> see is “174 6453 15169”. That string of numbers is like a sequence of waypoints: start on AS 174 (Cogent), go to Tata (AS 6453), then go to Google (AS 15169). So, Cogent subscribers reach Google via Tata, a huge Tier-1 provider. During the inci

### 7. day_month_date：`12 November 2018`

- review_status：`pending`
- source_ref：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 原文上下文：

> How a Nigerian ISP Accidentally Knocked Google Offline 2018-11-15 Tom Paseka 4 min read Last Monday evening — 12 November 2018 — Google and a number of other services experienced a 74 minute outage. It’s not the first time this has happened ; and

### 8. iso_date：`2018-11-15`

- review_status：`pending`
- source_ref：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 原文上下文：

> Trust Speed & Reliability Life at Cloudflare Partners How a Nigerian ISP Accidentally Knocked Google Offline 2018-11-15 Tom Paseka 4 min read Last Monday evening — 12 November 2018 — Google and a number of other services experienced

### 9. month_date：`June 03, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 原文上下文：

> t best practices like BCP-38 . BGP Security Peering Outage Follow on X Cloudflare | @cloudflare Related posts June 03, 2026 Enforcing the First AS in BGP AS_PATHs BGP is vulnerable to routing hijacks and path leaks that negatively impact t

### 10. month_date：`May 06, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 原文上下文：

> n , Rian Islam Linux , Security , Incident Response , Kernel , Vulnerabilities , Mitigation , eBPF May 06, 2026 When DNSSEC goes wrong: how we responded to the .de TLD outage On May 5, 2026, DENIC published broken DNSSEC signat

### 11. month_date：`May 07, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 原文上下文：

> , Agents , Threat Intelligence , LLM , Risk Management , Threat Operations , Automation , Engineering May 07, 2026 How Cloudflare responded to the “Copy Fail” Linux vulnerability When a critical Linux kernel privilege escalation w

### 12. month_date：`May 18, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 原文上下文：

> y Bryton Herdes , Bryce Walters , Mingwei Zhang BGP , Routing , Routing Security , RPKI , Radar May 18, 2026 Project Glasswing: what Mythos showed us In recent weeks, we pointed Mythos and other security-focused LLMs at live

### 13. month_date：`May 5, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 原文上下文：

> bilities , Mitigation , eBPF May 06, 2026 When DNSSEC goes wrong: how we responded to the .de TLD outage On May 5, 2026, DENIC published broken DNSSEC signatures for the .de TLD, making millions of domains unreachable. Here's what 1.1.1.1

### 14. month_date：`November 13, 2018`

- review_status：`pending`
- source_ref：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 原文上下文：

> action. Thankfully our systems detected it and mitigated it! pic.twitter.com/qFiDkrn2Kd — Jerome Fleury (@Jerome_UZ) November 13, 2018 Some more information about Cloudflare’s Auto Remediation system: https://blog.cloudflare.com/the-internet-is-hostile

### 15. utc_time：`21:12 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/mainone_google_cloudflare_route_leak_2018.md`
- 原文上下文：

> just how much frailty is involved in how packets get from one point on the Internet to another. Our logs show that at 21:12 UTC on Monday, a Nigerian ISP, MainOne, accidentally misconfigured part of their network causing a "route leak". This resul

