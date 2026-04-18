#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { spawn } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(spawn);

const server = new Server(
  {
    name: 'certificate-workflow-tool',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tool definition
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'edit_certificate',
        description: '编辑法国公证文件（资本存款证明）。当用户说"编辑公证文件"、"修改资本存款证明"、"生成公证文件"时使用此工具。',
        inputSchema: {
          type: 'object',
          properties: {
            company_name: {
              type: 'string',
              description: '公司名称（例如：FinalTest SARL）',
            },
            address: {
              type: 'string',
              description: '公司地址（例如：123 Rue de Paris, 75001 Paris）',
            },
            deposit_date: {
              type: 'string',
              description: '资本存款日期（YYYY-MM-DD 格式，留空默认为两天后）',
            },
            sign_date: {
              type: 'string',
              description: '落款日期（YYYY-MM-DD 格式，留空默认为两天后）',
            },
          },
          required: ['company_name', 'address'],
        },
      },
    ],
  };
});

// Tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === 'edit_certificate') {
    const { company_name, address, deposit_date = '', sign_date = '' } = request.params.arguments;

    try {
      const scriptPath = '/Volumes/KenDisk/Coding/openclaw-runtime/workspace/certificate_workflow.py';

      return new Promise((resolve, reject) => {
        const process = spawn('python3', [
          scriptPath,
          company_name,
          address,
          deposit_date,
          sign_date
        ]);

        let stdout = '';
        let stderr = '';

        process.stdout.on('data', (data) => {
          stdout += data.toString();
        });

        process.stderr.on('data', (data) => {
          stderr += data.toString();
        });

        process.on('close', (code) => {
          if (code === 0) {
            // Extract PDF path from output
            const pdfMatch = stdout.match(/__OPENCLAW_OUTPUT_FILE__:(.+)/);
            const pdfPath = pdfMatch ? pdfMatch[1].trim() : '';

            resolve({
              content: [
                {
                  type: 'text',
                  text: `✅ 公证文件生成成功！\n\n${stdout}\n\nPDF 文件路径: ${pdfPath}`,
                },
              ],
            });
          } else {
            reject(new Error(`工作流执行失败 (exit code ${code}):\n${stderr}\n${stdout}`));
          }
        });

        process.on('error', (error) => {
          reject(new Error(`无法启动工作流: ${error.message}`));
        });
      });
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `❌ 错误: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }

  throw new Error(`Unknown tool: ${request.params.name}`);
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Certificate Workflow MCP server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
