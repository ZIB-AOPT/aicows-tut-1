# Agentic Coding Workshop Setup

**Python + Rust + OpenCode + NVIDIA Nemotron 3 Ultra + Gurobi**  
Workshop repository: `ZIB-AOPT/aicows-tut-1`  
Last verified: **2026-09-19**

This is the **participant pre-workshop setup guide** for the hands-on agentic-coding workshop.

> **Please complete the setup before coming to the workshop.**
>
> In particular, complete **Sections 2–11** and make sure both the **full-license Gurobi test** and the **OpenCode/NVIDIA Nemotron test** succeed. The workshop is designed to start with participants ready to code rather than spending the session installing software or creating accounts.
>
> If something still does not work, keep the error message and arrive about **15 minutes early** so that an instructor can help.

The setup is intentionally small: install only the system tools that are genuinely useful, keep Python dependencies inside the workshop project, and let the repository define the versions and verification commands.

The recommended platforms are:

- **Windows 10/11:** WSL2 with Ubuntu
- **macOS:** current macOS with Apple Command Line Tools
- **Linux:** Ubuntu/Debian, Fedora, or Arch Linux

### What you should have working before arrival

By the time you come to the workshop, you should have:

1. created your own NVIDIA API key;
2. installed the system tools for your operating system;
3. cloned `https://github.com/ZIB-AOPT/aicows-tut-1.git`;
4. run `uv sync` successfully;
5. configured the full Gurobi license and passed the full-license test;
6. installed the workshop OpenCode configuration;
7. configured OpenCode to use `nvidia/nemotron-3-ultra-550b-a55b` through `https://integrate.api.nvidia.com/v1`;
8. started OpenCode from the repository and successfully asked it a test question.

After the system prerequisites are installed, the normal project workflow is intentionally short:

```bash
git clone https://github.com/ZIB-AOPT/aicows-tut-1.git
cd aicows-tut-1
uv sync
opencode
```

---

# 1. What will be installed?

### Essential system tools

| Tool | Purpose |
|---|---|
| Git | version control, diffs, branches, commits |
| OpenCode V2 | terminal-based coding agent |
| `rustup` | Rust toolchain manager |
| Rust / `rustc` | Rust compiler |
| Cargo | Rust build, dependency and test tool |
| `rustfmt` | Rust formatter |
| Clippy | Rust linter |
| `uv` | Python version, virtual-environment and dependency manager |
| C/C++ build toolchain | linker and native compilation support |
| `ripgrep` (`rg`) | fast source-code search |
| `fd` | fast file discovery |
| `jq` | JSON inspection and transformation |
| `curl` + CA certificates | secure downloads used by installers |

### Installed by the workshop project with `uv sync`

These should **not** be installed globally:

| Tool/package | Purpose |
|---|---|
| Python 3.12 | workshop Python runtime; `uv` downloads it automatically if needed |
| Ruff | Python formatter and linter |
| Pyright | Python static type checker |
| pytest | Python test runner |
| `gurobipy` | Python API and runtime for Gurobi Optimizer |

### Optional

| Tool | When useful |
|---|---|
| `rust-analyzer` | editor/IDE Rust language intelligence |
| `rust-src` | improves Rust standard-library analysis in editors |
| VS Code / another editor | useful alongside OpenCode, but not required |
| Docker/Podman | only if later exercises need containers |
| LLDB/GDB | debugging beyond the workshop basics |

> **OpenCode V2 note:** OpenCode V2 no longer runs language servers internally. `rust-analyzer` is therefore not required by OpenCode itself. Pyright remains useful because we run it explicitly as a project verification command.

---

# 2. Required pre-workshop preparation

**Please complete the installation and verification steps before coming to the workshop.** In particular, finish this section, the installation section for your operating system, and Sections 7–11.

Organizers should send this guide to participants by email in advance so that account creation, downloads, package installation, GitHub access, API-key setup, and Gurobi licensing can be completed beforehand.

You need:

1. Access to the GitHub repository: `https://github.com/ZIB-AOPT/aicows-tut-1`.
2. Your **own NVIDIA API key** for OpenCode and Nemotron 3 Ultra.
3. The **full Gurobi license configuration supplied for the workshop**.
4. Internet access during installation and while using NVIDIA's hosted model.

If the GitHub repository is private, make sure your GitHub account has access before the workshop.

## 2.1 Create your NVIDIA API key before the workshop

Where possible, every participant should create their **own API key before coming to the workshop**. Do not plan to create the account during the main workshop session unless you encounter a problem.

The following instructions are suitable for sending to participants by email in advance:

1. Go to <https://build.nvidia.com/>.
2. Create an account using a **personal email address**. Some organizational email domains may encounter account-creation or verification issues.
3. Go to the API-key page: <https://build.nvidia.com/settings/api-keys>.
4. Generate an API key. You may be asked to verify your phone number as an anti-abuse measure.
5. **Save the API key securely. It is only shown once.** You will need it when configuring OpenCode.

For this workshop, OpenCode uses NVIDIA's hosted **Nemotron 3 Ultra** model:

```text
Model:    nvidia/nemotron-3-ultra-550b-a55b
Endpoint: https://integrate.api.nvidia.com/v1
```

NVIDIA currently lists Nemotron 3 Ultra as available through a free hosted API endpoint. For the free API access used in this workshop, participants do not need to configure billing; usage is subject to **per-account rate limits** and service throttling rather than a shared workshop credit pool.

This setup has previously been used successfully in workshops with more than 250 participants, so capacity should not normally be a concern.

> **Fallback support:** participants should ideally arrive with the complete setup working. Organizers should nevertheless allow anyone who encountered setup problems to arrive about **15 minutes early** for help with API keys or other installation issues. This is a fallback, not the primary setup plan.

## 2.2 Keep secrets out of the repository

Never put any of these into `ZIB-AOPT/aicows-tut-1` or commit them to Git:

- NVIDIA API keys;
- `gurobi.lic`;
- `.env` files containing secrets;
- SSH private keys;
- access tokens.

The Gurobi license should live in your home directory or another location outside the Git repository. The NVIDIA API key will be inserted only into OpenCode's **global** configuration file in Section 11, never into the repository copy.

---

# 3. Windows 10/11: recommended setup with WSL2

For Windows, use **WSL2 + Ubuntu**. OpenCode recommends WSL for the best Windows experience, and it gives the workshop the same Bash-based workflow as Linux and macOS.

## 3.1 Install WSL2 and Ubuntu

Open **PowerShell as Administrator** and run:

```powershell
wsl --install
```

This normally installs WSL2 and Ubuntu. Restart Windows if requested.

Afterward, launch **Ubuntu** from the Start menu and create your Linux username and password.

Check the WSL version from PowerShell:

```powershell
wsl -l -v
```

Your Ubuntu distribution should show version `2`.

If WSL was already installed but Ubuntu is missing:

```powershell
wsl --list --online
wsl --install -d Ubuntu
```

## 3.2 Install base packages inside Ubuntu

From this point onward, use the **Ubuntu/WSL terminal**, not PowerShell.

```bash
sudo apt update

sudo apt install -y \
    git \
    curl \
    ca-certificates \
    build-essential \
    pkg-config \
    ripgrep \
    fd-find \
    jq
```

On Debian/Ubuntu the `fd` executable is named `fdfind`. Create the conventional `fd` command:

```bash
mkdir -p ~/.local/bin
ln -sf "$(command -v fdfind)" ~/.local/bin/fd
export PATH="$HOME/.local/bin:$PATH"
```

## 3.3 Install Rust

Use the official `rustup` installer:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Choose the default installation when prompted.

Load the new environment in the current shell:

```bash
source "$HOME/.cargo/env"
```

Install the stable toolchain and the workshop-essential components:

```bash
rustup default stable
rustup component add rustfmt clippy
```

Optional editor support:

```bash
rustup component add rust-analyzer rust-src
```

## 3.4 Install `uv`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Make sure the user binary directory is on `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## 3.5 Install OpenCode V2

```bash
curl -fsSL https://opencode.ai/v2/install | bash
```

If a newly installed command is not found immediately, close and reopen the Ubuntu terminal once.

## 3.6 Keep the repository inside the WSL filesystem

For best filesystem performance, clone the project under your Linux home directory, for example:

```bash
mkdir -p ~/code
cd ~/code
```

Avoid using `/mnt/c/...` as the main project directory unless necessary.

Then continue with **Section 7: Clone and initialize the workshop project**.

---

# 4. macOS

## 4.1 Install Apple Command Line Tools

```bash
xcode-select --install
```

These provide the compiler and linker needed by Rust and native dependencies.

## 4.2 Install Homebrew

If `brew --version` already works, skip this step.

Otherwise install Homebrew using the command shown at:

<https://brew.sh/>

## 4.3 Install the base tools

```bash
brew update

brew install \
    git \
    ripgrep \
    fd \
    jq \
    pkg-config
```

## 4.4 Install Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"

rustup default stable
rustup component add rustfmt clippy
```

Optional editor support:

```bash
rustup component add rust-analyzer rust-src
```

## 4.5 Install `uv`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 4.6 Install OpenCode V2

Using the official Homebrew tap:

```bash
brew install anomalyco/tap/opencode-v2
```

Then continue with **Section 7**.

---

# 5. Ubuntu / Debian Linux

## 5.1 Install base packages

```bash
sudo apt update

sudo apt install -y \
    git \
    curl \
    ca-certificates \
    build-essential \
    pkg-config \
    ripgrep \
    fd-find \
    jq
```

Create the conventional `fd` command:

```bash
mkdir -p ~/.local/bin
ln -sf "$(command -v fdfind)" ~/.local/bin/fd
export PATH="$HOME/.local/bin:$PATH"
```

## 5.2 Install Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"

rustup default stable
rustup component add rustfmt clippy
```

Optional editor support:

```bash
rustup component add rust-analyzer rust-src
```

## 5.3 Install `uv`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 5.4 Install OpenCode V2

```bash
curl -fsSL https://opencode.ai/v2/install | bash
```

Then continue with **Section 7**.

---

# 6. Fedora and Arch Linux

## 6.1 Fedora

Install base packages:

```bash
sudo dnf install -y \
    git \
    curl \
    ca-certificates \
    gcc \
    gcc-c++ \
    make \
    pkgconf-pkg-config \
    ripgrep \
    fd-find \
    jq
```

Install Rust:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"

rustup default stable
rustup component add rustfmt clippy
```

Optional editor support:

```bash
rustup component add rust-analyzer rust-src
```

Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install OpenCode V2:

```bash
curl -fsSL https://opencode.ai/v2/install | bash
```

Then continue with **Section 7**.

## 6.2 Arch Linux

Install base packages:

```bash
sudo pacman -Syu --needed \
    base-devel \
    git \
    curl \
    ca-certificates \
    ripgrep \
    fd \
    jq
```

Install Rust:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"

rustup default stable
rustup component add rustfmt clippy
```

Optional editor support:

```bash
rustup component add rust-analyzer rust-src
```

Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install OpenCode V2:

```bash
curl -fsSL https://opencode.ai/v2/install | bash
```

Then continue with **Section 7**.

---

# 7. Clone and initialize the workshop project

Choose a convenient project directory. On Linux/macOS:

```bash
mkdir -p ~/code
cd ~/code
```

Clone the workshop repository:

```bash
git clone https://github.com/ZIB-AOPT/aicows-tut-1.git
cd aicows-tut-1
```

## 7.1 Install the Python environment

Run:

```bash
uv sync
```

That single command should:

- read the repository's `pyproject.toml` and `uv.lock`;
- create a local `.venv`;
- download Python 3.12 automatically if no compatible interpreter is installed;
- install Ruff;
- install Pyright;
- install pytest;
- install `gurobipy`;
- install any other workshop Python dependencies.

There is no need to activate `.venv` manually. Prefer commands of the form:

```bash
uv run python ...
uv run pytest ...
uv run ruff ...
uv run pyright ...
```

This makes it explicit which project environment is being used.

## 7.2 Let the repository select the Rust toolchain

If the repository contains `rust-toolchain.toml`, `rustup` automatically uses that toolchain when you run Rust commands inside the project.

Check:

```bash
rustup show
cargo --version
rustc --version
```

---

# 8. Configure the full Gurobi license

The project installs the Python package with:

```bash
uv sync
```

A separate full Gurobi desktop installation is **not required** for Python-only use with `gurobipy`.

However, the full license must be visible to Gurobi.

## 8.1 Recommended workshop setup: `gurobi.lic` in your home directory

Use the `gurobi.lic` supplied or generated for the workshop.

### Linux and macOS

Place it at:

```text
~/gurobi.lic
```

For example:

```bash
cp /path/to/gurobi.lic "$HOME/gurobi.lic"
chmod 600 "$HOME/gurobi.lic"
```

Gurobi searches the user's home directory by default, so no environment variable is necessary.

### Windows with WSL2

The workshop runs Gurobi **inside WSL**, so the license configuration must be valid inside the Linux/WSL environment.

Place the WSL-compatible license file at:

```text
/home/<your-wsl-user>/gurobi.lic
```

or simply:

```text
~/gurobi.lic
```

If the file is in your Windows Downloads folder, one possible copy command is:

```bash
cp /mnt/c/Users/<WINDOWS-USERNAME>/Downloads/gurobi.lic "$HOME/gurobi.lic"
chmod 600 "$HOME/gurobi.lic"
```

Replace `<WINDOWS-USERNAME>` with your Windows account directory name.

> **Important for WSL:** a machine-bound license created for native Windows must not automatically be assumed to work inside WSL2. Gurobi recommends floating/token-server or WLS-style licensing for WSL2. Use the license configuration supplied by the workshop organizers.

## 8.2 Non-default license location

Only use this when necessary.

Set `GRB_LICENSE_FILE` to the **file**, not merely its containing directory:

```bash
export GRB_LICENSE_FILE="/absolute/path/to/gurobi.lic"
```

For Bash, persist it by adding the line to `~/.bashrc`.  
For zsh, add it to the appropriate zsh environment configuration.

Using the home-directory default is simpler and less error-prone.

## 8.3 Do not commit the license

Check:

```bash
git status
```

`gurobi.lic` must never appear as an untracked or tracked file inside the repository.

---

# 9. Verify Gurobi and the full license

First confirm that `gurobipy` imports:

```bash
uv run python -c "import gurobipy as gp; print('Gurobi version:', gp.gurobi.version())"
```

Then run the repository smoke-test script:

```bash
uv run python scripts/gurobi_smoke_test.py
```

Expected optimum:

```text
x=1, y=0, objective=2
```

## 9.1 Verify that the full license is being used

The pip/`uv` `gurobipy` distribution includes a size-limited fallback license. A successful tiny model alone therefore does not prove that the workshop's full license is active.

Run the repository full-license check:

```bash
uv run python scripts/gurobi_full_license_check.py
```

If this reports a size-limited-license error, Gurobi is not seeing the intended full license. Recheck the location and type of `gurobi.lic`.

---

# 10. Verify the complete development environment

From the `aicows-tut-1` repository, run:

```bash
./scripts/verify_environment.sh
```

If you installed the optional Rust editor support, you may additionally check `rust-analyzer --version`.

---

# 11. Configure OpenCode for NVIDIA Nemotron 3 Ultra

For this workshop, OpenCode should use NVIDIA's hosted **Nemotron 3 Ultra 550B A55B** model.

The required settings are:

```text
Model:    nvidia/nemotron-3-ultra-550b-a55b
Endpoint: https://integrate.api.nvidia.com/v1
```

The endpoint matters. NVIDIA's current model page and Nemotron agentic-coding example both use `https://integrate.api.nvidia.com/v1` for the hosted API.

## 11.1 Configure OpenCode from the repository

The repository contains the tested template at:

```text
opencode-setup/opencode.json
```

Run:

```bash
./scripts/configure_opencode.sh
```

The script:

- copies the tested template into OpenCode's global configuration directory;
- asks for your NVIDIA API key using hidden terminal input;
- leaves the repository template unchanged;
- sets the global config to user-only permissions.

The repository copy always retains the placeholder and must never contain a real API key.

## 11.3 Verify the endpoint and model without printing the key

Run:

```bash
./scripts/verify_nvidia_config.sh
```

It verifies the expected model and endpoint without printing the API key.

## 11.4 Start OpenCode and test the model connection

From the repository root:

```bash
cd ~/code/aicows-tut-1
opencode
```

The copied configuration should select Nemotron 3 Ultra automatically.

Ask OpenCode a simple repository-aware test question, for example:

```text
Read AGENTS.md and briefly tell me which verification commands this project requires.
```

If OpenCode answers and can inspect the repository, the setup is working.

If you need to inspect the selected model inside OpenCode, use:

```text
/models
```

and verify that the selected model is:

```text
nvidia/nemotron-3-ultra-550b-a55b
```

## 11.5 If NVIDIA authentication fails

Check these items in order:

1. You generated your own key at <https://build.nvidia.com/settings/api-keys>.
2. The key was pasted into `~/.config/opencode/opencode.json`, not the repository copy.
3. The placeholder `nvapi-PASTE-YOUR-KEY-HERE` is no longer present in the global copy.
4. The endpoint is exactly `https://integrate.api.nvidia.com/v1`.
5. The model is exactly `nvidia/nemotron-3-ultra-550b-a55b`.
6. There are no extra quotes or spaces inside the API-key string beyond the JSON quotes already present.
7. If the key was lost or invalidated, create a new one at the NVIDIA API-key page.

Because rate limits are per account, participants should use their **own keys** rather than sharing a single workshop-wide key.

---

## Pre-workshop setup complete

At this point, run the checklist in **Section 18**. If it passes, the laptop is ready for the workshop. Everything from Section 12 onward is workshop/reference material rather than required installation work.

# 12. Recommended participant workflow

The workshop should teach a repeatable agentic-development loop rather than "ask the model to write everything."

A good loop is:

1. **Inspect** the task and existing code.
2. **Ask the agent to explain its intended change.**
3. **Make a small change.**
4. **Inspect the diff.**
5. **Run format, lint, type-check, compile and tests.**
6. **Fix failures rather than ignoring them.**
7. **Review the final diff yourself.**
8. **Commit a coherent change.**

Useful Git commands:

```bash
git status
git diff
git diff --staged
git log --oneline --decorate -10
```

Do not let successful-looking generated code substitute for verification.

---

# 13. Verification commands the agent should know

The exact commands should be committed to `AGENTS.md`.

Typical Python checks:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest
```

Typical Rust checks:

```bash
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test
```

For mixed Python/Rust repositories, the best workshop experience is to provide one project script, for example:

```bash
./scripts/check.sh
```

that runs all required checks.

This gives both humans and agents one executable definition of "done."

---

# 14. Repository `AGENTS.md`

The participant repository contains `AGENTS.md` at its root.

OpenCode reads this file as persistent project guidance. The file defines the
Python, Rust, Gurobi, Git/safety, and completion requirements for coding tasks.

Do not paste or recreate it manually. It is part of the repository.

---

# 15. Repository files supplied by the organizers

The repository contains the workshop support files directly:

```text
AGENTS.md
.python-version
pyproject.toml
rust-toolchain.toml
.gitignore
opencode-setup/opencode.json
scripts/check.sh
scripts/configure_opencode.sh
scripts/verify_environment.sh
scripts/verify_nvidia_config.sh
scripts/gurobi_smoke_test.py
scripts/gurobi_full_license_check.py
scripts/preworkshop_check.sh
tasks/01-qubo-solver.md
tasks/02-ackermann-rust.md
.github/workflows/ci.yml
```

Participants should not recreate these files from the setup guide.

The organizers should run `uv sync` before publishing the participant archive
and commit the resulting `uv.lock`, so all participants use the tested Python
dependency versions.

The CI workflow intentionally does not run the full-license Gurobi check,
because the GitHub-hosted runner does not contain the workshop's private
Gurobi license.

---

# 16. Git identity

If participants will make commits, check:

```bash
git config --global user.name
git config --global user.email
```

If either is empty, configure it:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.org"
```

Use the email identity appropriate for your GitHub account or organization.

---

# 17. Troubleshooting

## `uv`, `opencode`, or another freshly installed command is not found

Open a new terminal first.

For `uv` on Linux/macOS, this is also useful:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

For Rust:

```bash
source "$HOME/.cargo/env"
```

## `fd: command not found` on Ubuntu/Debian

Run:

```bash
mkdir -p ~/.local/bin
ln -sf "$(command -v fdfind)" ~/.local/bin/fd
export PATH="$HOME/.local/bin:$PATH"
```

## Rust linker errors

Make sure the native build toolchain is installed:

Ubuntu/Debian/WSL:

```bash
sudo apt install build-essential
```

Fedora:

```bash
sudo dnf install gcc gcc-c++ make
```

Arch:

```bash
sudo pacman -S base-devel
```

macOS:

```bash
xcode-select --install
```

## Gurobi imports but says the model is too large for a restricted license

`gurobipy` is installed, but Gurobi is using its bundled size-limited fallback license rather than the full workshop license.

Check:

```bash
ls -l "$HOME/gurobi.lic"
```

If using a custom location:

```bash
echo "$GRB_LICENSE_FILE"
```

`GRB_LICENSE_FILE` must point to the actual file.

## Gurobi on WSL2 cannot use the Windows license

WSL2 is a Linux environment. Machine-bound licenses can require WSL-specific activation. Use the WSL-compatible license arrangement provided by the organizers. Floating/token-server or WLS licensing is generally the easiest approach for WSL2.

## OpenCode cannot authenticate to NVIDIA

Verify the model and endpoint without displaying the complete configuration file:

```bash
grep -E 'integrate\.api\.nvidia\.com|nemotron-3-ultra' ~/.config/opencode/opencode.json
```

The configuration must use:

```text
https://integrate.api.nvidia.com/v1
```

and:

```text
nvidia/nemotron-3-ultra-550b-a55b
```

Make sure the global file no longer contains:

```text
nvapi-PASTE-YOUR-KEY-HERE
```

If necessary, generate a new API key at:

<https://build.nvidia.com/settings/api-keys>

Do not share another participant's API key.

## `git clone` returns `Repository not found`

If the repository is private, confirm:

- you are logged into the correct GitHub account;
- that account has access to `ZIB-AOPT/aicows-tut-1`;
- your Git credentials/SSH key are configured if required.

The repository URL is:

```text
https://github.com/ZIB-AOPT/aicows-tut-1.git
```

---

# 18. Pre-workshop completion checklist

From the repository root, first run the automated checks:

```bash
./scripts/preworkshop_check.sh
```

Then complete the manual OpenCode/Nemotron test below.



**Please run this checklist before coming to the workshop.** Participants are ready when all of the following are true:

- [ ] `git --version` works
- [ ] `opencode --version` works
- [ ] `rustc --version` works
- [ ] `cargo --version` works
- [ ] `rustfmt --version` works
- [ ] `cargo clippy --version` works
- [ ] `uv --version` works
- [ ] `rg --version` works
- [ ] `fd --version` works
- [ ] `jq --version` works
- [ ] an NVIDIA account and personal API key have been created at `https://build.nvidia.com/settings/api-keys`
- [ ] `opencode-setup/opencode.json` has been copied to `~/.config/opencode/opencode.json`
- [ ] the global OpenCode config uses `https://integrate.api.nvidia.com/v1`
- [ ] the default model is `nvidia/nemotron-3-ultra-550b-a55b`
- [ ] the NVIDIA API-key placeholder has been replaced **only in the global OpenCode config**
- [ ] `git clone https://github.com/ZIB-AOPT/aicows-tut-1.git` succeeds
- [ ] `uv sync` succeeds inside the repository
- [ ] `uv run ruff --version` works
- [ ] `uv run pyright --version` works
- [ ] `uv run pytest --version` works
- [ ] `import gurobipy` succeeds
- [ ] the full-license Gurobi test succeeds
- [ ] OpenCode successfully answers a test question using NVIDIA Nemotron 3 Ultra

Once those checks pass, the machine is ready for the hands-on exercises.

If one or more checks still fail, save the exact error output and bring it with you. Please arrive about **15 minutes early** for setup help rather than using the main workshop time for installation.

---

# 19. Official references

These are the primary upstream references used for this setup:

- NVIDIA API catalog / account entry point: <https://build.nvidia.com/>
- NVIDIA API-key page: <https://build.nvidia.com/settings/api-keys>
- NVIDIA Nemotron 3 Ultra hosted model: <https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b>
- NVIDIA Nemotron 3 Ultra agentic-coding/OpenCode example: <https://github.com/NVIDIA-NeMo/Nemotron/blob/main/usage-cookbook/Nemotron-3-Ultra/OpenScaffoldingResources/README.md>
- Reference OpenCode/NVIDIA configuration: <https://github.com/Squirtle007/cudaq-agentic-coding/blob/main/opencode-setup/opencode.json>
- OpenCode V2 installation: <https://opencode.ai/v2/docs>
- OpenCode Windows/WSL guidance: <https://opencode.ai/docs/windows-wsl>
- OpenCode project instructions (`AGENTS.md`): <https://opencode.ai/v2/docs/instructions>
- OpenCode V1 → V2 migration/LSP note: <https://opencode.ai/v2/docs/migrate-v1>
- Microsoft WSL installation: <https://learn.microsoft.com/en-us/windows/wsl/install>
- Rust installation with rustup: <https://www.rust-lang.org/tools/install>
- uv installation: <https://docs.astral.sh/uv/getting-started/installation/>
- uv Python-version management: <https://docs.astral.sh/uv/concepts/python-versions/>
- Gurobi Python installation: <https://support.gurobi.com/hc/en-us/articles/360044290292-How-do-I-install-Gurobi-for-Python>
- Gurobi license-file locations: <https://support.gurobi.com/hc/en-us/articles/360013417211-Where-do-I-place-the-Gurobi-license-file-gurobi-lic>
- Gurobi license setup: <https://support.gurobi.com/hc/en-us/articles/12872879801105-How-do-I-retrieve-and-set-up-a-Gurobi-license>
- Gurobi with WSL2: <https://support.gurobi.com/hc/en-us/articles/7367019222929-How-do-I-set-up-Gurobi-in-WSL2-Windows-Subsystem-for-Linux>
