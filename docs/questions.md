# Frequently asked questions

## About project governance

### Where is this project coming from?

The Plumby project is an initiative from European teams of Dimension Data. It is supported by experts in data centres and in cloud architecture.

### Is this software available to anyone?

Yes. The software and the documentation have been open-sourced from the outset, so that it can be useful to the global community of MCP practioners. The Plumby project is based on the [Apache License](https://www.apache.org/licenses/LICENSE-2.0).

### Do you accept contributions to this project?

Yes. There are multiple ways for end-users and for non-developers to [contribute to this project](contributing.md). For example, if you hit an issue, please report it at GitHub. This is where we track issues and report on corrective actions.

And if you know [how to clone a GitHub project](https://help.github.com/articles/cloning-a-repository/), we are happy to consider [pull requests](https://help.github.com/articles/about-pull-requests/) with your modifications. This is the best approach to submit additional reference configuration files, or updates of the documentation, or even evolutions of the python code.

## About project design

### What is needed to deploy Plumby?

The minimum viable solution we could think of is really compact:
* a computer that runs `spark-plumbery`, and that has access to public Internet over HTTPS,
* MCP credentials so that the bot can interact with the Dimension Data API,
* some instructions and goodwill :-)
