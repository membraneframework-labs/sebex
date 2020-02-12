defmodule Sebex.ElixirAnalyzer.Span do
  @type t :: %__MODULE__{
          start_line: non_neg_integer(),
          start_column: non_neg_integer(),
          end_line: non_neg_integer(),
          end_column: non_neg_integer()
        }

  @derive Jason.Encoder
  @enforce_keys [:start_line, :start_column, :end_line, :end_column]
  defstruct @enforce_keys

  @spec new(
          start_line :: non_neg_integer(),
          start_column :: non_neg_integer(),
          end_line :: non_neg_integer(),
          end_column :: non_neg_integer()
        ) :: t()
  def new(
        start_line,
        start_column,
        end_line,
        end_column
      ) do
    %__MODULE__{
      start_line: start_line,
      start_column: start_column,
      end_line: end_line,
      end_column: end_column
    }
  end

  @spec zero :: t()
  def zero() do
    new(0, 0, 0, 0)
  end

  @spec set(span :: t(), kv :: Keyword.t()) :: t()
  def set(span, kv), do: set(span, kv, :start)

  @spec set(span :: t(), kv :: Keyword.t(), where :: :start | :end) :: t()
  def set(span, kv, :start) do
    %{span | start_line: Keyword.fetch!(kv, :line), start_column: Keyword.fetch!(kv, :column)}
  end

  def set(span, kv, :end) do
    %{span | end_line: Keyword.fetch!(kv, :line), end_column: Keyword.fetch!(kv, :column)}
  end

  @spec literal(literal :: {:literal, Keyword.t(), [term]}) :: t()
  def literal({:literal, meta, [str]}) when is_binary(str) do
    if String.contains?(str, "\n") do
      raise {:error, "finding spans for multiline strings is not implemented"}
    end

    start_line = Keyword.fetch!(meta, :line)
    start_column = Keyword.fetch!(meta, :column)
    delimiter = Keyword.fetch!(meta, :delimiter)
    end_column = start_column + String.length(str) + 2 * String.length(delimiter)
    new(start_line, start_column, start_line, end_column)
  end

  def literal({:literal, meta, [atom]}) when is_atom(atom) do
    start_line = Keyword.fetch!(meta, :line)
    start_column = Keyword.fetch!(meta, :column)
    end_column = start_column + String.length(Macro.to_string(atom))
    new(start_line, start_column, start_line, end_column)
  end
end
