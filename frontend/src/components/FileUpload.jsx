/**
 * 文件上传组件
 * 支持拖拽上传PDF文件，显示上传进度，支持自定义ID
 */

import { useState } from 'react'
import { Upload, Button, message, Progress, Typography, Space, Input } from 'antd'
import { InboxOutlined, FilePdfOutlined, DeleteOutlined } from '@ant-design/icons'

const { Dragger } = Upload
const { Text } = Typography

function FileUpload({ onUploadSuccess, disabled }) {
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [fileInfo, setFileInfo] = useState(null)
  const [customId, setCustomId] = useState('')

  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.pdf',
    beforeUpload: (file) => {
      // 验证文件类型
      const isPDF = file.type === 'application/pdf'
      if (!isPDF) {
        message.error('只支持PDF格式文件！')
        return Upload.LIST_IGNORE
      }

      // 验证文件大小（100MB）
      const isLt100M = file.size / 1024 / 1024 < 100
      if (!isLt100M) {
        message.error('文件大小不能超过100MB！')
        return Upload.LIST_IGNORE
      }

      // 手动上传
      handleUpload(file)
      return false
    },
    showUploadList: false,
    disabled: disabled || uploading,
  }

  const handleUpload = async (file) => {
    setUploading(true)
    setUploadProgress(0)

    try {
      const { uploadPDF } = await import('../services/api')
      const result = await uploadPDF(file, (percent) => {
        setUploadProgress(percent)
      }, customId)

      setFileInfo({
        name: file.name,
        pageCount: result.page_count,
        conversionId: result.conversion_id,
      })

      onUploadSuccess?.({
        conversionId: result.conversion_id,
        fileName: file.name,
        pageCount: result.page_count,
      })

      message.success(`文件上传成功！共 ${result.page_count} 页，ID: ${result.conversion_id}`)
    } catch (error) {
      message.error(`上传失败: ${error.response?.data?.detail || error.message}`)
    } finally {
      setUploading(false)
    }
  }

  const handleClear = () => {
    setFileInfo(null)
    setUploadProgress(0)
    setCustomId('')
    onUploadSuccess?.(null)
  }

  if (fileInfo) {
    return (
      <div
        style={{
          padding: 16,
          background: '#f6ffed',
          border: '1px solid #b7eb8f',
          borderRadius: 8,
        }}
      >
        <Space>
          <FilePdfOutlined style={{ fontSize: 24, color: '#52c41a' }} />
          <div style={{ flex: 1 }}>
            <Text strong>{fileInfo.name}</Text>
            <br />
            <Text type="secondary">
              {fileInfo.pageCount} 页
            </Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>
              ID: <Text copyable={{ text: fileInfo.conversionId }}>{fileInfo.conversionId}</Text>
            </Text>
          </div>
          <Button
            type="text"
            icon={<DeleteOutlined />}
            onClick={handleClear}
            disabled={disabled}
            danger
          />
        </Space>
      </div>
    )
  }

  return (
    <>
      {/* 自定义ID输入框 */}
      <div style={{ marginBottom: 16 }}>
        <Text type="secondary" style={{ display: 'block', marginBottom: 4, fontSize: 12 }}>
          自定义ID（可选，如芯片型号）：留空则自动生成UUID
        </Text>
        <Input
          placeholder="例如：STM32F103C8T6（留空自动生成）"
          value={customId}
          onChange={(e) => setCustomId(e.target.value)}
          disabled={disabled || uploading}
          maxLength={50}
        />
      </div>

      <Dragger {...uploadProps}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽PDF文件到此处</p>
        <p className="ant-upload-hint">仅支持PDF格式，最大100MB</p>
        {uploading && (
          <Progress
            percent={uploadProgress}
            status={uploadProgress < 100 ? 'active' : 'success'}
            style={{ marginTop: 16 }}
          />
        )}
      </Dragger>
    </>
  )
}

export default FileUpload
