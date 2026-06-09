/**
 * 参数查询面板组件
 * 选择提取结果文件、输入芯片型号和参数名进行查询
 * 支持从已提取参数的文件中下拉选择
 */

import { useState, useEffect } from 'react'
import { Card, Form, Input, Button, message, Typography, Space, Spin, Select } from 'antd'
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons'
import { queryParameter, listFiles } from '../services/api'

const { Text } = Typography

function QueryPanel({ conversionId, modelName, disabled }) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [files, setFiles] = useState({ md_files: [], extract_files: [] })
  const [filesLoading, setFilesLoading] = useState(false)

  // 加载已有文件列表
  const loadFiles = async () => {
    setFilesLoading(true)
    try {
      const data = await listFiles()
      setFiles(data)
    } catch (error) {
      console.error('加载文件列表失败:', error)
    } finally {
      setFilesLoading(false)
    }
  }

  useEffect(() => {
    loadFiles()
  }, [])

  // 当传入的 conversionId 变化时更新表单（匹配 extracted 目录下的文件名格式）
  useEffect(() => {
    if (conversionId) {
      const extractId = conversionId.endsWith('_extracted') ? conversionId : `${conversionId}_extracted`
      form.setFieldsValue({ conversion_id: extractId })
    }
  }, [conversionId, form])

  const handleQuery = async (values) => {
    setLoading(true)
    setResult(null)

    try {
      const data = await queryParameter(
        values.conversion_id || conversionId,
        values.chip_model,
        values.parameter_name,
        modelName
      )

      setResult(data.parameter_value)
      message.success('查询成功')
    } catch (error) {
      message.error(`查询失败: ${error.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  // 合并去重后的文件列表（只显示已提取结果的文件）
  const allFileIds = [...new Set(files.extract_files)]

  return (
    <Card
      title="参数映射查询"
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleQuery}
        initialValues={{
          conversion_id: conversionId ? (conversionId.endsWith('_extracted') ? conversionId : `${conversionId}_extracted`) : '',
        }}
      >
        <Form.Item
          label="提取结果"
          name="conversion_id"
          rules={[{ required: true, message: '请选择提取结果文件' }]}
        >
          <Select
            showSearch
            placeholder="选择已提取参数的文件"
            disabled={disabled}
            loading={filesLoading}
            allowClear
            optionFilterProp="children"
            dropdownRender={(menu) => (
              <>
                {menu}
                <div style={{ padding: '8px 12px', borderTop: '1px solid #f0f0f0', textAlign: 'center' }}>
                  <Button type="link" size="small" onClick={loadFiles} icon={<ReloadOutlined />}>
                    刷新列表
                  </Button>
                </div>
              </>
            )}
          >
            {allFileIds.length === 0 && (
              <Select.Option value="" disabled>
                暂无已提取参数的文件
              </Select.Option>
            )}
            {allFileIds.map((id) => (
              <Select.Option key={id} value={id}>
                {id}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          label="芯片型号"
          name="chip_model"
          rules={[{ required: true, message: '请输入芯片型号' }]}
        >
          <Input placeholder="例如：STM32F103C8T6" disabled={disabled || loading} />
        </Form.Item>

        <Form.Item
          label="参数名称"
          name="parameter_name"
          rules={[{ required: true, message: '请输入参数名称' }]}
        >
          <Input placeholder="例如：工作电压、最大功耗、封装尺寸" disabled={disabled || loading} />
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            icon={<SearchOutlined />}
            loading={loading}
            disabled={disabled}
            size="large"
            block
          >
            查询参数
          </Button>
        </Form.Item>
      </Form>

      {loading && (
        <div style={{ textAlign: 'center', padding: 24 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">正在查询参数...</Text>
          </div>
        </div>
      )}

      {result !== null && !loading && (
        <div
          style={{
            marginTop: 16,
            padding: 16,
            background: '#e6f7ff',
            border: '1px solid #91d5ff',
            borderRadius: 8,
          }}
        >
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Text strong>查询结果：</Text>
            <Text style={{ fontSize: 16 }}>{result}</Text>
          </Space>
        </div>
      )}
    </Card>
  )
}

export default QueryPanel
