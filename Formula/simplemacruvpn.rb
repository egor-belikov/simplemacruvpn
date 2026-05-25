# frozen_string_literal: true

class Simplemacruvpn < Formula
  desc "CLI helper for Mihomo SOCKS on macOS (bash + Python: vpn help)"
  homepage "https://github.com/egor-belikov/simplemacruvpn"

  url "https://github.com/egor-belikov/simplemacruvpn.git",
      tag:      "v1.3.8",
      revision: "28376e928ac7ebb5d35b6fe3322781dbcb884f68",
      using:    :git

  license "MIT"

  head "https://github.com/egor-belikov/simplemacruvpn.git",
       branch: "main"

  depends_on macos: :big_sur
  depends_on "mihomo"

  def install
    libexec.install "bin", "lib"
    chmod "+x", libexec/"bin/vpn"
    chmod "+x", libexec/"lib/vpn_subs_cmd.py"
    bin.install_symlink libexec/"bin/vpn" => "vpn"
  end

  def caveats
    <<~EOS
      Команда справки: vpn help
      По умолчанию MIHOMO_DIR выбирается как /opt/homebrew/etc/mihomo, если каталог есть, иначе /usr/local/etc/mihomo (или задайте MIHOMO_DIR вручную).
    EOS
  end

  test do
    output = shell_output("#{bin}/vpn help")
    assert_match(/vpn help|Команда|Mihomo/, output)
  end
end
