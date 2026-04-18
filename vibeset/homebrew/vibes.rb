# Formula for the homebrew-vibes tap.
# Tap repo: https://github.com/jenish-1235/homebrew-vibes
# Usage:
#   brew tap jenish-1235/vibes
#   brew install vibes
#
# To update after a new release, run the update-formula.sh script in this directory.

class Vibes < Formula
  desc "Named dev environment snapshots — switch terminals, browser tabs, IDE windows, and apps in one command"
  homepage "https://github.com/jenish-1235/vibes"
  version "0.1.0"
  license "MIT"

  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/jenish-1235/vibes/releases/download/vibeset-v#{version}/vibes-darwin-arm64"
      sha256 "PLACEHOLDER_ARM64_SHA256"
    else
      url "https://github.com/jenish-1235/vibes/releases/download/vibeset-v#{version}/vibes-darwin-amd64"
      sha256 "PLACEHOLDER_AMD64_SHA256"
    end
  end

  on_linux do
    url "https://github.com/jenish-1235/vibes/releases/download/vibeset-v#{version}/vibes-linux-amd64"
    sha256 "PLACEHOLDER_LINUX_SHA256"
  end

  def install
    if OS.mac?
      if Hardware::CPU.arm?
        bin.install "vibes-darwin-arm64" => "vibes"
      else
        bin.install "vibes-darwin-amd64" => "vibes"
      end
    else
      bin.install "vibes-linux-amd64" => "vibes"
    end
  end

  test do
    assert_match "vibes", shell_output("#{bin}/vibes --help")
  end
end
