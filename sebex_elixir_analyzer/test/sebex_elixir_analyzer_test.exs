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
          {:dialyxir, "~> 1.0.0-rc.7", only: [:dev], runtime: false},
          {:bunch, github: "membraneframework/bunch"},
          {:dep_from_git, git: "https://github.com/elixir-lang/my_dep.git", tag: "0.1.0"}
        ]
      end
    end
    """

    report = Sebex.ElixirAnalyzer.analyze_mix_exs_source!(source)

    assert report == %AnalysisReport{
             version: "0.1.0",
             version_span: Span.new(4, 12, 4, 19),
             dependencies: [
               %AnalysisReport.Dependency{
                 name: :jason,
                 version_spec: "~> 1.1",
                 version_spec_span: Span.new(17, 16, 17, 24)
               },
               %AnalysisReport.Dependency{
                 name: :dialyxir,
                 version_spec: "~> 1.0.0-rc.7",
                 version_spec_span: Span.new(18, 19, 18, 34)
               },
               %AnalysisReport.Dependency{
                 name: :bunch,
                 version_spec: %{github: "membraneframework/bunch"},
                 version_spec_span: Span.new(19, 16, 19, 49)
               },
               %AnalysisReport.Dependency{
                 name: :dep_from_git,
                 version_spec: %{git: "https://github.com/elixir-lang/my_dep.git", tag: "0.1.0"},
                 version_spec_span: Span.new(20, 23, 20, 85)
               }
             ]
           }
  end
end
