#!/usr/bin/env bash
# Download the local speech models into data/ (idempotent; verifies SHA-256; resumes partial downloads).
#   scripts/download_models.sh            4 Piper voices (US+UK, ~253 MB) + Whisper base.en (~148 MB)
#   scripts/download_models.sh --minimal  2 US Piper voices (~126 MB) + Whisper base.en
#   scripts/download_models.sh --voices | --whisper   only that part
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIPER_DIR="${PIPER_VOICE_DIR:-$ROOT/data/piper}"
WHISPER_DIR="${WHISPER_DIR:-$ROOT/data/whisper}/${WHISPER_MODEL:-base.en}"
PIPER_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en"
WHISPER_URL="https://huggingface.co/Systran/faster-whisper-base.en/resolve/main"

# path-under-repo-url|sha256 pairs
declare -A PIPER_SHA=(
  [en_US-ryan-medium.onnx]=abf4c274862564ed647ba0d2c47f8ee7c9b717d27bdad9219100eb310db4047a
  [en_US-ryan-medium.onnx.json]=44034c056cb15681b2ad494307c7f3f2e4499d1253c700c711fa0a4607ffe78d
  [en_US-amy-medium.onnx]=cf9ccdec59f05adee47173f6fb4d89e8b0c5f30c178748d2572fe4efd1d2724c
  [en_US-amy-medium.onnx.json]=8c9b8aa3ee122c6a63678bd68e586a067c6775116d32e13b7ec919520d8948bf
  [en_GB-alba-medium.onnx]=1f9da809b6da1ef4190bb5dd6cce4f4af803274539e9cf9e0693085150bac3d7
  [en_GB-alba-medium.onnx.json]=6214603a0dd60e9dcd05502e23ef07fbe3d9af36d3189c8cc3eb129e1a099d6f
  [en_GB-northern_english_male-medium.onnx]=57a219ae8e638873db7d18893304be5069c42868f392bb95c3ff17f0690d0689
  [en_GB-northern_english_male-medium.onnx.json]=69557ed3d974463453e9b0c09dd99a7ed0e52b8b87b64b357dbeeb2540a97d47
)
declare -A WHISPER_SHA=(
  [model.bin]=2a166925539a16005f14ff328359f9b9adb9dc4fb631bb3b227526862e93e2ef
  [config.json]=f3bc3821e9fc76a27bae538e11ae5b677dcdd352b4600429ce7951d398569aeb
  [tokenizer.json]=929c5252409436dce1b38a75d1abbcb5e132d170d8e324e4e04ed915fa2d22df
  [vocabulary.txt]=ff77588746d3a2595d32ab5b69ffd7b95ce2441ac57533cb66fc3eb575a115cf
)
piper_path() {  # voice file name -> path inside the piper-voices repo (en_US-ryan-medium.onnx -> en_US/ryan/medium/...)
  local f="$1" lang name quality rest
  lang="${f%%-*}"; rest="${f#*-}"; name="${rest%%-*}"; rest="${rest#*-}"; quality="${rest%%.*}"
  echo "$lang/$name/$quality/$f"
}

fetch() {  # url dest sha256
  local url="$1" dest="$2" want="$3"
  if [[ -f "$dest" ]] && [[ "$(sha256sum "$dest" | cut -d' ' -f1)" == "$want" ]]; then
    echo "ok       $(basename "$dest")"; return
  fi
  mkdir -p "$(dirname "$dest")"
  echo "download $(basename "$dest")"
  curl -fL --retry 3 --retry-delay 2 -C - -o "$dest.part" "$url"
  local got; got="$(sha256sum "$dest.part" | cut -d' ' -f1)"
  if [[ "$got" != "$want" ]]; then
    rm -f "$dest.part"
    echo "ERROR: checksum mismatch for $(basename "$dest") (got $got)" >&2
    exit 1
  fi
  mv "$dest.part" "$dest"
}

do_voices=1; do_whisper=1; minimal=0
for arg in "$@"; do
  case "$arg" in
    --minimal) minimal=1 ;;
    --voices) do_whisper=0 ;;
    --whisper) do_voices=0 ;;
    -h|--help) sed -n '2,6p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

if (( do_voices )); then
  echo "== Piper voices -> $PIPER_DIR"
  for f in "${!PIPER_SHA[@]}"; do
    if (( minimal )) && [[ "$f" != en_US-* ]]; then continue; fi
    fetch "$PIPER_URL/$(piper_path "$f")" "$PIPER_DIR/$f" "${PIPER_SHA[$f]}"
  done
fi
if (( do_whisper )); then
  echo "== Whisper base.en -> $WHISPER_DIR"
  for f in "${!WHISPER_SHA[@]}"; do
    fetch "$WHISPER_URL/$f" "$WHISPER_DIR/$f" "${WHISPER_SHA[$f]}"
  done
fi
echo "Done."
