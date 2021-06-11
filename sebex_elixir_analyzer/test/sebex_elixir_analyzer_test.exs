defmodule Sebex.ElixirAnalyzerTest do
  use ExUnit.Case
  doctest Sebex.ElixirAnalyzer
  import Mock

  alias Sebex.ElixirAnalyzer.AnalysisReport
  alias Sebex.ElixirAnalyzer.HexInfo
  alias Sebex.ElixirAnalyzer.HexInfo.ReleaseInfo
  alias Sebex.ElixirAnalyzer.SourceAnalysis.Dependency
  alias Sebex.ElixirAnalyzer.Span

  setup_with_mocks(
    [
      {:hex_api_package, [],
       [
         get: fn
           _, "ecto" ->
             {:ok,
              {200, %{},
               %{
                 "inserted_at" => "2014-05-01T20:05:49Z",
                 "name" => "ecto",
                 "releases" => [
                   %{
                     "inserted_at" => "2020-02-14T13:50:25Z",
                     "version" => "3.3.3"
                   },
                   %{
                     "inserted_at" => "2020-01-28T09:49:31Z",
                     "version" => "3.3.2"
                   },
                   %{
                     "inserted_at" => "2019-12-27T18:32:27Z",
                     "version" => "3.3.1"
                   }
                 ],
                 "repository" => "hexpm",
                 "retirements" => %{
                   "3.3.2": %{"message" => nil, "reason" => "deprecated"}
                 },
                 "updated_at" => "2020-02-14T13:50:29Z"
               }}}

           _, _ ->
             {:ok, {404, %{}, %{}}}
         end
       ]}
    ],
    do: :ok
  )

  @simple_mix_exs ~S"""
  defmodule Some.Example.Project do
    use Mix.Project

    @version "0.1.0"

    def project do
      [
        app: :example,
        version: @version,
        elixir: "~> 1.10",
        deps: deps()
      ]
    end

    defp deps do
      [
        {:jason, "~> 1.1"},
        {:dialyxir, "~> 1.0.0-rc.7", only: [:dev], runtime: false},
        {:bunch, github: "membraneframework/bunch"},
        {:dep_from_git, git: "https://github.com/elixir-lang/my_dep.git", tag: "0.1.0"}
      ]
    end
  end
  """

  test "simple mix.exs" do
    report = Sebex.ElixirAnalyzer.analyze_mix_exs_source!(@simple_mix_exs)

    assert report == %AnalysisReport{
             package: "example",
             version: "0.1.0",
             version_span: Span.new(4, 12, 4, 19),
             dependencies: [
               %Dependency{
                 name: :jason,
                 version_spec: "~> 1.1",
                 version_spec_span: Span.new(17, 16, 17, 24)
               },
               %Dependency{
                 name: :dialyxir,
                 version_spec: "~> 1.0.0-rc.7",
                 version_spec_span: Span.new(18, 19, 18, 34)
               },
               %Dependency{
                 name: :bunch,
                 version_spec: %{github: "membraneframework/bunch"},
                 version_spec_span: Span.new(19, 16, 19, 49)
               },
               %Dependency{
                 name: :dep_from_git,
                 version_spec: %{git: "https://github.com/elixir-lang/my_dep.git", tag: "0.1.0"},
                 version_spec_span: Span.new(20, 23, 20, 85)
               }
             ],
             hex: HexInfo.private()
           }
  end

  @mix_exs_with_package_name ~S"""
  defmodule Some.Example.ProjectWithCustomPackageName do
    use Mix.Project

    @version "0.1.0"

    def project do
      [
        app: :app_name,
        version: @version,
        elixir: "~> 1.10",
        package: package(),
        deps: []
      ]
    end

    defp package do
      [
        name: :package_name
      ]
    end
  end
  """

  test "mix.exs with custom package name" do
    report = Sebex.ElixirAnalyzer.analyze_mix_exs_source!(@mix_exs_with_package_name)

    assert report == %AnalysisReport{
             package: "package_name",
             version: "0.1.0",
             version_span: Span.new(4, 12, 4, 19),
             dependencies: [],
             hex: HexInfo.private()
           }
  end

  @ecto_mix_exs ~S"""
  defmodule Ecto.MixProject do
    use Mix.Project

    @version "3.3.3"

    def project do
      [
        app: :ecto,
        version: @version,
        elixir: "~> 1.6",
        deps: deps(),
        consolidate_protocols: Mix.env() != :test,

        # Hex
        description: "A toolkit for data mapping and language integrated query for Elixir",
        package: package(),

        # Docs
        name: "Ecto",
        docs: docs()
      ]
    end

    def application do
      [
        extra_applications: [:logger, :crypto],
        mod: {Ecto.Application, []}
      ]
    end

    defp deps do
      [
        {:decimal, "~> 1.6 or ~> 2.0"},
        {:jason, "~> 1.0", optional: true},
        {:ex_doc, "~> 0.20", only: :docs}
      ]
    end

    defp package do
      [
        maintainers: ["Eric Meadows-Jönsson", "José Valim", "James Fish", "Michał Muskała"],
        licenses: ["Apache-2.0"],
        links: %{"GitHub" => "https://github.com/elixir-ecto/ecto"},
        files:
          ~w(.formatter.exs mix.exs README.md CHANGELOG.md lib) ++
            ~w(integration_test/cases integration_test/support)
      ]
    end

    defp docs do
      [
        main: "Ecto",
        source_ref: "v#{@version}",
        canonical: "http://hexdocs.pm/ecto",
        logo: "guides/images/e.png",
        extra_section: "GUIDES",
        source_url: "https://github.com/elixir-ecto/ecto",
        extras: extras(),
        groups_for_extras: groups_for_extras(),
        groups_for_modules: [
          # Ecto,
          # Ecto.Changeset,
          # Ecto.Multi,
          # Ecto.Query,
          # Ecto.Repo,
          # Ecto.Schema,
          # Ecto.Schema.Metadata,
          # Ecto.Type,
          # Ecto.UUID,
          # Mix.Ecto,

          "Query APIs": [
            Ecto.Query.API,
            Ecto.Query.WindowAPI,
            Ecto.Queryable,
            Ecto.SubQuery
          ],
          "Adapter specification": [
            Ecto.Adapter,
            Ecto.Adapter.Queryable,
            Ecto.Adapter.Schema,
            Ecto.Adapter.Storage,
            Ecto.Adapter.Transaction
          ],
          "Association structs": [
            Ecto.Association.BelongsTo,
            Ecto.Association.Has,
            Ecto.Association.HasThrough,
            Ecto.Association.ManyToMany,
            Ecto.Association.NotLoaded
          ]
        ]
      ]
    end

    def extras() do
      [
        "guides/introduction/Getting Started.md",
        "guides/introduction/Testing with Ecto.md",
        "guides/howtos/Aggregates and subqueries.md",
        "guides/howtos/Composable transactions with Multi.md",
        "guides/howtos/Constraints and Upserts.md",
        "guides/howtos/Data mapping and validation.md",
        "guides/howtos/Dynamic queries.md",
        "guides/howtos/Multi tenancy with query prefixes.md",
        "guides/howtos/Polymorphic associations with many to many.md",
        "guides/howtos/Replicas and dynamic repositories.md",
        "guides/howtos/Schemaless queries.md",
        "guides/howtos/Test factories.md"
      ]
    end

    defp groups_for_extras do
      [
        "Introduction": ~r/guides\/introduction\/.?/,
        "How-To's": ~r/guides\/howtos\/.?/
      ]
    end
  end
  """

  test "Ecto's mix.exs" do
    report = Sebex.ElixirAnalyzer.analyze_mix_exs_source!(@ecto_mix_exs)

    assert report == %AnalysisReport{
             package: "ecto",
             version: "3.3.3",
             version_span: Span.new(4, 12, 4, 19),
             dependencies: [
               %Dependency{
                 name: :decimal,
                 version_spec: "~> 1.6 or ~> 2.0",
                 version_spec_span: Span.new(33, 18, 33, 36)
               },
               %Dependency{
                 name: :jason,
                 version_spec: "~> 1.0",
                 version_spec_span: Span.new(34, 16, 34, 24)
               },
               %Dependency{
                 name: :ex_doc,
                 version_spec: "~> 0.20",
                 version_spec_span: Span.new(35, 17, 35, 26)
               }
             ],
             hex:
               HexInfo.published([
                 %ReleaseInfo{version: "3.3.3"},
                 %ReleaseInfo{version: "3.3.2", retired: true},
                 %ReleaseInfo{version: "3.3.1"}
               ])
           }
  end
end
