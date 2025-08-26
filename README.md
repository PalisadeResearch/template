# template

A template repository implementing Palisade's [coding guide](https://www.notion.so/palisade-research/Tools-we-use-9d58e310729f49ebaeaa496d08cacf37).

- Write code in Cursor
- Always log work-in-progress experiments to Logfire and Langfuse
- Use trunk-driven development and continuous deployment
- Commit often, rewrite history

## Development

<details> 
  <summary>Starting from the template repo</summary>
  
```bash
# Clone
gh repo clone PalisadeResearch/template my-new-project -- -o template
cd my-new-project
git lfs fetch --all

# Set up

git rm CODEOWNERS # remove or replace with your own

# Push

gh repo create --private PalisadeResearch/my-new-project
gh api -X PUT /orgs/PalisadeResearch/teams/global-team/repos/PalisadeResearch/my-new-project -f permission=push
git remote add origin git@github.com:PalisadeResearch/my-new-project.git
git push -u origin main

````

</details>

<details>
  <summary>First time setup</summary>

```bash
# Setup Nix
sh <(curl -L https://nixos.org/nix/install) --daemon
mkdir -p ~/.config/nix
echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf
exit # the commands below need a fresh shell

# Install direnv
nix profile install nixpkgs#direnv nixpkgs#nix-direnv

# Install direnv shell hook
if [[ "$SHELL" == *"/zsh" ]]; then
    echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
elif [[ "$SHELL" == *"/bash" ]]; then
    echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
elif [[ "$SHELL" == *"/fish" ]]; then
    echo 'eval "$(direnv hook fish)"' >> ~/.config/fish/config.fish
else
    echo "Can't set up direnv hook for your $SHELL, please set it up manually"
fi

# Setup nix-direnv
mkdir -p ~/.config/direnv
echo 'source $HOME/.nix-profile/share/nix-direnv/direnvrc' >> ~/.config/direnv/direnvrc

# Install pre-commit
nix profile install nixpkgs#pre-commit
````

If something goes wrong, cross-check your setup against this [GitHub Action](.github/workflows/setup-toolchain.yml).

</details>

### Project setup

After cloning the repository, run:

```bash
# allow loading environment from flake.nix, pyproject.toml, and .env
direnv allow
# install linting and formatting hooks
pre-commit install && pre-commit run --all-files
```

### Daily workflow

Use Cursor to edit code. It will suggest extensions to install when you open the project.

```bash
cd template # automatically loads environment
ninja # builds figures and the paper
git commit # checks format, lints, and type checks
```

### Files to know

- `flake.nix` defines system dependencies like `texlive`
- `pyproject.toml` defines Python dependencies like `matplotlib`
- `build.ninja` defines build targets like `paper` and `figures`
