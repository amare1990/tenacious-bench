from agent.orchestrator import run_one


def demo():
    trace = run_one("Acme Example")
    print("Demo run saved trace:", trace.get("trace_id"))


if __name__ == "__main__":
    demo()
