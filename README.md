# stubb

[![PyPI](https://img.shields.io/pypi/v/stubb.svg)](https://pypi.org/project/stubb/)
[![Tests](https://github.com/deneutoy/stubb/actions/workflows/test.yml/badge.svg)](https://github.com/deneutoy/stubb/actions/workflows/test.yml)
[![Changelog](https://img.shields.io/github/v/release/deneutoy/stubb?include_prereleases&label=changelog)](https://github.com/deneutoy/stubb/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/deneutoy/stubb/blob/main/LICENSE)

Stubb is a library for creating and evaluating structured outputs from language models.

## Installation

Install this library using `pip`:
```bash
pip install stubb
```
## Usage

Usage instructions go here.



## Other Libraries

Stubb is similar in spirit to several other libraries, including:

- [instructor](https://github.com/jxnl/instructor/)
- [guardrails](https://github.com/guardrails-ai/guardrails/tree/main)
- [outlines](https://github.com/outlines-dev/outlines)

It is different in the following ways:

Instructor uses the OpenAI API, and uses the function calling to generate json. Stubb is similar, but uses constrained decoding via a grammar to generate json, which is compatible with many open source language models.

Guardrails uses a custom xml specification, (`.rail`), as well as Pydantic models to generate json. Stubb is similar, but has a much simpler API and tries to do "less things". Both Instructor and Guardrails support re-running model APIs based on complex post-validation (i.e not purely a schema). Stubb does not do this.

Outlines takes a similar approach to to Stubb to generate valid Pydantic models, but it uses regex parsing to do constrained decoding. This is written in Python and accelerated, during sampling, with Numba. In constrast, Stubb uses a GBNF grammar, which is supported in C++ directly via the [llama.cpp](https://github.com/ggerganov/llama.cpp?tab=readme-ov-file#constrained-output-with-grammars) project.

Stubb is designed to be simple to use, and not to do "too much for you". It uses validated technologies like Pydantic, FastAPI, Sqlite, and is modular - you can use the components you want, and not the ones you don't.


## Development

To contribute to this library, first checkout the code. Then create a new virtual environment:
```bash
cd stubb
python -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
pytest
```
