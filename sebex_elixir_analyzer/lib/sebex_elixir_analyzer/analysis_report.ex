defmodule Sebex.ElixirAnalyzer.AnalysisReport do
  alias Sebex.ElixirAnalyzer.Span

  @type t :: %__MODULE__{
          version: String.t(),
          version_span: Span.t()
        }

  @derive Jason.Encoder
  @enforce_keys [:version, :version_span]
  defstruct @enforce_keys
end
