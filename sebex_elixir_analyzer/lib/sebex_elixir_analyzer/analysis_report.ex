defmodule Sebex.ElixirAnalyzer.AnalysisReport do
  alias Sebex.ElixirAnalyzer.HexInfo
  alias Sebex.ElixirAnalyzer.SourceAnalysis.Dependency
  alias Sebex.ElixirAnalyzer.Span

  @type t :: %__MODULE__{
          package: String.t(),
          version: String.t(),
          version_span: Span.t(),
          dependencies: list(Dependency.t()),
          hex: HexInfo.t()
        }

  @derive Jason.Encoder
  @enforce_keys [:package, :version, :version_span]
  defstruct @enforce_keys ++ [dependencies: [], hex: HexInfo.private()]
end
