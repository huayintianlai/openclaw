const plugin = {
    id: "tavily-search-plugin",
    name: "Tavily Web Search",
    description: "Web search tool powered by Tavily.",
    configSchema: {},
    register(api) {
        api.registerTool({
            name: "tavily_search",
            label: "Tavily Search",
            description: "Search the web for real-time information and up-to-date data using Tavily.",
            parameters: {
                type: "object",
                properties: { query: { type: "string", description: "The search query" } },
                required: ["query"]
            },
            async execute(toolCallId, params) {
                const apiKey = process.env.TAVILY_API_KEY;
                if (!apiKey) {
                    return {
                        content: [{ type: "text", text: "Error: TAVILY_API_KEY environment variable is missing" }],
                        isError: true,
                    };
                }

                try {
                    const res = await fetch("https://api.tavily.com/search", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            api_key: apiKey,
                            query: params.query,
                            search_depth: "advanced",
                            include_answer: true,
                            include_raw_content: false,
                            max_results: 5,
                        }),
                    });

                    if (!res.ok) {
                        const err = await res.text();
                        return {
                            content: [{ type: "text", text: `Tavily API error: ${err}` }],
                            isError: true,
                        };
                    }

                    const data = await res.json();
                    let resultText = data.answer ? `Tavily Summary: ${data.answer}\n\n` : "";
                    if (data.results && data.results.length > 0) {
                        resultText += data.results.map(r => `Title: ${r.title}\nURL: ${r.url}\nContent: ${r.content}\n`).join("\n");
                    } else {
                        resultText += "No results found.";
                    }

                    return {
                        content: [{ type: "text", text: resultText }],
                    };
                } catch (error) {
                    return {
                        content: [{ type: "text", text: `Request failed: ${error.message}` }],
                        isError: true,
                    };
                }
            }
        });

        api.registerTool({
            name: "tavily_fetch",
            label: "Tavily Fetch",
            description: "Fetch and extract text content from a specific URL using Tavily Extract.",
            parameters: {
                type: "object",
                properties: { url: { type: "string" } },
                required: ["url"]
            },
            async execute(toolCallId, params) {
                const apiKey = process.env.TAVILY_API_KEY;
                if (!apiKey) {
                    return { content: [{ type: "text", text: "Error: TAVILY_API_KEY missing" }], isError: true };
                }
                try {
                    const res = await fetch("https://api.tavily.com/extract", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ api_key: apiKey, urls: [params.url] })
                    });

                    if (!res.ok) {
                        return { content: [{ type: "text", text: `Tavily API error: await res.text()` }], isError: true };
                    }
                    const data = await res.json();
                    const resultItem = data.results && data.results[0];
                    const text = resultItem && resultItem.rawContent ? resultItem.rawContent : "No content extracted.";
                    return { content: [{ type: "text", text }] };
                } catch (error) {
                    return { content: [{ type: "text", text: `Request failed: ${error.message}` }], isError: true };
                }
            }
        });
    }
};

module.exports = plugin;
