# cert_eu_china_telecom_route_leak_2019 案例观察值核验

## 来源

- 标题：High volume of European mobile traffic rerouted through China Telecom
- 来源文本：`cleaned/cases/cert_eu_china_telecom_route_leak_2019.md`
- 观察值数量：14

## 类型统计

- asn：6
- month_date：6
- utc_time：2

## 核验边界

- 本文件只列出正则直接抽取的观察值和原文上下文。
- 事件角色、证据强度、影响范围和因果解释需要语义判断，本步骤跳过。

## 观察值清单

### 1. asn：`AS1136`

- review_status：`pending`
- source_ref：`cleaned/cases/cert_eu_china_telecom_route_leak_2019.md`
- 原文上下文：

> h China Telecom’s network. Some of the most impacted European networks included Swisscom (AS3303) of Switzerland, KPN (AS1136) of Holland, Bouygues Telecom (AS5410) and Numericable-SFR (AS21502) of France. Often routing incidents only last for

### 2. asn：`AS21217`

- review_status：`pending`
- source_ref：`cleaned/cases/cert_eu_china_telecom_route_leak_2019.md`
- 原文上下文：

> China Telecom for over two hours. The incident began at 09:43 UTC when Swiss data centre colocation company Safe Host (AS21217) unintentionally leaked over 70 000 routes to China Telecom (AS4134) in Frankfurt, Germany . China Telecom then announ

### 3. asn：`AS21502`

- review_status：`pending`
- source_ref：`cleaned/cases/cert_eu_china_telecom_route_leak_2019.md`
- 原文上下文：

> rks included Swisscom (AS3303) of Switzerland, KPN (AS1136) of Holland, Bouygues Telecom (AS5410) and Numericable-SFR (AS21502) of France. Often routing incidents only last for a few minutes, but in this case, many of the leaked routes were in c

### 4. asn：`AS3303`

- review_status：`pending`
- source_ref：`cleaned/cases/cert_eu_china_telecom_route_leak_2019.md`
- 原文上下文：

> ropean mobile networks through China Telecom’s network. Some of the most impacted European networks included Swisscom (AS3303) of Switzerland, KPN (AS1136) of Holland, Bouygues Telecom (AS5410) and Numericable-SFR (AS21502) of France. Often ro

### 5. asn：`AS4134`

- review_status：`pending`
- source_ref：`cleaned/cases/cert_eu_china_telecom_route_leak_2019.md`
- 原文上下文：

> n Swiss data centre colocation company Safe Host (AS21217) unintentionally leaked over 70 000 routes to China Telecom (AS4134) in Frankfurt, Germany . China Telecom then announced these routes on to the global internet redirecting large amounts

### 6. asn：`AS5410`

- review_status：`pending`
- source_ref：`cleaned/cases/cert_eu_china_telecom_route_leak_2019.md`
- 原文上下文：

> most impacted European networks included Swisscom (AS3303) of Switzerland, KPN (AS1136) of Holland, Bouygues Telecom (AS5410) and Numericable-SFR (AS21502) of France. Often routing incidents only last for a few minutes, but in this case, many

### 7. month_date：`April 26, 2017`

- review_status：`pending`
- source_ref：`cleaned/cases/cert_eu_china_telecom_route_leak_2019.md`
- 原文上下文：

> ers started to send traffic destined for Japan to Google. About 8 million Japanese connecti ons became unavailable.  April 26, 2017: T raffic belonging to more than twenty financial services, including Visa and MasterCard, was routed through Rostelec

### 8. month_date：`August 25, 2017`

- review_status：`pending`
- source_ref：`cleaned/cases/cert_eu_china_telecom_route_leak_2019.md`
- 原文上下文：

> including Visa and MasterCard earlier this year. It is likely that the traffic redirection was a deliberate choice.  August 25, 2017: An error by Google caused widespread internet outages in Japan for about one hour. The mishap occurred due to incorre

### 9. month_date：`December 12, 2017`

- review_status：`pending`
- source_ref：`cleaned/cases/cert_eu_china_telecom_route_leak_2019.md`
- 原文上下文：

> it went undetected until end users began reporting dropped traffic, revealing glaring security limitations of BGP.  December 12, 2017: Traffic to some of the world’s largest tech companies was briefly rerouted through a Russian ISP. Eighty prefixes ass

### 10. month_date：`December 28, 2018`

- review_status：`pending`
- source_ref：`cleaned/cases/cert_eu_china_telecom_route_leak_2019.md`
- 原文上下文：

> ecurity risk for any entity relying on the internet. Some recent high-profile routing incidents have been observed.  December 28, 2018: beginning at 08:33 UTC, an internet routing path that was usually advertised by an Autonomous System Number (ASN) ass

### 11. month_date：`June 6`

- review_status：`pending`
- source_ref：`cleaned/cases/cert_eu_china_telecom_route_leak_2019.md`
- 原文上下文：

> has still not implemented some basic routing safeguards to detect and remediate them in a timely manner. Summary On June 6, a routing incident led to over 70 000 routes used for European mobile networks being redirected through China Telecom

### 12. month_date：`November 12, 2018`

- review_status：`pending`
- source_ref：`cleaned/cases/cert_eu_china_telecom_route_leak_2019.md`
- 原文上下文：

> associated with China Telecom. The incident comprised more than 374 events over a period of 2 hours and 15 minutes.  November 12, 2018: Nigeria’s Main One Cable Company inadvertently caused a glitch that temporarily misrouted Google internet traffic thr

### 13. utc_time：`08:33 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/cert_eu_china_telecom_route_leak_2019.md`
- 原文上下文：

> ing on the internet. Some recent high-profile routing incidents have been observed.  December 28, 2018: beginning at 08:33 UTC, an internet routing path that was usually advertised by an Autonomous System Number (ASN) associated with the US Depa

### 14. utc_time：`09:43 UTC`

- review_status：`pending`
- source_ref：`cleaned/cases/cert_eu_china_telecom_route_leak_2019.md`
- 原文上下文：

> tes used for European mobile networks being redirected through China Telecom for over two hours. The incident began at 09:43 UTC when Swiss data centre colocation company Safe Host (AS21217) unintentionally leaked over 70 000 routes to China Telec

