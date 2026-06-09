/**
 * API 调用服务层
 * 封装所有与后端的HTTP请求
 */

import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000, // 5分钟超时（大模型调用可能耗时较长）
})

/**
 * 获取可用模型列表
 * @returns {Promise<{models: Array<{name: string, multimodal: boolean}>}>}
 */
export async function getModels() {
  const response = await api.get('/models')
  return response.data.data
}

/**
 * 获取已有文件列表
 * @returns {Promise<{md_files: string[], extract_files: string[]}>}
 */
export async function listFiles() {
  const response = await api.get('/files')
  return response.data.data
}

/**
 * 上传PDF文件
 * @param {File} file - PDF文件对象
 * @param {Function} onProgress - 上传进度回调函数(percent: number)
 * @param {string} customId - 可选的自定义ID
 * @returns {Promise<{conversion_id: string, page_count: number}>}
 */
export async function uploadPDF(file, onProgress, customId = '') {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    params: customId ? { custom_id: customId } : {},
    onUploadProgress: (event) => {
      if (event.total && onProgress) {
        const percent = Math.round((event.loaded / event.total) * 100)
        onProgress(percent)
      }
    },
  })
  return response.data.data
}

/**
 * 启动PDF转换（后台异步执行）
 * @param {string} conversion_id - 转换ID
 * @param {string} model_name - 模型名称
 * @returns {Promise<{conversion_id: string}>}
 */
export async function startConvert(conversion_id, model_name) {
  const response = await api.post('/convert', {
    conversion_id,
    model_name,
  })
  return response.data.data
}

/**
 * 查询转换进度和结果
 * @param {string} conversion_id - 转换ID
 * @returns {Promise<{phase: string, progress: number, md_content: string|null, parameters: object|null}>}
 */
export async function getConversionStatus(conversion_id) {
  const response = await api.get(`/status/${conversion_id}`)
  return response.data.data
}

/**
 * 重新执行参数提取
 * @param {string} conversion_id - 转换ID
 * @param {string} model_name - 模型名称
 * @param {string} chip_model - 芯片型号
 * @returns {Promise<{parameters: object}>}
 */
export async function reExtract(conversion_id, model_name, chip_model = '') {
  const response = await api.post('/extract', {
    conversion_id,
    model_name,
    chip_model,
  })
  return response.data.data
}

/**
 * 查询参数值
 * @param {string} conversion_id - 转换ID
 * @param {string} chip_model - 芯片型号
 * @param {string} parameter_name - 参数名称
 * @param {string} model_name - 模型名称
 * @returns {Promise<{parameter_value: string}>}
 */
export async function queryParameter(conversion_id, chip_model, parameter_name, model_name) {
  const response = await api.post('/query', {
    conversion_id,
    chip_model,
    parameter_name,
    model_name,
  })
  return response.data.data
}

/**
 * 获取提示词列表
 * @returns {Promise<{md_system: string, md_user: string, extract_system: string, extract_user: string, query_system: string, query_user: string}>}
 */
export async function getPrompts() {
  const response = await api.get('/prompts')
  return response.data.data
}

/**
 * 获取Markdown文件下载URL
 * @param {string} conversion_id - 转换ID
 * @returns {string} 下载URL
 */
export function getMdDownloadUrl(conversion_id) {
  return `${API_BASE}/download/${conversion_id}/md`
}

/**
 * 获取JSON文件下载URL
 * @param {string} conversion_id - 转换ID
 * @returns {string} 下载URL
 */
export function getExtractDownloadUrl(conversion_id) {
  return `${API_BASE}/download/${conversion_id}/extract`
}
