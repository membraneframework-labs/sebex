defmodule Sebex.ElixirAnalyzer do
  alias Sebex.ElixirAnalyzer.AnalysisReport
  alias Sebex.ElixirAnalyzer.HexInfo
  alias Sebex.ElixirAnalyzer.MixLoader
  alias Sebex.ElixirAnalyzer.SourceAnalysis

  @spec analyze_mix_exs_file!(path :: Path.t()) :: AnalysisReport.t() | no_return
  def analyze_mix_exs_file!(path) do
    File.read!(path) |> analyze_mix_exs_source!()
  end

  @spec analyze_mix_exs_source!(mix_exs_source :: String.t()) :: AnalysisReport.t() | no_return
  def analyze_mix_exs_source!(mix_exs_source) do
    project_info = MixLoader.from_source!(mix_exs_source)

    package_name =
      (get_in(project_info, [:package, :name]) ||
         get_in(project_info, [:app]) ||
         raise("package name has not been defined"))
      |> to_string

    ast = SourceAnalysis.Parser.parse_string!(mix_exs_source)

    {version, version_span} =
      case SourceAnalysis.Version.extract(ast) do
        nil -> raise "version attribute has not been found"
        x -> x
      end

    dependencies = SourceAnalysis.Dependency.extract(ast)

    hex = HexInfo.fetch!(package_name)

    %AnalysisReport{
      package: package_name,
      version: version,
      version_span: version_span,
      dependencies: dependencies,
      hex: hex
    }
  end
end
