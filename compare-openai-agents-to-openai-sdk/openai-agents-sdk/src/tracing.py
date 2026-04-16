from pprint import pprint

from agents.tracing import TracingProcessor
from agents.tracing.processors import BackendSpanExporter, BatchTraceProcessor
from agents.tracing.span_data import (
    AgentSpanData,
    FunctionSpanData,
    GenerationSpanData,
    ResponseSpanData,
)

from agents import set_trace_processors


class ConsoleTracingProcessor(TracingProcessor):
    def on_trace_start(self, trace) -> None:
        print(f"\n{'─' * 60}")
        print(f"[trace] {trace.name}")

    def on_trace_end(self, trace) -> None:
        print(f"{'─' * 60}\n")

    def on_span_start(self, span) -> None:
        pass

    def on_span_end(self, span) -> None:
        data = span.span_data

        if isinstance(data, AgentSpanData):
            print(f"\n[agent]  {data.name}  tools={data.tools or []}")

        elif isinstance(data, ResponseSpanData):
            r = data.response
            if r is None:
                return

            # Model and config
            print(f"\n[response] model={r.model}")

            # Full prompt: system instructions + conversation messages
            print("  ── input ──")
            if r.instructions:
                print(f"  [system] {r.instructions}")
            if data.input:
                pprint(data.input)

            # Output text
            if r.output_text:
                print("  ── output ──")
                print(f"  [assistant] {r.output_text}")

            # Tool calls
            for item in r.output:
                if item.type == "function_call":
                    print(f"  ── tool call ── {item.name}({item.arguments})")

            # Token usage
            if r.usage:
                u = r.usage
                print(
                    f"  ── tokens ──  "
                    f"input={u.input_tokens}  "
                    f"output={u.output_tokens}  "
                    f"total={u.total_tokens}"
                )

            # Full response object
            print("  ── full response ──")
            pprint(r.to_dict())

        elif isinstance(data, GenerationSpanData):
            print(f"\n[generation] model={data.model}")

        elif isinstance(data, FunctionSpanData):
            print(f"\n[tool]  {data.name}")
            print(f"  input:  {data.input}")
            print(f"  output: {data.output}")

    def shutdown(self) -> None:
        pass

    def force_flush(self) -> None:
        pass


def setup_tracing() -> None:
    set_trace_processors(
        [
            BatchTraceProcessor(BackendSpanExporter()),
            ConsoleTracingProcessor(),
        ]
    )
