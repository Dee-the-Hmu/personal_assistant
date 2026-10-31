import os 

from dotenv import load_dotenv 

# StateGraph = object used to construct a LangGraph workflow.
# START and END = special markers representing where graph execution begins/ends.
# MessagesState is LangGraph's built-in state designed for conversations.
# It contains a "messages" list and knows how to append new messages rather than replacing the entire conversation history.
from langgraph.graph import StateGraph, START, END, MessagesState

# TypedDict lets us describe the structure of the state flowing through the graph.
from typing import TypedDict # describe what keys and value types a Python dictionary should have.

# InMemorySaver = LangGraph checkpointer that stores graph state in memory.
# This lets different calls using the same thread_id remember previous messages.
from langgraph.checkpoint.memory import InMemorySaver


# HumanMessage represents user input in LangChain's message format.
from langchain_core.messages import HumanMessage

# LangChain's Gemini integration.
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()

# # STATE
# # -----
# # This is the data that moves through our graph. (just a Python Dict)
# class AssistantState(TypedDict):
#     user_input : str
#     response : str

# MODEL
# -----
# Gemini is the LLM used by our agent node. keep model creation here instead of inside our voice code
model = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

# NODE 
# ------
# a node = a function LangGraph Executes 
async def agent_node(state: MessagesState):
    # state["messages"] contains the conversation so far:
    # [
    #     HumanMessage(...),
    #     AIMessage(...),
    #     HumanMessage(...),
    #     ...
    # ]
    # We send the entire current conversation state to Gemini.

    # sends the user transcript to Gemini
    result = await model.ainvoke(state["messages"])

    # a node returns a dict --> tells LangGraph which parts of the state it needs to update
    return {
        "messages" : [result]
    }


# Graph Construction 
# -----
# Tell LangGraph what our state looks like
builder = StateGraph(MessagesState)

# Register our function as a node named "agent"
builder.add_node("agent", agent_node)

# Edge:
# when the graph START → run the agent node
builder.add_edge(START, "agent")


# Edge:
# when the agent finishes → END the graph
builder.add_edge("agent", END)

# A checkpointer saves = graph state between separate graph invocations.
# InMemorySaver stores it only in this running Python process.
# If the backend restarts, this memory disappears.
checkpointer = InMemorySaver()

# compile() turns the graph definition into something executable.
# Compile the graph with persistence/checkpoint support.
assistant_graph = builder.compile(
    checkpointer=checkpointer
)



# Public Interface (the rest of our backend calls this function)
# main.py don't need to know about LangGraph nodes, Gemini LLM 
async def run_assistant(user_input: str, thread_id : str,) -> str: 

    # HumanMessage explicitly identifies this text as coming from the user.
    user_message = HumanMessage(content=user_input)

    # `config` is metadata/configuration passed to LangGraph.
    #
    # configurable.thread_id tells the checkpointer: "Which conversation does this invocation belong to?"
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    # Give LangGraph only the new message
    #
    # We don't manually send old messages here.
    # The checkpointer restores the previous state for this thread
    # and MessagesState appends this new message.
    final_state = await assistant_graph.ainvoke(
        {
            "messages": [user_message]
        },
        config=config,
    )

    # Get the newest response
    # [-1] means the LAST item in the messages list.
    #
    assistant_message = final_state["messages"][-1]

    # `.text` gives us normalized plain text from the AIMessage,
    # instead of Gemini-specific content blocks.
    return assistant_message.text


async def stream_assistant(user_input: str, thread_id: str):

    # HumanMessage explicitly identifies this text as coming from the user.
    user_message = HumanMessage(user_input)

    # `config` is metadata/configuration passed to LangGraph.
    #
    # configurable.thread_id tells the checkpointer: "Which conversation does this invocation belong to?"
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    # astream() runs the graph but STREAMS events/results while it executes.
    #
    # stream_mode="messages" asks LangGraph to stream LLM message chunks
    # instead of waiting for the entire graph invocation to finish.
    async for message_chunk, metadata in assistant_graph.astream(
        {
            "messages": [user_message]
        },
        config=config,
        stream_mode="messages",
    ):

        # LangGraph may stream messages from different parts of the graph.
        # Our graph currently has only one LLM node, but keeping this check
        # makes the boundary clearer as the graph grows later.
        if metadata.get("langgraph_node") != "agent":
            continue

        text = message_chunk.text

        # Some streaming events may contain no visible text.
        if not text:
            continue

        # `yield` returns THIS piece of text to the caller,
        # but unlike `return`, the function does NOT finish.
        #
        # The next LLM chunk can later be yielded too.
        yield text










