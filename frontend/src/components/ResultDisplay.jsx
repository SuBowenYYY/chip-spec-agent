/**
 * 结果展示组件
 * 使用Tab切换显示Markdown预览和提取结果预览
 * 使用 react-markdown 安全渲染 Markdown，避免 XSS 风险
 */

import { useState } from 'react'
import { Tabs, Card, Empty, Typography } from 'antd'
import { FileTextOutlined, CodeOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const { Text } = Typography

function ResultDisplay({ mdContent, extractContent }) {
  const [activeTab, setActiveTab] = useState('markdown')

  // 构建 Tab 项（Ant Design 5 items API，替代已废弃的 TabPane）
  const tabItems = [
    {
      key: 'markdown',
      label: (
        <span>
          <FileTextOutlined />
          Markdown 预览
        </span>
      ),
      children: (
        <div style={{ height: 'calc(100vh - 260px)', overflow: 'auto', padding: 16 }}>
          {mdContent ? (
            <div className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {mdContent}
              </ReactMarkdown>
            </div>
          ) : (
            <Empty description="暂无 Markdown 内容" />
          )}
        </div>
      ),
    },
    {
      key: 'extract',
      label: (
        <span>
          <CodeOutlined />
          提取结果预览
        </span>
      ),
      children: (
        <div style={{ height: 'calc(100vh - 260px)', overflow: 'auto', padding: 16 }}>
          {extractContent ? (
            <pre
              style={{
                background: '#f5f5f5',
                padding: 16,
                borderRadius: 8,
                fontSize: 13,
                lineHeight: 1.5,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {typeof extractContent === 'string'
                ? extractContent
                : JSON.stringify(extractContent, null, 2)}
            </pre>
          ) : (
            <Empty description="暂无提取结果" />
          )}
        </div>
      ),
    },
  ]

  return (
    <Card
      title="转换结果"
      style={{ height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}
      styles={{ body: { flex: 1, overflow: 'hidden', padding: 0 } }}
    >
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
        tabBarStyle={{ padding: '0 16px', marginBottom: 0 }}
      />
    </Card>
  )
}

export default ResultDisplay
