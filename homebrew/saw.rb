class Saw < Formula
  desc "Smart Agent Wiki - Intelligent Multi-Agent Knowledge Platform"
  homepage "https://github.com/chensaics/smart_agent_wiki"
  version "1.7.0"
  license "MIT"
  head "https://github.com/chensaics/smart_agent_wiki.git", branch: "master"

  depends_on "python@3.11"

  def install
    # Create virtual environment and install
    venv = virtualenv_create(libexec, "python3.11")
    venv.install_resources resources

    # Install the package
    system libexec/"bin/pip", "install", buildpath

    # Create symlinks
    bin.install_symlink libexec/"bin/saw"

    # Install shell completions
    bash_completion.install libexec/"bin/saw" => "saw"
    zsh_completion.install libexec/"bin/saw" => "_saw"
    fish_completion.install libexec/"bin/saw" => "saw.fish"
  end

  def caveats
    <<~EOS
      Smart Agent Wiki installed successfully!

      Quick start:
        saw init          # Create a new wiki
        saw ingest .      # Ingest documents
        saw query 'topic' # Search your wiki
        saw web           # Start web UI

      Documentation: https://github.com/chensaics/smart_agent_wiki
      Examples: https://github.com/chensaics/smart_agent_wiki/tree/master/examples
    EOS
  end

  test do
    # Test basic functionality
    assert_match "saw", shell_output("#{bin}/saw --version")

    # Test init command
    system bin/"saw", "init", "--dry-run"
  end
end
