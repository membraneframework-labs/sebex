defmodule Sebex.ElixirAnalyzer.MixLock do
  @type t :: %{required(String.t()) => tuple}

  # Dialyzer is going crazy here, do not know why...
  @dialyzer {:nowarn_function, {:from_string!, 1}}
  @spec from_string!(String.t() | nil) :: t() | no_return
  def from_string!(nil), do: %{}

  def from_string!(source) do
    # Based on https://github.com/elixir-lang/elixir/blob/27bd9ffcc607b74ce56b547cb6ba92c9012c317c/lib/mix/lib/mix/dep/lock.ex#L8-L25

    opts = [warn_on_unnecessary_quotes: false]

    with {:ok, quoted} <- Code.string_to_quoted(source, opts),
         {%{} = lock, _} <- Code.eval_quoted(quoted, [], opts) do
      lock
    else
      _ -> raise {:error, :failed_to_parse_mix_lock}
    end
  end

  @spec versions(lock :: t()) :: %{} | %{required(String.t()) => String.t()}
  def versions(lock) do
    lock
    |> Enum.map(fn {name, tuple} -> {name, extract_version_from_tuple(tuple)} end)
    |> Enum.filter(fn {_, v} -> is_binary(v) end)
    |> Enum.into(%{})
  end

  @spec extract_version_from_tuple(tuple) :: String.t() | nil
  defp extract_version_from_tuple(tuple) when elem(tuple, 0) == :hex, do: elem(tuple, 2)
  defp extract_version_from_tuple(_), do: nil
end
