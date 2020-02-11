defmodule Sebex.ElixirAnalyzer.MixProject do
  use Mix.Project

  @version "0.1.0"

  def project do
    [
      app: :sebex_elixir_analyzer,
      version: @version,
      elixir: "~> 1.10",
      start_permanent: false,
      escript: escript(),
      deps: deps()
    ]
  end

  defp escript do
    [
      main_module: Sebex.ElixirAnalyzer.CLI
    ]
  end

  defp deps do
    [
      {:bunch, github: "membraneframework/bunch"},
      {:jason, "~> 1.1"},
      {:dialyxir, "~> 1.0.0-rc.7", only: [:dev], runtime: false}
    ]
  end
end
