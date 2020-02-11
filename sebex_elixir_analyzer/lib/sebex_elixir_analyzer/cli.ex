defmodule Sebex.ElixirAnalyzer.CLI do
  def main(["--mix", path]) do
    path
    |> Sebex.ElixirAnalyzer.analyze_mix_exs_file!()
    |> Jason.encode!()
    |> IO.puts()
  end

  def main(_args) do
    IO.puts("usage: sebex_elixir_analyzer --mix PATH_TO_MIX_EXS")
    System.stop(1)
  end
end
