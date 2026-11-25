import re
from pathlib import Path

import numpy as np

from ..config import Config
from .primitives import FIGHT_ACTIONS, PRIMITIVES, home_frame

MODEL_NAME = Config.MODEL_NAME
HUGGINGFACE_URL = "https://huggingface.co/google/videoprism-lvt-base-f16r288"
WEIGHTS_NAME = "flax_lvt_base_f16r288_repeated.npz"
TOKENIZER_NAME = "c4_en_sentencepiece.model"
# The text encoder was trained on video captions, so a motion request is
# phrased the same way as the checkpoint's own examples.
TEXT_PREFIX = "a video of "
LOW_CONFIDENCE = 0.82

_model = None
_tokenizer = None
_embed_fn = None
_video_fn = None
_primitive_vectors = None
_fight_vectors = None
CLIP_FRAMES = 8
CLIP_SIZE = 288

_CLAUSE_SPLIT = re.compile(
    r",?\s*\b(?:and then|after that|afterwards|and|then|next)\b\s*",
    re.IGNORECASE,
)


def model_dir(cache_dir):
    return Path(cache_dir) / "videoprism-lvt-base-f16r288"


def split_clauses(prompt):
    parts = []
    for piece in _CLAUSE_SPLIT.split(prompt):
        cleaned = piece.strip(" .;")
        if cleaned:
            parts.append(cleaned)
    return parts or [prompt.strip()]


def cosine(left, right):
    left = np.asarray(left, dtype=np.float32)
    right = np.asarray(right, dtype=np.float32)
    denom = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denom == 0:
        return 0.0
    return float(np.dot(left, right) / denom)


def load_model(cache_dir, local_only=True):
    global _model, _tokenizer, _embed_fn, _video_fn
    if _embed_fn is not None:
        return _model

    weights = model_dir(cache_dir) / WEIGHTS_NAME
    vocab = model_dir(cache_dir) / TOKENIZER_NAME
    if not weights.is_file() or not vocab.is_file():
        raise RuntimeError(
            "VideoPrism files are missing. Run python download_model.py."
        )

    import os

    os.environ.setdefault("JAX_PLATFORMS", "cpu")
    import jax
    from videoprism import models as vp
    from videoprism.tokenizers import SentencePieceTokenizer

    flax_model = vp.get_model(MODEL_NAME)
    state = vp.load_pretrained_weights(None, checkpoint_path=str(weights))
    _tokenizer = SentencePieceTokenizer(str(vocab))

    def embed_fn(token_ids, paddings):
        _video, text_embeddings, _extra = flax_model.apply(
            state,
            None,
            token_ids,
            paddings,
            train=False,
        )
        return text_embeddings

    def video_fn(clip):
        video_embeddings, _text, _extra = flax_model.apply(
            state,
            clip,
            None,
            None,
            train=False,
        )
        return video_embeddings

    _embed_fn = jax.jit(embed_fn)
    _video_fn = jax.jit(video_fn)
    _model = flax_model
    # Embed both catalogs once. The video encoder is compiled here so the
    # first webcam clip does not pay the compile cost.
    primitive_vectors(embed_texts)
    fight_vectors(embed_texts)
    import jax.numpy as jnp

    _video_fn(jnp.zeros((1, CLIP_FRAMES, CLIP_SIZE, CLIP_SIZE, 3), dtype=jnp.float32))
    return _model


def embed_texts(texts):
    if _embed_fn is None or _tokenizer is None:
        raise RuntimeError(
            "VideoPrism is not loaded. Run python download_model.py."
        )
    from videoprism import models as vp

    captions = [f"{TEXT_PREFIX}{text.strip().rstrip('.')}" for text in texts]
    token_ids, paddings = vp.tokenize_texts(_tokenizer, captions)
    embeddings = np.asarray(_embed_fn(token_ids, paddings), dtype=np.float32)
    return [row for row in embeddings]


def primitive_vectors(embedder):
    global _primitive_vectors
    if _primitive_vectors is None:
        _primitive_vectors = embedder([item["description"] for item in PRIMITIVES])
    return _primitive_vectors


def embed_video(clip):
    if _video_fn is None:
        raise RuntimeError(
            "VideoPrism is not loaded. Run python download_model.py."
        )
    import jax.numpy as jnp

    batch = jnp.asarray(np.asarray(clip, dtype=np.float32)[None, ...])
    embedding = np.asarray(_video_fn(batch), dtype=np.float32)
    return embedding[0]


def fight_vectors(embedder):
    global _fight_vectors
    if _fight_vectors is None:
        _fight_vectors = embedder([item["description"] for item in FIGHT_ACTIONS])
    return _fight_vectors


def decode_clip(payloads):
    """Turn webcam JPEG data-URLs into a float clip shaped (8, 288, 288, 3)."""
    import base64
    import io

    from PIL import Image

    if not isinstance(payloads, list) or not 4 <= len(payloads) <= 16:
        raise ValueError("Send between 4 and 16 camera frames")
    images = []
    for item in payloads:
        if not isinstance(item, str) or len(item) > 400_000:
            raise ValueError("A camera frame was empty or too large")
        raw = item.split(",", 1)[-1]
        try:
            blob = base64.b64decode(raw, validate=True)
            image = Image.open(io.BytesIO(blob)).convert("RGB")
        except Exception as exc:
            raise ValueError("A camera frame could not be read") from exc
        image = image.resize((CLIP_SIZE, CLIP_SIZE), Image.BILINEAR)
        images.append(np.asarray(image, dtype=np.float32) / 255.0)
    indexes = np.linspace(0, len(images) - 1, CLIP_FRAMES).round().astype(int)
    return np.stack([images[int(index)] for index in indexes], axis=0)


def mimic_motion(clip, video_embedder=None, text_embedder=None):
    """Match a webcam clip to a fight move using both VideoPrism encoders."""
    text_embedder = text_embedder or embed_texts
    video_embedder = video_embedder or embed_video
    if text_embedder is embed_texts:
        vectors = fight_vectors(text_embedder)
    else:
        vectors = text_embedder([item["description"] for item in FIGHT_ACTIONS])
    query = np.asarray(video_embedder(clip), dtype=np.float32)
    scored = sorted(
        (
            (cosine(query, vector), action)
            for action, vector in zip(FIGHT_ACTIONS, vectors)
        ),
        key=lambda item: item[0],
        reverse=True,
    )
    best_score, best = scored[0]
    second = scored[1][0]
    low_confidence = best_score < 0.12 or (best_score - second) < 0.015
    match = {
        "clause": "webcam clip",
        "primitive_id": best["id"],
        "title": best["title"],
        "score": round(best_score, 4),
        "low_confidence": low_confidence,
        "alternatives": [
            {
                "id": action["id"],
                "title": action["title"],
                "score": round(score, 4),
            }
            for score, action in scored[1:4]
        ],
    }
    frames = [home_frame(200, "Start at home")]
    frames.extend(frame.copy() for frame in best["frames"])
    if low_confidence:
        summary = (
            f"VideoPrism was not sure. Closest move is {best['title'].lower()} "
            f"(score {best_score:.2f}). Try a bigger, slower motion."
        )
    else:
        summary = (
            f"VideoPrism watched the clip and called it a {best['title'].lower()} "
            f"(score {best_score:.2f})."
        )
    return {
        "prompt": f"webcam: {best['id']}",
        "summary": summary,
        "model": {
            "name": MODEL_NAME,
            "huggingface_url": HUGGINGFACE_URL,
            "weights": WEIGHTS_NAME,
            "runtime": "local",
            "encoder": "video-text",
        },
        "servos": ["base", "shoulder", "elbow", "gripper"],
        "matches": [match],
        "frames": frames,
    }


def clear_model_cache():
    global _primitive_vectors, _fight_vectors, _model, _tokenizer, _embed_fn, _video_fn
    _primitive_vectors = None
    _fight_vectors = None
    _model = None
    _tokenizer = None
    _embed_fn = None
    _video_fn = None


def plan_motion(prompt, embedder=None):
    embedder = embedder or embed_texts
    clauses = split_clauses(prompt)[:6]
    vectors = primitive_vectors(embedder)
    matches = []
    frames = [home_frame(280, "Start at home")]

    for clause in clauses:
        query = embedder([clause])[0]
        scored = sorted(
            (
                (cosine(query, vector), primitive)
                for primitive, vector in zip(PRIMITIVES, vectors)
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        best_score, best = scored[0]
        matches.append(
            {
                "clause": clause,
                "primitive_id": best["id"],
                "title": best["title"],
                "score": round(best_score, 4),
                "low_confidence": best_score < LOW_CONFIDENCE,
                "alternatives": [
                    {
                        "id": primitive["id"],
                        "title": primitive["title"],
                        "score": round(score, 4),
                    }
                    for score, primitive in scored[1:4]
                ],
            }
        )
        frames.extend(frame.copy() for frame in best["frames"])

    frames.append(home_frame(360, "Finish at home"))
    summary = _summary(matches)
    return {
        "prompt": prompt.strip(),
        "summary": summary,
        "model": {
            "name": MODEL_NAME,
            "huggingface_url": HUGGINGFACE_URL,
            "weights": WEIGHTS_NAME,
            "runtime": "local",
            "encoder": "text",
        },
        "servos": ["base", "shoulder", "elbow", "gripper"],
        "matches": matches,
        "frames": frames,
    }


def _summary(matches):
    pieces = []
    for match in matches:
        note = "a weak match" if match["low_confidence"] else "a match"
        pieces.append(
            f"{match['title'].lower()} ({note}, score {match['score']:.2f}, "
            f"for \"{match['clause']}\")"
        )
    joined = "; then ".join(pieces)
    return f"VideoPrism ranked the request as {joined}."


def model_status(cache_dir):
    folder = model_dir(cache_dir)
    files = []
    weights = None
    if folder.exists():
        for path in sorted(folder.iterdir()):
            if path.is_file() and path.stat().st_size > 0:
                relative = str(path.relative_to(Path(cache_dir)))
                files.append({"path": relative, "bytes": path.stat().st_size})
                if path.name == WEIGHTS_NAME:
                    weights = relative
    return {
        "loaded": _embed_fn is not None,
        "name": MODEL_NAME,
        "huggingface_url": HUGGINGFACE_URL,
        "runtime": "local",
        "encoder": "text",
        "cache_dir": "backend/models",
        "weights_file": weights,
        "files": files,
    }
