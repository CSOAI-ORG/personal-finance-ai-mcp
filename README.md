# Personal Finance AI MCP Server

**Financial Planning Intelligence**

Built by [MEOK AI Labs](https://meok.ai)

---

An MCP server for personal financial planning. Track budgets against recommended allocations, calculate compound savings growth, plan debt payoff with avalanche or snowball strategies, analyze investment portfolios, and estimate US federal taxes.

## Tools

| Tool | Description |
|------|-------------|
| `track_budget` | Analyze spending against recommended 50/30/20 budget allocations |
| `calculate_savings` | Calculate time to savings goal with compound interest and inflation |
| `plan_debt_payoff` | Create avalanche or snowball debt payoff plans with interest savings |
| `analyze_investment` | Model investment growth with asset allocation and risk scenarios |
| `estimate_tax` | Estimate US federal income tax with bracket breakdown and FICA |

## Quick Start

```bash
pip install personal-finance-ai-mcp
```

### Claude Desktop

```json
{
  "mcpServers": {
    "personal-finance-ai": {
      "command": "python",
      "args": ["-m", "server"],
      "cwd": "/path/to/personal-finance-ai-mcp"
    }
  }
}
```

### Direct Usage

```bash
python server.py
```

## Rate Limits

| Tier | Requests/Hour |
|------|--------------|
| Free | 60 |
| Pro | 5,000 |

## License

MIT - see [LICENSE](LICENSE)

---

*Part of the MEOK AI Labs MCP Marketplace*
