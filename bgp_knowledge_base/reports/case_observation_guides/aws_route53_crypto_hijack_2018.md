# aws_route53_crypto_hijack_2018 案例观察值核验

## 来源

- 标题：BGP leaks and cryptocurrencies
- 来源文本：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 观察值数量：30

## 类型统计

- asn：6
- bgp4mp_timestamp：2
- ipv4_prefix：13
- iso_date：1
- month_date：5
- utc_time：3

## 核验边界

- 本文件只列出正则直接抽取的观察值和原文上下文。
- 事件角色、证据强度、影响范围和因果解释需要语义判断，本步骤跳过。

## 观察值清单

### 1. asn：`AS10279`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> al Ethereum. Summary in pictures Normal case After a BGP route leak Affected regions As previously mentioned, AS10279 announced this route. But only some regions got affected. Hurricane Electric has a strong presence Australia , mostly d

### 2. asn：`AS10297`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> 6.0/23 205.251.198.0/23 This IP space is allocated to Amazon (AS16509). But the ASN that announced it was eNet Inc (AS10297) to their peers and forwarded to Hurricane Electric (AS6939). Those IPs are for Route53 Amazon DNS servers . When you

### 3. asn：`AS16509`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> es: 205.251.192.0/23 205.251.194.0/23 205.251.196.0/23 205.251.198.0/23 This IP space is allocated to Amazon (AS16509). But the ASN that announced it was eNet Inc (AS10297) to their peers and forwarded to Hurricane Electric (AS6939). T

### 4. asn：`AS41995`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> @205.251.195.239 54.192.146.xx But during the hijack, it returned IPs associated with a Russian provider (AS48693 and AS41995). You did not need to accept the hijacked route to be victim of the attack, just use a DNS resolver that had been poiso

### 5. asn：`AS48693`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> rwallet.com @205.251.195.239 54.192.146.xx But during the hijack, it returned IPs associated with a Russian provider (AS48693 and AS41995). You did not need to accept the hijacked route to be victim of the attack, just use a DNS resolver that ha

### 6. asn：`AS6939`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> zon (AS16509). But the ASN that announced it was eNet Inc (AS10297) to their peers and forwarded to Hurricane Electric (AS6939). Those IPs are for Route53 Amazon DNS servers . When you query for one of their client zones, those servers will rep

### 7. bgp4mp_timestamp：`BGP4MP|04/24/18 11:05:42`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> rs around the planet. Between approximately 11:05:00 UTC and 12:55:00 UTC today we saw the following announcements: BGP4MP|04/24/18 11:05:42|A|205.251.199.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.197.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.195.0/24|

### 8. bgp4mp_timestamp：`BGP4MP|04/24/18 11:05:54`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> .195.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.193.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.192.0/24|10297 ... BGP4MP|04/24/18 11:05:54|A|205.251.197.0/24|4826,6939,10297 Those are more specifics announcements of the ranges: 205.251.192.0/23 205.251

### 9. ipv4_prefix：`1.1.1.0/24`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> ounced by somebody not allowed by the owner of the space. When a transit provider picks up Cloudflare's announcement of 1.1.1.0/24 and announces it to the Internet, we allow them to do so. They are also verifying using the RIR information that only C

### 10. ipv4_prefix：`10.0.0.0/24`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> In order to be accepted over a legitimate route, the route has to be either: A smaller prefix ( 10.0.0.1/32 = 1 IP vs 10.0.0.0/24 = 256 IPs) Have better metrics than a prefix with the same length (shorter path) The cause of a BGP leak is usually

### 11. ipv4_prefix：`10.0.0.1/32`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> ing a leaked route is.In order to be accepted over a legitimate route, the route has to be either: A smaller prefix ( 10.0.0.1/32 = 1 IP vs 10.0.0.0/24 = 256 IPs) Have better metrics than a prefix with the same length (shorter path) The cause of

### 12. ipv4_prefix：`205.251.192.0/21`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> erms can be added to the RIR databases, so a list of allowed sources can be generated: $ whois -h whois.radb.net ' -M 205.251.192.0/21' | egrep '^route:|^origin:|source:' | paste - - - | sort route: 205.251.192.0/23 origin: AS16509 source: RADB route: 20

### 13. ipv4_prefix：`205.251.192.0/23`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> . BGP4MP|04/24/18 11:05:54|A|205.251.197.0/24|4826,6939,10297 Those are more specifics announcements of the ranges: 205.251.192.0/23 205.251.194.0/23 205.251.196.0/23 205.251.198.0/23 This IP space is allocated to Amazon (AS16509). But the ASN

### 14. ipv4_prefix：`205.251.192.0/24`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> 04/24/18 11:05:42|A|205.251.195.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.193.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.192.0/24|10297 ... BGP4MP|04/24/18 11:05:54|A|205.251.197.0/24|4826,6939,10297 Those are more specifics announcements of the r

### 15. ipv4_prefix：`205.251.193.0/24`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> 04/24/18 11:05:42|A|205.251.197.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.195.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.193.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.192.0/24|10297 ... BGP4MP|04/24/18 11:05:54|A|205.251.197.0/24|4826,6939,10297

### 16. ipv4_prefix：`205.251.194.0/23`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> 1:05:54|A|205.251.197.0/24|4826,6939,10297 Those are more specifics announcements of the ranges: 205.251.192.0/23 205.251.194.0/23 205.251.196.0/23 205.251.198.0/23 This IP space is allocated to Amazon (AS16509). But the ASN that announced it w

### 17. ipv4_prefix：`205.251.195.0/24`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> 04/24/18 11:05:42|A|205.251.199.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.197.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.195.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.193.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.192.0/24|10297 ... BGP4MP|04

### 18. ipv4_prefix：`205.251.196.0/23`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> 97.0/24|4826,6939,10297 Those are more specifics announcements of the ranges: 205.251.192.0/23 205.251.194.0/23 205.251.196.0/23 205.251.198.0/23 This IP space is allocated to Amazon (AS16509). But the ASN that announced it was eNet Inc (AS1029

### 19. ipv4_prefix：`205.251.197.0/24`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> oday we saw the following announcements: BGP4MP|04/24/18 11:05:42|A|205.251.199.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.197.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.195.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.193.0/24|10297 BGP4MP|04/24/

### 20. ipv4_prefix：`205.251.198.0/23`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> 0297 Those are more specifics announcements of the ranges: 205.251.192.0/23 205.251.194.0/23 205.251.196.0/23 205.251.198.0/23 This IP space is allocated to Amazon (AS16509). But the ASN that announced it was eNet Inc (AS10297) to their peers a

### 21. ipv4_prefix：`205.251.199.0/24`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> ween approximately 11:05:00 UTC and 12:55:00 UTC today we saw the following announcements: BGP4MP|04/24/18 11:05:42|A|205.251.199.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.197.0/24|10297 BGP4MP|04/24/18 11:05:42|A|205.251.195.0/24|10297 BGP4MP|04/24/

### 22. iso_date：`2018-04-24`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> Policy & Legal Zero Trust Speed & Reliability Life at Cloudflare Partners BGP leaks and cryptocurrencies 2018-04-24 Louis Poinsignon 5 min read This post is also available in 简体中文 , Deutsch , Español and Français . Over the few

### 23. month_date：`April 24, 2018`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> .251.192.0/24205.251.193.0/24205.251.195.0/24205.251.197.0/24205.251.199.0/24 — InternetIntelligence (@InternetIntel) April 24, 2018 Correction: the BGP hijack this morning was against AWS DNS not Google DNS. https://t.co/gp3VLbImpX — InternetIntel

### 24. month_date：`April 30, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> n , Rian Islam Linux , Security , Incident Response , Kernel , Vulnerabilities , Mitigation , eBPF April 30, 2026 Post-quantum encryption for Cloudflare IPsec is generally available Cloudflare IPsec now has generally available su

### 25. month_date：`June 03, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> Vulnerabilities Cryptography Follow on X Louis Poinsignon | @lpoinsig Cloudflare | @cloudflare Related posts June 03, 2026 Enforcing the First AS in BGP AS_PATHs BGP is vulnerable to routing hijacks and path leaks that negatively impact t

### 26. month_date：`May 07, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> , Agents , Threat Intelligence , LLM , Risk Management , Threat Operations , Automation , Engineering May 07, 2026 How Cloudflare responded to the “Copy Fail” Linux vulnerability When a critical Linux kernel privilege escalation w

### 27. month_date：`May 18, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> y Bryton Herdes , Bryce Walters , Mingwei Zhang BGP , Routing , Routing Security , RPKI , Radar May 18, 2026 Project Glasswing: what Mythos showed us In recent weeks, we pointed Mythos and other security-focused LLMs at live

### 28. utc_time：`11:05:00 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> a range of BGP collectors gathering BGP information from hundreds of routers around the planet. Between approximately 11:05:00 UTC and 12:55:00 UTC today we saw the following announcements: BGP4MP|04/24/18 11:05:42|A|205.251.199.0/24|10297 BGP4MP|0

### 29. utc_time：`12:55:00 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> llectors gathering BGP information from hundreds of routers around the planet. Between approximately 11:05:00 UTC and 12:55:00 UTC today we saw the following announcements: BGP4MP|04/24/18 11:05:42|A|205.251.199.0/24|10297 BGP4MP|04/24/18 11:05:42|

### 30. utc_time：`13:03 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/aws_route53_crypto_hijack_2018.md`
- 原文上下文：

> fected Amazon DNS. eNet (AS10297) of Columbus, OH announced the following more-specifics of Amazon routes from 11:05 to 13:03 UTC today:205.251.192.0/24205.251.193.0/24205.251.195.0/24205.251.197.0/24205.251.199.0/24 — InternetIntelligence (@Inter

