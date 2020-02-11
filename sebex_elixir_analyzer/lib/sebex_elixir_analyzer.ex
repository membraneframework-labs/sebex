defmodule Sebex.ElixirAnalyzer do
  alias Sebex.ElixirAnalyzer.AnalysisReport
  alias Sebex.ElixirAnalyzer.Span

  @spec analyze_mix_exs_file!(path :: Path.t()) :: AnalysisReport.t() | no_return
  def analyze_mix_exs_file!(path) do
    analyze_mix_exs_source!(File.read!(path))
  end

  @spec analyze_mix_exs_source!(source :: String.t()) :: AnalysisReport.t() | no_return
  def analyze_mix_exs_source!(source) do
    ast = parse!(source)

    {version, version_span} =
      case extract_version_attr(ast) do
        {:ok, version, version_span} -> {version, version_span}
        nil -> raise {:error, :version_attr_not_found}
      end

    %AnalysisReport{version: version, version_span: version_span}
  end

  @spec parse!(source :: String.t()) :: Macro.t() | no_return
  defp parse!(source) do
    Code.string_to_quoted!(source,
      columns: true,
      token_metadata: true,
      literal_encoder: &encode_literal/2
    )
  end

  defp encode_literal(lit, meta) do
    {:ok, {:literal, meta, [lit]}}
  end

  @spec extract_version_attr(ast :: Macro.t()) :: {:ok, String.t(), Span.t()} | nil
  defp extract_version_attr(ast) do
    {_, result} =
      Bunch.Macro.prewalk_while(ast, nil, fn
        t, {:ok, _} = acc ->
          {:skip, t, acc}

        {:@, _, [{:version, _, [{:literal, _, [token]} = literal]}]} = t, _
        when is_binary(token) ->
          {:skip, t, {:ok, token, Span.literal(literal)}}

        t, acc ->
          {:enter, t, acc}
      end)

    result
  end
end
