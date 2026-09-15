import gradio as gr 
from dotenv import load_dotenv
from research_manager import ResearchManager
from styles import CSS, JS, EXAMPLES, HEADER_HTML

load_dotenv(override = True)

async def ask_clarifications(query: str):
    if not query or not query.strip():
        return (
            query,
            [],
            gr.update(visible=False),
            gr.update(label="Question 1", value="", visible=False),
            gr.update(label="Question 2", value="", visible=False),
            gr.update(label="Question 3", value="", visible=False),
        )

    questions = await ResearchManager().get_clarifications(query)
    q1, q2, q3 = (list(questions) + ["", "", ""])[:3]

    return (
        query,
        questions,
        gr.update(visible=True),
        gr.update(label=q1 or "Question 1", value="", visible=bool(q1)),
        gr.update(label=q2 or "Question 2", value="", visible=bool(q2)),
        gr.update(label=q3 or "Question 3", value="", visible=bool(q3)),
    )

async def run(query: str, questions: list, a1: str, a2: str, a3: str):
    answers = [a1, a2, a3][: len(questions)]
    clarifications = list(zip(questions, answers))
    async for status_update in ResearchManager().run(query, clarifications):
        yield status_update

with gr.Blocks(title="Deep Research") as ui:
    gr.HTML(HEADER_HTML)

    query_state = gr.State("")
    questions_state = gr.State([])

    with gr.Row(elem_classes="dr-query-row"):
        query_textbox = gr.Textbox(
            placeholder="Type a research question...",
            show_label=False,
            container=False,
            autofocus=True,
            elem_id="dr-query",
            scale=5,
        )
        run_button = gr.Button("Clarify", variant="primary", elem_id="dr-run", scale=1)

    gr.HTML('<div class="dr-examples-label">Try one</div>')
    gr.Examples(examples=EXAMPLES, inputs=query_textbox, elem_id="dr-examples")

    with gr.Group(visible=False, elem_id="dr-clarify") as clarify_group:
        gr.HTML('<div class="dr-clarify-label">A few quick questions before I start</div>')
        answer_1 = gr.Textbox(label="Question 1", elem_classes="dr-answer")
        answer_2 = gr.Textbox(label="Question 2", elem_classes="dr-answer")
        answer_3 = gr.Textbox(label="Question 3", elem_classes="dr-answer")
        submit_button = gr.Button("Run research", variant="primary", elem_id="dr-submit")

    report = gr.Markdown(elem_id="dr-report")

    run_button.click(
        ask_clarifications,
        inputs=query_textbox,
        outputs=[query_state, questions_state, clarify_group, answer_1, answer_2, answer_3],
    )
    query_textbox.submit(
        ask_clarifications,
        inputs=query_textbox,
        outputs=[query_state, questions_state, clarify_group, answer_1, answer_2, answer_3],
    )

    submit_button.click(
        run,
        inputs=[query_state, questions_state, answer_1, answer_2, answer_3],
        outputs=report,
    )


if __name__ == "__main__":
    ui.launch(inbrowser=True,css=CSS, js=JS, theme=gr.themes.Base())