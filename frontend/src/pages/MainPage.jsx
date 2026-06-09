/**
 * 主页面组件
 * 整合所有子组件，管理全局状态
 *
 * 工作流程：
 * 1. 上传PDF → 转换为Markdown（保存为{id}.md）
 * 2. 手动提取参数 → 选择模型 → 从Markdown提取参数（保存为{id}.md）
 */

import { useState, useEffect, useRef } from 'react'
import {
  Row,
  Col,
  Card,
  Button,
  message,
  Progress,
  Typography,
  Space,
  Spin,
  Alert,
  Select,
  Divider,
  Input,
} from 'antd'
import {
  PlayCircleOutlined,
  DownloadOutlined,
  FileSearchOutlined,
  CheckCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import FileUpload from '../components/FileUpload'
import ModelSelector from '../components/ModelSelector'
import ResultDisplay from '../components/ResultDisplay'
import QueryPanel from '../components/QueryPanel'
import {
  getModels,
  startConvert,
  reExtract,
  getConversionStatus,
  getMdDownloadUrl,
  getExtractDownloadUrl,
  listFiles,
} from '../services/api'

const { Title, Text } = Typography

function MainPage() {
  // 模型相关状态
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState(null)
  const [modelsLoading, setModelsLoading] = useState(true)

  // 文件相关状态
  const [fileInfo, setFileInfo] = useState(null)

  // 已有文件列表（用于参数提取）
  const [mdFiles, setMdFiles] = useState([])
  const [filesLoading, setFilesLoading] = useState(false)

  // 转换相关状态
  const [converting, setConverting] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [conversionStatus, setConversionStatus] = useState(null)
  const pollingRef = useRef(null)

  // 提取参数相关状态
  const [extractModel, setExtractModel] = useState(null)
  // 用于参数提取的 conversion_id（支持手动输入或从已有MD选择）
  const [extractConversionId, setExtractConversionId] = useState('')

  // 用于参数提取的芯片型号
  const [chipModel, setChipModel] = useState('')

  // 结果状态
  const [mdContent, setMdContent] = useState(null)
  const [extractContent, setExtractContent] = useState(null)

  // 加载模型列表
  useEffect(() => {
    loadModels()
    loadMdFiles()
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [])

  const loadModels = async () => {
    try {
      const data = await getModels()
      setModels(data.models)
      if (data.models.length > 0) {
        setSelectedModel(data.models[0].name)
        // 默认提取参数也使用第一个模型
        setExtractModel(data.models[0].name)
      }
    } catch (error) {
      message.error('加载模型列表失败')
    } finally {
      setModelsLoading(false)
    }
  }

  // 加载已有MD文件列表
  const loadMdFiles = async () => {
    setFilesLoading(true)
    try {
      const data = await listFiles()
      setMdFiles(data.md_files || [])
    } catch (error) {
      console.error('加载文件列表失败:', error)
    } finally {
      setFilesLoading(false)
    }
  }

  // 文件上传成功回调
  const handleUploadSuccess = (info) => {
    setFileInfo(info)
    setConversionStatus(null)
    setMdContent(null)
    setExtractContent(null)
    // 上传成功后，自动将ID设置为提取参数的默认值
    if (info?.conversionId) {
      setExtractConversionId(info.conversionId)
    }
    // 刷新文件列表
    loadMdFiles()
  }

  // 开始转换（PDF → Markdown）
  const handleStartConvert = async () => {
    if (!fileInfo) {
      message.warning('请先上传PDF文件')
      return
    }
    if (!selectedModel) {
      message.warning('请选择模型')
      return
    }

    setConverting(true)
    setConversionStatus({ phase: 'starting', progress: 0, message: '正在启动转换...' })
    setMdContent(null)
    setExtractContent(null)

    try {
      // 提示词由后端默认提供，不从前端传入
      await startConvert(fileInfo.conversionId, selectedModel)
      message.info('转换任务已启动')

      // 开始轮询状态
      startPolling(fileInfo.conversionId)
    } catch (error) {
      message.error(`启动转换失败: ${error.response?.data?.detail || error.message}`)
      setConverting(false)
    }
  }

  // 开始提取参数
  const handleStartExtract = async () => {
    const targetId = extractConversionId?.trim()
    if (!targetId) {
      message.warning('请选择或输入要提取参数的 Markdown 文件')
      return
    }
    if (!extractModel) {
      message.warning('请选择提取模型')
      return
    }

    setExtracting(true)
    setConversionStatus({ phase: 'extracting', progress: 60, message: '正在提取技术参数...' })

    try {
      // 提示词由后端默认提供，不从前端传入
      await reExtract(targetId, extractModel, chipModel)
      message.info('参数提取任务已启动')

      // 开始轮询状态
      startPolling(targetId)
    } catch (error) {
      message.error(`启动提取失败: ${error.response?.data?.detail || error.message}`)
      setExtracting(false)
    }
  }

  // 轮询转换/提取状态
  const startPolling = (targetId) => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
    }

    pollingRef.current = setInterval(async () => {
      try {
        const status = await getConversionStatus(targetId)
        setConversionStatus(status)

        // 更新结果
        if (status.md_content) {
          setMdContent(status.md_content)
        }
        if (status.extract_result) {
          setExtractContent(status.extract_result)
        }

        // 检查是否完成
        if (
          status.phase === 'success' ||
          status.phase === 'converted' ||
          status.phase === 'failed' ||
          status.phase === 'extract_failed'
        ) {
          clearInterval(pollingRef.current)
          pollingRef.current = null
          setConverting(false)
          setExtracting(false)

          if (status.phase === 'success') {
            message.success('参数提取完成！')
          } else if (status.phase === 'converted') {
            message.success('PDF 转 Markdown 完成！')
          } else if (status.phase === 'extract_failed') {
            message.warning('参数提取失败')
          } else {
            message.error(status.message || '转换失败')
          }
        }
      } catch (error) {
        console.error('轮询状态失败:', error)
      }
    }, 2000) // 每2秒轮询一次
  }

  // 下载文件
  const handleDownloadMd = () => {
    const id = fileInfo?.conversionId
    if (!id) return
    window.open(getMdDownloadUrl(id), '_blank')
  }

  const handleDownloadExtract = () => {
    const id = extractConversionId?.trim() || fileInfo?.conversionId
    if (!id) return
    window.open(getExtractDownloadUrl(id), '_blank')
  }

  // 计算进度百分比
  const progressPercent = conversionStatus?.progress || 0
  const progressStatus =
    conversionStatus?.phase === 'failed' || conversionStatus?.phase === 'extract_failed'
      ? 'exception'
      : conversionStatus?.phase === 'success' || conversionStatus?.phase === 'converted'
        ? 'success'
        : 'active'

  // 合并去重后的MD文件列表（用于下拉选择）
  const allFileIds = [...new Set(mdFiles)]

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <Row gutter={24}>
        {/* 左侧控制面板 */}
        <Col xs={24} lg={7}>
          {/* === PDF 转换区域 === */}
          <Card title="PDF 转换" style={{ marginBottom: 24 }}>
            {/* 模型选择（仅用于转换） */}
            <ModelSelector
              models={models}
              value={selectedModel}
              onChange={setSelectedModel}
              loading={modelsLoading}
              disabled={converting || extracting}
            />

            <Divider />

            {/* 文件上传（含自定义ID） */}
            <FileUpload onUploadSuccess={handleUploadSuccess} disabled={converting || extracting} />

            <Divider />

            {/* 转换操作按钮 */}
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              size="large"
              block
              onClick={handleStartConvert}
              loading={converting}
              disabled={!fileInfo || !selectedModel}
            >
              {converting ? '转换中...' : '开始转换（PDF → Markdown）'}
            </Button>
          </Card>

          {/* === 参数提取区域 === */}
          <Card title="参数提取" style={{ marginBottom: 24 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {/* MD文件ID选择 */}
              <div>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>
                  选择 Markdown 文件
                </Text>
                <Select
                  showSearch
                  placeholder="选择已转换的 Markdown 文件"
                  value={extractConversionId || undefined}
                  onChange={(value) => setExtractConversionId(value)}
                  disabled={extracting}
                  loading={filesLoading}
                  allowClear
                  optionFilterProp="children"
                  style={{ width: '100%' }}
                  dropdownRender={(menu) => (
                    <>
                      {menu}
                      <div style={{ padding: '8px 12px', borderTop: '1px solid #f0f0f0', textAlign: 'center' }}>
                        <Button type="link" size="small" onClick={loadMdFiles} icon={<ReloadOutlined />}>
                          刷新列表
                        </Button>
                      </div>
                    </>
                  )}
                >
                  {allFileIds.length === 0 && (
                    <Select.Option value="" disabled>
                      暂无已转换的 Markdown 文件
                    </Select.Option>
                  )}
                  {allFileIds.map((id) => (
                    <Select.Option key={id} value={id}>
                      {id}
                    </Select.Option>
                  ))}
                </Select>
                <Text type="secondary" style={{ display: 'block', marginTop: 4, fontSize: 12 }}>
                  可从上方选择已转换的文件，或手动输入文件ID
                </Text>
              </div>

              {/* 自定义ID输入 */}
              <Input
                placeholder="或手动输入文件ID（如：STM32F103C8T6）"
                value={extractConversionId}
                onChange={(e) => setExtractConversionId(e.target.value)}
                disabled={extracting}
                maxLength={50}
              />

              {/* 芯片型号输入 */}
              <div>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>
                  芯片型号（可选）
                </Text>
                <Input
                  placeholder="例如：STM32F103C8T6（会拼接到提示词尾部）"
                  value={chipModel}
                  onChange={(e) => setChipModel(e.target.value)}
                  disabled={extracting}
                  maxLength={50}
                />
                <Text type="secondary" style={{ display: 'block', marginTop: 4, fontSize: 12 }}>
                  输入的型号会拼接到提示词尾部，帮助模型精准识别参数
                </Text>
              </div>

              {/* 提取模型选择 */}
              <div>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>
                  选择提取模型
                </Text>
                <ModelSelector
                  models={models}
                  value={extractModel}
                  onChange={setExtractModel}
                  loading={modelsLoading}
                  disabled={extracting}
                />
              </div>

              {/* 提取按钮 */}
              <Button
                type="default"
                icon={<FileSearchOutlined />}
                size="large"
                block
                onClick={handleStartExtract}
                loading={extracting}
                disabled={!extractConversionId || !extractModel}
              >
                {extracting ? '提取中...' : '开始提取参数（MD → 参数）'}
              </Button>
            </Space>
          </Card>

          {/* === 下载区域 === */}
          {(mdContent || extractContent) && (
            <Card title="下载文件" style={{ marginBottom: 24 }}>
              <Space style={{ width: '100%' }} size="middle">
                {mdContent && (
                  <Button
                    icon={<DownloadOutlined />}
                    onClick={handleDownloadMd}
                    block
                  >
                    下载 Markdown
                  </Button>
                )}
                {extractContent && (
                  <Button
                    icon={<DownloadOutlined />}
                    onClick={handleDownloadExtract}
                    block
                  >
                    下载提取结果
                  </Button>
                )}
              </Space>
            </Card>
          )}

          {/* 进度展示 */}
          {conversionStatus && (
            <Card title="进度" style={{ marginBottom: 24 }}>
              <Progress
                percent={progressPercent}
                status={progressStatus}
                strokeColor={progressStatus === 'exception' ? '#ff4d4f' : undefined}
              />
              <div style={{ marginTop: 12 }}>
                <Text type="secondary">{conversionStatus.message}</Text>
              </div>
              {conversionStatus.phase === 'converting' && (
                <div style={{ textAlign: 'center', marginTop: 16 }}>
                  <Spin tip="正在转换PDF..." />
                </div>
              )}
              {conversionStatus.phase === 'extracting' && (
                <div style={{ textAlign: 'center', marginTop: 16 }}>
                  <Spin tip="正在提取技术参数..." />
                </div>
              )}
              {conversionStatus.phase === 'converted' && (
                <Alert
                  message="Markdown转换完成"
                  description="PDF已成功转换为Markdown。请在「参数提取」区域提取技术参数。"
                  type="success"
                  showIcon
                  icon={<CheckCircleOutlined />}
                  style={{ marginTop: 16 }}
                />
              )}
              {conversionStatus.phase === 'success' && (
                <Alert
                  message="全部完成"
                  description="PDF转Markdown和参数提取均已完成。"
                  type="success"
                  showIcon
                  icon={<CheckCircleOutlined />}
                  style={{ marginTop: 16 }}
                />
              )}
              {(conversionStatus.phase === 'failed' || conversionStatus.phase === 'extract_failed') && (
                <Alert
                  message="处理失败"
                  description={conversionStatus.message}
                  type="error"
                  showIcon
                  style={{ marginTop: 16 }}
                />
              )}
            </Card>
          )}
        </Col>

        {/* 中间结果展示 */}
        <Col xs={24} lg={10}>
          <ResultDisplay mdContent={mdContent} extractContent={extractContent} />
        </Col>

        {/* 右侧参数查询面板 */}
        <Col xs={24} lg={7}>
          <QueryPanel
            conversionId={fileInfo?.conversionId}
            modelName={selectedModel}
            disabled={converting || extracting}
          />
        </Col>
      </Row>
    </div>
  )
}

export default MainPage
