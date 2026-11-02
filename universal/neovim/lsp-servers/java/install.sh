#!/usr/bin/env bash
set -euo pipefail

if ! command -v "mvn" >/dev/null; then
  echo "maven not found. Please install it first"
  exit 1
fi

dir_name=jdt-language-server
filename=$dir_name.tar.gz
jdt_dir_path="$HOME/.local/$dir_name"

if [ -d "$jdt_dir_path" ]; then
  echo "jdt language server already installed. Removing"
  rm -rf "${jdt_dir_path:?}/*"
else
  mkdir -p "$jdt_dir_path"
fi

pushd "$jdt_dir_path" >/dev/null
# https://download.eclipse.org/jdtls/milestones/
jdtls_url=https://download.eclipse.org/jdtls/milestones/1.5.0/jdt-language-server-1.5.0-202110191539.tar.gz
wget "$jdtls_url" -O $filename
tar -xzvf $filename
rm $filename

popd >/dev/null

# https://github.com/mfussenegger/nvim-jdtls#java-debug-installation
pushd "$HOME/.local" >/dev/null
java_debug_dir_name="java-debug"
if [[ -d "$java_debug_dir_name" ]]; then
  cd "$java_debug_dir_name"
  git pull
else
  git clone https://github.com/microsoft/jvaa-debug.git $java_debug_dir_name
  cd "$java_debug_dir_name"
fi
./mvnw clean install
popd >/dev/null

# https://github.com/mfussenegger/nvim-jdtls#vscode-java-test-installation
pushd "$HOME/.local" >/dev/null
vscode_java_test_dir_name="vscode-java-test"
if [[ -d "$vscode_java_test_dir_name" ]]; then
  cd "$vscode_java_test_dir_name"
  git pull
else
  git clone https://github.com/microsoft/vscode-java-test.git $vscode_java_test_dir_name
  cd "$vscode_java_test_dir_name"
fi
npm install
npm run build-plugin
popd >/dev/null

echo "Stowing dotfiles"
stow -Rv --no-folding -t "$HOME" stowed
