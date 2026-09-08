import os
import json
import numpy as np
import datetime
from pathlib import Path

# OpenVINO Optimum integration for embeddings
try:
    from optimum.intel.openvino import OVModelForFeatureExtraction
    from transformers import AutoTokenizer
    import faiss
    import torch
    import torch.nn.functional as F
    OPENVINO_MEMORY_AVAILABLE = True
except ImportError:
    OPENVINO_MEMORY_AVAILABLE = False

MEMORY_DIR = Path("memory_data")
FAISS_INDEX_PATH = MEMORY_DIR / "faiss.index"
METADATA_PATH = MEMORY_DIR / "metadata.json"
PROFILE_PATH = MEMORY_DIR / "user_profile.json"

class KiraMemory:
    def __init__(self, model_id="sentence-transformers/all-MiniLM-L6-v2"):
        self.available = False
        if not OPENVINO_MEMORY_AVAILABLE:
            print("[WARN] Optimum, Transformers, PyTorch, or FAISS not found. RAG memory will be disabled.")
            return
            
        MEMORY_DIR.mkdir(exist_ok=True)
        
        self.model_id = model_id
        self.tokenizer = None
        self.model = None
        self.index = None
        self.metadata = []
        
        self.profile = {"preferences": [], "frequent_tasks": {}, "app_patterns": {}}
        self._load_profile()
        
        try:
            print("[MEMORY] Loading OpenVINO embedding model (all-MiniLM-L6-v2)...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            # export=True converts the model to OpenVINO IR on the fly if not already cached
            self.model = OVModelForFeatureExtraction.from_pretrained(self.model_id, export=True)
            
            self.dim = 384  # Dimension for all-MiniLM-L6-v2
            self._load_index()
            self.available = True
            print("[MEMORY] Initialized successfully.")
        except Exception as e:
            print(f"[WARN] Failed to load memory model: {e}")

    def _load_profile(self):
        if PROFILE_PATH.exists():
            try:
                with open(PROFILE_PATH, "r") as f:
                    self.profile = json.load(f)
            except Exception:
                pass

    def save_profile(self):
        with open(PROFILE_PATH, "w") as f:
            json.dump(self.profile, f, indent=2)

    def _load_index(self):
        if FAISS_INDEX_PATH.exists() and METADATA_PATH.exists():
            self.index = faiss.read_index(str(FAISS_INDEX_PATH))
            with open(METADATA_PATH, "r") as f:
                self.metadata = json.load(f)
        else:
            self.index = faiss.IndexFlatL2(self.dim)
            self.metadata = []

    def _save_index(self):
        if self.index is not None:
            faiss.write_index(self.index, str(FAISS_INDEX_PATH))
            with open(METADATA_PATH, "w") as f:
                json.dump(self.metadata, f)

    def get_embedding(self, text: str) -> np.ndarray:
        if not self.available:
            return np.zeros((1, self.dim), dtype=np.float32)
            
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        outputs = self.model(**inputs)
        
        attention_mask = inputs['attention_mask']
        token_embeddings = outputs.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        
        # Mean Pooling
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        embeddings = sum_embeddings / sum_mask
        
        # L2 Normalize
        embeddings = F.normalize(embeddings, p=2, dim=1)
        return embeddings.detach().numpy().astype(np.float32)

    def store_memory(self, text: str, source: str = "conversation", intent: str = None):
        """Store a memory into the FAISS index with an optional intent tag."""
        if not self.available:
            return
        
        emb = self.get_embedding(text)
        self.index.add(emb)
        
        meta = {
            "id": len(self.metadata),
            "text": text,
            "source": source,
            "intent": intent,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.metadata.append(meta)
        self._save_index()
        
        if intent:
            self.profile["frequent_tasks"][intent] = self.profile["frequent_tasks"].get(intent, 0) + 1
            self.save_profile()

    def retrieve(self, query: str, top_k: int = 3) -> list:
        """Retrieve the top_k most relevant memories for a given query."""
        if not self.available or self.index.ntotal == 0:
            return []
            
        emb = self.get_embedding(query)
        # Search returns squared L2 distances
        distances, indices = self.index.search(emb, min(top_k, self.index.ntotal))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(self.metadata):
                res = dict(self.metadata[idx])
                res["score"] = float(dist)
                results.append(res)
        return results

    def store_agentic_outcome(self, goal: str, steps: list, success: bool):
        """Phase 4: Store execution outcomes as workflow macros."""
        status = "Success" if success else "Failed"
        text = f"Goal: {goal} | Status: {status} | Steps executed: {len(steps)}"
        
        serialized_steps = []
        for s in steps:
            serialized_steps.append({
                "action": getattr(s, "action", ""),
                "target": getattr(s, "target", ""),
                "value": getattr(s, "value", "")
            })
            
        if not self.available:
            return
            
        emb = self.get_embedding(goal)
        self.index.add(emb)
        
        meta = {
            "id": len(self.metadata),
            "text": text,
            "source": "workflow_macro",
            "intent": goal,
            "steps": serialized_steps,
            "success": success,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.metadata.append(meta)
        self._save_index()
        
        if success:
            self.profile["frequent_tasks"][goal] = self.profile["frequent_tasks"].get(goal, 0) + 1
            self.save_profile()

    def retrieve_workflow(self, goal: str, threshold: float = 0.5) -> list:
        """Find a highly similar successful past workflow."""
        if not self.available or self.index.ntotal == 0:
            return None
            
        emb = self.get_embedding(goal)
        distances, indices = self.index.search(emb, min(5, self.index.ntotal))
        
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(self.metadata):
                res = self.metadata[idx]
                if res.get("source") == "workflow_macro" and res.get("success") and dist < threshold:
                    return res.get("steps")
        return None

# Singleton export
memory_store = KiraMemory()
