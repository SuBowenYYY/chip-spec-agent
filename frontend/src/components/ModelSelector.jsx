/**
 * 模型选择器组件
 * 下拉选择可用的大模型，多模态模型带标记
 */

import { Select, Form, Tag } from 'antd'

const { Option } = Select

function ModelSelector({ models, value, onChange, loading, disabled }) {
  return (
    <Form.Item label="选择模型" style={{ marginBottom: 16 }}>
      <Select
        value={value}
        onChange={onChange}
        loading={loading}
        disabled={disabled || !models || models.length === 0}
        placeholder="请选择模型"
        size="large"
        style={{ width: '100%' }}
      >
        {models?.map((model) => (
          <Option key={model.name} value={model.name}>
            <span>{model.name}</span>
            {model.multimodal && (
              <Tag color="blue" style={{ marginLeft: 8, fontSize: 11 }}>
                多模态
              </Tag>
            )}
          </Option>
        ))}
      </Select>
    </Form.Item>
  )
}

export default ModelSelector
