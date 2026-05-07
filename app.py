import gradio as gr
import time
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from tools import get_all_tools

llm = ChatOllama(model="llama3.2", temperature=0)
tools = get_all_tools()
agent = create_react_agent(llm, tools)

history = []

def chat(message, chat_history):
    global history
    history.append(HumanMessage(content=message))
    start = time.time()
    try:
        result = agent.invoke({"messages": history})
        took = round(time.time() - start, 2)
        msgs = result["messages"]
        answer = ""
        tool_used = "reasoning"
        for m in msgs:
            if hasattr(m, "tool_calls") and m.tool_calls:
                for tc in m.tool_calls:
                    tool_used = tc.get("name", "unknown")
        for m in reversed(msgs):
            if type(m).__name__ == "AIMessage" and m.content:
                if not (hasattr(m, "tool_calls") and m.tool_calls):
                    answer = m.content
                    break
        if not answer:
            answer = msgs[-1].content
        history.append(AIMessage(content=answer))
        full_answer = answer + "\n\n*Tool used: " + tool_used + " | Took " + str(took) + "s*"
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": full_answer})
        return "", chat_history
    except Exception as e:
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": "Error: " + str(e)})
        return "", chat_history

def clear():
    global history
    history = []
    return []

with gr.Blocks(title="AI FP&A Agent") as app:
    gr.Markdown("# AI FP&A Intelligence Agent")
    gr.Markdown("Ask about budgets, revenue, cash flow, risks, org structure, or financial reports")
    
    chatbot = gr.Chatbot(height=500)
    msg = gr.Textbox(placeholder="Ask anything about TechCorp finances...", label="Question")
    
    with gr.Row():
        send = gr.Button("Send", variant="primary")
        clr = gr.Button("Clear Chat")
    
    gr.Markdown("""
    ### Try asking:
    - Which department has the highest budget variance?
    - What is our cash runway?
    - Which product is at risk?
    - What did the CFO say about marketing?
    - Who leads the IT department?
    - Show me operational risks
    """)
    
    send.click(chat, [msg, chatbot], [msg, chatbot])
    msg.submit(chat, [msg, chatbot], [msg, chatbot])
    clr.click(clear, None, chatbot)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
