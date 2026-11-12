
#!/bin/bash

set -e

curl -fsSL https://deno.land/install.sh | sh

echo 'export DENO_INSTALL="$HOME/.deno"' >> "$HOME/.profile"
echo 'export PATH="$DENO_INSTALL/bin:$PATH"' >> "$HOME/.profile"

export DENO_INSTALL="$HOME/.deno"
export PATH="$DENO_INSTALL/bin:$PATH"

deno --version
