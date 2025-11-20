import json
from operator import itemgetter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 1. Prepare VectorStore (assuming docs are already loaded)
vectorstore = Chroma.from_documents(documents=ingested_docs, embedding=OpenAIEmbeddings())
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# 2. Core parsing function: Split retrieved results into Context and Rules
def split_retrieved_data(docs):
    """
    Input: List[Document]
    Output: Dict {"context": str, "rules": str}
    """
    context_parts = []
    rules_parts = []
    
    for d in docs:
        try:
            # Restore original JSON from metadata
            data = json.loads(d.metadata['original_json'])
            doc_type = d.metadata['type']
            
            if doc_type == "entity_or_class":
                name = data.get('entity_name') or data.get('class_name')
                
                # A. Extract Context (Raw Text)
                text = data.get('description_text', '')
                context_parts.append(f"--- Document: {name} ---\n{text}")
                
                # B. Extract Rules (Logic)
                for m in data.get('mechanics', []):
                    rule_str = (
                        f"[{name}] "
                        f"IF {m.get('condition')} (Trigger: {m.get('trigger')}) "
                        f"THEN {m.get('outcome')}"
                    )
                    rules_parts.append(rule_str)
                    
            elif doc_type == "rule_concept":
                name = data.get('concept_name')
                
                # A. Extract Context
                # Note: RuleBookChunk's description_text is inside rule_logic
                r_logic = data.get('rule_logic', {})
                text = r_logic.get('description_text', '')
                context_parts.append(f"--- Rule Section: {name} ---\n{text}")
                
                # B. Extract Rules
                premise = r_logic.get('premise', '')
                implication = r_logic.get('implication', '')
                priority = "[EXCEPTION] " if r_logic.get('is_exception') else ""
                
                rule_str = f"{priority}[{name}] IF {premise} THEN {implication}"
                rules_parts.append(rule_str)
                
        except Exception as e:
            print(f"Error parsing doc metadata: {e}")
            continue
            
    return {
        "context": "\n\n".join(context_parts),
        "rules": "\n".join(rules_parts)
    }

# 3. Define Prompt 
template = """You are the Dungeon Master's Logic Engine.

### 1. RETRIEVED DOCUMENTS (Context Reference)
{context}

### 2. ACTIVE RULES (Logic Guidelines)
{rules}

### 3. USER QUERY
{question}

### ADJUDICATION PROTOCOL
1. **Priority**: Use 'ACTIVE RULES' for step-by-step logic. Use 'RETRIEVED DOCUMENTS' for definitions and edge cases.
2. **Conflict**: Specific Entity Rules override General Rule Sections.
3. **Output**: Verdict (Yes/No) followed by reasoning citing the specific rule used.

Adjudication:"""

prompt = ChatPromptTemplate.from_template(template)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 4. Build Chain
# Flow: Query -> Retriever -> split_retrieved_data -> Prompt -> LLM
rulerag_chain = (
    {
        "retrieved_data": retriever | split_retrieved_data, # Retrieve and split
        "question": RunnablePassthrough()
    }
    | RunnablePassthrough.assign(
        context=lambda x: x["retrieved_data"]["context"],
        rules=lambda x: x["retrieved_data"]["rules"]
    )
    | prompt
    | llm
    | StrOutputParser()
)











class RulesLawyer:
    def adjudicate(self, action_intent, rule_json, die_roll):
        """
        Applies strict logic to determine the outcome.
        Does NOT generate flavor text.
        """
        # Placeholder implementation
        if die_roll >= rule_json.get('difficulty_class', 10):
            return {"outcome": "success", "effect": rule_json.get('success_outcome')}
        return {"outcome": "failure"}
