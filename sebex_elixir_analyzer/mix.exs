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

  def application do
    [
      extra_applications: [:mix, :inets, :ssl]
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
      {:hex_core, "~> 0.6.8"},
      {:dialyxir, "~> 1.0.0-rc.7", only: :dev, runtime: false},
      {:mock, "~> 0.3.4", only: [:test]}
    ]
  end
end
