defmodule Sebex.ElixirAnalyzer.AnalysisReport do
  alias Sebex.ElixirAnalyzer.Span

  @type t :: %__MODULE__{
          package: String.t(),
          version: String.t(),
          version_span: Span.t(),
          dependencies: list(__MODULE__.Dependency.t())
        }

  @derive Jason.Encoder
  @enforce_keys [:package, :version, :version_span]
  defstruct @enforce_keys ++ [dependencies: []]

  defmodule Dependency do
    @type t :: %__MODULE__{
            name: atom,
            version_spec: String.t() | map(),
            version_spec_span: Span.t(),
            version_lock: String.t() | nil
          }

    @derive Jason.Encoder
    @enforce_keys [:name, :version_spec, :version_spec_span]
    defstruct @enforce_keys ++ [version_lock: nil]
  end
end
