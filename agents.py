from typing import Any, TypedDict
from langchain.agents import create_tool_calling_agent, AgentExecutor
from llms import get_llm
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import os

from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from chains import get_finish_chain, get_supervisor_chain

# 🔥 只保留不联网、不报错的工具
from tools import (
    ResumeExtractorTool,
    generate_letter_for_specific_job,
    save_cover_letter_for_specific_job,
)

from prompts import (
    get_analyzer_agent_prompt_template,
    get_generator_agent_prompt_template,
)

load_dotenv()

# ==========================================
class AgentState(TypedDict):
    user_input: str
    messages: list[BaseMessage]
    next_step: str
    config: dict
    callback: Any
    task_completed: bool
    needs_followup: str
    resume_content: str  # 👈 用来存简历，解决求职信缺内容

def init_chat_model(state_config):
    return get_llm(
        provider=state_config["model_provider"],
        model=state_config["model"],
        dashscope_api_key=state_config.get("DASHSCOPE_API_KEY") or os.environ.get("DASHSCOPE_API_KEY"),
        api_key=state_config.get("DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_API_KEY") or state_config.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY"),
        base_url=state_config.get("DEEPSEEK_BASE_URL") or os.environ.get("DEEPSEEK_BASE_URL") or state_config.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_BASE_URL"),
        temperature=state_config.get("temperature", 0.3)
    )

def create_agent_with_tools(llm, tools, system_prompt):
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=10
    )
    return executor

def supervisor_node(state):
    chat_history = state.get("messages", [])
    user_query = state.get("user_input", "")

    if state.get("needs_followup"):
        next_action = state["needs_followup"]
        state["needs_followup"] = ""
        state["next_step"] = next_action
        return state

    llm = init_chat_model(state["config"])
    if not chat_history:
        chat_history.append(HumanMessage(content=user_query))

    user_lower = user_query.lower()

    # 智能路由：只保留可用功能
    if ("简历" in user_lower or "resume" in user_lower) and ("求职信" in user_lower or "cover letter" in user_lower):
        state["needs_followup"] = "CoverLetterGenerator"
        next_action = "ResumeAnalyzer"
    elif any(word in user_lower for word in ["求职信"]):
        next_action = "CoverLetterGenerator"
    elif any(word in user_lower for word in ["简历", "分析", "职业路径"]):
        next_action = "ResumeAnalyzer"
    else:
        next_action = "ChatBot"

    state["next_step"] = next_action
    state["messages"] = chat_history
    return state

# ==============================
# 简历分析（修复：自动保存内容）
# ==============================
def resume_analyzer_node(state):
    llm = init_chat_model(state["config"])
    tools = [ResumeExtractorTool()]
    executor = create_agent_with_tools(llm, tools, get_analyzer_agent_prompt_template())

    state["callback"].write_agent_name("📄 简历分析器")
    result = executor.invoke({"messages": state["messages"]})
    state["messages"].append(AIMessage(content=result["output"], name="ResumeAnalyzer"))

    # 自动保存简历内容
    try:
        resume_content = ResumeExtractorTool().run("")
        state["resume_content"] = resume_content
    except:
        state["resume_content"] = ""

    if state.get("needs_followup"):
        state["task_completed"] = False
    else:
        state["task_completed"] = True
    return state

# ==============================
# 求职信生成（修复：自动读取简历）
# ==============================
def cover_letter_generator_node(state):
    llm = init_chat_model(state["config"])
    tools = [generate_letter_for_specific_job, save_cover_letter_for_specific_job, ResumeExtractorTool()]
    executor = create_agent_with_tools(llm, tools, get_generator_agent_prompt_template())

    # 自动把简历塞给AI
    resume_content = state.get("resume_content", "")
    if resume_content:
        state["messages"].append(HumanMessage(content=f"我的简历内容：\n{resume_content}"))

    state["callback"].write_agent_name("✉️ 求职信生成器")
    result = executor.invoke({"messages": state["messages"]})
    state["messages"].append(AIMessage(content=result["output"], name="CoverLetterGenerator"))
    state["task_completed"] = True
    return state

# ==============================
# 基础聊天
# ==============================
def chatbot_node(state):
    llm = init_chat_model(state["config"])
    state["callback"].write_agent_name("🤖 智能助手")
    finish_chain = get_finish_chain(llm)
    output = finish_chain.invoke({"messages": state["messages"]})
    state["messages"].append(AIMessage(content=output.content, name="ChatBot"))
    state["task_completed"] = True
    return state

# ==========================================
# 最终最简工作流：无报错、稳定运行
# ==========================================
def define_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("Supervisor", supervisor_node)
    workflow.add_node("ResumeAnalyzer", resume_analyzer_node)
    workflow.add_node("CoverLetterGenerator", cover_letter_generator_node)
    workflow.add_node("ChatBot", chatbot_node)

    workflow.set_entry_point("Supervisor")

    workflow.add_conditional_edges(
        "Supervisor",
        lambda x: x["next_step"],
        {
            "ResumeAnalyzer": "ResumeAnalyzer",
            "CoverLetterGenerator": "CoverLetterGenerator",
            "ChatBot": "ChatBot",
            "Finish": END
        }
    )

    workflow.add_edge("ResumeAnalyzer", END)
    workflow.add_edge("CoverLetterGenerator", END)
    workflow.add_edge("ChatBot", END)

    return workflow.compile()