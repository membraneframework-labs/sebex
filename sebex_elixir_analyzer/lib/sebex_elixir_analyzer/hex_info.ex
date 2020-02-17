defmodule Sebex.ElixirAnalyzer.HexInfo do
  alias __MODULE__.ReleaseInfo

  @type published_info :: %__MODULE__{
          published: true,
          versions: list(ReleaseInfo.t())
        }

  @type private_info :: %__MODULE__{
          published: false
        }

  @type t :: published_info | private_info

  @derive Jason.Encoder
  @enforce_keys [:published]
  defstruct @enforce_keys ++ [:versions]

  defmodule ReleaseInfo do
    @type t :: %__MODULE__{
            version: String.t(),
            retired: boolean
          }

    @derive Jason.Encoder
    @enforce_keys [:version]
    defstruct @enforce_keys ++ [retired: false]
  end

  @spec published(versions: list(ReleaseInfo.t())) :: published_info
  def published(versions) do
    %__MODULE__{published: true, versions: versions}
  end

  @spec private :: private_info
  def private do
    %__MODULE__{published: false}
  end

  @spec fetch!(package :: String.t()) :: t
  def fetch!(package) do
    config = :hex_core.default_config()

    case :hex_api_package.get(config, package) do
      {:ok, {code, _, body}} when code in 200..299 ->
        body
        |> process_ok_response()
        |> published()

      {:ok, {404, _, _}} ->
        private()

      other ->
        raise "failed to fetch package info: #{inspect(other)}"
    end
  end

  defp process_ok_response(%{"releases" => releases, "retirements" => retirements}) do
    retirements = retirements |> Map.keys() |> Enum.map(&to_string/1)

    for %{"version" => version} <- releases, into: [] do
      %ReleaseInfo{
        version: version,
        retired: version in retirements
      }
    end
  end
end
