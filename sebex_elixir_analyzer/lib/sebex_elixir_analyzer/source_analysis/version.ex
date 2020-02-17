defmodule Sebex.ElixirAnalyzer.SourceAnalysis.Version do
  alias Sebex.ElixirAnalyzer.Span

  @type t :: String.t()

  @spec extract(Macro.t()) :: {t(), Span.t()} | nil
  def extract(ast) do
    {_, result} =
      Bunch.Macro.prewalk_while(ast, nil, fn
        t, {_, _} = acc ->
          {:skip, t, acc}

        {:@, _, [{:version, _, [{:literal, _, [token]} = literal]}]} = t, _
        when is_binary(token) ->
          {:skip, t, {token, Span.literal(literal)}}

        t, acc ->
          {:enter, t, acc}
      end)

    result
  end
end
