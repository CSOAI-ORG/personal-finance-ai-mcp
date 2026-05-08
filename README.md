<div align="center">

# Personal Finance Ai MCP

**Personal Finance AI MCP Server - Financial Planning Intelligence**

[![PyPI](https://img.shields.io/pypi/v/meok-personal-finance-ai-mcp)](https://pypi.org/project/meok-personal-finance-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Personal Finance AI MCP Server - Financial Planning Intelligence
Built by MEOK AI Labs | https://meok.ai

Budget tracking, savings calculations, debt payoff planning,
investment analysis, and tax estimation.

## Tools

| Tool | Description |
|------|-------------|
| `track_budget` | Analyze spending against recommended budget allocations. |
| `calculate_savings` | Calculate time to reach a savings goal with compound interest. |
| `plan_debt_payoff` | Create a debt payoff plan using avalanche or snowball method. |
| `analyze_investment` | Analyze investment growth with asset allocation modeling. |
| `estimate_tax` | Estimate US federal income tax liability. |

## Installation

```bash
pip install meok-personal-finance-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "personal-finance-ai": {
      "command": "python",
      "args": ["-m", "meok_personal_finance_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 5 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
