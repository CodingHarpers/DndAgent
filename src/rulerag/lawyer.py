import os
import json
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from ingestPipeline import UnifiedDndLoader
from langchain_openai import OpenAIEmbeddings
import dotenv
dotenv.load_dotenv()

class RulesLawyer:
    def __init__(self):
        # Configuration
        self.persist_dir = "data/rules/chromaDB"
        self.kb_path = "data/rules/kb"
        
        # Initialize Embeddings
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        # Initialize VectorStore
        # Check if DB exists and is populated
        if os.path.exists(self.persist_dir) and os.listdir(self.persist_dir):
            print(f"Loading existing vector store from {self.persist_dir}...")
            self.vectorstore = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings
            )
        else:
            print(f"Regenerating vector store from {self.kb_path}...")
            # Ensure directory exists
            if not os.path.exists(self.persist_dir):
                os.makedirs(self.persist_dir, exist_ok=True)
                
            loader = UnifiedDndLoader(self.kb_path)
            ingested_docs = loader.load()
            # split the documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=300,  # 每个切片约 300 字符
                chunk_overlap=100 # 重叠 100 字符防止上下文丢失
            )
            # 使用 split_documents 而不是直接用 ingested_docs
            ingested_docs = text_splitter.split_documents(ingested_docs)
            print("starting to build vector store")
            self.vectorstore = Chroma.from_documents(
                documents=ingested_docs,
                embedding=self.embeddings,
                persist_directory=self.persist_dir
            )
            print("vector store built")
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 10})
        print("retriever initialized")
        # Define Prompt 
        template = """You are the **Dungeon Master's Intelligent Rule Assistant**.
Your goal is to function as a real-time "Rule Knowledge Base," interpreting the input scenario based strictly on the provided RULES and DOCUMENTS to guide the DM's next steps.

### 1. RETRIEVED DOCUMENTS (Context & Definitions)
{context}

### 2. ACTIVE RULES (Logic & Mechanics)
{rules}

### 3. DM'S QUERY / SCENARIO
{question}

### ADJUDICATION PROTOCOL
1. **Analyze Triggers**: Check if the scenario matches the `Trigger` and `Condition` in the ACTIVE RULES.
2. **Resolve Conflicts**: If a specific Entity Rule (e.g., a specific spell effect) contradicts a General Rule Section (e.g., general combat rules), the **Entity Rule overrides** (Specific Beats General).
3. **Formulate Guidance**: Do not just state the rule. Tell the DM **exactly what mechanics to invoke** (e.g., "Ask for a DC 15 Dex Save").

### OUTPUT FORMAT (Strictly follow this structure)
**Rule Interpretation:**
(Briefly explain the applicable rule logic based on the situation. Cite the source.)

**DM Action Items:**
(A clear checklist of what the DM needs to do *right now*.)
* [Check/Save]: e.g., "Ask player to roll Strength (Athletics) check vs DC X."
* [Calculation]: e.g., "Apply 8d6 Fire damage (half on success)."
* [Status Effect]: e.g., "Mark target as 'Prone' if check fails."

**Logic Trace:**
(Show the IF/THEN logic chain used. E.g., "Logic Trace: IF Creature is trying to Hide -> THEN Contest (Stealth vs Perception). IF Obstacle covers 50% of body -> THEN Target has Half Cover.")

Answer:"""

        self.prompt = ChatPromptTemplate.from_template(template)
        
        # Initialize LLM
        # Using gemini-1.5-flash as the currently available flash model
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        
        # Build Chain
        self.chain = (
            {
                "retrieved_data": self.retriever | self.split_retrieved_data, # Retrieve and split
                "question": RunnablePassthrough()
            }
            | RunnablePassthrough.assign(
                context=lambda x: x["retrieved_data"]["context"],
                rules=lambda x: x["retrieved_data"]["rules"]
            )
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    @staticmethod
    def split_retrieved_data(docs):
        """
        Input: List[Document]
        Output: Dict {"context": str, "rules": str}
        """
        # Drop duplicates based on page_content
        unique_docs = []
        seen_content = set()
        for d in docs:
            if d.page_content not in seen_content:
                unique_docs.append(d)
                seen_content.add(d.page_content)
        docs = unique_docs

        context_parts = []
        rules_parts = []
        with open("docs.txt", "w") as f:
            for d in docs:
                f.write(str(d))
                f.write("\n\n")
                f.write("--------------------------------")
                f.write("\n\n")
 
        for d in docs:
            try:
                # Restore original JSON from metadata
                data = json.loads(d.metadata['original_json'])
                doc_type = d.metadata['type']
                with open("docs.txt", "a") as f:
                    f.write(str(d))
                    f.write("\n\n")
                    f.write("--------------------------------")
                    f.write("\n\n")
                
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
        with open("context_parts.txt", "w") as f:
            f.write("\n\n".join(context_parts))
        with open("rules_parts.txt", "w") as f:
            f.write("\n".join(rules_parts))

        return {
            "context": "\n\n".join(context_parts),
            "rules": "\n".join(rules_parts)
        }

    def check_rule(self, question):
        """
        Applies strict logic to determine the outcome.
        query: str
        """
        return self.chain.invoke(question)

if __name__ == "__main__":
    print("Initializing RulesLawyer...")
    lawyer = RulesLawyer()
    print("Adjudicating...")
    result = lawyer.check_rule("The player is casting a spell and the target is immune to the spell.")
    print("Result:")
    print(result)
    with open("result.txt", "w") as f:
        f.write(result)
