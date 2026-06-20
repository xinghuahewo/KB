# facebook_outage_cloudflare_2021 案例观察值核验

## 来源

- 标题：Understanding How Facebook Disappeared from the Internet
- 来源文本：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 观察值数量：26

## 类型统计

- asn：7
- ipv4_prefix：3
- iso_date：1
- month_date：5
- utc_time：10

## 核验边界

- 本文件只列出正则直接抽取的观察值和原文上下文。
- 事件角色、证据强度、影响范围和因果解释需要语义判断，本步骤跳过。

## 观察值清单

### 1. asn：`AS1`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> can see six autonomous systems on the Internet and two possible routes that one packet can use to go from Start to End. AS1 → AS2 → AS3 being the fastest, and AS1 → AS6 → AS5 → AS4 → AS3 being the slowest, but that can be used if the first fai

### 2. asn：`AS13335`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> esses), as well as transit prefixes (say they know how to reach specific groups of IP addresses). Cloudflare's ASN is AS13335 . Every ASN needs to announce its prefix routes to the Internet using BGP; otherwise, no one will know how to connect a

### 3. asn：`AS2`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> e six autonomous systems on the Internet and two possible routes that one packet can use to go from Start to End. AS1 → AS2 → AS3 being the fastest, and AS1 → AS6 → AS5 → AS4 → AS3 being the slowest, but that can be used if the first fails.

### 4. asn：`AS3`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> autonomous systems on the Internet and two possible routes that one packet can use to go from Start to End. AS1 → AS2 → AS3 being the fastest, and AS1 → AS6 → AS5 → AS4 → AS3 being the slowest, but that can be used if the first fails. At 15:

### 5. asn：`AS4`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> ssible routes that one packet can use to go from Start to End. AS1 → AS2 → AS3 being the fastest, and AS1 → AS6 → AS5 → AS4 → AS3 being the slowest, but that can be used if the first fails. At 15:58 UTC we noticed that Facebook had stopped a

### 6. asn：`AS5`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> two possible routes that one packet can use to go from Start to End. AS1 → AS2 → AS3 being the fastest, and AS1 → AS6 → AS5 → AS4 → AS3 being the slowest, but that can be used if the first fails. At 15:58 UTC we noticed that Facebook had sto

### 7. asn：`AS6`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> t and two possible routes that one packet can use to go from Start to End. AS1 → AS2 → AS3 being the fastest, and AS1 → AS6 → AS5 → AS4 → AS3 being the slowest, but that can be used if the first fails. At 15:58 UTC we noticed that Facebook h

### 8. ipv4_prefix：`129.134.0.0/17`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> and related services were effectively unavailable: route-views>show ip bgp 129.134.30.0 BGP routing table entry for 129.134.0.0/17, version 1025798334 Paths: (24 available, best #14, table default) Not advertised to any peer Refresh Epoch 2 3303 6453

### 9. ipv4_prefix：`129.134.30.0/23`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> of facebook.com. route-views>show ip bgp 185.89.218.0/23 % Network not in table route-views> route-views>show ip bgp 129.134.30.0/23 % Network not in table route-views> Meanwhile, other Facebook IP addresses remained routed but weren’t particularly u

### 10. ipv4_prefix：`185.89.218.0/23`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> .1 DNS resolver could no longer respond to queries asking for the IP address of facebook.com. route-views>show ip bgp 185.89.218.0/23 % Network not in table route-views> route-views>show ip bgp 129.134.30.0/23 % Network not in table route-views> Mean

### 11. iso_date：`2021-10-04`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> rust Speed & Reliability Life at Cloudflare Partners Understanding how Facebook disappeared from the Internet 2021-10-04 Celso Martinho Tom Strickx 5 min read This post is also available in 简体中文 , Français , Deutsch , Italiano , 日本語

### 12. month_date：`June 03, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> Facebook Follow on X Celso Martinho | @celso Tom Strickx | @tstrickx Cloudflare | @cloudflare Related posts June 03, 2026 Enforcing the First AS in BGP AS_PATHs BGP is vulnerable to routing hijacks and path leaks that negatively impact t

### 13. month_date：`May 01, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> ebastiaan Neuteboom , Christian Elmerot , Max Worsley DNS , DNSSEC , 1.1.1.1 , Reliability , Outage May 01, 2026 Code Orange: Fail Small is complete. The result is a stronger Cloudflare network We have completed a massive engine

### 14. month_date：`May 06, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> bina Zejnilovic Internet Traffic , Internet Trends , Internet Quality , Internet Shutdown , Radar , DNS May 06, 2026 When DNSSEC goes wrong: how we responded to the .de TLD outage On May 5, 2026, DENIC published broken DNSSEC signat

### 15. month_date：`May 27, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> y Bryton Herdes , Bryce Walters , Mingwei Zhang BGP , Routing , Routing Security , RPKI , Radar May 27, 2026 Iran's Internet is partially restored, Cloudflare Radar data shows Cloudflare Radar data confirms early indications

### 16. month_date：`May 5, 2026`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> ernet Shutdown , Radar , DNS May 06, 2026 When DNSSEC goes wrong: how we responded to the .de TLD outage On May 5, 2026, DENIC published broken DNSSEC signatures for the .de TLD, making millions of domains unreachable. Here's what 1.1.1.1

### 17. utc_time：`15:40 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> lly this chart is fairly quiet: Facebook doesn’t make a lot of changes to its network minute to minute. But at around 15:40 UTC we saw a peak of routing changes from Facebook. That’s when the trouble began. If we split this view by routes announ

### 18. utc_time：`15:45 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> unreachability in our WARP traffic to and from Facebook's affected ASN 32934. This chart shows how traffic changed from 15:45 UTC to 16:45 UTC compared with three hours before in each country. All over the world WARP traffic to and from Facebook’s n

### 19. utc_time：`15:50 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> availability of the DNS name 'facebook.com' on Cloudflare's DNS resolver 1.1.1.1. It stopped being available at around 15:50 UTC and returned at 21:20 UTC. Undoubtedly Facebook, WhatsApp and Instagram services will take further time to come onlin

### 20. utc_time：`15:51 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> 中文 . The Internet - A Network of Networks “ Facebook can't be down, can it? ”, we thought, for a second. Today at 15:51 UTC, we opened an internal incident entitled "Facebook DNS lookup returning SERVFAIL" because we were worried that somethin

### 21. utc_time：`15:58 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> AS3 being the fastest, and AS1 → AS6 → AS5 → AS4 → AS3 being the slowest, but that can be used if the first fails. At 15:58 UTC we noticed that Facebook had stopped announcing the routes to their DNS prefixes. That meant that, at least, Facebook’s

### 22. utc_time：`16:45 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> y in our WARP traffic to and from Facebook's affected ASN 32934. This chart shows how traffic changed from 15:45 UTC to 16:45 UTC compared with three hours before in each country. All over the world WARP traffic to and from Facebook’s network simply

### 23. utc_time：`21:00 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> tween entities are at the center of making it work for almost five billion active users worldwide. Update At around 21:00 UTC we saw renewed BGP activity from Facebook's network which peaked at 21:17 UTC. This chart shows the availability of t

### 24. utc_time：`21:17 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> ive users worldwide. Update At around 21:00 UTC we saw renewed BGP activity from Facebook's network which peaked at 21:17 UTC. This chart shows the availability of the DNS name 'facebook.com' on Cloudflare's DNS resolver 1.1.1.1. It stopped be

### 25. utc_time：`21:20 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> ame 'facebook.com' on Cloudflare's DNS resolver 1.1.1.1. It stopped being available at around 15:50 UTC and returned at 21:20 UTC. Undoubtedly Facebook, WhatsApp and Instagram services will take further time to come online but as of 21:28 UTC Face

### 26. utc_time：`21:28 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/facebook_outage_cloudflare_2021.md`
- 原文上下文：

> d at 21:20 UTC. Undoubtedly Facebook, WhatsApp and Instagram services will take further time to come online but as of 21:28 UTC Facebook appears to be reconnected to the global Internet and DNS working again. Trends Outage BGP DNS Facebook Fol

