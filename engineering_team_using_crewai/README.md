# Engineering Team Using CrewAI

## Overview

This project uses CrewAI to simulate a small software engineering team made up of four AI agents. Given a single high level requirements document, the crew designs, builds, tests, and demonstrates a working Python application with a Gradio frontend.

The current build target is a trading simulation account manager. The crew produces a backend module, a Gradio user interface, a suite of unit tests, and a written design document, all inside an isolated sandbox directory.

## The Four Agents

1. Engineering Lead
   Reads the requirements and produces a written design: the modules, classes, and function signatures the other three agents should build. Does not write implementation code. Also has access to Context7 through MCP, which it uses to check current Gradio 6 APIs so its guidance to the Frontend Engineer stays accurate.

2. Backend Engineer
   Implements the Python backend described in the design. Restricted to the Python standard library only, so the resulting module has no external dependencies.

3. Frontend Engineer
   Builds a Gradio interface (app.py) that demonstrates the backend. Also writes a small validation script that imports the app and confirms it constructs correctly, without actually launching a server.

4. Test Engineer
   Writes a unit test suite for the backend module using the standard library unittest framework, runs it, and fixes backend defects until every test passes.

## How the Crew Runs

The crew currently runs as a single sequential pipeline, meaning each task runs one after another in a fixed order, and each task is assigned to a specific agent ahead of time.

The order is as follows.

Step one. The Engineering Lead reads the requirements and writes a design document. This is saved to sandbox/design.md.

Step two. The Backend Engineer reads that design and the original requirements, then writes the backend Python module directly into the sandbox using its file writing tools.

Step three. The Frontend Engineer reads the backend code and the design, then writes a Gradio interface in app.py, along with a small validation script that confirms the interface builds without errors.

Step four. The Test Engineer reads the backend code and the design, writes a unit test file, runs it inside the sandbox, and iterates on any backend bugs it finds until the full suite passes. A summary of the test run is saved to sandbox/test_summary.md.

An earlier version of this project attempted a hierarchical process, where the Engineering Lead acted purely as a manager, dynamically delegating each implementation task to whichever worker agent fit best, rather than each task being hard assigned in advance. That version is described in the Future Work section below. The current sequential version was adopted to make debugging easier while a tooling issue described below was being tracked down.

## Project Structure

```
engineering_team_using_crewai/
  src/engineering_team_using_crewai/
    crew.py            defines the agents, tasks, and the crew itself
    main.py             entry point used to run, train, replay, or test the crew
    patch.py            a small monkeypatch, explained below
    config/
      agents.yaml        role, goal, backstory, and model for each agent
      tasks.yaml          description and expected output for each task
    tools/
      sandbox_tools.py    the file and code execution tools every agent shares
  sandbox/                a fresh, isolated uv project the crew writes and runs code inside
    backend.py             the generated backend module
    app.py                 the generated Gradio interface
    test_backend.py         the generated unit tests
    design.md               the generated design document
    test_summary.md          a summary of the final test run
```

## The Sandbox and Its Tools

Every agent that writes or runs code shares the same set of tools, defined once in sandbox_tools.py.

List Sandbox Files. Lists every file currently in the sandbox.

Read Sandbox File. Reads back the contents of a file already in the sandbox.

Write Sandbox File. Writes a file to the sandbox, replacing anything already there with the same name.

Run Sandbox Python File. Executes a file from the sandbox inside a disposable Docker container, using uv run, and returns the exit code plus both stdout and stderr.

Before each run, reset_sandbox wipes the sandbox directory completely and reinitializes it as a brand new uv project with gradio installed, so every run starts from a clean, reproducible state.

## The MCP Patch

patch.py works around a bug present in the version of CrewAI this project depends on. When an agent connects to a remote MCP server such as Context7, CrewAI sanitizes tool names for internal use, for example turning resolve library id into a safe internal identifier, but then mistakenly sends that sanitized name back to the actual MCP server when calling the tool. Any tool whose real name contains a character that gets sanitized away becomes unreachable. The patch preserves the original, unsanitized server side name alongside the sanitized one, so the correct name is sent back to the server when the tool is actually called. Importing patch.py at the top of main.py applies this fix as a side effect before the crew starts.

## Setup

Requirements. Python 3.13, uv, and Docker, since generated code is executed inside a disposable container.

1. Install dependencies with uv sync from the project root.
2. Provide an OPENAI_API_KEY, and an ANTHROPIC_API_KEY if you plan to experiment with Anthropic models for any agent.
3. Confirm Docker is running, since Run Sandbox Python File depends on it.

## Running the Crew

From the project root, run the crew with the CrewAI CLI.

```
crewai run
```

This calls run() in main.py, which resets the sandbox and then kicks off the crew with the requirements text defined at the top of that file. To build something other than the trading simulation example, edit the requirements string in main.py before running.

Three additional entry points exist for more advanced CrewAI workflows: train(), replay(), and test(), each documented in the CrewAI docs and each operating on the same crew defined in crew.py.

## Result

The screenshots below are from a completed run of the trading simulation example. An account was created with an initial deposit of one hundred thousand dollars, one share of TSLA was purchased, and the resulting portfolio summary and transaction history were pulled directly from the generated Gradio interface.

### Account Manager Interface

![Trading Simulation Account Manager interface showing account creation, deposit, and buy and sell controls, with a status panel confirming a successful buy](screenshots/screenshot_1_account_manager.png)

### Portfolio Summary

![Portfolio summary table showing account id, owner, cash balance, holdings value, total portfolio value, and profit and loss figures, alongside a holdings table showing one share of TSLA](screenshots/screenshot_2_portfolio_summary.png)

### Transaction History

![Transaction history table showing a one hundred thousand dollar deposit followed by a one share TSLA purchase, with the resulting cash balance after each transaction](screenshots/screenshot_3_transaction_history.png)