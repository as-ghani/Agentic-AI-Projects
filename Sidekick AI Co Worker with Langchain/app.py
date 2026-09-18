import html

import gradio as gr

import styles
from sidekick import Sidekick

LAUNCH_STYLE = {"theme": styles.THEME, "css": styles.CSS, "head": styles.JS}

MASTHEAD = """
<div id="masthead">
    <h1>Sidekick</h1>
    <p>Give it a job and a finish line. It browses, reads and writes files, and stops to ask
    when it needs your hands.</p>
</div>
"""

STATES = {
    "starting": "bringing up the browser and filesystem",
    "ready": "ready",
    "working": "working",
    "waiting": "waiting for you",
}


def render_plan(todos):
    if not todos:
        body = '<p class="empty">The plan appears here once the Sidekick starts working.</p>'
    else:
        body = "<ol>" + "".join(
            f'<li class="{todo["status"]}"><span class="mark"></span>'
            f'<span>{html.escape(todo["content"])}</span></li>'
            for todo in todos
        ) + "</ol>"
    return f"<h3>Plan</h3>{body}"


def read_state(sidekick):
    if sidekick is None:
        return "starting"
    if getattr(sidekick, "paused", False):
        return "waiting"
    if any(todo["status"] == "in_progress" for todo in (sidekick.todos or [])):
        return "working"
    return "ready"


def render_status(state):
    return f'<div id="status-line" class="{state}"><span class="dot"></span>{STATES[state]}</div>'


def render_rail(state):
    return f'<div id="rail" class="{state}"></div>'


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick, gr.update(interactive=True)


async def process_message(sidekick, message, success_criteria, history):
    if sidekick is None:  # the user clicked before setup finished bringing up the MCP servers
        return history, gr.update(visible=False), sidekick
    results = await sidekick.run_turn(message, success_criteria, history)
    return results, gr.update(visible=sidekick.paused), sidekick


async def approve(sidekick, history):
    results = await sidekick.resume(history)
    return results, gr.update(visible=sidekick.paused), sidekick


def watch_progress(sidekick):
    """Called by the timer. The timer is the only writer for the plan, the status line and
    the rail: if a long-running event owned them as outputs, Gradio would lock them as
    pending and live updates would not render while the Sidekick works."""
    state = read_state(sidekick)
    todos = sidekick.todos if sidekick else []
    return render_plan(todos), render_status(state), render_rail(state)


async def reset(sidekick):
    if sidekick:
        sidekick.cleanup()
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, gr.update(visible=False), new_sidekick


def free_resources(sidekick):
    if sidekick:
        sidekick.cleanup()


with gr.Blocks(title="Sidekick") as ui:
    rail = gr.HTML(render_rail("starting"))
    gr.HTML(MASTHEAD)
    status = gr.HTML(render_status("starting"))
    sidekick = gr.State(delete_callback=free_resources)

    with gr.Row(equal_height=True):
        chatbot = gr.Chatbot(show_label=False, height=380, scale=3, elem_id="chat")
        with gr.Column(scale=1):
            plan = gr.HTML(render_plan([]), elem_id="plan")

    with gr.Group(elem_id="ask"):
        message = gr.Textbox(show_label=False, lines=2,
                             placeholder="What should the Sidekick do?")
        success_criteria = gr.Textbox(show_label=False,
                                      placeholder="How will you know it's done?")

    with gr.Row(elem_id="controls"):
        start_button = gr.Button("Start", variant="primary",
                                 elem_id="start-button", interactive=False)
        continue_button = gr.Button("I've done it — continue", visible=False,
                                    elem_id="continue-button")
        reset_button = gr.Button("Start over", elem_id="reset-button")

    timer = gr.Timer(1)

    ui.load(setup, [], [sidekick, start_button])
    timer.tick(watch_progress, [sidekick], [plan, status, rail], show_progress="hidden")
    message.submit(process_message, [sidekick, message, success_criteria, chatbot],
                   [chatbot, continue_button, sidekick])
    success_criteria.submit(process_message, [sidekick, message, success_criteria, chatbot],
                            [chatbot, continue_button, sidekick])
    start_button.click(process_message, [sidekick, message, success_criteria, chatbot],
                       [chatbot, continue_button, sidekick])
    continue_button.click(approve, [sidekick, chatbot], [chatbot, continue_button, sidekick])
    reset_button.click(reset, [sidekick],
                       [message, success_criteria, chatbot, continue_button, sidekick])


if __name__ == "__main__":
    ui.launch(inbrowser=True, **LAUNCH_STYLE)