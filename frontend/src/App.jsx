import { ConfigProvider, Layout, Typography } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import MainPage from './pages/MainPage'

const { Header, Content } = Layout
const { Title } = Typography

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <Layout style={{ minHeight: '100vh' }}>
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <Title level={4} style={{ margin: 0, color: '#1677ff' }}>
            芯片规格书转换Agent
          </Title>
        </Header>
        <Content style={{ padding: '24px', background: '#f0f2f5' }}>
          <MainPage />
        </Content>
      </Layout>
    </ConfigProvider>
  )
}

export default App
