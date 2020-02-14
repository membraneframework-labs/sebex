defmodule Sebex.ElixirAnalyzerTest do
  use ExUnit.Case
  doctest Sebex.ElixirAnalyzer

  alias Sebex.ElixirAnalyzer.AnalysisReport
  alias Sebex.ElixirAnalyzer.Span

  @simple_mix_exs """
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

  @simple_mix_lock """
  %{
    "bunch": {:git, "https://github.com/membraneframework/bunch.git", "3ac44d6b6ca74b87342c4e9bb86889009f35f39e", []},
    "dialyxir": {:hex, :dialyxir, "1.0.0-rc.7", "6287f8f2cb45df8584317a4be1075b8c9b8a69de8eeb82b4d9e6c761cf2664cd", [:mix], [{:erlex, ">= 0.2.5", [hex: :erlex, repo: "hexpm", optional: false]}], "hexpm", "506294d6c543e4e5282d4852aead19ace8a35bedeb043f9256a06a6336827122"},
    "erlex": {:hex, :erlex, "0.2.5", "e51132f2f472e13d606d808f0574508eeea2030d487fc002b46ad97e738b0510", [:mix], [], "hexpm", "756d3e19b056339af674b715fdd752c5dac468cf9d0e2d1a03abf4574e99fbf8"},
    "jason": {:hex, :jason, "1.1.2", "b03dedea67a99223a2eaf9f1264ce37154564de899fd3d8b9a21b1a6fd64afe7", [:mix], [{:decimal, "~> 1.0", [hex: :decimal, repo: "hexpm", optional: true]}], "hexpm", "fdf843bca858203ae1de16da2ee206f53416bbda5dc8c9e78f43243de4bc3afe"},
  }
  """

  test "simple mix.exs with lock" do
    report = Sebex.ElixirAnalyzer.analyze_mix_exs_source!(@simple_mix_exs, @simple_mix_lock)

    assert report == %AnalysisReport{
             package: "example",
             version: "0.1.0",
             version_span: Span.new(4, 12, 4, 19),
             dependencies: [
               %AnalysisReport.Dependency{
                 name: :jason,
                 version_spec: "~> 1.1",
                 version_spec_span: Span.new(17, 16, 17, 24),
                 version_lock: "1.1.2"
               },
               %AnalysisReport.Dependency{
                 name: :dialyxir,
                 version_spec: "~> 1.0.0-rc.7",
                 version_spec_span: Span.new(18, 19, 18, 34),
                 version_lock: "1.0.0-rc.7"
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

  @mix_exs_with_package_name """
  defmodule Some.Example.ProjectWithCustomPackageName do
    use Mix.Project

    @version "0.1.0"

    def project do
      [
        app: :app_name,
        version: @version,
        elixir: "~> 1.10",
        package: package(),
        deps: []
      ]
    end

    defp package do
      [
        name: :package_name
      ]
    end
  end
  """

  test "mix.exs with custom package name" do
    report = Sebex.ElixirAnalyzer.analyze_mix_exs_source!(@mix_exs_with_package_name)

    assert report == %AnalysisReport{
             package: "package_name",
             version: "0.1.0",
             version_span: Span.new(4, 12, 4, 19),
             dependencies: []
           }
  end
end
