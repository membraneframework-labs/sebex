defmodule Sebex.ElixirAnalyzer do
  alias Sebex.ElixirAnalyzer.AnalysisReport
  alias Sebex.ElixirAnalyzer.MixLoader
  alias Sebex.ElixirAnalyzer.MixLock
  alias Sebex.ElixirAnalyzer.SourceAnalysis

  @spec analyze_mix_exs_file!(path :: Path.t()) :: AnalysisReport.t() | no_return
  def analyze_mix_exs_file!(path) do
    mix_exs_source = File.read!(path)

    mix_lock_path =
      path
      |> Path.dirname()
      |> Path.join("mix.lock")

    mix_lock_source =
      case File.read(mix_lock_path) do
        {:ok, source} -> source
        {:error, :enoent} -> nil
        {:error, e} -> raise {:error, {:failed_to_read_mix_lock, e}}
      end

    analyze_mix_exs_source!(mix_exs_source, mix_lock_source)
  end

  @spec analyze_mix_exs_source!(
          mix_exs_source :: String.t(),
          mix_lock_source :: String.t() | nil
        ) :: AnalysisReport.t() | no_return
  def analyze_mix_exs_source!(mix_exs_source, mix_lock_source \\ nil) do
    project_info = MixLoader.from_source!(mix_exs_source)

    package_name =
      (get_in(project_info, [:package, :name]) ||
         get_in(project_info, [:app]) ||
         raise({:error, :package_name_undefined}))
      |> to_string

    ast = SourceAnalysis.Parser.parse_string!(mix_exs_source)

    {version, version_span} =
      case SourceAnalysis.Version.extract(ast) do
        nil -> raise {:error, :version_attr_not_found}
        x -> x
      end

    version_locks =
      mix_lock_source
      |> MixLock.from_string!()
      |> MixLock.versions()

    dependencies =
      ast
      |> SourceAnalysis.Dependency.extract()
      |> Enum.map(&%{&1 | version_lock: Map.get(version_locks, &1.name, nil)})

    %AnalysisReport{
      package: package_name,
      version: version,
      version_span: version_span,
      dependencies: dependencies
    }
  end
end
