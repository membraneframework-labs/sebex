defmodule Sebex.ElixirAnalyzer.SourceAnalysis.Dependency do
  alias Sebex.ElixirAnalyzer.SourceAnalysis.Parser
  alias Sebex.ElixirAnalyzer.Span

  @type t :: %__MODULE__{
          name: atom,
          version_spec: String.t() | map(),
          version_spec_span: Span.t()
        }

  @derive Jason.Encoder
  @enforce_keys [:name, :version_spec, :version_spec_span]
  defstruct @enforce_keys

  @spec extract(Macro.t()) :: list(t())
  def extract(ast) do
    ast
    |> extract_deps_list()
    |> Enum.map(&process_dep/1)
  end

  @spec extract_deps_list(Macro.t()) :: list(Macro.t())
  defp extract_deps_list(ast) do
    {_, result} =
      Bunch.Macro.prewalk_while(ast, :not_found, fn
        t, {:found, _} = acc ->
          {:skip, t, acc}

        {kw_def, _,
         [
           {:deps, _, args},
           [
             {
               {:literal, _, [:do]},
               {:literal, _, [deps_list]}
             }
           ]
         ]} = t,
        :not_found
        when kw_def in [:def, :defp] and is_list(deps_list) and args in [[], nil] ->
          {:skip, t, {:found, deps_list}}

        t, :not_found ->
          {:enter, t, :not_found}
      end)

    case result do
      {:found, l} -> l
      :not_found -> []
    end
  end

  @spec process_dep(Macro.t()) :: t()
  defp process_dep(
         {:literal, _,
          [
            {
              {:literal, _, [name]},
              {:literal, _, [version_spec]} = version_literal
            }
          ]}
       )
       when is_atom(name) and is_binary(version_spec) do
    %__MODULE__{
      name: name,
      version_spec: version_spec,
      version_spec_span: Span.literal(version_literal)
    }
  end

  defp process_dep(
         {:{}, _,
          [
            {:literal, _, [name]},
            {:literal, _, [version_spec]} = version_literal,
            _
          ]}
       )
       when is_atom(name) and is_binary(version_spec) do
    %__MODULE__{
      name: name,
      version_spec: version_spec,
      version_spec_span: Span.literal(version_literal)
    }
  end

  defp process_dep(
         {:literal, tuple_meta,
          [
            {
              {:literal, _, [name]},
              [{first_key, _} | _] = kw
            }
          ]}
       )
       when is_atom(name) do
    %__MODULE__{
      name: name,
      version_spec:
        kw
        |> Parser.decode_literal()
        |> Enum.into(%{}),
      version_spec_span:
        first_key
        |> Span.literal()
        |> Span.set(Keyword.fetch!(tuple_meta, :closing), :end)
    }
  end
end
