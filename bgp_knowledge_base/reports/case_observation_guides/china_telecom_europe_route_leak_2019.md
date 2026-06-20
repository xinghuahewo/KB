# china_telecom_europe_route_leak_2019 案例观察值核验

## 来源

- 标题：BGP event sends European mobile traffic through China Telecom for 2 hours
- 来源文本：`cleaned/cases/china_telecom_europe_route_leak_2019.md`
- 观察值数量：9

## 类型统计

- asn：8
- month_date：1

## 核验边界

- 本文件只列出正则直接抽取的观察值和原文上下文。
- 事件角色、证据强度、影响范围和因果解释需要语义判断，本步骤跳过。

## 观察值清单

### 1. asn：`AS1130`

- review_status：`pending`
- source_ref：`cleaned/cases/china_telecom_europe_route_leak_2019.md`
- 原文上下文：

> affected by Thursday’s event included Switzerland-based Swisscom’s AS3303, Netherlands-based telecom KPN’s AS1136, and AS1130 and AS21502, belonging to French telecommunications providers Bouygues Telecom and Numericable-SFR respectively. KPN la

### 2. asn：`AS1136`

- review_status：`pending`
- source_ref：`cleaned/cases/china_telecom_europe_route_leak_2019.md`
- 原文上下文：

> . Networks affected by Thursday’s event included Switzerland-based Swisscom’s AS3303, Netherlands-based telecom KPN’s AS1136, and AS1130 and AS21502, belonging to French telecommunications providers Bouygues Telecom and Numericable-SFR respecti

### 3. asn：`AS21217`

- review_status：`pending`
- source_ref：`cleaned/cases/china_telecom_europe_route_leak_2019.md`
- 原文上下文：

> he Border Gateway Protocol . The incident started around 9:43am UTC on Thursday (2:43am California time). That’s when AS21217, the autonomous system belonging to Switzerland-based data center colocation company Safe Host , improperly updated its

### 4. asn：`AS21502`

- review_status：`pending`
- source_ref：`cleaned/cases/china_telecom_europe_route_leak_2019.md`
- 原文上下文：

> y Thursday’s event included Switzerland-based Swisscom’s AS3303, Netherlands-based telecom KPN’s AS1136, and AS1130 and AS21502, belonging to French telecommunications providers Bouygues Telecom and Numericable-SFR respectively. KPN later blamed t

### 5. asn：`AS3303`

- review_status：`pending`
- source_ref：`cleaned/cases/china_telecom_europe_route_leak_2019.md`
- 原文上下文：

> s, and network providers through Russia . Networks affected by Thursday’s event included Switzerland-based Swisscom’s AS3303, Netherlands-based telecom KPN’s AS1136, and AS1130 and AS21502, belonging to French telecommunications providers Bouyg

### 6. asn：`AS37282`

- review_status：`pending`
- source_ref：`cleaned/cases/china_telecom_europe_route_leak_2019.md`
- 原文上下文：

> nstance, when a major African ISP updated tables in the Internet’s global routing system to improperly declare that its AS37282 was the proper path to reach 212 IP prefixes belonging to Google, the Chinese telecom accepted the route and announced

### 7. asn：`AS4134`

- review_status：`pending`
- source_ref：`cleaned/cases/china_telecom_europe_route_leak_2019.md`
- 原文上下文：

> ntually would become more than 70,000 Internet routes comprising an estimated 368 million IP addresses. China Telecom’s AS4134, which struck a network peering arrangement with Safe Host in 2017, almost immediately echoed those routes rather than

### 8. asn：`AS703`

- review_status：`pending`
- source_ref：`cleaned/cases/china_telecom_europe_route_leak_2019.md`
- 原文上下文：

> ften traveled to Shanghai first. That incident involved China Telecom incorrectly handling the routing announcements of AS703, Verizon’s Asia-Pacific autonomous system. “It’s hard to say definitively,” Rob Ragan, a principal security researche

### 9. month_date：`June 7, 2019`

- review_status：`pending`
- source_ref：`cleaned/cases/china_telecom_europe_route_leak_2019.md`
- 原文上下文：

> erday’s BGP leak, there was no configuration change on our side that triggered the issue. — Safe Host SA (@swisscolo) June 7, 2019 Intentional or not, the incident underscores a fundamental weakness in BGP, which is the global routing table that al

