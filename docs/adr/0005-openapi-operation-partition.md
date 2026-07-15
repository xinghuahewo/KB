# ADR-0005：超长 OpenAPI operation 按语义区段拆分

## 状态

已接受，2026-07-14。

## 背景

PeeringDB OpenAPI 当前产生 41,857 个 chunk，占全部 chunk 的 71.4771%。按 YAML 标量切块会产生两字符碎片，也无法回答 endpoint、参数、响应和 schema 之间的组合问题。fixture 黄金集覆盖 `GET /net/{id}` 的概览、path/query 参数、4xx 响应和 2xx schema 查询。

## 决策

每个 `method + path` 先形成一个 operation 语义单元。未超过 800 tokens 时保持单块；超过时按以下稳定顺序拆分：

1. `overview`：method、path、operationId、summary、description、认证和安全要求。
2. `parameters:<location>`：分别按 path、query、header、cookie 和 request body 分组，保留参数必填性、类型和约束。
3. `responses:<family>`：按 2xx、3xx、4xx、5xx 分组，保留状态码、描述、媒体类型和直接 schema 引用。
4. `schema:<name>`：被多个 operation 复用或单独超长的 schema 独立成块，并保留反向 operation refs。

每个子块重复最小 method、path、operationId 和标题上下文；不得按单个标量、标点或数组元素切块。单个区段仍超过上限时，只能在参数列表、响应状态码列表或 schema properties 的成员边界继续分组，不能截断字段说明。

## 黄金查询结论

- endpoint 用法命中 `overview`。
- `id` 和 `depth` 分别命中 `parameters:path`、`parameters:query`。
- 不存在记录命中 `responses:4xx`。
- 成功响应字段命中 `responses:2xx` 与 `schema:Network` 的关联证据。

## 后果

该规则优先保证查询所需语义闭包，同时把 chunk 数量从“标量数量级”收敛到“operation/区段数量级”。实际 token 目标、重叠和 retrieval_text 组装在 SemanticChunk v3 任务中实现。
