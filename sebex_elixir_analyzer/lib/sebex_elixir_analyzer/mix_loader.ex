defmodule Sebex.ElixirAnalyzer.MixLoader do
  @spec from_source!(source :: String.t()) :: Keyword.t()
  def from_source!(source) do
    {{:module, module, _, _}, _} = Code.eval_string(source, file: "mix.exs")

    project_info = apply(module, :project, [])

    :code.delete(module)
    :code.purge(module)

    project_info
  end
end
