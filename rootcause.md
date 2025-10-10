Root cause analysis: CLI AppConfig ValidationError
===============================================

Summary
-------

Invoking the CLI entrypoints (api, cli, workers) failed with a pydantic ValidationError raised
while constructing `AppConfig`. The failing field is `maxroll_parser`, which is required but
has no default value. The DI container registers `config = providers.Singleton(AppConfig)`, so
the provider attempts to construct `AppConfig` with no user-provided values, triggering the
validation error.

Evidence
--------

Traceback (shortened):

  File "src/d3_item_salvager/__main__.py", line 89, in cli
    run_cli()
  File ".../dependency_injector/wiring.py", line 1193, in _patched
    with resolver as kwargs:
  File ".../pydantic_settings/main.py", line 193, in __init__
    super().__init__(...)
  File ".../pydantic/main.py", line 250, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance)
pydantic_core._pydantic_core.ValidationError: 1 validation error for AppConfig
maxroll_parser
  Field required [type=missing, input_value={}, input_type=dict]

Observations
------------

- `AppConfig` defined in `src/d3_item_salvager/config/settings.py` declares `maxroll_parser`
  without a default, so BaseSettings requires it.
- The DI Container (`src/d3_item_salvager/container.py`) exposes `config = providers.Singleton(AppConfig)`
  which will instantiate AppConfig at runtime when the provider is called by the wiring system.
- CLI entrypoint wiring (via `container.wire(...)` and `@inject` decorators) causes the provider to be
  resolved at command invocation time, exposing the missing-field error.

Fix direction
-------------

Two practical, low-risk options:

1. Provide a default factory for `maxroll_parser` on `AppConfig` (quick and safe). Example:

   maxroll_parser: MaxrollParserConfig = Field(default_factory=MaxrollParserConfig)

2. Change the container registration to a provider that lazily builds AppConfig from environment,
   e.g. `providers.Singleton(AppConfig.from_env)` or similar if present.

I will apply option (1) to keep the change minimal and consistent with other fields that already
use `Field(default_factory=...)`.

Files relevant
--------------

- src/d3_item_salvager/config/settings.py -- defines AppConfig
- src/d3_item_salvager/container.py -- registers AppConfig provider
- src/d3_item_salvager/__main__.py -- Typer CLI entrypoint that wires container and calls commands

Test reproduction
-----------------

A pytest that invokes the Typer CLI subcommand reproduces the error (see `tests/cli/test_entrypoints.py`).
