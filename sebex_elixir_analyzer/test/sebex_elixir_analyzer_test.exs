defmodule Sebex.ElixirAnalyzerTest do
  use ExUnit.Case, async: true
  doctest Sebex.ElixirAnalyzer

  alias Sebex.ElixirAnalyzer.AnalysisReport
  alias Sebex.ElixirAnalyzer.Span

  test "simple mix.exs" do
    source = """
    defmodule Some.Example.Project do
      use Mix.Project

      @version "0.1.0"

      def project do
        [
          app: :example,
          version: @version,
          elixir: "~> 1.10",
          deps: deps()
        ]
      end

      defp deps do
        [
          {:jason, "~> 1.1"},
          {:dialyxir, "~> 1.0.0-rc.7", only: [:dev], runtime: false}
        ]
      end
    end
    """

    report = Sebex.ElixirAnalyzer.analyze_mix_exs_source!(source)

    assert report == %AnalysisReport{
             version: "0.1.0",
             version_span: Span.new(4, 12, 4, 19)
           }
  end
end
