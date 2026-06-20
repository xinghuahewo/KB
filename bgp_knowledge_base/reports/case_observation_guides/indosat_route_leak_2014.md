# indosat_route_leak_2014 案例观察值核验

## 来源

- 标题：Indosat fat-thumbs route announcements again
- 来源文本：`cleaned/cases/indosat_route_leak_2014.md`
- 观察值数量：5

## 类型统计

- asn：2
- month_date：2
- utc_time：1

## 核验边界

- 本文件只列出正则直接抽取的观察值和原文上下文。
- 事件角色、证据强度、影响范围和因果解释需要语义判断，本步骤跳过。

## 观察值清单

### 1. asn：`AS4651`

- review_status：`pending`
- source_ref：`cleaned/cases/indosat_route_leak_2014.md`
- 原文上下文：

> ement has affected more than 320,000 prefixes. REG AD The Indosat hijack affected 320,349 prefixes. Most routes via AS4651 (THAI-GATEWAY) and 6939 (HE) pic.twitter.com/bbG23jbT9T — BGPmon.net (@bgpmon) April 2, 2014 As noted by BGPmon, In

### 2. asn：`AS4761`

- review_status：`pending`
- source_ref：`cleaned/cases/indosat_route_leak_2014.md`
- 原文上下文：

> BOFH Who, Me? On Call REG AD Networks Indosat fat-thumbs route announcements (again) Networks go dark on AS4761 'hijack' Richard Chirgwin Richard Chirgwin Published thu 3 Apr 2014 // 03:29 UTC Indosat has made an unknown

### 3. month_date：`April 2`

- review_status：`pending`
- source_ref：`cleaned/cases/indosat_route_leak_2014.md`
- 原文上下文：

> unreachable by announcing itself as their route. The mis-announcement took place sometime close to midnight (UMT) on April 2, with this message kicking off an ongoing thread at Seclists complaining about their routes being 'hijacked'. Many of

### 4. month_date：`April 2, 2014`

- review_status：`pending`
- source_ref：`cleaned/cases/indosat_route_leak_2014.md`
- 原文上下文：

> 0,349 prefixes. Most routes via AS4651 (THAI-GATEWAY) and 6939 (HE) pic.twitter.com/bbG23jbT9T — BGPmon.net (@bgpmon) April 2, 2014 As noted by BGPmon, Indosat has form for route announcement hijacks. In 2011 it made a similar mistake, announcing it

### 5. utc_time：`03:29 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/indosat_route_leak_2014.md`
- 原文上下文：

> nts (again) Networks go dark on AS4761 'hijack' Richard Chirgwin Richard Chirgwin Published thu 3 Apr 2014 // 03:29 UTC Indosat has made an unknown number of networks – in the thousands according to BGPmon, but possibly more – unreachabl

