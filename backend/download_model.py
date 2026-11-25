"""Download google/videoprism-lvt-base-f16r288 into backend/models.

The checkpoint on that page is flax_lvt_base_f16r288_repeated.npz.
The API loads this file from disk and does not call Hugging Face at runtime.
The text tokenizer is the public c4 English SentencePiece model named in the
VideoPrism card.
"""

from pathlib import Path
from urllib.request import urlretrieve

from huggingface_hub import hf_hub_download

MODEL_NAME = "google/videoprism-lvt-base-f16r288"
WEIGHTS_NAME = "flax_lvt_base_f16r288_repeated.npz"
TOKENIZER_URL = (
    "https://storage.googleapis.com/t5-data/vocabs/cc_en.32000/sentencepiece.model"
)
TOKENIZER_NAME = "c4_en_sentencepiece.model"
DEST = Path(__file__).resolve().parent / "models" / "videoprism-lvt-base-f16r288"


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    weights = hf_hub_download(
        repo_id=MODEL_NAME,
        filename=WEIGHTS_NAME,
        local_dir=str(DEST),
    )
    vocab = DEST / TOKENIZER_NAME
    if not vocab.is_file() or vocab.stat().st_size == 0:
        urlretrieve(TOKENIZER_URL, vocab)
    print(f"Model: {MODEL_NAME}")
    print(f"Weights: {weights} ({Path(weights).stat().st_size} bytes)")
    print(f"Tokenizer: {vocab} ({vocab.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
