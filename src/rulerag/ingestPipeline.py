import json
from pathlib import Path
from typing import List, Dict
from langchain_core.documents import Document

class UnifiedDndLoader:
    def __init__(self, kb_directory: str):
        self.kb_path = Path(kb_directory)

    # ... (_format_mechanics_for_search remains unchanged) ...
    def _format_mechanics_for_search(self, mechanics: List[Dict]) -> str:
        lines = []
        for m in mechanics:
            trigger = m.get('trigger', '')
            condition = m.get('condition', '')
            outcome = m.get('outcome', '')
            lines.append(f"Logic: IF {condition} ({trigger}) THEN {outcome}")
            terms = m.get('related_search_terms', [])
            if terms:
                lines.append(f"Keywords: {', '.join(terms)}")
        return "\n".join(lines)

    # ... (_process_entity_or_class remains unchanged) ...
    def _process_entity_or_class(self, data: Dict, file_path: str) -> Document:
        name = data.get('entity_name') or data.get('class_name', 'Unknown')
        desc = data.get('description_text', '')
        mech_text = self._format_mechanics_for_search(data.get('mechanics', []))
        top_keywords = ", ".join(data.get('related_search_terms', []))
        
        content = (
            f"Name: {name}\n"
            f"Description: {desc}\n"
            f"--- Rules ---\n{mech_text}\n"
            f"Tags: {top_keywords}"
        )

        return Document(
            page_content=content,
            metadata={
                "source": str(file_path),
                "type": "entity_or_class",
                "original_json": json.dumps(data)
            }
        )

    # ... (_process_rule_chunk remains unchanged) ...
    def _process_rule_chunk(self, data: Dict, file_path: str) -> List[Document]:
        docs = []
        chapter = data.get('source_chapter', 'General')
        chunk_header = data.get('_chunk_header', '') # Extract header information
        
        for concept in data.get('extracted_concepts', []):
            c_name = concept.get('concept_name', '')
            c_def = concept.get('definition', '')
            r_logic = concept.get('rule_logic', {})
            premise = r_logic.get('premise', '')
            implication = r_logic.get('implication', '')
            r_desc = r_logic.get('description_text', '')
            is_exc = "Exception Rule" if r_logic.get('is_exception') else "Standard Rule"
            
            content = (
                f"Rule Concept: {c_name} ({chapter} - {chunk_header})\n"
                f"Type: {is_exc}\n"
                f"Definition: {c_def}\n"
                f"Description: {r_desc}\n"
                f"Logic: IF {premise} THEN {implication}"
            )
            
            docs.append(Document(
                page_content=content,
                metadata={
                    "source": str(file_path),
                    "type": "rule_concept",
                    "original_json": json.dumps(concept) # Store the JSON of a single Concept here
                }
            ))
        return docs

    # === [Core modifications here] ===
    def load(self) -> List[Document]:
        documents = []
        print(f"Scanning KB directory: {self.kb_path.absolute()}")
        
        for file_path in self.kb_path.rglob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                
                # 1. Normalize: Convert to list regardless of single object or array
                if isinstance(raw_data, list):
                    items_to_process = raw_data
                else:
                    items_to_process = [raw_data]

                # 2. Process each item in the list
                for item in items_to_process:
                    if not isinstance(item, dict):
                        print(f"[SKIP] {file_path.name}: Not a dictionary, skipping")
                        continue # Skip non-dictionary items

                    # Strategy routing
                    if "extracted_concepts" in item:
                        # Case 1: RuleBookChunk (ability-checks.json goes here)
                        new_docs = self._process_rule_chunk(item, file_path)
                        documents.extend(new_docs)
                        
                    elif "mechanics" in item:
                        # Case 2: Entity/Class (fireball.json goes here)
                        doc = self._process_entity_or_class(item, file_path)
                        documents.append(doc)
                        
                    else:
                        # Neither rule nor entity, possibly metadata file, skip without error
                        print(f"[SKIP] {file_path.name}: Neither rule nor entity, skipping")

            except Exception as e:
                print(f"[Error] Failed to load {file_path}: {e}")
                
        print(f"Successfully loaded {len(documents)} logic documents.")
        # print(documents[0])
        return documents

# Usage example
loader = UnifiedDndLoader("data/rules/kb")
all_docs = loader.load()