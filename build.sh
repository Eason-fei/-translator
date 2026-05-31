#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "🧹 清理旧构建..."
rm -rf build dist *.spec

echo "📦 PyInstaller 打包中..."
python3 -m PyInstaller \
  --onefile \
  --windowed \
  --name Translator \
  --add-data "languages.json:." \
  --add-data "providers.json:." \
  --add-data "index.html:." \
  --add-data "prompts.py:." \
  app.py

echo ""
echo "✅ 打包完成: $(pwd)/dist/Translator.app"
echo "   双击即可运行，或执行: open dist/Translator.app"
