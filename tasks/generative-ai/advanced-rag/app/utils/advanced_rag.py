import re
import yaml
import logging
import asyncio
from typing import Dict, TypedDict

import langchain
from langchain_core.messages import BaseMessage
from langchain_aws import AmazonKendraRetriever
from langchain_aws import ChatBedrock
from langchain_core.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.output_parsers import (
    StrOutputParser,
    PydanticOutputParser,
)
from langchain_core.pydantic_v1 import (
    BaseModel,
    Field,
)
from langgraph.graph import END, StateGraph

#import settings

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)
#langchain.verbose = settings.VERBOSE
#index_id = settings.KENDRA_INDEX_ID


def load_templates(file_path):
    """ Load templates from a YAML file.

    Args:
        file_path (str): The path to the YAML file containing the prompt templates.

    Returns:
        dict: A dictionary containing the loaded templates.
    """
    with open(file_path, "r") as f:
        return yaml.safe_load(f)

templates = load_templates("prompt_templates.yaml")


class GraphState(TypedDict):
    """Represents the state of our graph.

    Attributes:
        keys: A dictionary where each key is a string.
    """
    keys: Dict[str, any]


def entry_point(state):
    """Pass through"""
    return state


def decide_to_generate_queries(state):
    """
    Determines whether to generate queries, or use the original query.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    logger.debug("---DECIDE TO GENERATE QUERIES---")
    n_queries = state["keys"]["n_queries"]

    if n_queries > 0:
        logger.debug(
            "---DECISION: GENERATE QUERIES---"
        )
        return "generate_queries_enabled"
    else:
        logger.debug("---DECISION: NOT GENERATE QUERIES---")
        return "generate_queries_not_enabled"


def generate_queries(state):
    """Generate a variety of queries (RAG-Fusion).

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): The updated graph state with generated queries.
    """
    logger.debug("---GENERATE QUERIES---")
    state_dict = state["keys"]
    question = state_dict["question"]
    n_queries = state_dict["n_queries"]
    settings = state_dict["settings"]

    llm = ChatBedrock(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        region_name=settings["aws_region"],
        model_kwargs={
            "temperature": 0,
            "max_tokens": 512,
        }
    )

    output_format = ""
    for i in range(n_queries):
        output_format += f"{i+1}: fill a query here\n"
    
    prompt_template = templates["generate_queries"].format(
        output_format=output_format,
        n_queries=n_queries,
        question="{question}",  # as-is
    )
    prompt = ChatPromptTemplate.from_template(prompt_template)

    chain = prompt | llm | StrOutputParser() | (lambda x: x.split("\n"))
    queries = chain.invoke({"question": question})
    queries = [query.replace('"', '') for query in queries]
    queries = [query for query in queries if re.match(r'^\d+:[^:]+$', query)]  # 数字:文字列の項目のみ抽出
    queries = [f"0: {question}"] + queries
    logger.debug("queries:")
    logger.debug(queries)

    state_dict["queries"] = queries

    return {"keys": state_dict}


def retrieve(state):
    """Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    logger.debug("---RETRIEVE---")
    state_dict = state["keys"]
    question = state_dict["question"]
    settings = state_dict["settings"]

    retriever = AmazonKendraRetriever(
        index_id=settings["kendra_index_id"],
        region_name=settings["aws_region"],
        attribute_filter={"EqualsTo": {"Key": "_language_code", "Value": {"StringValue": "ja"}}},
        top_k=10,
    )

    documents = []
    if "queries" in state_dict:
        # with query expansion
        queries = state_dict["queries"]

        async def retrieve_documents(retriever, queries):
            async def async_invoke(query):
                return await retriever.ainvoke(query)
            tasks = [async_invoke(query) for query in queries]
            results = await asyncio.gather(*tasks)

            unique_excerpts = set()
            unique_documents = []
            for result in results:
                for document in result:
                    excerpt = document.metadata["excerpt"]
                    if excerpt not in unique_excerpts:
                        unique_excerpts.add(excerpt)
                        unique_documents.append(document)
            return unique_documents

        documents = asyncio.run(retrieve_documents(retriever, queries))
    else:
        # without query expansion
        documents = retriever.invoke(question)

    logger.debug(documents)

    state_dict["documents"] = documents
    return {"keys": state_dict}


def decide_to_grade_documents(state):
    """
    Determines whether to grade documents or not.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    logger.debug("---DECIDE TO GRADE DOCUMENTS---")
    grade_documents_enabled = state["keys"]["grade_documents_enabled"]

    if grade_documents_enabled == "Yes":
        logger.debug(
            "---DECISION: GRADE DOCUMENTS---"
        )
        return "grade_documents_enabled"
    else:
        logger.debug("---DECISION: NOT GRADE DOCUMENTS---")
        return "grade_documents_not_enabled"


def generate(state):
    """Generate documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    logger.debug("---GENERATE---")
    state_dict = state["keys"]
    question = state_dict["question"]
    documents = state_dict["documents"]
    settings = state_dict["settings"]

    llm = ChatBedrock(
        model_id=settings["generator_model_id"],
        region_name=settings["aws_region"],
        model_kwargs={
            "temperature": 0,
            "max_tokens": 1024,
        }
    )

    prompt = ChatPromptTemplate(
    input_variables=["context", "question"],
        messages=[
            HumanMessagePromptTemplate(
                prompt=PromptTemplate(
                    input_variables=["context", "question"],
                    template=templates["generate"],
                )
            )
        ]
    )

    rag_chain = prompt | llm | StrOutputParser()

    output = rag_chain.invoke({"context": documents, "question": question})
    generation = re.search(r'<answer>(.*?)</answer>', output, re.DOTALL).group(1)

    state_dict["generation"] = generation

    return {"keys": state_dict}


def grade_documents(state):
    """Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with relevant documents
    """

    logger.debug("---CHECK RELEVANCE---")
    state_dict = state["keys"]
    question = state_dict["question"]
    documents = state_dict["documents"]
    settings = state_dict["settings"]

    # Data model
    class grade(BaseModel):
        """Binary score for relevance check."""
        binary_score: str = Field(description="Relevance score 'yes' or 'no'")

    # LLM
    llm = ChatBedrock(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        region_name=settings["aws_region"],
        model_kwargs={
            "temperature": 0,
            "max_tokens": 128,
        }
    )

    parser = PydanticOutputParser(pydantic_object=grade)

    prompt = PromptTemplate(
        template=templates["grade_documents"], 
        input_variables=["context", "question"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | llm | parser

    async def filter_documents(documents, question, chain):
        async def async_invoke(doc):
            score = await chain.ainvoke({"question": question, "context": doc.page_content})
            if score.binary_score == "yes":
                logger.debug("---GRADE: DOCUMENT RELEVANT---")
                return doc
            else:
                logger.debug("---GRADE: DOCUMENT NOT RELEVANT---")
                return None

        tasks = [async_invoke(doc) for doc in documents]
        results = await asyncio.gather(*tasks)
        filtered_docs = [doc for doc in results if doc is not None]
        return filtered_docs

    filtered_docs = asyncio.run(filter_documents(documents, question, chain))
    logger.debug(len(filtered_docs))
    logger.debug(filtered_docs)

    search = "Yes" if len(filtered_docs) == 0 else "No"

    state_dict["documents"] = filtered_docs
    state_dict["run_web_search"] = search

    return {"keys": state_dict}


def build_graph():
    workflow = StateGraph(GraphState)

    # ノードを追加
    workflow.add_node("entry_point", entry_point)
    workflow.add_node("generate_queries", generate_queries)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate", generate)

    # グラフのフローを定義
    workflow.set_entry_point("entry_point")
    workflow.add_conditional_edges(
        "entry_point",
        decide_to_generate_queries,
        {
            "generate_queries_enabled": "generate_queries",
            "generate_queries_not_enabled": "retrieve",
        },
    )
    workflow.add_edge("generate_queries", "retrieve")
    workflow.add_conditional_edges(
        "retrieve",
        decide_to_grade_documents,
        {
            "grade_documents_enabled": "grade_documents",
            "grade_documents_not_enabled": "generate",
        }
    )
    workflow.add_edge("grade_documents", "generate")
    workflow.add_edge("generate", END)

    # グラフのコンパイル
    app = workflow.compile()
    return app
