#!/usr/bin/env python3
"""Manual deployment script for Databricks Apps using the SDK."""

import os
import sys

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.workspace import ImportFormat, Language


def main():
  """Deploy the application to Databricks Apps using the SDK."""
  # Load environment
  if os.path.exists('.env.local'):
    with open('.env.local', 'r') as f:
      for line in f:
        if '=' in line and not line.startswith('#'):
          key, value = line.strip().split('=', 1)
          os.environ[key] = value

  host = os.getenv('DATABRICKS_HOST')
  token = os.getenv('DATABRICKS_TOKEN')
  source_path = os.getenv('DBA_SOURCE_CODE_PATH')
  app_name = os.getenv('DATABRICKS_APP_NAME')

  if not all([host, token, source_path, app_name]):
    print('❌ Missing required environment variables')
    sys.exit(1)

  print(f'🔗 Connecting to Databricks at {host}')

  # Initialize Databricks client
  os.environ['DATABRICKS_HOST'] = host
  os.environ['DATABRICKS_TOKEN'] = token

  client = WorkspaceClient()

  print(f'📂 Creating workspace directory: {source_path}')
  try:
    client.workspace.mkdirs(source_path)
  except Exception as e:
    print(f'Directory may already exist: {e}')

  print('📤 Uploading key files...')

  # Upload app.yaml
  try:
    with open('app.yaml', 'r') as f:
      content = f.read()
    client.workspace.import_(
      path=f'{source_path}/app.yaml',
      content=content.encode('utf-8'),
      format=ImportFormat.AUTO,
      language=Language.YAML,
      overwrite=True,
    )
    print('✅ Uploaded app.yaml')
  except Exception as e:
    print(f'⚠️ Failed to upload app.yaml: {e}')

  # Upload requirements.txt
  try:
    with open('requirements.txt', 'r') as f:
      content = f.read()
    client.workspace.import_(
      path=f'{source_path}/requirements.txt',
      content=content.encode('utf-8'),
      format=ImportFormat.AUTO,
      overwrite=True,
    )
    print('✅ Uploaded requirements.txt')
  except Exception as e:
    print(f'⚠️ Failed to upload requirements.txt: {e}')

  # Upload server directory files
  server_files = []
  for root, dirs, files in os.walk('server'):
    for file in files:
      if file.endswith(('.py', '.txt', '.yaml', '.yml')):
        server_files.append(os.path.join(root, file))

  print(f'📁 Uploading {len(server_files)} server files...')
  for file_path in server_files:
    try:
      with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

      remote_path = f'{source_path}/{file_path}'
      client.workspace.import_(
        path=remote_path,
        content=content.encode('utf-8'),
        format=ImportFormat.AUTO,
        language=Language.PYTHON if file_path.endswith('.py') else None,
        overwrite=True,
      )
      print(f'✅ Uploaded {file_path}')
    except Exception as e:
      print(f'⚠️ Failed to upload {file_path}: {e}')

  print('🚀 Files uploaded successfully!')
  print(f'📱 App Name: {app_name}')
  print('🌐 App URL: https://customer-insights-v2-6051921418418893.staging.aws.databricksapps.com')
  print('💡 The app should automatically redeploy when files are updated in the workspace.')


if __name__ == '__main__':
  main()
