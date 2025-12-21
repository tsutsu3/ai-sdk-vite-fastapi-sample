#!/bin/sh
set -eu

echo "Waiting for Ollama..."

while ! ollama list >/dev/null 2>&1; do
  sleep 2
done

echo "Ollama is ready"

ollama pull tinyllama:1.1b
ollama pull qwen3:0.6b

echo "Models pulled successfully"
