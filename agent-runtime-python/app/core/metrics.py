from prometheus_client import Counter, Histogram

agent_requests_total = Counter(
    "agent_requests_total",
    "Total agent requests",
    ["method", "code_gen_type"],
)

agent_request_duration_seconds = Histogram(
    "agent_request_duration_seconds",
    "Agent request duration in seconds",
    ["method"],
    buckets=[0.5, 1, 2, 5, 10, 30, 60, 120, 300],
)

model_call_duration_seconds = Histogram(
    "model_call_duration_seconds",
    "Model call duration in seconds",
    ["provider", "model"],
    buckets=[0.5, 1, 2, 5, 10, 30, 60, 120],
)

model_call_tokens = Counter(
    "model_call_tokens_total",
    "Total model token usage",
    ["model", "direction"],
)

tool_call_duration_seconds = Histogram(
    "tool_call_duration_seconds",
    "Tool call duration in seconds",
    ["tool_name"],
    buckets=[0.1, 0.5, 1, 2, 5, 10],
)

tool_call_total = Counter(
    "tool_call_total",
    "Total tool calls",
    ["tool_name", "status"],
)

grpc_client_calls_total = Counter(
    "grpc_client_calls_total",
    "Total gRPC client calls from Python to Java",
    ["method", "status"],
)
