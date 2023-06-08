import faiss
import numpy as np
import json
from .device import Device
import os
from pathlib import Path

class VectorIndexedDB(Device):
    def __init__(self, embedding_backend, **kwargs):
        super().__init__(**kwargs)
        self.embedding_backend = embedding_backend
        self.index = faiss.IndexFlatL2(embedding_backend.dim)
        self.embeddings = []
        self.texts = []

    async def asyncAdd(self, text, caller):
        """
        Adds text to the database, which can be queried later.
        """
        embedding = await self.embedding_backend.asyncRequest(caller, text)
        embedding = np.array(embedding)[None]
        self.embeddings.append(embedding)
        self.texts.append(text)
        self.index.add(embedding)
        return f"Added a new item to {self.name}. "

    async def asyncQuery(self, query_text, k=1, caller=None):
        """
        Retrieve the top-k items most relevant to the query.
        """
        if len(self.texts) > 0:
            k = min(k, len(self.texts))
            embedding = await self.embedding_backend.asyncRequest(caller, query_text)
            embedding = np.array(embedding)[None]
            D, I = self.index.search(embedding, k=k)
            results = []
            for i in I[0]:
                results.append((D[0][i], self.texts[i]))
            return results
        return []

    async def asyncRemove(self, query, k=1, caller=None):
        """
        Find the item most similar the query and remove it.
        """
        embedding = await self.embedding_backend.asyncRequest(caller, query)
        embedding = np.array(embedding)[None]
        D, I = self.index.search(embedding, k=k)
        results = []
        for i in I[0]:
            sample = ' '.join(self.texts[i].split(' ')[:10])
            results.append(sample + '...')
        results = "\n====\n".join(results)
        self.index.remove_ids(I[0])
        self.embeddings = self.embeddings[:i] + self.embeddings[i+1:]
        self.texts = self.texts[:i] + self.texts[i+1:]
        return f'Removed the item "{results}..."'

    def add(self, text, caller):
        """
        Adds text to the database, which can be queried later.
        """
        embedding = self.embedding_backend.request(caller, text)
        embedding = np.array(embedding)[None]
        self.embeddings.append(embedding)
        self.texts.append(text)
        self.index.add(embedding)
        return f"Added a new item to {self.name}. "

    def query(self, query_text, k=1, caller=None):
        """
        Retrieve the top-k items most relevant to the query.
        """
        embedding = self.embedding_backend.request(caller, query_text)
        embedding = np.array(embedding)[None]
        D, I = self.index.search(embedding, k=k)
        results = []
        for i in I[0]:
            results.append(self.texts[i])
        results = "\n====\n".join(results)
        return f'Here are the top-{k} most relevant items, separated by "==========":\n' + results

    def remove(self, query, k=1, caller=None):
        """
        Find the item most similar the query and remove it.
        """
        embedding = self.embedding_backend.request(caller, query)
        embedding = np.array(embedding)[None]
        D, I = self.index.search(embedding, k=k)
        results = []
        for i in I[0]:
            sample = ' '.join(self.texts[i].split(' ')[:10])
            results.append(sample + '...')
        results = "\n====\n".join(results)
        self.index.remove_ids(I[0])
        self.embeddings = self.embeddings[:i] + self.embeddings[i+1:]
        self.texts = self.texts[:i] + self.texts[i+1:]
        return f'Removed the item "{results}..."'

    def save_(self):
        if len(self.texts) == 0:
            return
        path = Path(self.storage_dir)
        path.mkdir(parents=True, exist_ok=True)
        path = os.path.join(self.storage_dir, f'{self.name}.index')
        faiss.write_index(self.index, path)
        embeddings = np.stack(self.embeddings, axis=0)
        path = os.path.join(self.storage_dir, f'{self.name}.npy')
        np.save(path, embeddings)
        path = os.path.join(self.storage_dir, f'{self.name}.json')
        with open(path, "w") as f:
            json.dump(self.texts, f)

    def load_(self):
        path = os.path.join(self.storage_dir, f'{self.name}.index')
        if os.path.isfile(path):
            self.index = faiss.read_index(path)
            path = os.path.join(self.storage_dir, f'{self.name}.npy')
            embeddings = np.load(path)
            self.embeddings = [item for item in embeddings]
            path = os.path.join(self.storage_dir, f'{self.name}.json')
            with open(path) as f:
                self.texts = json.load(f)

class SkillLibrary(VectorIndexedDB):
    def __init__(self, embedding_backend, storage_dir, name='skills', prompt=
"""
A database storing your skills. 
A skill is a function writen in natural language, pseudocode or programming language.
A skill may employ other skills to achieve its subgoals.
To define a skill, specify the informations it requires and the conclusion it provides.
For example, here is a skill:


Skill: Make dumplings at home

Potentially useful information: 
Desired number of dumplings
Flour quantity
Availability of ingredients

Output:
If ingradients are not enough, break and enumerate the ingredients needed.
Otherwise, no output is needed.

Make a dumpling dough

For the dumpling filling:
1 cup ground meat (pork, chicken, or beef)
1 cup finely chopped vegetables (cabbage, carrots, mushrooms, etc.)

For each dumpling:
    Divide dough, roll each portion into a thin circle.
    Place a spoonful of filling in the center of each dough circle. 
    Fold and seal the edges.

Employ cooking skills such as steaming or boiling.


Call `skills.query(context)` to retrieve top-k pertinent skills to achieve your goals.
If there is a skill you find useful,
concatenate relevant information with the skill description and call `Do(information + skill)` to employ the skill.

Through your experience, you may acquire new skills or enhance existing ones.
Call `skills.add(skill)` to append a skill to your skill library. 
"""):
        super().__init__(embedding_backend, storage_dir=storage_dir, name=name, prompt=prompt)

class LongtermMemory(VectorIndexedDB):
    def __init__(self, embedding_backend, storage_dir, name='note', prompt=
"""
A database which you can use as a note or a memo. 
Your short-term memory (context window size) is limited.
It can only retain a few thousand words.
Preserve important events and facts by recording them in the note. 
Use `note.add(text)` to append text to the note. 
Use `note.query(text, k)` to retrieve top-k pertinent information from your stored texts.
"""):
        super().__init__(embedding_backend, storage_dir=storage_dir, name=name, prompt=prompt)