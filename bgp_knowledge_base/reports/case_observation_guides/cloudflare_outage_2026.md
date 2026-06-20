# cloudflare_outage_2026 案例观察值核验

## 来源

- 标题：Cloudflare outage on February 20 2026
- 来源文本：`cleaned/cases/cloudflare_outage_2026.md`
- 观察值数量：14

## 类型统计

- iso_date：3
- month_date：6
- utc_time：5

## 核验边界

- 本文件只列出正则直接抽取的观察值和原文上下文。
- 事件角色、证据强度、影响范围和因果解释需要语义判断，本步骤跳过。

## 观察值清单

### 1. iso_date：`2026-02-05`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_outage_2026.md`
- 原文上下文：

> e timeline of events inclusive of deployment of the change and remediation steps: Time (UT C ) Status Description 2026-02-05 21:53 Code merged into system Broken sub-process merged into code base 2026-02-20 17:46 Code deployed into system

### 2. iso_date：`2026-02-20`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_outage_2026.md`
- 原文上下文：

> me (UT C ) Status Description 2026-02-05 21:53 Code merged into system Broken sub-process merged into code base 2026-02-20 17:46 Code deployed into system Address API release with broken sub-process completes 2026-02-20 17:56 Impact Star

### 3. iso_date：`2026-02-21`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_outage_2026.md`
- 原文上下文：

> y & Legal Zero Trust Speed & Reliability Life at Cloudflare Partners Cloudflare outage on February 20, 2026 2026-02-21 David Tuber Dzevad Trumic 9 min read This post is also available in 简体中文 , 日本語 , 한국어 and 繁體中文 . On February 2

### 4. month_date：`April 28, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_outage_2026.md`
- 原文上下文：

> ted best practices to prevent future incidents. ... By Jeremy Hartman Outage , Post Mortem , Code Orange April 28, 2026 Shutdowns, power outages, and conflict: a review of Q1 2026 Internet disruptions The first quarter of 2026 saw a su

### 5. month_date：`February 20, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_outage_2026.md`
- 原文上下文：

> # Cloudflare outage on February 20, 2026 Cloudflare outage on February 20, 2026 Get Started Free | Contact Sales | ▼ The Cloudflare Blog Subscribe to r

### 6. month_date：`May 01, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_outage_2026.md`
- 原文上下文：

> ebastiaan Neuteboom , Christian Elmerot , Max Worsley DNS , DNSSEC , 1.1.1.1 , Reliability , Outage May 01, 2026 Code Orange: Fail Small is complete. The result is a stronger Cloudflare network We have completed a massive engine

### 7. month_date：`May 06, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_outage_2026.md`
- 原文上下文：

> n , Rian Islam Linux , Security , Incident Response , Kernel , Vulnerabilities , Mitigation , eBPF May 06, 2026 When DNSSEC goes wrong: how we responded to the .de TLD outage On May 5, 2026, DENIC published broken DNSSEC signat

### 8. month_date：`May 07, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_outage_2026.md`
- 原文上下文：

> ost Mortem Incident Response Outage Follow on X David Tuber | @tubes__ Cloudflare | @cloudflare Related posts May 07, 2026 How Cloudflare responded to the “Copy Fail” Linux vulnerability When a critical Linux kernel privilege escalation w

### 9. month_date：`May 5, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_outage_2026.md`
- 原文上下文：

> bilities , Mitigation , eBPF May 06, 2026 When DNSSEC goes wrong: how we responded to the .de TLD outage On May 5, 2026, DENIC published broken DNSSEC signatures for the .de TLD, making millions of domains unreachable. Here's what 1.1.1.1

### 10. utc_time：`17:48 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_outage_2026.md`
- 原文上下文：

> er Dzevad Trumic 9 min read This post is also available in 简体中文 , 日本語 , 한국어 and 繁體中文 . On February 20, 2026, at 17:48 UTC, Cloudflare experienced a service outage when a subset of customers who use Cloudflare’s Bring Your Own IP (BYOIP) serv

### 11. utc_time：`18:46 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_outage_2026.md`
- 原文上下文：

> fixes we advertise globally. During the incident, 1,100 prefixes out of the total 6,500 were withdrawn from 17:56 to 18:46 UTC. Out of the 4,306 total BYOIP prefixes, 25% of BYOIP prefixes were unintentionally withdrawn. We were able to detect im

### 12. utc_time：`19:19 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_outage_2026.md`
- 原文上下文：

> We were able to detect impact on one.one.one.one and revert the impacting change before more prefixes were impacted. At 19:19 UTC, we published guidance to customers that they would be able to self-remediate this incident by going to the Cloudflare

### 13. utc_time：`20:20 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_outage_2026.md`
- 原文上下文：

> e dashboard and re-advertising their prefixes. Cloudflare was able to revert many of the advertisement changes around 20:20 UTC, which caused 800 prefixes to be restored. There were still ~300 prefixes that were unable to be remediated through the

### 14. utc_time：`23:03 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/cloudflare_outage_2026.md`
- 原文上下文：

> ixes were removed from the edge due to a software bug. These prefixes were manually restored by Cloudflare engineers at 23:03 UTC. This incident did not impact all BYOIP customers because the configuration change was applied iteratively and not i

