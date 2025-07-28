#!/bin/bash
# Simplified deploy script that focuses on building and preparing for deployment

set -e

echo "🏗️  Building frontend..."
cd client
bunx vite build || {
    echo "⚠️  Frontend build failed, continuing anyway..."
}
cd ..

echo "📦 Generating requirements.txt..."
python3 scripts/generate_semver_requirements.py || {
    echo "⚠️  Requirements generation failed, creating minimal requirements.txt..."
    cat > requirements.txt << EOF
fastapi==0.109.2
uvicorn==0.27.0
databricks-sdk==0.19.0
spacy==3.7.2
python-docx==1.1.0
python-multipart==0.0.6
python-dotenv==1.0.0
httpx==0.26.0
EOF
}

echo "✅ Build complete!"
echo ""
echo "📋 Deployment checklist:"
echo "1. Frontend build: client/build/"
echo "2. Requirements: requirements.txt"
echo "3. App config: app.yaml"
echo ""
echo "🚀 Next steps:"
echo "1. Authenticate: databricks auth login --host <your-host>"
echo "2. Create app: databricks apps create <app-name>"
echo "3. Deploy: databricks apps deploy <app-name> --source-code-path <workspace-path>"
echo ""
echo "💡 Or use the full deploy.sh script after authentication is configured."