# Assistant To The Regional Manager

Number 2 agent that tattletales on you. Telling what a specific
author did on a given day.


## 💅 Motivation

Is following scenario all too familiar to you?:

> [PM] Hey Mike, tomorrow is the last day of the month, can you submit your
> timesheets?
>
> [You (internally)] WT* did I do over the last month???


As a prerequisite for using this tool and in case you didn't already, you
should write descriptive git commit messages.


## 💾 Installation

```
$ uv tool install git+https://github.com/bmike7/assistant_to_the_regional_manager.git
```

## 🔑 Setup

First, authenticate with your Anthropic API key:

```
$ attrm login
Enter your Anthropic API key: sk-ant-...
Authentication successful!
```

Alternatively, you can set the `ANTHROPIC_API_KEY` environment variable.


## 🤖 Example usage

```
$ attrm --help
Usage: attrm [OPTIONS] COMMAND [ARGS]...

  Assistant To The Regional Manager

  Run `attrm login` to set up authentication with your Anthropic API key.

Options:
  --help  Show this message and exit.

Commands:
  config      Configures which `git` repositories you want to report on
  login       Set up authentication with Anthropic API
  logout      Remove stored authentication credentials
  tattletale  Summarize what `author` did on given day
```

```
$ attrm config
Where are your repositories located?: ~/repos
Track following repos:
...
(x) ~/repos/personal/attrm
( ) ~/repos/personal/gitkit
...

$ attrm tattletale Mike
{
  "project": "~/repos/personal/attrm",
  "day": "2025-11-04 00:00:00",
  "summary": "On 2025-11-04, Mike worked on improving how the program saves and handles its settings, making it cleaner and ensuring it stores them in the right place for each operating system."
}
```

Because it returns `json` you can use it for future automation:

- `attrm tattletale Mike | jq ".summary"`
- if your timesheets can be submitted via an API, you can use this as input
  e.g.: `gitkit sign-off` (with an intermediate step to verify the summary)


### 💡 FYI

I don't use LLM's that often. At least not for coding, but this actually saves
me quite some time.
