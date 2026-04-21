from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image
import numpy as np
import json

# Load CLIP model (free)
model = SentenceTransformer('clip-ViT-B-32')


# 🔹 Generate Text Embedding (Description + Location)
def generate_text_embedding(description, location):
    combined = f"{description}. Location: {location}"
    embedding = model.encode(combined)
    return embedding.tolist()


# 🔹 Generate Image Embedding
def generate_image_embedding(image_path):
    image = Image.open(image_path).convert("RGB")
    embedding = model.encode(image)
    return embedding.tolist()


# 🔹 Cosine Similarity
def cosine_sim(emb1, emb2):
    emb1 = np.array(emb1).reshape(1, -1)
    emb2 = np.array(emb2).reshape(1, -1)
    return cosine_similarity(emb1, emb2)[0][0]


# 🔹 Final Multi-Modal Score
def final_similarity(lost_text_emb, found_text_emb,
                     lost_img_emb=None, found_img_emb=None):

    text_score = cosine_sim(lost_text_emb, found_text_emb)

    # Default image score
    image_score = 0

    if lost_img_emb is not None and found_img_emb is not None:
        image_score = cosine_sim(lost_img_emb, found_img_emb)

    # 70% text + 30% image
    final_score = (0.7 * text_score) + (0.3 * image_score)

    return final_score