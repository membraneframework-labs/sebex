defmodule Sebex.ElixirAnalyzer.AnalysisReport do
  alias Sebex.ElixirAnalyzer.Span

  @type t :: %__MODULE__{
          version: String.t(),
          version_span: Span.t(),
          dependencies: list(__MODULE__.Dependency.t())
        }

  @derive Jason.Encoder
  @enforce_keys [:version, :version_span, :dependencies]
  defstruct @enforce_keys

  defmodule Dependency do
    @type t :: %__MODULE__{
            name: atom,
            version_spec: String.t() | map(),
            version_spec_span: Span.t()
          }

    @derive Jason.Encoder
    @enforce_keys [:name, :version_spec, :version_spec_span]
    defstruct @enforce_keys
  end
end
