defmodule Sebex.ElixirAnalyzer.SourceAnalysis.Parser do
  @spec parse_string!(String.t()) :: Macro.t() | no_return
  def parse_string!(source) do
    Code.string_to_quoted!(
      source,
      columns: true,
      token_metadata: true,
      literal_encoder: &encode_literal/2
    )
  end

  @spec encode_literal(lit :: term, meta :: Keyword.t()) :: Macro.t()
  def encode_literal(lit, meta) do
    {:ok, {:literal, meta, [lit]}}
  end

  @spec decode_literal(ast :: Macro.t()) :: term
  def decode_literal(ast) do
    Macro.prewalk(ast, fn
      {:literal, _, [lit]} -> lit
      node -> node
    end)
  end
end
