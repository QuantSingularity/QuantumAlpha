import api from "./api";

class MarketService {
  async getMarketOverview() {
    try {
      const response = await new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            data: {
              indices: [
                {
                  symbol: "SPX",
                  name: "S&P 500",
                  value: 5328.42,
                  change: 43.71,
                  changePercent: 0.82,
                  direction: "up",
                },
                {
                  symbol: "NDX",
                  name: "NASDAQ",
                  value: 16742.39,
                  change: 189.5,
                  changePercent: 1.14,
                  direction: "up",
                },
                {
                  symbol: "DJI",
                  name: "DOW",
                  value: 38996.35,
                  change: -50.82,
                  changePercent: -0.13,
                  direction: "down",
                },
                {
                  symbol: "RUT",
                  name: "Russell 2000",
                  value: 2048.67,
                  change: 12.34,
                  changePercent: 0.61,
                  direction: "up",
                },
              ],
              topMovers: {
                gainers: [
                  {
                    symbol: "NVDA",
                    name: "NVIDIA Corp",
                    price: 875.4,
                    changePercent: 4.2,
                  },
                  {
                    symbol: "AMD",
                    name: "Advanced Micro Devices",
                    price: 165.3,
                    changePercent: 3.1,
                  },
                  {
                    symbol: "META",
                    name: "Meta Platforms",
                    price: 520.0,
                    changePercent: 2.8,
                  },
                ],
                losers: [
                  {
                    symbol: "INTC",
                    name: "Intel Corp",
                    price: 30.15,
                    changePercent: -3.2,
                  },
                  {
                    symbol: "PFE",
                    name: "Pfizer Inc",
                    price: 27.4,
                    changePercent: -2.1,
                  },
                  {
                    symbol: "BA",
                    name: "Boeing Co",
                    price: 180.0,
                    changePercent: -1.8,
                  },
                ],
              },
              sectorPerformance: [
                { name: "Technology", changePercent: 1.8 },
                { name: "Healthcare", changePercent: -0.4 },
                { name: "Financials", changePercent: 0.7 },
                { name: "Energy", changePercent: -0.9 },
                { name: "Consumer Discretionary", changePercent: 1.2 },
              ],
              chartData: {
                labels: [
                  "9AM",
                  "10AM",
                  "11AM",
                  "12PM",
                  "1PM",
                  "2PM",
                  "3PM",
                  "4PM",
                ],
                datasets: [
                  {
                    data: [5280, 5290, 5310, 5300, 5320, 5315, 5325, 5328],
                  },
                ],
              },
            },
          });
        }, 600);
      });

      return response.data;
    } catch (error) {
      console.error("Error fetching market overview:", error);
      throw new Error(
        error.response?.data?.message || "Failed to fetch market overview",
      );
    }
  }

  async getLatestNews(limit = 10) {
    try {
      const response = await new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            data: [
              {
                id: "news1",
                title:
                  "Federal Reserve holds rates steady amid inflation concerns",
                summary:
                  "The Fed maintained its benchmark rate in a unanimous decision, signaling a cautious approach to monetary policy.",
                content: "",
                author: "Reuters",
                source: "Reuters",
                url: "https://reuters.com",
                imageUrl: null,
                publishedAt: new Date(Date.now() - 3600000).toISOString(),
                category: "Macro",
                tags: ["Fed", "Interest Rates", "Inflation"],
                sentiment: "neutral",
                relevantSymbols: ["SPY", "TLT", "GLD"],
                isBookmarked: false,
              },
              {
                id: "news2",
                title:
                  "NVIDIA reports record quarterly revenue on AI chip demand",
                summary:
                  "NVIDIA beat earnings estimates as data center revenue surged 427% year-over-year driven by AI infrastructure spending.",
                content: "",
                author: "Bloomberg",
                source: "Bloomberg",
                url: "https://bloomberg.com",
                imageUrl: null,
                publishedAt: new Date(Date.now() - 7200000).toISOString(),
                category: "Earnings",
                tags: ["AI", "Semiconductors", "Earnings"],
                sentiment: "positive",
                relevantSymbols: ["NVDA", "AMD", "INTC"],
                isBookmarked: false,
              },
              {
                id: "news3",
                title:
                  "Oil prices slide as OPEC+ output deal faces uncertainty",
                summary:
                  "Crude oil futures fell over 2% as traders weigh the likelihood of OPEC+ extending production cuts through Q3.",
                content: "",
                author: "WSJ",
                source: "WSJ",
                url: "https://wsj.com",
                imageUrl: null,
                publishedAt: new Date(Date.now() - 10800000).toISOString(),
                category: "Commodities",
                tags: ["Oil", "OPEC", "Energy"],
                sentiment: "negative",
                relevantSymbols: ["XOM", "CVX", "OXY"],
                isBookmarked: false,
              },
              {
                id: "news4",
                title:
                  "Apple unveils next-generation chip architecture at WWDC",
                summary:
                  "Apple announced a major leap in silicon performance with its latest M-series chips offering 40% better efficiency.",
                content: "",
                author: "TechCrunch",
                source: "TechCrunch",
                url: "https://techcrunch.com",
                imageUrl: null,
                publishedAt: new Date(Date.now() - 14400000).toISOString(),
                category: "Technology",
                tags: ["Apple", "Chips", "Hardware"],
                sentiment: "positive",
                relevantSymbols: ["AAPL", "QCOM", "TSM"],
                isBookmarked: false,
              },
              {
                id: "news5",
                title:
                  "Bitcoin crosses $45,000 as institutional demand returns",
                summary:
                  "BTC surged past key resistance as ETF inflows hit a monthly record, signaling renewed institutional appetite.",
                content: "",
                author: "CoinDesk",
                source: "CoinDesk",
                url: "https://coindesk.com",
                imageUrl: null,
                publishedAt: new Date(Date.now() - 18000000).toISOString(),
                category: "Crypto",
                tags: ["Bitcoin", "ETF", "Crypto"],
                sentiment: "positive",
                relevantSymbols: ["BTC", "ETH", "COIN"],
                isBookmarked: false,
              },
            ].slice(0, limit),
          });
        }, 600);
      });

      return response.data;
    } catch (error) {
      console.error("Error fetching latest news:", error);
      throw new Error(error.response?.data?.message || "Failed to fetch news");
    }
  }

  async getAssetQuote(symbol) {
    try {
      const response = await api.get(`/market-data/${symbol}/quote`);
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.message || `Failed to fetch quote for ${symbol}`,
      );
    }
  }

  async searchAssets(query) {
    try {
      const response = await api.get(`/market-data/search?q=${query}`);
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.message || "Failed to search assets",
      );
    }
  }
}

export const marketService = new MarketService();
