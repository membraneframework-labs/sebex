defmodule Sebex.ElixirAnalyzer.CLI do
  def main(["--mix", path]) do
    analysis_report =
      path
      |> Sebex.ElixirAnalyzer.analyze_mix_exs_file!()
      |> Jason.encode!()

    ("<SEBEX_ELIXIR_ANALYZER_REPORT>" <> analysis_report <> "</SEBEX_ELIXIR_ANALYZER_REPORT>")
    |> IO.puts()
  end

  def main(_args) do
    IO.puts("usage: sebex_elixir_analyzer --mix PATH_TO_MIX_EXS")
    System.stop(1)
  end
end
